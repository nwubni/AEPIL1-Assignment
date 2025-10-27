from ast import Mod
import json
import os
import sys
import time
from typing import Dict, Any, Tuple, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# File paths
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "main_prompt.txt")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "metrics", "metrics.json")

# Model configuration
MODEL = "gpt-4o-mini"
PRICING = {
    "gpt-4o-mini": {
        "input": 0.15 / 1000000,  # $0.15 per 1M tokens input
        "output": 0.60 / 1000000,  # $0.60 per 1M tokens output
    }
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the cost of an API call based on token usage.
    
    Args:
        model: The model used for the API call
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        
    Returns:
        float: The estimated cost in USD
    """
    return round((prompt_tokens * PRICING[model]["input"]) + 
                (completion_tokens * PRICING[model]["output"]), 6)


def log_metrics(metrics_log: Dict[str, Any]) -> None:
    """Log metrics to a JSON file.
    
    Args:
        metrics_log: Dictionary containing metrics to log
    """
    try:
        # Ensure the metrics directory exists
        metrics_dir = os.path.dirname(os.path.abspath(METRICS_PATH))
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Append the metrics to the file
        with open(METRICS_PATH, "a") as f:
            f.write(json.dumps(metrics_log, indent=2) + "\n")
    except Exception as e:
        print(f"Error logging metrics: {e}", file=sys.stderr)


def validate_response(response_data: Dict[str, Any]) -> None:
    """Validate the structure and types of the response.
    
    Args:
        response_data: The parsed JSON response to validate
        
    Raises:
        ValueError: If the response doesn't match the expected format
    """

    required_fields = ["answer", "confidence", "actions"]
    missing_fields = [field for field in required_fields if field not in response_data]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    if not isinstance(response_data["answer"], str):
        raise ValueError("Field 'answer' must be a string")
    if not isinstance(response_data["confidence"], (int, float)) or not (0 <= response_data["confidence"] <= 100):
        raise ValueError("Field 'confidence' must be a number between 0 and 100")
    if not isinstance(response_data["actions"], list):
        raise ValueError("Field 'actions' must be a list")


def process_query(user_prompt: str, client: Optional[OpenAI] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process a user query using the OpenAI API.
    
    Args:
        user_prompt: The user's question or prompt
        client: Optional OpenAI client (for testing)
        
    Returns:
        tuple: (response_data, metrics) where response_data is the processed response with answer, confidence, and actions and metrics is a dictionary containing metrics about the API call
    """
    start_time = time.time()
    
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        # Load the system prompt from the prompts directory
        try:
            with open(PROMPT_PATH, "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are a helpful assistant."
        
        # Prepare messages for the API call to the OpenAI API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Make the API call to the OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        
        # Parse and validate the response from the OpenAI API
        content = response.choices[0].message.content
        
        # Initialize metrics
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # Try to parse and validate the JSON
        json_data = {}
        
        try:
            json_data = json.loads(content)
            validate_response(json_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback for invalid JSON or validation errors
            fallback_messages = [
                {"role": "system", "content": "Fix invalid JSON. Output only valid JSON with the fields: answer (string), confidence (number 0-100), actions (array of strings)"},
                {"role": "user", "content": content}
            ]
            
            fallback_response = client.chat.completions.create(
                model=MODEL,
                messages=fallback_messages,
                temperature=0.7,
                max_tokens=150,
                response_format={"type": "json_object"},
            )
            
            # Accumulate token counts from both calls
            prompt_tokens += fallback_response.usage.prompt_tokens
            completion_tokens += fallback_response.usage.completion_tokens
            total_tokens += fallback_response.usage.total_tokens
            
            json_data = json.loads(fallback_response.choices[0].message.content)
            
            # Ensure all required fields exist. If not, set default values.
            json_data.setdefault("answer", "Unable to process request")
            json_data.setdefault("confidence", 0)
            json_data.setdefault("actions", ["Escalate to human agent"])
        
        # Calculate metrics
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Calculate cost based on token usage
        cost = calculate_cost(MODEL, prompt_tokens, completion_tokens)
        
        # Prepare metrics dictionary
        metrics = {
            "model": MODEL,
            "timestamp": int(time.time()),
            "tokens_prompt": prompt_tokens,
            "tokens_completion": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "estimated_cost_usd": cost,
        }
        
        return json_data, metrics
        
    except Exception as e:
        # Handle any other errors
        end_time = time.time()
        metrics = {
            "timestamp": time.time(),
            "error": str(e),
            "latency_ms": round((end_time - start_time) * 1000, 2),
            "estimated_cost_usd": 0
        }
        
        # Return default error response with confidence 0 and actions "Contact support"
        return {
            "answer": "An error occurred while processing your request.",
            "confidence": 0,
            "actions": ["Contact support"]
        }, metrics


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.endpoint \"Your question here\"")
        sys.exit(1)
    
    user_prompt = sys.argv[1]
    
    try:
        response, metrics = process_query(user_prompt)
        print("Response:", json.dumps(response, indent=2))
        print("\nMetrics:", json.dumps(metrics, indent=2))
        
        if metrics.get("estimated_cost_usd", 0) > 0:
            log_metrics(metrics)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
