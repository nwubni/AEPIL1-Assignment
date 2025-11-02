# AEPIL1-Assignment

Andela GenAI First Assignment

This repository provides a simple way for an e-commerce service to utilize AI to query their customer service for complaints and get answers. The purpose is to reduce the time spent attending to customer complaints and improve customer experience.

## Project Setup Instructions

1. Open your command terminal
2. Clone the repository in your directory of choice by running the git command:
   ```bash
   git clone https://github.com/nwubni/AEPIL1-Assignment.git
   ```
3. Change into the project's root directory:
   ```bash
   cd AEPIL1-Assignment
   ```
4. Create a virtual environment to isolate the project's dependencies:
   ```bash
   python3 -m venv .venv
   ```
5. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
6. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   The dependencies include OpenAI to use OpenAI models to process user prompts.

## Environment Variables

This project requires an OpenAI API key to function. Create a `.env` file in the project root directory and add:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

Format for running the application:
```bash
python -m app.endpoint "Your query here"
```

Example:
```bash
python -m app.endpoint "What payment options do you have?"
```

## Testing

This assignment uses Pytest to validate the functionalities of the e-commerce customer agent program. The tests are located in the `tests/test_core.py` file.

The tests cover:
- Profanity filter
- Safety checker
- End-to-end flow
- Cost calculation
- Response validation
- Process query
- Full flow

To run the tests:
```bash
python -m pytest
```

## Reproducing Metrics

Metrics are automatically logged to `metrics/metrics.json` when running queries that generate API costs. The metrics file contains:
- Model used
- Timestamp
- Token usage (prompt, completion, total)
- Latency in milliseconds
- Estimated cost in USD

To view logged metrics:
```bash
cat metrics/metrics.json
```

## Known Limitations

### Metrics and Logging
- **Metrics logging**: Metrics are only logged when `estimated_cost_usd > 0`. Failed queries or safety-checked queries (with 0 cost) are not logged.

### Error Handling
- **API key validation**: If the API key is missing or invalid, the error may not be clearly communicated to the user until an API call is attempted.
- **Fallback mechanism**: When JSON parsing fails, the system makes an additional API call to fix the JSON, which doubles the cost and latency for those cases.

### Security and Moderation
- **Rate limiting**: There is no rate limiting implemented to prevent API abuse or excessive usage.