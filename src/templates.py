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

Analyze the provided scientific paper excerpt. Your task is to act as a scientific logician and extract the reasoning structures the authors use to construct their narrative. You will identify two distinct types of logical triplets: **Type Q1 (Inquiry Logic)** and **Type Q2 (Discovery Logic)**.

Process the text subsection by subsection, extracting all logical structures.

---

## Definitions of Logical Structures

### Type Q1: Inquiry Logic (The Experimental Setup)

**Concept:** This represents the author's planning phase. It connects a gap in knowledge to a specific action.

**Logic Flow:** *Desire to Know [main_content] + Available Resources/Justification [context] → Operational Step [outcome]*

| Component | Description | Example |
|-----------|-------------|---------|
| `main_content` | The specific research question, knowledge gap, or objective driving the immediate action. It describes *what* the authors want to understand. | "To determine whether CREM functions as a negative regulator in CAR-NK cells" |
| `context` | The background information, prior availability of data, or existing model systems that make the experiment feasible or relevant. This justifies *why* this specific approach was chosen. | "Given the established function of calcium as an activator of PKA (Ref: 32,33)" |
| `outcome` | The actual methodological step, assay, or analysis performed to achieve the goal. | "we used CRISPR–Cas9 to KO CREM in two CAR-NK cell models" |

---

### Type Q2: Discovery Logic (The Result Interpretation)

**Concept:** This represents the author's synthesis phase. It connects raw data to new biological understanding.

**Logic Flow:** *Empirical Evidence [main_content] + Established Theory [context] → New Insight [outcome]*

| Component | Description | Example |
|-----------|-------------|---------|
| `main_content` | The objective data points, statistical results, or morphological descriptions generated *specifically* in this study. It describes *what* was seen. | "CREM KO significantly enhanced the cytotoxicity of CAR-IL-15 NK cells in long-term cultures (Fig. 3a–d)" |
| `context` | Established biological rules, physical laws, or citations from external literature that act as a "lens" through which the raw data is viewed. | "These patterns mirror epigenetic signatures associated with long-lived memory T cells (Ref: 40)" |
| `outcome` | The novel conclusion, hypothesis, or meaningful interpretation derived from combining the observation with the context. It describes *what it implies* for the biological system. | "This suggests that CREM acts as an inhibitory checkpoint downstream of IL-15 stimulation" |

---

## Extraction Rules

### Rule 1: Exhaustive Coverage
Every sentence from any results subsection must belong to `main_content`, `context`, or `outcome` of either a Q1 or Q2 triplet. Sentences are rarely redundant—if you're tempted to skip one, reconsider where it fits.

### Rule 2: Verbatim Extraction
Extract text exactly as it appears in the excerpt:
- **Include** figure/table references (e.g., "Fig. 1a") as they indicate evidence
- **Include** reference markers (e.g., "Ref: 14") as they indicate literature support
- **Do NOT** correct grammar, rephrase, truncate mid-sentence, use "..." to shorten the text, or any other measures that compromise the exact extraction of the text.

### Rule 3: Marking Missing Components
Use `(missing)` ONLY when the text contains no explicit statement for that component:
- If authors state a method without an explicit goal → `main_content` = `(missing)`
- If authors state a result without citing literature or principles → `context` = `(missing)`
- If authors state a result without interpretation → `outcome` = `(missing)`

**Important:** Do NOT infer from general scientific knowledge. Only extract what is written.

### Rule 4: One Logical Unit Per Triplet
- Extract ONE triplet per logical unit (one goal → one method, or one observation → one interpretation)
- If a single experiment yields multiple **independent** observations, create separate Q2 triplets for each
- If multiple observations **collectively** support ONE conclusion, group them into one Q2 triplet with combined `main_content`

### Rule 5: Negative Results Are Observations
Null findings (e.g., "X did NOT show Y", "there was no significant difference") ARE valid observations and should be extracted as Q2 `main_content`. Their interpretive significance belongs in `outcome`.

---

## Handling Special Cases

### Summary/Conclusion Statements

When authors provide concluding statements (e.g., "Collectively...", "Together, these data suggest...", "These findings indicate..."):

**Option A (Preferred):** Create a final Q2 triplet for the subsection where:
- `main_content` = the key observations being synthesized (may repeat/combine prior observations)
- `context` = `(missing)` unless literature is cited
- `outcome` = the synthesis statement

**Option B:** If the conclusion directly follows a single observation, attach it as the `outcome` of that Q2 triplet instead of creating a new one.

