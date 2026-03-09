import json
import argparse
import sys

def build_intro_md(data):
    md = f"# {data.get('article_title', 'Untitled')}\n\n"
    
    # # Metadata
    # if 'metadata' in data:
    #     md += f"**DOI:** {data['metadata'].get('doi', 'N/A')}\n\n"
    #     authors = ", ".join(data['metadata'].get('authors', []))
    #     md += f"**Authors:** {authors}\n\n"

    # Abstract
    if 'abstract' in data:
        md += f"## Abstract\n\n{data['abstract']}\n\n"

    # Introduction
    if 'introduction' in data:
        md += f"## Introduction\n\n{data['introduction']}\n\n"
        
    return md

def build_subsection_md(sub, include_figures=True):
    md = f"### Subsection: {sub.get('title', 'Untitled Section')}\n\n"
    md += f"{sub.get('content', '')}\n\n"
    
    if include_figures:
        for fig in sub.get('figures', []):
            md += f"> {fig}\n\n"
    return md

def build_discussion_md(data):
    if 'discussion' in data:
        return f"## Discussion\n\n{data['discussion']}\n"
    return ""

def generate_document(
        data, 
        include_abstract,
        include_intro, 
        include_result, 
        include_discussion, 
        chunk_subsections,
        include_figures
    ):
    documents = []

    # Pre-build static sections
    title = f"# {data.get('article_title', 'Untitled')}\n\n"
    abstract_text = f"## Abstract\n\n{data.get('abstract', '')}\n\n"
    intro_text = f"## Introduction\n\n{data.get('introduction', '')}\n\n"

    prefix = title
    if include_abstract: prefix += abstract_text
    if include_intro: prefix += intro_text
    # intro_text = build_intro_md(data) if include_intro else ""
    disc_text = build_discussion_md(data) if include_discussion else ""
    
    results_data = data.get('results', {}).get('subsections', [])

    if include_result and chunk_subsections and results_data:
        # Strategy: Build multiple docs (Intro + 1 Subsection + Discussion)
        for sub in results_data:
            doc_content = prefix
            doc_content += build_subsection_md(sub, include_figures)
            doc_content += disc_text
            documents.append(doc_content)
    else:
        # Strategy: Build single doc (Intro + All Results + Discussion)
        doc_content = prefix
        
        if include_result:
            if not chunk_subsections:
                doc_content += "## Results\n\n"
            for sub in results_data:
                doc_content += build_subsection_md(sub, include_figures)
        
        doc_content += disc_text
        documents.append(doc_content)

    return documents

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Extraction JSON to Markdown.")
    parser.add_argument('input_file', type=str, help='Path to the input JSON file')
    parser.add_argument('--include-abstract', action='store_true', help='Include Abstract')
    parser.add_argument('--include-intro', action='store_true', help='Include Introduction')
    parser.add_argument('--include-result', action='store_true', help='Include Results section')
    parser.add_argument('--include-discussion', action='store_true', help='Include Discussion section')
    parser.add_argument('--chunk-subsections', action='store_true', help='Split results into separate documents')
    parser.add_argument('--include-figures', action='store_true', help='Include Figures')

    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        docs = generate_document(
            data, 
            args.include_abstract,
            args.include_intro, 
            args.include_result, 
            args.include_discussion, 
            args.chunk_subsections,
            args.include_figures
        )

        # Output logic
        for i, doc in enumerate(docs):
            print(f"--- DOCUMENT {i+1} START ---")
            print(doc)
            print(f"--- DOCUMENT {i+1} END ---\n")

    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{args.input_file}'.")