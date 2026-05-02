import json
import pandas as pd
import re
import csv
from pathlib import Path
from .utils.common import read_jsonl, read_json, parse_json, read_csv
import os

def reformat_jsonl(input_file, output_file):
    """Convert multi-line JSON objects (blank-line separated) to proper JSONL format"""
    data = []
    buffer = []
    brace_count = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            buffer.append(line)
            brace_count += stripped.count('{') - stripped.count('}')

            if brace_count == 0 and buffer:
                raw = '\n'.join(buffer)
                raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)  # fix invalid escape sequences
                try:
                    obj = json.loads(raw)
                    data.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse object: {e}\nContent: {raw[:200]}")
                buffer = []

    if buffer:
        raw = '\n'.join(buffer)
        raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
        try:
            obj = json.loads(raw)
            data.append(obj)
        except json.JSONDecodeError as e:
            print(f"Failed to parse trailing object: {e}\nContent: {raw[:200]}")

    with open(output_file, 'w', encoding='utf-8') as f:
        for obj in data:
            f.write(json.dumps(obj) + '\n')

    print(f"Converted {len(data)} objects from {input_file} to {output_file}")


def convert_jsonl_to_csv(jsonl_file, csv_file):
    temp_file = str(jsonl_file) + ".tmp"
    reformat_jsonl(jsonl_file, temp_file)
    rows = list(read_jsonl(temp_file))

    data = []
    for i, row in enumerate(rows):
        try:
            new_row = dict(
                main_content=row.get("main_content"),
                gpt_references=row.get("references"),
                gpt_context=row.get("context"),
                gpt_outcome=row.get("outcome")
            )
            data.append(new_row)
        except Exception as e:
            print(f"Error at row {i}: {e}")

    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)  # force quoting
    os.remove(temp_file)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    jsonl_file = base_dir / 'data' / 'gpt-experiments' / 'results.jsonl'
    csv_file = base_dir / 'data' / 'gpt-experiments' / 'results.csv'
    convert_jsonl_to_csv(jsonl_file, csv_file)
    print(f"Converted {jsonl_file} to {csv_file}")

if __name__ == "__main__":
    main()