### Compound Sentences

If a sentence contains elements of both Q1 and Q2 (e.g., "Given X, we did Y and found Z"):

1. Determine the sentence's PRIMARY function:
   - If primarily setting up an experiment → Q1
   - If primarily reporting data → Q2
2. If truly balanced, split into two triplets
3. The secondary elements can inform the appropriate field (e.g., a brief result mention in a Q1 can inform that the method was successful)

### Transitional Phrases

Pure transitions like "We next examined..." or "We also investigated..." should be:
- Incorporated into the Q1 `main_content` if they express a goal
- Marked as `main_content` = `(missing)` if they only introduce a method with no stated purpose

---

## What NOT to Extract as Separate Triplets

- Figure legends or detailed panel descriptions (unless they contain interpretive claims)
- Pure statistical method details without biological interpretation
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

## Decision Flowchart

```
For each sentence/clause, ask:

1. Does it state what the authors WANTED to know or do?
   → Yes: This is Q1 main_content
   → No: Continue to #2

2. Does it state HOW something was done (method/analysis)?
   → Yes: This is Q1 outcome
   → No: Continue to #3

3. Does it report DATA or OBSERVATIONS from this study?
   → Yes: This is Q2 main_content
   → No: Continue to #4

4. Does it cite external literature or state established principles?
   → Yes: This is context (for either Q1 or Q2, depending on what it supports)
   → No: Continue to #5

5. Does it state an INTERPRETATION, CONCLUSION, or IMPLICATION?
   → Yes: This is Q2 outcome
   → No: Re-examine—the sentence likely fits one of the above
```

---

## Self-Validation Checklist

Before finalizing your extraction, verify:

- [ ] Every data-containing sentence is captured in at least one triplet
- [ ] No observation appears as `main_content` in multiple Q2 triplets (avoid redundancy)
- [ ] Q1 triplets have methods (`outcome`) that logically address the stated goal (`main_content`)
- [ ] Q2 triplets have conclusions (`outcome`) that logically follow from observation + context
- [ ] `(missing)` is used only when text is truly absent, not merely implicit
- [ ] Summary statements at subsection ends are handled consistently (either as standalone Q2 or attached to prior triplet)

---

## Examples

### Example 1: Complete Q1 Triplet

**Text:** "To determine whether the canonical PKA–CREB axis is involved in CREM induction after NK cell activation, we measured phosphorylated CREB (pCREB) levels in NK cells after CAR or IL-15 stimulation."

```json
{
  "type": "Q1",
  "main_content": "To determine whether the canonical PKA–CREB axis is involved in CREM induction after NK cell activation",
  "context": "(missing)",
  "outcome": "we measured phosphorylated CREB (pCREB) levels in NK cells after CAR or IL-15 stimulation"
}
```

### Example 2: Q1 with Context

**Text:** "Given the established function of calcium as an activator of PKA (Ref: 32,33) and its pivotal role in the immune cell activation cascade (Ref: 34), we also chelated calcium with EGTA."

```json
{
  "type": "Q1",
  "main_content": "(missing)",
  "context": "Given the established function of calcium as an activator of PKA (Ref: 32,33) and its pivotal role in the immune cell activation cascade (Ref: 34)",
  "outcome": "we also chelated calcium with EGTA"
}
```

### Example 3: Simple Q2 (Observation Only)

**Text:** "UMAP clearly distinguished the transcriptional profiles of CAR19-IL-15 NK cells before and after infusion (Fig. 1b)."

```json
{
  "type": "Q2",
  "main_content": "UMAP clearly distinguished the transcriptional profiles of CAR19-IL-15 NK cells before and after infusion (Fig. 1b)",
  "context": "(missing)",
  "outcome": "(missing)"
}
```

### Example 4: Complete Q2 Triplet

**Text:** "Motif enrichment analysis revealed that binding motifs for JUN-related factors were highly enriched in CREM KO compared with WT cells (Fig. 5h,i). These patterns of enriched AP-1 motifs mirror epigenetic signatures associated with long-lived memory T cells (Ref: 40) and may underlie the enhanced persistence and function of CREM KO CAR-NK cells."

```json
{
  "type": "Q2",
  "main_content": "Motif enrichment analysis revealed that binding motifs for JUN-related factors were highly enriched in CREM KO compared with WT cells (Fig. 5h,i)",
  "context": "These patterns of enriched AP-1 motifs mirror epigenetic signatures associated with long-lived memory T cells (Ref: 40)",
  "outcome": "and may underlie the enhanced persistence and function of CREM KO CAR-NK cells"
}
```

