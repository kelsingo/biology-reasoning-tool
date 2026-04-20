"""
Usage:
python -m src.gemini-experiments.convert \
    --input-folder ./data/gemini-experiments/pdf/ \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/conversion/raw \
    --output-folder ./data/gemini-experiments/conversion/formatted \
    --aggregate-only
"""


from ..utils.inference_gemini import run_inference
from ..utils.common import read_jsonl, read_json, parse_json
from .templates import PDF2TEXT_TEMPLATE
from pathlib import Path
import pandas as pd
import os
import json
import argparse


def build_prompts(input_folder: Path, response_folder: Path):
    """
    Finds all .md files in a folder, creates a prompt for each, and saves them
    to a 'tmp.jsonl' file in the same folder.
    
    Args:
        input_folder: The path to the folder containing the .md files.
    """
    template = PDF2TEXT_TEMPLATE
    prompts = []
    for pdf_file in input_folder.glob("*.pdf"):
        prompts.append({
            "prompt": template,
            "file_path": str(pdf_file.resolve())
        })

    response_path = response_folder / "prompts.jsonl"
    with open(response_path, "w", encoding="utf-8") as f:
        for p in prompts[:]:
            f.write(json.dumps(p) + "\n")

    return response_path


def aggregate_results(response_folder: Path, output_folder: Path):
    responses_file = response_folder / "responses.jsonl"
    data = read_jsonl(responses_file)
    for row in data:
        try:
            response = row["response"]
            parsed = parse_json(response)[0]
            filestem = Path(row["file_path"]).stem
            output_file = output_folder / f"{filestem}.json"
            with open(output_file, "w") as f:
                json.dump(parsed, f, indent=4)
        except:
            print(f"Cannot parse json from response of file {row['file_path']}!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-folder", type=Path, required=True)
    parser.add_argument("-c", "--config-path", type=Path, required=True)
    parser.add_argument("-r", "--response-folder", type=Path, required=True)
    parser.add_argument("-o", "--output-folder", type=Path, required=True)
    parser.add_argument("--aggregate-only", action='store_true')
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    input_folder = args.input_folder.resolve()
    response_folder = args.response_folder.resolve()
    output_folder = args.output_folder.resolve()
    config_path = args.config_path.resolve()

    responses_file = response_folder / "responses.jsonl"
    responses_file.parent.mkdir(parents=True, exist_ok=True)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    if not args.aggregate_only:
        # 1. Build the prompts from the markdown files
        print("--- Step 1: Building Prompts ---")
        prompts_file = build_prompts(input_folder, response_folder)

        # 2. Run the inference using the generated prompts
        print("\n--- Step 2: Running Inference ---")
        print(f"Using config: {config_path}")
        print(f"Input prompts: {prompts_file}")
        print(f"Saving responses to: {responses_file}")
        
        run_inference(
            str(config_path),
            str(prompts_file),
            str(responses_file),
            api_key=api_key
        )
    
    aggregate_results(response_folder, output_folder)
        
if __name__ == "__main__":
    main()