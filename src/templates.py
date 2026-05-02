PDF2TEXT_TEMPLATE = """
Extract text from the provided document to populate the JSON template below. Adhere strictly to the following descriptive rules:

1.  **Content Extraction Strategy:**
    *   **Verbatim Transcription:** Extract all text exactly as it appears in the source. Do not summarize, paraphrase, or correct grammatical errors.
    *   **Citation Preservation:** Format all in-text citations to consist of numerals, including ranges and comma-separated lists. Detailed description is in the output specification.
    *   **Artifact Removal:** Eliminate layout artifacts such as page numbers, journal running heads, and hyphens caused by line breaks within words. Merge text separated by page breaks into continuous paragraphs.

2.  **Section Mapping:**
    *   **Metadata:** Extract the full article title, the Digital Object Identifier (DOI) string, and the complete list of authors as an array of individual strings.
    *   **Abstract:** Extract the bolded summary paragraph typically located at the very beginning of the article.
    *   **Introduction:** Identify and extract the body text immediately following the abstract but preceding the first distinct section heading.
    *   **Results Subsections:** Identify all distinct section headings within the main body of the text (excluding the Abstract, Introduction, and Discussion). For each section found, create an entry containing the heading title, the body text associated with that heading, and the full text of any figure captions located within or relevant to that section.
    *   **Discussion:** Extract the body text from the section explicitly labeled "Discussion."

3.  **Output Specification:**
    *   Return the output as valid, parseable JSON.
    *   Ensure the structure matches the provided schema exactly.
    *   Ensure the citation format follows the regular expression: `\(Ref: \d+(?:[,-]\d+)*\)`, which enforce reference citations like: (Ref: 3), (Ref: 3,4,9), (Ref: 30-34), (Ref: 1,5-7,12). Pattern breakdown:
```
\(        \)     Literal parentheses
Ref:            Literal text
\d+             First number (1+ digits)
(?:[,-]\d+)*    Zero or more numbers preceded by comma or hyphen
```

**JSON Template:**
```json
{
  "article_title": "String",
  "metadata": {
    "doi": "String",
    "authors": ["String", "String"]
  },
  "abstract": "String (Verbatim text)",
  "introduction": "String (Verbatim text of the introductory paragraphs)",
  "results": {
    "subsections": [
      {
        "title": "String (The section header)",
        "content": "String (Verbatim body text of this section)",
        "figures": [
            "String (Full text of Figure caption associated with this section)",
            "String (Full text of additional Figure captions, if any)"
        ]
      }
    ]
  },
  "discussion": "String (Verbatim text of the Discussion section)"
}
```
""".strip()

