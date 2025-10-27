Architecture overview, prompt technique(s) used and why, metrics summary with sample results, challenges, improvements.

I modularized everything into functions to isolate codes and improve testability.

Prompt Technique:
Since this is a simple system that won't require deep reason to produce responses, I used Few-Shot to guide the response and output format through an example I provided. This is to help the model generate better response that stay within the context of an ecommerce assistance agent.
In this case, Zero-Shot may produce a general response that may be out of context of ecommerce customer service.

I experimented with the three ways of prompting, and they gave different results for the task.
Their output samples and matrics for the same prompt ---- are documented below.
Zero-Shot:

Few-Shot:

Chain-Of-Thought