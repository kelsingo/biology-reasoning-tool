import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[5] / "src"))
from utils.common import read_jsonl, read_json, parse_json


def aggregate_results(response_folder: Path, output_folder: Path):
    
    responses_file = response_folder / "responses.jsonl"
    results_csv = output_folder / "results.csv"

    for row in read_jsonl(responses_file):
        response = str(row["response"])
        filestem = Path(row["from"]).stem
        title = row.get("title") if "title" in row else row.get("paper_title")
        extractions = row.get("extractions")

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
    script_dir = Path(__file__).parent.resolve()
    response_folder = script_dir
    output_folder = script_dir

    aggregate_results(response_folder, output_folder)

if __name__ == "__main__":
    main()