### Example 5: Summary Statement as Q2

**Text:** "Collectively, these findings indicate that both CAR ITAM signalling and IL-15 are potent inducers of CREM in NK cells, thereby highlighting their complex interplay in regulating NK cell activity."

```json
{
  "type": "Q2",
  "main_content": "Stimulation with CD70 antigen increased CREM expression only in CAR70 NK cells. IL-15 treatment resulted in a dose-dependent increase in CREM expression. Stimulation with both CD70 antigen and exogenous IL-15 resulted in an additive increase in CREM expression.",
  "context": "(missing)",
  "outcome": "Collectively, these findings indicate that both CAR ITAM signalling and IL-15 are potent inducers of CREM in NK cells, thereby highlighting their complex interplay in regulating NK cell activity."
}
```

### Example 6: Negative Result

**Text:** "CREM KO did not have a significant effect on the function of NT NK cells."

```json
{
  "type": "Q2",
  "main_content": "CREM KO did not have a significant effect on the function of NT NK cells",
  "context": "(missing)",
  "outcome": "(missing)"
}
```

---

Now, analyze the provided scientific paper excerpt following these instructions.

# PAPER EXCERPT:
{{paper}}
""".strip()

TEMPLATE_PREDICTION_1 = """
# TASK: Experimental Design Generation (Type Q1)

## Overview
You will act as a Principal Investigator planning a scientific study. You will be provided with a specific research question or objective (`main_content`). Your task is to generate the logical reasoning required to design an experiment to address this objective. You must construct the "Inquiry Logic" triplet by generating the missing `context` and `outcome`.

## Logical Components

1. **Input: Research Goal (`main_content`)**
   This is the specific knowledge gap, hypothesis, or objective provided to you.

2. **Generate: Justification (`context`)**
   You must generate the scientific background or reasoning that makes the proposed experiment feasible or relevant. This should describe established biological principles, properties of specific model systems, or prior knowledge that serves as the foundation for the chosen method. Do not invent specific citations (e.g., "Ref: 12"), but rather state the general scientific consensus or established biological rule.

3. **Generate: Methodology (`outcome`)**
   You must generate the specific operational step, assay, or technique that creates the data necessary to answer the Research Goal. This should be a concrete action (e.g., "perform RNA-seq," "use CRISPR-Cas9 to knockout X," "stain with antibodies against Y") rather than a vague statement.

## Reasoning Flow
Your generation must follow this logical path:
*Because we want to know [main_content], and considering [context], we will perform [outcome].*

## Output Format
Return your response in the following JSON format:

```json
{
    "main_content": "The provided input goal",
    "context": "The scientific justification or background principle used to select the method.",
    "outcome": "The specific experimental method or assay performed."
}
```

**Input (Goal):** 
{{main_content}}
""".strip()

TEMPLATE_PREDICTION_2 = """
# TASK: Scientific Interpretation Generation (Type Q2)

## Overview
You will act as a Senior Scientific Reviewer analyzing raw data. You will be provided with a specific empirical observation or statistical result (`main_content`). Your task is to apply scientific theory to this observation to derive a meaningful conclusion. You must construct the "Discovery Logic" triplet by generating the missing `context` and `outcome`.

## Logical Components

1. **Input: Empirical Observation (`main_content`)**
   This is the specific data point, morphological description, or statistical finding provided to you.

2. **Generate: Established Principle (`context`)**
   You must generate the "lens" through which this data is interpreted. This should be an established biological rule, physical law, or known association (e.g., "It is well established that protein X is a marker for Y," or "Changes in nuclear shape are indicative of Z"). This provides the theoretical bridge between the raw number/image and its biological meaning.

3. **Generate: New Insight (`outcome`)**
   You must generate the novel conclusion or hypothesis that arises from combining the Observation with the Principle. This represents the new understanding or implication for the biological system (e.g., "Therefore, this suggests the pathway is upregulated," or "This indicates a transition to a mesenchymal state").

## Reasoning Flow
Your generation must follow this logical path:
*We observed [main_content]. Since it is known that [context], we conclude that [outcome].*

## Output Format
Return your response in the following JSON format:

```json
{
    "main_content": "The provided input observation",
    "context": "The general biological rule or established theory applied to the data.",
    "outcome": "The specific biological interpretation or conclusion derived."
}
```

**Input (Observation):** 
{{main_content}}
""".strip()