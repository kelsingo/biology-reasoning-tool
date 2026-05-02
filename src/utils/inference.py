import json
import requests
import time
import argparse
import os
import yaml
import threading
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class GeminiRateLimiter:
    """Simple token bucket rate limiter for Gemini API calls."""
    # Source: https://oneuptime.com/blog/post/2026-02-17-how-to-manage-quotas-and-rate-limits-for-gemini-api-requests-in-vertex-ai/view

    def __init__(self, requests_per_minute=20):
        self.rate = requests_per_minute / 60.0  # Convert to per-second
        self.tokens = requests_per_minute
        self.max_tokens = requests_per_minute
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        """Wait until a token is available, then consume it."""
        while True:
            with self.lock:
                # Refill tokens based on elapsed time
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(
                    self.max_tokens,
                    self.tokens + elapsed * self.rate
                )
                self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                sleep_time = (1 - self.tokens) / self.rate
            # Wait a short time before trying again
            time.sleep(sleep_time)

def send_request(url, pload_config, data, request_id, rate_limiter=None):
    """Sends a single request to the vLLM server."""
    # Apply rate limiting if provided
    if rate_limiter:
        rate_limiter.acquire()
    
    headers = {"Content-Type": "application/json"}
    prompt = data.get("prompt")
    
    pload = {
        **pload_config,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    result_entry = {}
    error_entry = None

    try:
        # Reduced timeout to 300s (5 mins) to prevent massive hangs on stuck requests
        response = requests.post(url, headers=headers, json=pload, timeout=900)
        response.raise_for_status()

        response_json = response.json()
        
        # Handle cases where reasoning_content might be missing depending on model
        message = response_json["choices"][0]["message"]
        reasoning = message.get("reasoning_content", None)
        
        result_entry = {
            "request_id": request_id,
            "reasoning": reasoning,
            "response": message["content"],
            **data
        }
    except Exception as e:
        error_entry = (request_id, str(e))
        result_entry = {
            "request_id": request_id,
            "prompt": prompt,
            "response": None,
            **data
        }
    
    return request_id, result_entry, error_entry

def run_inference(config_path, input_file, results_file, rate_limit=20):
    """Run batch inference with config file using ThreadPoolExecutor.
    
    Args:
        config_path: Path to YAML config file
        input_file: Path to JSONL input file
        results_file: Path to output JSONL file
        rate_limit: Number of requests per minute (default: 20, which is 1 request every 3 seconds)
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    hostname = config.pop("hostname")
    port = config.pop("port")
    # This now controls actual thread count, not just active requests
    concurrent_requests = config.pop("concurrent_requests", 10)
    
    url = f"http://{hostname}:{port}/v1/chat/completions"
    pload_config = config
    
    dataset = []
    with open(input_file, "r") as f:
        for line in f:
            if line.strip(): # Skip empty lines
                dataset.append(json.loads(line))

    results = {}
    errors = {}
    start_time = time.time()

    # Create rate limiter (convert seconds between requests to requests per minute)
    rate_limiter = GeminiRateLimiter(requests_per_minute=rate_limit)
    
    print(f"Starting inference with {concurrent_requests} concurrent workers...")
    print(f"Rate limit: 1 request every {60/rate_limit} seconds ({rate_limit:.2f} requests/minute)")

    # USE THREADPOOLEXECUTOR INSTEAD OF RAW THREADS
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        # Submit all tasks to the pool
        future_to_req = {
            executor.submit(send_request, url, pload_config, data, i, rate_limiter): i 
            for i, data in enumerate(dataset)
        }

        # Process results as they complete
        with tqdm(total=len(dataset), desc="Processing requests") as pbar:
            for future in as_completed(future_to_req):
                request_id, result_data, error_data = future.result()
                
                results[request_id] = result_data
                if error_data:
                    errors[error_data[0]] = error_data[1]
                
                pbar.update(1)

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Write sorted results
    sorted_results = [results[i] for i in sorted(results.keys())]

    with open(results_file, "w") as outfile:
        for result in sorted_results:
            json.dump(result, outfile)
            outfile.write('\n')

    successful_requests = sum(1 for res in results.values() if res.get("response") is not None)
    total_requests = len(dataset)
    throughput = successful_requests / elapsed_time if elapsed_time > 0 else 0

    stats = {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": total_requests - successful_requests,
        "failed_request_ids": list(errors.keys()),
        "elapsed_time": elapsed_time,
        "throughput": throughput,
    }

    input_file_name = os.path.splitext(input_file)[0]
    stats_file_name = f"{input_file_name}_stats.json"

    with open(stats_file_name, "w") as f:
        json.dump(stats, f, indent=4)

    print(f"\nStatistics written to {stats_file_name}")
    print(f"Throughput: {throughput:.2f} requests/second")

    if errors:
        print("=" * 20)
        print(f"Encoutered {len(errors)} errors. First 5:")
        for i, (rid, err) in enumerate(errors.items()):
            if i >= 5: break
            print(f"ID {rid}: {err}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch inference script for vLLM server.")
    parser.add_argument("--config", type=str, required=True, help="YAML config file")
    parser.add_argument("--input-file", type=str, required=True, help="JSONL file with input prompts")
    parser.add_argument("--results-file", type=str, required=True, help="Output file for results (JSONL)")
    parser.add_argument("--rate-limit", type=int, default=20, help="Number of requests per minute (default: 20)")
    args = parser.parse_args()

    run_inference(args.config, args.input_file, args.results_file, rate_limit=args.rate_limit)