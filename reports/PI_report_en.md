Architecture overview, prompt technique(s) used and why, metrics summary with sample results, challenges, improvements.

Overview:
This is a terminal based program that uses AI engineering knowledge to act as an ecommerce customer agent.
The program takes user/customer questions via the terminal and gives a response inform of JSON string containing the model used to generate the response, timestamp, tokens prompt, tokens completion, total tokens, latency in milliseconds, and estimated cost in USD."
Here is the command to run the program from the root directory of the project:
python app/endpoint.py "User prompt/question"

Prompt Technique:
Since this is a simple system that won't require deep reasoning to produce responses, I made a quick decision not to use the Chain-Of-Thought prompting technique.

After ruling out the Chain-Of-Thought, I proceeded by experimenting with Zero-Shot and Few-Shot prompt techniques to select a prompt style that would produce the kind of response a knowledgeable ecommerce customer agent would give a client, along with better output metrics in terms of latency and costs.
I settled for Few-Shot after several experimentations with the prompts because it gave the output that I was looking for that would fit the context of the problem.

During the prompt engineering iteration phase, Zero-Shot produces a general response that may be out of context of an ecommerce customer service.
The responses are verbose in most cases and sometimes gives irrelevant details.

I have included samples of my experiments with the two ways of prompting methods below, and their corresponding output metrics for the same user prompt.

Zero-Shot:
python app/endpoint.py "What payment options do you have?"
Response: {
  "answer": "I don't handle transactions or payments directly, but common payment options for online services typically include: 1. Credit/Debit Cards: Visa, MasterCard, American Express, Discover, etc. 2. Digital Wallets: PayPal, Apple Pay, Google Pay, etc. 3. Bank Transfers: Direct transfers from bank accounts. 4. Cryptocurrency: Bitcoin, Ethereum, and other digital currencies, depending on the service. 5. Buy Now, Pay Later: Services like Afterpay or Klarna. For specific payment options, please refer to the website or service you are inquiring about.",
  "confidence": 90,
  "actions": []
}

Metrics: {
  "model": "gpt-4o-mini",
  "timestamp": 1761654378,
  "tokens_prompt": 188,
  "tokens_completion": 271,
  "total_tokens": 459,
  "latency_ms": 9772.89,
  "estimated_cost_usd": 0.000191
}


Few-Shot:
python app/endpoint.py "What payment options do you have?"
Response: {
  "answer": "We accept major credit cards, PayPal, and Apple Pay.",
  "confidence": 0.9,
  "actions": [
    "Provide payment link",
    "Verify customer account"
  ]
}

Metrics: {
  "model": "gpt-4o-mini",
  "timestamp": 1761654504,
  "tokens_prompt": 215,
  "tokens_completion": 43,
  "total_tokens": 258,
  "latency_ms": 1891.97,
  "estimated_cost_usd": 5.8e-05
}

From the results, Few-Shots gave me a clear and concise answer and uses less tokens, which in turn reduces costs, and had an overall better latency.

Challenges and Improvements:
I ran into structural and code organizational challenges as I built the solution, which was difficult to isolate and test correctness of various functionalities such as reading prompts, input validation, calculating costs, measuring latency, and logging metrics.
I was able to improve the program by modularizing and isolating major functionlities to make it easier for scaling, testing logic, and debugging.