EXTRACTION_TEMPLATE = """
# TASK: Scientific Reasoning Extraction

## Overview

Analyze the provided scientific paper excerpt. Your task is to act as a scientific logician and extract the reasoning structures the authors use to construct their narrative. You will identify three distinct types of logical triplets: **Type Q1 (Inquiry Logic)** and **Type Q2 (Discovery Logic)** and **Type Q3 (Control Logic)**, each contains subtype(s) defined below. 

Extracting all logical structures into subtypes of Q1, Q2, and Q3.

## Definitions of Logical Structures

### Type Q1: Inquiry Logic (Experimental Setup)

**Concept:** This represents the author's planning phase. It connects a gap in knowledge to a specific action.

**Logic Flow:** 
- **Q1.1:** *Research Question/Objective [main_content] + Available Resources/Justification [context] → Operational Step [outcome]*
- **Q1.2:** *Hypothesized mechanism [main_content] + Available Resources/Justification [context] → Operational Step [outcome]*

| Component | Description | Example |
|-----------|-------------|---------|
| `main_content` (Q1.1) | The specific research question, knowledge gap, or objective driving the immediate action. It describes *what* the authors want to understand. | "To determine whether CREM functions as a negative regulator in CAR-NK cells" |
| `main_content` (Q1.2) | The hypothesized mechanism, causal relationship, or working model being tested. It describes what the authors think might be happening. | "We examined how the confined invasive state affects therapeutic response, hypothesizing that the HMGB2-high neuronal state induced by confinement may promote drug tolerance"|
| `context` | The background information, prior availability of data, or existing model systems that make the experiment feasible or relevant. For Q1.2, this may also include known biological systems or pathways that motivate the proposed mechanism. This justifies *why* this specific approach was chosen. | "Given the established function of calcium as an activator of PKA (Ref: 32,33)" |
| `outcome` | The actual methodological step, assay, or analysis performed to address the objective (Q1.1) or to test the hypothesis (Q1.2). | "we used CRISPR–Cas9 to KO CREM in two CAR-NK cell models" |

---

### Type Q2: Discovery Logic (Interpretation)

**Concept:** This represents the author's synthesis phase. It connects raw data or existing biological understanding to new biological insights.

**Logic Flow:** 
- **Q2.1:** *Research Question [main_content] + Established Theory [context] → New Insight [outcome]*
- **Q2.2:** *Mechanism [main_content] + Established Theory [context] → New Insight [outcome]*
- **Q2.3:** *Empirical Evidence [main_content] + Established Theory [context] → Confirmed Insight [outcome]*
- **Q2.4:** *Empirical Evidence [main_content] + Established Theory [context] → Hypothesized Insight [outcome]*

| Component | Description | Example |
|-----------|-------------|---------|
| `main_content` (Q2.1) | The research question or objective that the author want to understand. It is used as a starting point to generate a possible mechanistic explanation when combined with prior knowledge. | "To investigate how mechanical confinement induces HMGB2 upregulation" |
| `main_content` (Q2.2) | The hypothesized mechanism, causal relationship, or working model being tested. | "mTOR signalling has a key role downstream of taurine in leukaemia cells.  (Fig. 3a–d)" |
| `main_content` (Q2.3 or Q2.4) | The objective data points, statistical results, or morphological descriptions generated *specifically* in this study. It describes *what* was seen. | "CREM KO significantly enhanced the cytotoxicity of CAR-IL-15 NK cells in long-term cultures (Fig. 3a–d)" |
| `context` | Established biological rules, physical laws, or citations from external literature that act as a "lens" through which the research question can be addressed (Q2.1), the mechanism can be generalized, refined, or extended (Q2.2), or the raw data is viewed (Q2.3 and Q2.4). | "These patterns mirror epigenetic signatures associated with long-lived memory T cells (Ref: 40)" |
| `outcome` | The novel conclusion, hypothesis, or meaningful interpretation derived from combining the observation with the context. It describes *what it implies* for the biological system. | "This suggests that CREM acts as an inhibitory checkpoint downstream of IL-15 stimulation" |

**Note:** 
- Use Q2.3 when the authors present a strongly supported conclusion in `outcome` (e.g., "demonstrates", "confirms", "establishes").
- Use Q2.4 when the authors present a tentative interpretation or hypothesis in `outcome` (e.g., "suggests", "may", "could").

---

### Type Q3: Control Logic (Research Question)
**Concept:** This represents the author's effort to confirm a mechanism or the validity of a therapeutic strategy. It formulates questions or experimental directions to eliminate confounding factors, test alternative explanations, or assess robustness.

**Logic Flow:** 
- **Q3.1:** *Proposed Mechanism/Insight [main_content] + Established Theory [context] → Control/Validation Question [outcome]*

| Component | Description | Example |
|-----------|-------------|---------|
| `main_content` | The hypothesized mechanism, which can be a biological mechanism or effectiveness of a therapeutic strategy. | "It is therefore possible that non-genetic approaches using small-molecule inhibitors or gene silencing may identify a therapeutic window for TAUT targeting in human cells." |
| `context` | Established biological principles, known pathways, or prior findings that introduce potential confounders, alternative explanations, or limitations. | "These patterns mirror epigenetic signatures associated with long-lived memory T cells (Ref: 40)" |
| `outcome` | A research question or validation objective designed to test the validity or limitations of the proposed mechanism. It describes what needs to be ruled out or confirmed. | "We therefore tested the impact of TAUT inhibition on growth and proliferation of normal human HSPCs as well as patient-derived AML cells." |


---

## Extraction Rules

### Rule 1: Exhaustive Coverage
Every sentence or phrase from any results subsection must belong to `main_content`, `context`, or `outcome` in a Q1’s or Q2’s or Q3’s subtype. Sentences are rarely redundant—if you're tempted to skip one, reconsider where it fits.

### Rule 2: Verbatim Extraction
Extract text exactly as it appears in the excerpt:
- **Include** figure/table references (e.g., "Fig. 1a") as they indicate evidence
- **Include** reference markers (e.g., "Ref: 14") as they indicate literature support
- **Do NOT** correct grammar, rephrase, truncate mid-sentence, use "..." to shorten the text, or any other measures that compromise the exact extraction of the text.

### Rule 3: Marking Missing Components
Use `(missing)` ONLY when the text contains no explicit statement for that component:
- If authors state a result without citing literature or principles → `context` = `(missing)`
- If authors state a result without interpretation → `outcome` = `(missing)`
**Note:** The `(main_content)` is rarely missing, if you see `(context)` or `(outcome)` standalone, please recheck surrounding phrases/sentences, or consider being another triplet type. 
**Important:** Do NOT infer from general scientific knowledge. Only extract what is written.

### Rule 4: One Logical Unit Per Triplet
- Extract ONE triplet per logical unit (one goal → one method (may include multiple experiments), or one observation → one interpretation)
- If multiple observations **collectively** support ONE conclusion, group them into one Q2 triplet with combined `main_content`
- If a single experiment yields multiple **independent** observations, create separate Q2 triplets for each

### Rule 5: Negative Results Are Observations
Null findings (e.g., "X did NOT show Y", "there was no significant difference") ARE valid observations and should be extracted as Q2 `main_content`. Their interpretive significance belongs in `outcome`.

---
## Handling Special Cases

### Summary/Conclusion Statements

When authors provide concluding statements that infer a mechanism using multiple results (e.g., "Collectively...", "Together, these data suggest...", "These findings indicate..."):

**Option A (Preferred):** Create a final Q2 triplet for the subsection where:
- `main_content` = the key observations being synthesized (may repeat/combine prior observations)
- `context` = `(missing)` unless literature is cited
- `outcome` = the synthesis statement

**Option B:** If the conclusion directly follows a single observation, attach it as the `outcome` of that Q2 triplet instead of creating a new one.

However, if the concluding statements simply summarize findings rather than infer a biological understanding, treat it as a separate result. 

### Compound Sentences

If a sentence contains elements of both Q1 and Q2 (e.g., "Given X, we did Y and found Z"):
1. Determine the sentence's PRIMARY function:
- If primarily setting up an experiment → Q1
- If primarily reporting data → Q2
- If primarily resulting in a control/validation step → Q3
2. If truly balanced, split into separate triplets
3. The secondary elements can inform the appropriate field (e.g., a brief result mention in a Q1 can inform that the method was successful)

### Transitional Phrases

Pure transitions like "We next examined..." or "We also investigated..." should be:
- Incorporated into the Q1 `main_content` if they express a goal
- Incorporated into the Q2/Q3 `outcome` if they logically follows a previous result or interpretation 

---

## What NOT to Extract as Separate Triplets

- Figure legends or detailed panel descriptions (unless they contain interpretive claims)
- Repeated statements of the same finding in different words (consolidate into one triplet)
- Background information in the Introduction (only extract from Results sections)

---
## Output Format


```json
{
  "paper_title": "Title of the paper",
  "extractions": [
    {
      "subsection": "Name of subsection",
      "triplets": [
        {
          "type": "Q1",
          "main_content": "The research question or goal (verbatim) OR (missing)",
          "context": "Background/justification for approach (verbatim) OR (missing)",
          "outcome": "The method/analysis performed (verbatim) OR (missing)"
        },
        {
          "type": "Q2",
          "main_content": "The empirical observation (verbatim) OR (missing)",
          "context": "Literature or established principle (verbatim) OR (missing)",
          "outcome": "The interpretation/conclusion (verbatim) OR (missing)"
        }
      ]
    }
  ]
}
```
---

Now, analyze the provided scientific paper excerpt following these instructions.

# PAPER EXCERPT:
{{paper}}
""".strip()

