# Scientific Reasoning Extraction Pipeline

A research pipeline for extracting and analyzing scientific reasoning structures from academic papers using Large Language Models. The system identifies two types of logical triplets in scientific writing:

- **Type Q1 (Inquiry Logic)**: Research Question → Context/Justification → Methodology
- **Type Q2 (Discovery Logic)**: Empirical Observation → Established Theory → Novel Interpretation

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start: PDF Extraction](#quick-start-pdf-extraction)
- [Experiments](#experiments)
  - [Experiment 1: PDF to JSON Conversion](#experiment-1-pdf-to-json-conversion)
  - [Experiment 2: Triplet Extraction](#experiment-2-triplet-extraction)
  - [Experiment 3: Triplet Prediction](#experiment-3-triplet-prediction)
- [Configuration](#configuration)
- [Other Usages](#other-usages)
- [Technical Concerns](#technical-concerns)

## Features

- **PDF Conversion**: Extract structured content (title, abstract, introduction, results, discussion) from scientific PDFs
- **Triplet Extraction**: Automatically identify Q1 and Q2 reasoning structures from papers
- **Triplet Prediction**: Generate missing components of reasoning triplets given partial information
- **Dual Input Support**: Process papers from either structured JSON or raw PDF files
- **Parallel Processing**: Concurrent API requests for efficient batch processing

---

## Project Structure

```
.
├── configs/                          # Model configuration files
│   ├── gemini-2.5-flash.yaml
│   ├── gemini-3-flash.yaml
│   └── gemini-3-pro.yaml
│
├── src/
│   ├── gemini-experiments/           # Main experiment scripts
│   │   ├── convert.py               # PDF → JSON conversion
│   │   ├── extract.py               # Triplet extraction
│   │   ├── predict.py               # Triplet prediction
│   │   └── templates.py             # Prompt templates
│   │
│   └── utils/                        # Utility modules
│       ├── inference_gemini.py      # Gemini API client
│       ├── common.py                # File I/O helpers
│       └── document_builder.py      # JSON to markdown converter
│
└── data/
    └── gemini-experiments/           # Experiment data
        ├── pdf/                     # Input PDFs
        ├── conversion/              # JSON outputs
        ├── extraction/              # Extracted triplets
        └── prediction/              # Prediction results
```

## Installation

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Setup

1. Clone the repository
```
git clone https://github.com/dourofficer/biology-reasoning-tool.git
cd biology-reasoning-tool
```

2. Install dependencies (using uv recommended)
```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv venv
source .venv/bin/activate
uv pip install vllm==0.10.2 --torch-backend=auto
uv pip install docling==2.55.1
uv pip install PyPDF2==3.0.1
```

3. Set up your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Quick Start: PDF Extraction

Extract scientific reasoning triplets directly from PDF files in one command. The following script reads all PDF files from an input folder, sends them to Gemini API with extraction prompts, parses responses into structured triplets, and finally outputs CSV files with extracted Q1/Q2 triplets:

```bash
python -m src.gemini-experiments.extract \
    --input-folder ./data/gemini-experiments/taurine \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/extraction/from-pdf/raw \
    --output-folder ./data/gemini-experiments/extraction/results \
    --input-format pdf
```

**What you should do to get started:**
1. Prepare all your PDF files from `./data/gemini-experiments/pdf`. If you want to process only 1 file, please make a directory dedicatedly for it, as the script has not conveniently support single file processing.
2. Run the script above and view the results at `./data/gemini-experiments/extraction/from-pdf/formatted`. The output folder contains CSV files with extracted Q1/Q2 triplets.

**Output:** Each PDF will generate a corresponding CSV file in the output folder with columns:
- `title`: Paper title
- `subsection`: Results subsection name
- `type`: Q1 or Q2
- `main_content`: Research question (Q1) or observation (Q2)
- `context`: Justification or established theory
- `outcome`: Methodology (Q1) or interpretation (Q2)

**Note:** For this extraction pipeline, you are **RECOMMENDED** to truncate each of your PDF file up to 10 pages only. This is designed and tested with Nature papers only, in which the main text only appear within first 10 pages. Otherwise, processing a whole paper means including so many less relevant information from appendices, which make up for a major volume in a typical published paper. In other words, while it is possible to process a whole paper with Gemini, it would result in poorer performance.

Though I did not include the truncation in the experiment pipelines, I do provide a script for you to truncate files yourself as follows:
```bash
python -m src.utils.split_pdf document.pdf --slice 1 10 -o truncated_document.pdf
```
---

## Experiments

### Experiment 1: PDF to JSON Conversion

Convert scientific PDFs into structured JSON format for downstream processing.

#### Command

```bash
python -m src.gemini-experiments.convert \
    --input-folder ./data/gemini-experiments/pdf/ \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/conversion/raw \
    --output-folder ./data/gemini-experiments/conversion/formatted
```

#### Parameters

- `--input-folder` / `-i`: Directory containing PDF files to convert
- `--config-path` / `-c`: YAML configuration file specifying Gemini model settings
- `--response-folder` / `-r`: Directory to store raw API responses and prompts
- `--output-folder` / `-o`: Directory for final structured JSON outputs
- `--aggregate-only`: (Optional) Skip API calls and only parse existing responses

#### Output Format

Each PDF produces a JSON file with the following structure:

```json
{
  "article_title": "Paper Title",
  "metadata": {
    "doi": "10.xxxx/xxxxx",
    "authors": ["Author 1", "Author 2"]
  },
  "abstract": "Verbatim abstract text...",
  "introduction": "Verbatim introduction text...",
  "results": {
    "subsections": [
      {
        "title": "Subsection Header",
        "content": "Verbatim body text...",
        "figures": ["Figure caption 1...", "Figure caption 2..."]
      }
    ]
  },
  "discussion": "Verbatim discussion text..."
}
```

#### Processing Pipeline

1. **Prompt Generation**: Creates prompts for each PDF using the `PDF2TEXT_TEMPLATE`
2. **API Inference**: Sends requests to Gemini API with concurrent workers
3. **Response Aggregation**: Parses JSON from responses and saves to output folder

---

### Experiment 2: Triplet Extraction

Extract Q1 and Q2 reasoning triplets from scientific papers.

#### From JSON Files

```bash
python -m src.gemini-experiments.extract \
    --input-folder ./data/gemini-experiments/conversion/formatted/ \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/extraction/from-json/raw \
    --output-folder ./data/gemini-experiments/extraction/from-json/formatted \
    --input-format json
```

#### From PDF Files (Direct)

```bash
python -m src.gemini-experiments.extract \
    --input-folder ./data/gemini-experiments/pdf \
    --config-path ./configs/gemini-3-pro.yaml \
    --response-folder ./data/gemini-experiments/extraction/from-pdf/raw \
    --output-folder ./data/gemini-experiments/extraction/from-pdf/formatted \
    --input-format pdf
```

#### Parameters

- `--input-folder` / `-i`: Directory containing input files (JSON or PDF)
- `--config-path` / `-c`: YAML configuration file for model settings
- `--response-folder` / `-r`: Directory for raw API responses
- `--output-folder` / `-o`: Directory for parsed CSV outputs
- `--input-format` / `-f`: Input file format (`json` or `pdf`)
- `--aggregate-only`: (Optional) Skip inference and only parse existing responses

#### Output Format

CSV files with one row per extracted triplet:

| Column | Description |
|--------|-------------|
| `title` | Paper title |
| `subsection` | Results subsection where triplet was found |
| `type` | Q1 (Inquiry Logic) or Q2 (Discovery Logic) |
| `main_content` | Research question/goal (Q1) or empirical observation (Q2) |
| `context` | Background/justification (Q1) or established theory (Q2) |
| `outcome` | Methodology (Q1) or interpretation/hypothesis (Q2) |

#### Triplet Definitions

**Type Q1 (Inquiry Logic):**
- *main_content*: "To determine whether CREM functions as a negative regulator..."
- *context*: "Given the established function of calcium as an activator of PKA..."
- *outcome*: "we used CRISPR-Cas9 to KO CREM in two CAR-NK cell models"

**Type Q2 (Discovery Logic):**
- *main_content*: "CREM KO significantly enhanced cytotoxicity (Fig. 3a-d)"
- *context*: "These patterns mirror epigenetic signatures of memory T cells (Ref: 40)"
- *outcome*: "This suggests CREM acts as an inhibitory checkpoint"

---

### Experiment 3: Triplet Prediction

Generate missing components of reasoning triplets given the first component.

#### Command

```bash
python -m src.gemini-experiments.predict \
    --paper-path ./data/gemini-experiments/conversion/formatted/mechanical.json \
    --triplets-file ./data/gemini-experiments/triplets.mechanical.csv \
    --output-folder ./data/gemini-experiments/prediction/ \
    --config-path ./configs/gemini-3-pro.yaml
```

#### Parameters

- `--paper-path` / `-p`: Path to paper JSON file (provides context via introduction)
- `--triplets-file` / `-t`: CSV file with triplets to predict (must have `type` and `main_content` columns)
- `--output-folder` / `-o`: Directory for prediction outputs
- `--config-path` / `-c`: YAML configuration file
- `--aggregate-only`: (Optional) Skip inference and only aggregate existing results

#### Input CSV Format

Your triplets CSV should contain:

```csv
title,type,subsection,main_content,context,outcome
"Paper Title",Q1,"Section Name","Research question here...","",""
"Paper Title",Q2,"Section Name","Observation here...","",""
```

#### Output Format

CSV with predicted components:

| Column | Description |
|--------|-------------|
| `title` | Paper title |
| `type` | Q1 or Q2 |
| `subsection` | Section name |
| `main_content` | Original first component (question or observation) |
| `context` | Ground truth context |
| `outcome` | Ground truth outcome |
| `predicted_context` | Model-generated context |
| `predicted_outcome` | Model-generated outcome |

#### Use Cases

- **Q1 Prediction**: Given a research question, predict the scientific justification and methodology
- **Q2 Prediction**: Given an observation, predict the theoretical framework and interpretation
- **Evaluation**: Compare predicted vs. ground truth components for model assessment

---

## Configuration

Model configurations are stored as YAML files in the `configs/` directory.

### Example: Gemini 3 Pro

```yaml
model_name: gemini-3-pro-preview
topP: 
topK: 
thinkingConfig:
  thinkingBudget: 64000
concurrent_requests: 5
temperature: 1.0
```

### Available Configurations

- `configs/gemini-2.5-flash.yaml` - Fast, efficient model
- `configs/gemini-3-flash.yaml` - Balanced performance
- `configs/gemini-3-pro.yaml` - Highest quality, extended reasoning

### Key Parameters

- `model_name`: Gemini model identifier
- `temperature`: Sampling temperature (0.0-2.0)
- `topP`: Nucleus sampling threshold
- `topK`: Top-k sampling limit
- `thinkingConfig.thinkingBudget`: Token budget for extended thinking
- `concurrent_requests`: Number of parallel API requests

## Other Usages

### 1. PDF to Text Conversion

Convert scientific PDFs to structured markdown using Docling:

#### Single File Conversion

```bash
python -m src.pdf2text.pdf2text input.pdf output_dir/
```

#### Batch Processing

```bash
# Edit paths in src/pdf2text/run_batch.sh
cd src/pdf2text
bash run_batch.sh
```

**Configuration:**
- Modify `PDF_DIR`, `MD_DIR`, `JSON_DIR` in `run_batch.sh`
- Set `CUDA_VISIBLE_DEVICES` to select GPU
- Uses Docling pipeline with OCR and table structure detection

#### PDF Layout Annotation (Visualization)

Visualize predicted layout elements:

```bash
# Annotate layout predictions
CUDA_VISIBLE_DEVICES=1 python -m src.pdf2text.annotate_pdf \
    input_file.pdf output_file.pdf

# Show only unmasked components (for OCR debugging)
CUDA_VISIBLE_DEVICES=1 python -m src.pdf2text.annotate_pdf \
    input_file.pdf output_file.pdf --mask
```

---

### 2. vLLM Server Setup

Host open-source LLMs locally for inference. Examples from `scripts/vllm.sh`:

#### Serving GPT-OSS-20B (1x A100 40GB)

```bash
vllm serve openai/gpt-oss-20b \
    --port 8881 \
    --gpu-memory-utilization 0.90 \
    --tensor-parallel-size 1 \
    --disable-log-requests \
    --max-model-len 32000 \
    --max-num-batched-tokens 16000 \
    --generation-config auto
```

#### Serving GPT-OSS-120B (2x A100 80GB)

```bash
vllm serve openai/gpt-oss-120b \
    --tensor-parallel-size 2 \
    --port 8881 \
    --disable-log-requests \
    --async-scheduling
```

#### Serving Gemma-3-27B (1x A100 80GB)

```bash
vllm serve unsloth/gemma-3-27b-it \
    --port 8881 \
    --gpu-memory-utilization 0.98 \
    --tensor-parallel-size 1 \
    --disable-log-requests \
    --max-model-len 32000 \
    --max-num-batched-tokens 16000 \
    --generation-config auto
```

#### Serving Qwen3-32B with Reasoning

```bash
vllm serve Qwen/Qwen3-32B \
    --port 8881 \
    --tensor-parallel-size 2 \
    --disable-log-requests \
    --reasoning-parser qwen3
```

#### Test Request

```bash
curl -X POST http://34.12.60.86:8881/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "user", "content": "What are the applications of LLMs in biology research?"}
        ],
        "max_tokens": 1000,
        "temperature": 0.9,
        "reasoning_effort": "high"
    }'
```

---

### 3. Extract Reasoning Structures (Benchmark Pipeline)

Alternative extraction pipeline supporting vLLM-hosted models:

#### From JSON (Structured Papers)

```bash
python -m src.benchmark.extract \
    --input-folder ./data/casestudies/json \
    --output-folder ./data/output/gpt-oss-120b \
    --config-path ./configs/gpt-oss-120b.yaml \
    --input-format json
```

#### From Markdown Files

```bash
python -m src.benchmark.extract \
    --input-folder ./data/casestudies/markdown \
    --output-folder ./data/output/markdown-results \
    --config-path ./configs/gpt-oss-20b.yaml \
    --input-format markdown
```

**Key Differences from Gemini Pipeline:**
- Uses `src/utils/inference.py` for vLLM-hosted models
- Does not support direct document (pdf/images/etc) processing yet
- Supports OpenAI-compatible API endpoints
- Different prompt templates (`TEMPLATE_SUBPROBLEM_2b`, `TEMPLATE_SUBPROBLEM_2c`)

---

### 4. Triplet Prediction - Deprecated (Benchmark Pipeline)

Predict missing triplet components using vLLM models:

```bash
python -m src.prediction.predict \
    --paper-path ./data/casestudies/json/mechanical.json \
    --triplets-file ./data/casestudies/triplets.mechanical.tsv \
    --output-folder ./data/output/prediction/gpt-oss-120b \
    --config-path ./configs/gpt-oss-120b.yaml
```

**Input Format (TSV):**
```tsv
type	subsection	main	context	outcome
Q1	Section Name	Research question here...		
Q2	Section Name	Observation here...		
```

**Output:** CSV with `predicted_context` and `predicted_outcome` columns.

**Note:** This script is outdated, use it at your own risks.

---

### 5. Batch Inference Testing

Test batch inference on sample prompts, in which the throughput is controlled by `concurrent_requests` in config files:

#### Using vLLM Models

```bash
python -m src.utils.inference \
    --config configs/gpt-oss-20b.yaml \
    --input-file data/inference_samples/prompts.jsonl \
    --results-file data/inference_samples/results.jsonl
```

#### Using Gemini API

```bash
export GEMINI_API_KEY="your-api-key"
python -m src.utils.inference_gemini \
    --config configs/gemini-2.5-flash.yaml \
    --input-file data/inference_samples/prompts.jsonl \
    --results-file data/inference_samples/results_gemini.jsonl
```

**Input Format (JSONL):**
```jsonl
{"prompt": "Create a table of contents for this article..."}
{"prompt": "Persuade the reader to sign up..."}
{"prompt": "Rephrase this sentence...", "file_path": "optional_attachment.pdf"}
```

**Output:** JSONL with `request_id`, `reasoning`, `response`, and statistics file with throughput metrics.

### 6. vLLM Model Configs

Located in `configs/` directory for self-hosted models:

```yaml
# configs/gpt-oss-120b.yaml
model: openai/gpt-oss-120b
temperature: 0.9
reasoning_effort: high          # For reasoning-capable models

hostname: 34.12.60.86          # vLLM server address
port: 8881
concurrent_requests: 2          # Parallel requests
```

**Available vLLM Configs:**
- `configs/gpt-oss-20b.yaml` - 20B parameter model
- `configs/gpt-oss-120b.yaml` - 120B parameter reasoning model
- `configs/gemma-3-27b-it.yaml` - Gemma 3 instruction-tuned
- `configs/qwen3-32b.yaml` - Qwen3 with reasoning parser

---

### Notes on Pipeline Differences

**Gemini Experiments (`src/gemini-experiments/`):**
- Designed for cloud Gemini API
- Support PDF processing with multimodal inputs

**Benchmark Pipeline (`src/benchmark/`, `src/prediction/`):**
- Designed for self-hosted vLLM models
- Does not support PDF processing, resort to its own PDF2Text conversion pipeline using `docling`.
- More control over model deployment

Both pipelines produce compatible output formats for analysis.

## Technical Concerns

### Inference throughput
For more optimized batch processing, you may want to adopt the official script: https://github.com/vllm-project/vllm/blob/main/examples/offline_inference/batch_llm_inference.py

Instead, in this repo, I opted for building a minimal yet more configurable script for handling input-output and steaming. Throughput varies by model, context length, and hardware. In your config file, be aware of `concurrent_requests` in configs to optimize for your setup. The higher `concurent_requests`, the larger the throughput, as well as the higher chance of timeout. You may want to add `timeout` config as each model has different average response time.

### PDF2Text
The local pipeline does not process PDF directly because open models cannot work with PDF natively. Instead it first OCR the PDF to text before using LLM.
1. The quality of OCR-ed text may affect the quality of extraction and 
2. Open-source solutions are not reliable as proprietary models (Gemini/GPT/etc). Rough observation: gpt-oss-20b can extract 20 triples with OCR-ed text from the best opensource solution I found, meanwhile it can extract 25 triples with clean OCR-text from Gemini.

Currently I use Gemini to do the OCR. I made this decision because: (1) I want to focus on the capability of LLM at extracting first, having noisy input data would make my judgement not clear, and (2) I suppose that when we scale up our experiment with thousands of papers, they will all be open-access paper with clean text version, hence no need for pre-processing PDF->text.
