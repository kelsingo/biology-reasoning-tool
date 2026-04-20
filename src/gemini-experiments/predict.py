"""
Prediction pipeline for Q1 and Q2 triplets.

Usage:
python -m src.gemini-experiments.predict \
    --paper-path "./data/gemini-experiments/conversion/formatted/" \
    --triplets-file "./data/gemini-experiments/triplets.mechanical.csv" \
    --output-folder "./data/gemini-experiments/prediction/results/taurine" \
    --config-path "./configs/gemini-3-pro.yaml" \ 
    --output-file "results_v0"
"""

from ..templates import TEMPLATE_PREDICTION_11, TEMPLATE_PREDICTION_12, TEMPLATE_PREDICTION_2
from ..utils.inference_gemini import run_inference
from ..utils.common import read_jsonl, read_json, parse_json, read_csv
from ..utils.document_builder import generate_document
from pathlib import Path
import pandas as pd
import os
import json
import argparse

def build_prompt(paper_path, input):
    paper_title = input["paper"]
    print(f"Building prompt for paper: {paper_title}")
    paper = read_json(paper_path / f"{paper_title}.json")
    prefix = generate_document(
        paper,
        include_abstract=False, # Not include abstract because of data contamination.
        include_intro=True,
        include_result=False,
        chunk_subsections=False,
        include_figures=False,
        include_discussion=False
    )[0].strip()
    content_type = input["type"]
    query = input["main_content"]
    template = TEMPLATE_PREDICTION_11 if "Q1.1" in content_type else TEMPLATE_PREDICTION_12 if "Q1.2" in content_type else TEMPLATE_PREDICTION_2

    content = f"{prefix}\n\nQUERY: {query}"
    prompt = template.replace("{{main_content}}", content)
    return prompt

def build_prompts(paper_path: Path, triplets_file: Path, output_folder: Path):
    """
    Docstring for build_prompts
    
    :param paper_path: Path to a paper in JSON format.
    :type paper_path: Path
    
    :param triplets_file: Path to a the prepared curated file of triplets for Q1 and Q2,
        in which Q1 = (research question, literature, experiment)
        and      Q2 = (experiment result, literature, suggested hypothesis)
    :type triplets_file: Path
    
    :param output_folder: The output folder storing built prompts for entries in 
        the triplets_file. There will be adjustment depending on the entry type 
        (Q1 or Q2). The responses for calling API and aggregated results will also 
        be stored in this directory.
    :type output_folder: Path
    """
    triplets = read_csv(triplets_file)
    prompts = []
    for triplet in triplets:
        prompt = build_prompt(paper_path, triplet)
        prompts.append({
            "prompt": prompt,
            **triplet
        })

    output_path = output_folder / "prompts.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for p in prompts[:]:
            f.write(json.dumps(p) + "\n")

    return output_path

def aggregate_results(output_folder: Path, output_file: str):
    responses_file = output_folder / "responses.jsonl"
    results_csv = output_folder / output_file

    results = []
    rows = list(read_jsonl(responses_file))
    for i in range(len(rows)):
        try: 
            row = rows[i]
            response = str(row["response"])
            parsed_json = parse_json(response)[0]
            new_row = dict(
                title=row.get("title"),
                type=row.get("type"),
                subsection=row.get("subsection"),
                main_content=row.get("main_content"),
                context=row.get("context"),
                outcome=row.get("outcome"),
                predicted_reference=parsed_json.get("reference"),
                predicted_context=parsed_json["context"],
                predicted_outcome=parsed_json["outcome"]
            )
            results.append(new_row)
        except Exception as e:
            print(f"Error at row {i}: {e}")
    pd.DataFrame(results).to_csv(results_csv, index=False)
    return results_csv

def main():
    parser = argparse.ArgumentParser(
        description="Build prompts and aggregate prediction results for Q1/Q2 triplets"
    )
    parser.add_argument(
        "-p", "--paper-path",
        type=Path,
        required=True,
        help="Path to paper in JSON format"
    )
    parser.add_argument(
        "-t", "--triplets-file",
        type=Path,
        required=True,
        help="Path to TSV file containing curated triplets for Q1 and Q2"
    )
    parser.add_argument(
        "-o", "--output-folder",
        type=Path,
        required=True,
        help="Path to output folder for prompts, responses, and results"
    )
    parser.add_argument(
        "-c", "--config-path",
        type=Path,
        required=True,
        help="Path to model configuration file"
    )
    parser.add_argument(
        "-of", "--output-file",
        required=True, 
        help="results filename"
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip prompt building and inference, only aggregate existing results"
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    paper_path = args.paper_path.resolve()
    triplets_file = args.triplets_file.resolve()
    output_folder = args.output_folder.resolve()
    config_path = args.config_path.resolve()
    output_file = args.output_file

    responses_file = output_folder / "responses.jsonl"
    responses_file.parent.mkdir(parents=True, exist_ok=True)

    if not args.aggregate_only:
        # 1. Build the prompts from the paper and triplets
        print("--- Step 1: Building Prompts ---")
        print(f"Paper: {paper_path}")
        print(f"Triplets: {triplets_file}")
        prompts_file = build_prompts(paper_path, triplets_file, output_folder)

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

    # 3. Aggregate results
    print("\n--- Step 3: Aggregating Results ---")
    results_csv = aggregate_results(output_folder, output_file)
    print(f"Saving results to csv at: {results_csv}, filename {output_file}")

    print("\nPipeline finished successfully.")


if __name__ == "__main__":
    main()