TEMPLATE_PREDICTION_11 = """
# TASK: Experimental Design Generation 


## Overview
You are a biologist designing an experiment to address a specific research objective. You will be provided with a specific research question or objective (`main_content`). Your task is to logically construct the "Inquiry Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Research Goal (`main_content`)**
This is the specific knowledge gap, research question, or objective provided to you.


2. **Generate: Justification (`context`)**
You must generate the scientific background or reasoning that makes the proposed experiment feasible or relevant. This should state a method that a previous study used to address the similar objective, or describe established biological principles, properties of specific model systems, or prior knowledge that serves as the foundation for the chosen method. Please state the general scientific consensus or established biological rule, and include **real, verifiable DOI(s)** that supports the stated context. 


3. **Generate: Methodology (`outcome`)**
You must generate the specific operational step, assay, or technique that creates the data necessary to answer the Research Goal. This should be a concrete action (e.g., "perform RNA-seq," "use CRISPR-Cas9 to knockout X," "stain X with antibodies against Y", "Use cell line X,") rather than a vague statement. 


## Reasoning Flow
Your generation must follow this logical path:
*Because we want to know [main_content], and considering [context], we will perform [outcome].*


## Output Format
Return your response in the following JSON format:


```json
{
"main_content": "The provided input goal",
"context": "The scientific justification or background principle used to select the method.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific experimental method or assay performed."
}
```


**Input (Goal):**
{{main_content}}
""".strip()


