#!/bin/bash
CSV_FILE="../../data/triplets.csv"

declare -A paper_urls
paper_urls["Mechanical confinement governs phenotypic plasticity in melanoma"]="https://notebooklm.google.com/notebook/183a759a-a3a7-47fc-96ad-29f738924a58" 
paper_urls["Taurine from tumour niche drives glycolysis to promote leukaemogenesis"]="https://notebooklm.google.com/notebook/2d3a4ed3-ba3e-4cfc-a252-51b8a7917273"  
paper_urls["From genotype to phenotype with 1,086 near telomere-to-telomere yeast genomes"]="https://notebooklm.google.com/notebook/93fc03a0-a8a5-4427-89e1-10dea9c47b2f"
paper_urls["Whole-genome landscapes of 1,364 breast cancers"]="https://notebooklm.google.com/notebook/237ddf89-e1fc-45df-a253-f1d13ab0460f"  
paper_urls["An ultrasensitive method for detection of cell-free RNA"]="https://notebooklm.google.com/notebook/dcb3615f-f1bd-4d30-8be6-1031247b518f"   
paper_urls["Custom CRISPR–Cas9 PAM variants via scalable engineering and machine learning"]="https://notebooklm.google.com/notebook/2f226afc-b478-40be-95d8-bf70ceffaeb3"

tail -n +2 "$CSV_FILE" | while IFS=',' read -r main_content paper
do
    # Trim whitespace from the paper name
    paper=$(echo "$paper" | xargs)
    
    # Get the URL from our mapping
    url=${paper_urls[$paper]}

    # Skip if the paper name doesn't match our map
    if [ -z "$url" ]; then
        echo "Warning: No URL found for paper: $paper"
        continue
    fi

    echo "Sending question from paper: $paper"

    # 3. Construct JSON and send the POST request
    curl -X POST http://localhost:3000/ask \
      -H "Content-Type: application/json" \
      -d "$(jq -n --arg q "$main_content" --arg u "$url" '{question: $q, notebook_url: $u}')"

    echo -e "\n---"
done