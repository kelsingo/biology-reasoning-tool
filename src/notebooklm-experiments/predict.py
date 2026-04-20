import csv
import requests
import json
import time
import pandas as pd # Ensure pandas is imported for aggregate_results
from pathlib import Path
from ..templates import TEMPLATE_PREDICTION_1, TEMPLATE_PREDICTION_2
from ..utils.common import parse_json, read_csv, read_json, read_jsonl

# --- DYNAMIC PATH SETUP ---
# SCRIPT_DIR is where this actual file lives
SCRIPT_DIR = Path(__file__).resolve().parent
# Make sure we look for the CSV in the same folder as the script
CSV_FILE = SCRIPT_DIR / 'triplets.csv' 
RESULTS_FILE = SCRIPT_DIR / "responses_notebooklm.jsonl"
API_URL = 'http://localhost:3000/ask'

PAPER_URLS = {
    "Mechanical confinement governs phenotypic plasticity in melanoma": "https://notebooklm.google.com/notebook/183a759a-a3a7-47fc-96ad-29f738924a58",
    "Taurine from tumour niche drives glycolysis to promote leukaemogenesis": "https://notebooklm.google.com/notebook/2d3a4ed3-ba3e-4cfc-a252-51b8a7917273",
    "From genotype to phenotype with 1,086 near telomere-to-telomere yeast genomes": "https://notebooklm.google.com/notebook/93fc03a0-a8a5-4427-89e1-10dea9c47b2f",
    "Whole-genome landscapes of 1,364 breast cancers": "https://notebooklm.google.com/notebook/237ddf89-e1fc-45df-a253-f1d13ab0460f",
    "An ultrasensitive method for detection of cell-free RNA": "https://notebooklm.google.com/notebook/dcb3615f-f1bd-4d30-8be6-1031247b518f",
    "Custom CRISPR–Cas9 PAM variants via scalable engineering and machine learning": "https://notebooklm.google.com/notebook/2f226afc-b478-40be-95d8-bf70ceffaeb3"
}

def aggregate_results(output_folder: Path, output_file: str):
    # Use the RESULTS_FILE global or ensure path is absolute
    responses_file = output_folder / "responses_notebooklm.jsonl"
    
    if not responses_file.exists():
        print(f"Aggregation Error: {responses_file} not found. No data to aggregate.")
        return None

    results_csv = output_folder / output_file
    results = []
    
    print(f"--- Aggregating responses from {responses_file} ---")
    rows = list(read_jsonl(responses_file))
    
    for i, row in enumerate(rows):
        try: 
            raw_response = str(row.get("response", ""))
            parsed_data = parse_json(raw_response)
            prediction = parsed_data[0] if isinstance(parsed_data, list) and parsed_data else parsed_data
            
            # Map fields safely
            new_row = {
                "title": row.get("title", row.get("paper")),
                "type": row.get("type", row.get("content_type")),
                "subsection": row.get("subsection"),
                "main_content": row.get("main_content"),
                "context": row.get("context"),
                "outcome": row.get("outcome"),
                "predicted_context": prediction.get("context") if isinstance(prediction, dict) else None,
                "predicted_outcome": prediction.get("outcome") if isinstance(prediction, dict) else None
            }
            results.append(new_row)
        except Exception as e:
            print(f"Error at row {i}: {e}")

    if results:
        pd.DataFrame(results).to_csv(results_csv, index=False)
        print(f"Successfully created: {results_csv}")
    return results_csv

def send_request():
    if not CSV_FILE.exists():
        print(f"Error: {CSV_FILE} not found in {SCRIPT_DIR}")
        return

    try:
        reader = read_csv(CSV_FILE)
        print(f"--- Starting processing ---")
        
        with open(RESULTS_FILE, mode='a', encoding='utf-8') as f_out:
            for i, row in enumerate(reader, start=1):
                paper_name = row.get('paper', '').strip()
                content_type = row.get('content_type', '').strip()
                
                if not paper_name: continue

                template = TEMPLATE_PREDICTION_1 if ("Q1.1" in content_type or "Q1.2" in content_type) else TEMPLATE_PREDICTION_2
                question = template.replace("{{main_content}}", row.get('main_content', '').strip())
                
                url = PAPER_URLS.get(paper_name)
                if not url:
                    print(f"Row {i}: Paper '{paper_name[:20]}...' not in URL mapping. Skipping.")
                    continue

                print(f"Row {i}: Sending request...")
                try:
                    response = requests.post(API_URL, json={"question": question, "notebook_url": url}, timeout=120)
                    if response.status_code == 200:
                        api_data = response.json()
                        record = {**row, "response": api_data.get("answer", "")}
                        f_out.write(json.dumps(record) + '\n')
                        f_out.flush()
                        print(f"Row {i}: Success!")
                    else:
                        print(f"Row {i}: Failed with status {response.status_code}")
                except Exception as e:
                    print(f"Row {i}: Request error: {e}")
    except Exception as e:
        print(f"General Error in send_request: {e}")

if __name__ == "__main__":
    send_request() 
    aggregate_results(SCRIPT_DIR, "final_results_notebooklm.csv")