TEMPLATE_PREDICTION_12 = """
# TASK: Experimental Design Generation 


## Overview
You will act as a biologist planning a scientific study. You will be provided with a hypothesized mechanism (`main_content`). Your task is to logically construct the "Inquiry Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Research Goal (`main_content`)**
This is the specific hypothesized mechanism provided to you.


2. **Generate: Justification (`context`)**
Provide the scientific reasoning or background that makes the experiment feasible. This must:
- Describe a **specific biological mechanism, pathway, or experimental precedent** directly relevant to the hypothesis 
- Describe specific model systems and/or techniques that are relevant for the chosen method
- Ensure the reasoning **naturally leads to a specific experimental approach**
Please state the general scientific consensus or established biological rule, and include **real, verifiable DOI(s)** that supports the stated context. Be specific, avoid vague statements.


3. **Generate: Methodology (`outcome`)**
You must generate the specific operational step, assay, or technique that creates the data necessary to verify or explain the Research Goal. This should be a concrete action (e.g., "perform RNA-seq," "use CRISPR-Cas9 to knockout X," "stain X with antibodies against Y", "Use cell line X,") rather than a vague statement.


## Reasoning Flow
Your generation must follow this logical path:
*Because we want to investigate [main_content], and considering [context], we will perform [outcome].*


## Output Format
Return your response in the following JSON format:


```json
{
"main_content": "The provided input goal",
"context": "The scientific justification or background principle used to select the method.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific experimental method or assay performed."
}
```


**Input (Goal):**
{{main_content}}
""".strip()


TEMPLATE_PREDICTION_21 = """
# TASK: Scientific Interpretation Generation


## Overview
You will act as a biologist who logically derives mechanism. You will be provided with a specific research question (`main_content`). Your task is to apply known quantitative result, mechanism, and/or experimental precedent to construct the "Discovery Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Research Question (`main_content`)**
This is the specific research question provided to you.


2. **Generate: Established Principle (`context`)**
You must generate the potential mechanism or quantitative findings that are relevant to answering the Research Question. This should indicate known biological principles, pathways, or quantitative findings that can engage entities in the Research Question into a coherent causal explanation. Be specific, avoid vague statements, and include **real, verifiable DOI(s)** that supports the stated context.


3. **Generate: New Insight (`outcome`)**
You must generate the novel mechanism that formulate a **causal mechanism or pathway** connecting the key entities in the Research Question using the Established Principle. This represents the derived mechanism from the biological insights in context (e.g., "Therefore, this suggests X induces Y through pathway A"). 


## Reasoning Flow
Your generation must follow this logical path:
*Since it is known that [context], we conclude that [main_content] can be explained by [outcome].*


## Output Format
Return your response in the following JSON format:


```json
{
"main_content": "The provided input observation",
"context": "The general biological rule or established theory applied to the data.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific biological interpretation or conclusion derived."
}
```


**Input (Observation):**
{{main_content}}
""".strip()

