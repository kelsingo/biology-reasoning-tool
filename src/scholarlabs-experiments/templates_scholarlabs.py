TEMPLATE_PREDICTION_11 = """
Search for scientific literature related to the following research goal:
{{main_content}}


Focus on:
- experimental methods used to study this research goal
- relevant biological facts, mechanisms, and pathways
- studies with functional assays or interventions
""".strip()

TEMPLATE_PREDICTION_12 = """
Search for scientific literature related to the following mechanism:
{{main_content}}


Focus on:
- studies investigating this or similar biological mechanisms
- experimental systems and techniques used to test the mechanism
- evidence linking or confirming mechanism
""".strip()

TEMPLATE_PREDICTION_21 = """
Search for scientific literature related to the following research goal:
{{main_content}}


Focus on:
- known biological mechanisms and pathways involved
- quantitative or experimental findings explaining this question
- interactions between key entities of the research goal
""".strip()

TEMPLATE_PREDICTION_22 = """
Search for scientific literature related to the following mechanism:
{{main_content}}


Focus on:
- established biological principles and pathways
- related mechanisms in similar systems or diseases
- studies supporting causal relationships
""".strip()

TEMPLATE_PREDICTION_23 = """
Search for scientific literature related to the following finding:
{{main_content}}


Focus on:
- biological mechanisms explaining this observation
- studies linking similar observations to functional outcomes
""".strip()

TEMPLATE_PREDICTION_31 = """
Search for scientific literature related to the following mechanism:
{{main_content}}
Focus on:
- alternative mechanisms or pathways 
- regulatory constraints or confounding factors
- studies reporting limitations, side effects, or opposing evidence in case of therapeutic approaches. 
""".strip()