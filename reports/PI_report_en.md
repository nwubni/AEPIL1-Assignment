# AI Engineering Project Report

## Overview

This is a terminal-based program that uses AI engineering knowledge to act as an e-commerce customer agent. The program takes user/customer questions via the terminal and provides a response in the form of a JSON/Dictionary string containing the model used to generate the response, timestamp, prompt tokens, completion tokens, total tokens, latency in milliseconds, and estimated cost in USD.

**Command to run the program from the root directory:**
```bash
python -m app.endpoint "User prompt/question"
```

## Prompt Technique

Since this is a simple system that won't require deep reasoning to produce responses, I made a quick decision not to use the Chain-of-Thought prompting technique.

After ruling out Chain-of-Thought, I proceeded by experimenting with Zero-Shot and Few-Shot prompt techniques to select a prompt style that would produce the kind of response a knowledgeable e-commerce customer agent would give a client, along with better output metrics in terms of latency and costs.

I settled on Few-Shot after several experiments with the prompts because it gave the output that I was looking for that would fit the context of the problem.

This mini project also implements and utilizes a simple moderation functionality to sanitize input, prevent profanity, adversarial prompt injections, data leakage, and only send ethical user prompts to the AI model for processing.

The moderation approach is enforced at the ingress and egress gates. At the ingress gate, user input is checked for profanity, prompt injection attempts, and other adversarial patterns before being sent to the AI model. At the egress gate, the AI model's response content is checked for safety (profanity, inappropriate content, etc.) before being presented to the user. Additionally, the system validates the structure and format of the AI response to ensure it matches the expected JSON schema.

### Moderation Sample
`python -m app.endpoint "Who the fuck shit is this?"`

**Response:**
```json
 {
  "answer": "I'm sorry, but I can't process that request. Potential adversarial prompt detected with risk score: 0.80. Flagged patterns: profanity_detected",
  "confidence": 100,
  "actions": [],
  "error": "Potential adversarial prompt detected with risk score: 0.80. Flagged patterns: profanity_detected",
  "success": false
}
```

**Metrics:**
```json
{
  "model": "safety_check",
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "latency_ms": 0,
  "estimated_cost_usd": 0.0,
  "timestamp": "2025-11-02T14:01:36.727060"
}
```

During the prompt engineering iteration phase, Zero-Shot produces a general response that may be out of context for an e-commerce customer service. The responses are verbose in most cases and sometimes provide irrelevant details.

I have included samples of my experiments with the two prompting methods below, along with their corresponding output metrics for the same user prompt.

### Zero-Shot Approach

**Command:**
```bash
python -m app.endpoint "What payment options do you have?"
```

**Response:**
```json
{
  "answer": "I don't handle transactions or payments directly, but common payment options for online services typically include: 1. Credit/Debit Cards: Visa, MasterCard, American Express, Discover, etc. 2. Digital Wallets: PayPal, Apple Pay, Google Pay, etc. 3. Bank Transfers: Direct transfers from bank accounts. 4. Cryptocurrency: Bitcoin, Ethereum, and other digital currencies, depending on the service. 5. Buy Now, Pay Later: Services like Afterpay or Klarna. For specific payment options, please refer to the website or service you are inquiring about.",
  "confidence": 90,
  "actions": []
}
```

**Metrics:**
```json
{
  "model": "gpt-4o-mini",
  "timestamp": 1761654378,
  "tokens_prompt": 188,
  "tokens_completion": 271,
  "total_tokens": 459,
  "latency_ms": 9772.89,
  "estimated_cost_usd": 0.000191
}
```

### Few-Shot Approach

**Command:**
```bash
python -m app.endpoint "What payment options do you have?"
```

**Response:**
```json
{
  "answer": "We accept major credit cards, PayPal, and Apple Pay.",
  "confidence": 0.9,
  "actions": [
    "Provide payment link",
    "Verify customer account"
  ]
}
```

**Metrics:**
```json
{
  "model": "gpt-4o-mini",
  "timestamp": 1761654504,
  "tokens_prompt": 215,
  "tokens_completion": 43,
  "total_tokens": 258,
  "latency_ms": 1891.97,
  "estimated_cost_usd": 5.8e-05
}
```

## Results Analysis

From the results, Few-Shot provides a clear and concise answer, uses fewer tokens, which in turn reduces costs, and has an overall better latency.

## Challenges and Improvements

I encountered structural and code organizational challenges as I built the solution, which made it difficult to isolate and test the correctness of various functionalities such as reading prompts, input validation, calculating costs, measuring latency, and logging metrics.

I was able to improve the program by modularizing and isolating major functionalities to make it easier for scaling, testing logic, and debugging.