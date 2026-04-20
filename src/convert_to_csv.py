import json
import pandas as pd
import re
from pathlib import Path
from .utils.common import read_jsonl, read_json, parse_json, read_csv

def reformat_jsonl(input_file, output_file):
    """Convert multi-line JSON objects (blank-line separated) to proper JSONL format"""
    data = []
    buffer = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            
            if not stripped:
                if buffer:
                    try:
                        obj = json.loads('\n'.join(buffer))
                        data.append(obj)
                        buffer = []
                    except json.JSONDecodeError:
                        buffer.append(line)
            elif stripped == '}' and buffer:
                buffer.append(line)
                try:
                    obj = json.loads('\n'.join(buffer))
                    data.append(obj)
                    buffer = []
                except json.JSONDecodeError:
                    pass
            else:
                buffer.append(line)
    
    if buffer:
        try:
            obj = json.loads('\n'.join(buffer))
            data.append(obj)
        except json.JSONDecodeError:
            pass

    with open(output_file, 'w', encoding='utf-8') as f:
        for obj in data:
            f.write(json.dumps(obj) + '\n')
    
    print(f"Converted {len(data)} objects from {input_file} to {output_file}")


def convert_jsonl_to_csv(jsonl_file, csv_file):
    rows = list(read_jsonl(jsonl_file))    
    if not rows:
        print("File appears malformed, reformatting...")
        reformat_jsonl(jsonl_file, jsonl_file)
        rows = list(read_jsonl(jsonl_file))
    
    data = []
    for i in range(len(rows)):
        try: 
            row = rows[i]
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
    df.to_csv(csv_file, index=False, encoding='utf-8')

def main():
    base_dir = Path(__file__).resolve().parent.parent
    jsonl_file = base_dir / 'data' / 'gpt-experiments' / 'results.jsonl'
    csv_file = base_dir / 'data' / 'gpt-experiments' / 'results.csv'
    convert_jsonl_to_csv(jsonl_file, csv_file)
    print(f"Converted {jsonl_file} to {csv_file}")
    
if __name__ == "__main__":
    main()