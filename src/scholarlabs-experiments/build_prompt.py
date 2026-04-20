"""
Prediction prompts building for GPT and NotebookLM.

Usage:
python -m src.scholarlabs-experiments.build_prompt \
    --triplets-file "./data/gemini-experiments/triplets.selected.csv" \
    --output-folder "./data/scholarlabs-experiments/prompts/" \
"""

from .templates_scholarlabs import TEMPLATE_PREDICTION_11, TEMPLATE_PREDICTION_12, TEMPLATE_PREDICTION_21, TEMPLATE_PREDICTION_22, TEMPLATE_PREDICTION_23, TEMPLATE_PREDICTION_31
from ..utils.common import read_csv, read_jsonl, read_json, parse_json
from ..utils.document_builder import generate_document
from pathlib import Path
import pandas as pd
import os
import json
import argparse

def build_prompt(input):
    content_type = input["type"]
    query = input["main_content"]
    template = ""
    if "Q1.1" in content_type:
        template = TEMPLATE_PREDICTION_11
    elif "Q1.2" in content_type:
        template = TEMPLATE_PREDICTION_12
    elif "Q2.1" in content_type:
        template = TEMPLATE_PREDICTION_21
    elif "Q2.2" in content_type:
        template = TEMPLATE_PREDICTION_22
    elif "Q2.3" in content_type or "Q2.4" in content_type:
        template = TEMPLATE_PREDICTION_23
    elif "Q3.1" in content_type:
        template = TEMPLATE_PREDICTION_31

    # content = f"{prefix}\n\nQUERY: {query}"
    prompt = template.replace("{{main_content}}", query)
    # prompt = f"{prefix}\n\nGiven the context above:\n\n{prompt}"
    return prompt

def build_prompts(triplets_file: Path, output_folder: Path):
    """
    Docstring for build_prompts
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
        prompt = build_prompt(triplet)
        prompts.append({
            "prompt": prompt,
            **triplet
        })

    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / "prompts.csv"
    df = pd.DataFrame(prompts)
    df.to_csv(output_path, index=False, encoding="utf-8")

    return output_path

def main():
    parser = argparse.ArgumentParser(description="Build prompts for prediction.")
    parser.add_argument("--triplets-file", type=Path, required=True, help="Path to the CSV file containing triplets for Q1 and Q2.")
    parser.add_argument("--output-folder", type=Path, required=True, help="Path to the output folder for storing built prompts and results.")
    
    args = parser.parse_args()
    
    output_path = build_prompts(args.triplets_file, args.output_folder)
    print(f"Prompts have been built and saved to: {output_path}")

if __name__ == "__main__":
    main()