"""
Usage:

python -m src.gemini-experiments.extract \
    --input-folder ./data/gemini-experiments/conversion/formatted/ \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/extraction/from-json/raw \
    --output-folder ./data/gemini-experiments/extraction/from-json/formatted \
    --input-format json \
    --aggregate-only

python -m src.gemini-experiments.extract \
    --input-folder ./data/gemini-experiments/pdf \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/extraction/from-pdf/raw \
    --output-folder ./data/gemini-experiments/extraction/from-pdf/formatted \
    --input-format pdf \
    --aggregate-only
"""

from ..templates import EXTRACTION_TEMPLATE
from ..utils.inference_gemini import run_inference
from ..utils.common import read_jsonl, read_json, parse_json
from ..utils.document_builder import generate_document
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
    template = EXTRACTION_TEMPLATE
    prompts = []
    for json_file in input_folder.glob("*.json"):
        data = read_json(json_file.resolve())
        title = data.get("article_title", "Untitled Article")
        documents = generate_document(
            data,
            include_abstract=True,
            include_intro=True,
            include_result=True,
            include_discussion=False,
            include_figures=True,
            chunk_subsections=False
        )
        for doc in documents:
            prompt = template.replace("{{paper}}", doc)
            prompts.append({
                "prompt": prompt,
                "title": title,
                "from": str(json_file)
            })

    output_path = response_folder / "prompts.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for p in prompts[:]:
            f.write(json.dumps(p) + "\n")

    return output_path

def build_prompts_from_pdfs(input_folder: Path, response_folder: Path):
    template = EXTRACTION_TEMPLATE
    text_part = template.replace("{{paper}}", "")
    prompts = []
    for pdf_file in input_folder.glob("*.pdf"):
        prompts.append({
            "prompt": text_part,
            "file_path": str(pdf_file.resolve()),
            "from": str(pdf_file)
        })

    response_path = response_folder / "prompts.jsonl"
    with open(response_path, "w", encoding="utf-8") as f:
        for p in prompts[:]:
            f.write(json.dumps(p) + "\n")

    return response_path

def aggregate_results(response_folder: Path, output_folder: Path):
    
    responses_file = response_folder / "responses.jsonl"
    results_csv = output_folder / "results.csv"

    for row in read_jsonl(responses_file):
        response = str(row["response"])
        filestem = Path(row["from"]).stem
        parsed_json = parse_json(response)[0]
        title = row.get("title") if "title" in row else parsed_json.get("paper_title")
        extractions = parsed_json["extractions"]

        results = []
        for subsection in extractions:
            subtitle = subsection["subsection"]
            triplets = subsection["triplets"]
            new_rows = [{
                "title": title,
                "subsection": subtitle,
                **triplet
            } for triplet in triplets]
            results += new_rows
        
        results_csv = output_folder / f"{filestem}.csv"
        pd.DataFrame(results).to_csv(results_csv, index=False)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-folder", type=Path, required=True)
    parser.add_argument("-c", "--config-path", type=Path, required=True)
    parser.add_argument("-r", "--response-folder", type=Path, required=True)
    parser.add_argument("-o", "--output-folder", type=Path, required=True)
    parser.add_argument("-f", "--input-format", type=str, required=True, choices=["pdf", "json"])
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

    if args.input_format in ["pdf", "json"]:
        print(f"Running extraction from file format: {args.input_format.upper()}.")
    else:
        print(f"{args.input_format} is not a supported file format, fall back to PDF.")
    build_prompts_func = dict(
        json=build_prompts,
        pdf=build_prompts_from_pdfs
    ).get(args.input_format, "pdf")

    if not args.aggregate_only:
        # 1. Build the prompts from the markdown files
        print("--- Step 1: Building Prompts ---")
        prompts_file = build_prompts_func(input_folder, response_folder)

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

    # 3. Parse results
    print("\n--- Step 3: Parsing Results ---")
    aggregate_results(response_folder, output_folder)

    print("\nPipeline finished successfully.")

if __name__ == "__main__":
    main()