TEMPLATE_PREDICTION_22 = """
# TASK: Scientific Interpretation Generation


## Overview
You will act as a biologist generalizing understanding about biological mechanisms. You will be provided with a specific biological mechanism. Your task is to apply related biological knowledge to derive a meaningful conclusion. You must construct the "Discovery Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Biological Mechanism (`main_content`)**
This is the specific biological mechanism provided to you.


2. **Generate: Established Principle (`context`)**
You must generate the biological knowledge or quantitative findings that are relevant to the Biological Mechanism. This should indicate known biological principles, pathways, or experimental precedent that can be used to derive the pathway or a causal explanation underlying the Biological Mechanism. Be specific, avoid vague statement, and include **real, verifiable DOI(s)** that supports the stated context.


3. **Generate: New Insight (`outcome`)**
You must generate the novel mechanism that formulate a **causal mechanism or pathway** integrating the Biological Mechanism and Established Principle into a coherent causal explanation. This represents the generalized mechanism derived from the observations in context and main_content (e.g., "Therefore, this suggests the pathway is upregulated," or "This indicates a transition to a mesenchymal state"). 


## Reasoning Flow
Your generation must follow this logical path:
*Given [main_content], and since it is known that [context], we conclude that [outcome].*


## Output Format
Return your response in the following JSON format:


```json
{
"main_content": "The provided input observation",
"context": "The general biological rule or established theory applied to the data.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific biological interpretation or conclusion derived."
}
```


**Input (Observation):**
{{main_content}}
""".strip()

# Q2.3 + Q2.4
TEMPLATE_PREDICTION_23 = """
# TASK: Scientific Interpretation Generation


## Overview
You will act as a biologist analyzing raw data. You will be provided with a specific empirical observation or statistical result (`main_content`). Your task is to apply scientific theory to this observation to derive a meaningful conclusion. You must construct the "Discovery Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Empirical Observation (`main_content`)**
This is the specific data point, morphological description, or statistical finding provided to you.


2. **Generate: Established Principle (`context`)**
You must generate the "lens" through which this data is interpreted. This should:
- Indicate whether the current findings are consistent or inconsistent with similar studies AND/OR 
- Established biological rule, physical law, known functional association (e.g., "consistent with study X", "It is well established that protein X is a marker for Y," or "Changes in nuclear shape are indicative of Z" or "genomic region X is associated with function Y"). 
This provides the theoretical bridge between the raw number/image and its biological meaning. Be specific, avoid vague statements, and include **real, verifiable DOI(s)** that supports the stated context.


3. **Generate: New Insight (`outcome`)**
You must generate the novel mechanism that arises from combining the Observation with the Principle. This represents the generalized mechanism from the observations in context and main_content (e.g., "Therefore, this suggests the pathway is upregulated," or "This indicates a transition to a mesenchymal state"). 


## Reasoning Flow
Your generation must follow this logical path:
*We observed [main_content]. Since it is known that [context], we conclude that [outcome].*


## Output Format
Return your response in the following JSON format:


```json
{
"main_content": "The provided input observation",
"context": "The general biological rule or established theory applied to the data.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific biological interpretation or conclusion derived."
}
```


**Input (Observation):**
{{main_content}}
""".strip()

TEMPLATE_PREDICTION_31 = """
# TASK: Validation Question Generation


## Overview
You will act as a biologist critically evaluating a proposed biological mechanism. You are given a hypothesized mechanism (`main_content`). Your task is to generate a **control-oriented research question** by integrating this mechanism with established biological knowledge. You must construct the "Control Logic" triplet by generating the missing `context` and `outcome`.


## Logical Components


1. **Input: Biological Mechanism (`main_content`)**
This is the proposed mechanism or hypothesis to be evaluated.


2. **Generate: Established Principle (`context`)**
Provide relevant biological knowledge that introduces **constraints, alternative explanations, or known regulatory mechanisms** related to the hypothesis.
This should highlight **factors that could challenge, refine, or condition the mechanism or disvalue the hypothesis**
Be specific, avoid vague statements. Include **real, verifiable DOI(s)** that supports the stated context.


3. **Generate: New Insight (`outcome`)**
You must generate a **testable research question** that arises from combining the Biological Mechanism with the Established Principle. This question helps to rule out confounding factors, alternative pathways, or indirect effects, or to assess potential **undesired or harmful effects** of a potential therapeutic intervention where relevant. 


## Reasoning Flow
Your generation must follow this logical path:
*We propose that [main_content]. However, since it is known that [context], an important question is: [outcome]*


## Output Format
Return your response in the following JSON format:
```json
{
"main_content": "The provided input observation",
"context": "The general biological rule or established theory applied to the data.",
"references": "The DOI(s) of specific studies you cited in context.",
"outcome": "The specific biological interpretation or conclusion derived."
}
```


**Input (Observation):**
{{main_content}}
""".strip()
