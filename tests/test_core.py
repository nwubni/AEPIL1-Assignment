import json
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path to allow importing app modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.endpoint import (
    calculate_cost, 
    validate_response, 
    process_query,
    MODEL,
    PRICING
)

# Test data
SAMPLE_VALID_RESPONSE = {
    "answer": "We accept credit cards and PayPal.",
    "confidence": 95,
    "actions": ["Provide payment options", "Process return"]
}

SAMPLE_INVALID_RESPONSE = {
    "answer": "Test answer",
    "confidence": "high",  # Invalid type, should be number
    "actions": "not a list"  # Invalid type, should be list
}

class TestCostCalculation:
    """Tests for the calculate_cost function."""
    
    def test_cost_calculation(self):
        """Test that cost is calculated correctly."""
        prompt_tokens = 100
        completion_tokens = 50
        expected_cost = (100 * PRICING[MODEL]["input"]) + (50 * PRICING[MODEL]["output"])
        assert calculate_cost(MODEL, prompt_tokens, completion_tokens) == pytest.approx(expected_cost, 0.000001)
    
    def test_cost_with_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        assert calculate_cost(MODEL, 0, 0) == 0.0


class TestResponseValidation:
    """Tests for the validate_response function."""
    
    def test_valid_response(self):
        """Test that a valid response passes validation."""
        validate_response(SAMPLE_VALID_RESPONSE)  # Should not raise
    
    def test_missing_fields(self):
        """Test validation with missing required fields."""
        invalid = {"answer": "Test"}  # Missing confidence and actions
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_response(invalid)
    
    def test_invalid_confidence(self):
        """Test validation of confidence field."""
        # Test non-numeric confidence
        invalid = SAMPLE_VALID_RESPONSE.copy()
        invalid["confidence"] = "high"
        with pytest.raises(ValueError, match="must be a number"):
            validate_response(invalid)
        
        # Test out of range confidence
        invalid["confidence"] = 150
        with pytest.raises(ValueError, match="between 0 and 100"):
            validate_response(invalid)
    
    def test_invalid_actions(self):
        """Test validation of actions field."""
        invalid = SAMPLE_VALID_RESPONSE.copy()
        invalid["actions"] = "not a list"
        with pytest.raises(ValueError, match="must be a list"):
            validate_response(invalid)


class TestProcessQuery:
    """Tests for the process_query function using mocks."""
    
    @patch('app.endpoint.OpenAI')
    def test_successful_query(self, mock_openai):
        """Test a successful API call with valid response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(SAMPLE_VALID_RESPONSE)
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function
        response, metrics = process_query("test query", client=mock_client)
        
        # Assertions
        assert response == SAMPLE_VALID_RESPONSE
        assert metrics["tokens_prompt"] == 50
        assert metrics["tokens_completion"] == 30
        assert metrics["total_tokens"] == 80
        assert "latency_ms" in metrics
        assert "estimated_cost_usd" in metrics
        assert metrics["estimated_cost_usd"] == calculate_cost(MODEL, 50, 30)
    
    @patch('app.endpoint.OpenAI')
    def test_fallback_on_invalid_json(self, mock_openai):
        """Test that invalid JSON triggers the fallback mechanism."""
        # First call returns invalid JSON
        first_response = MagicMock()
        first_response.choices[0].message.content = "{invalid json"
        first_response.usage.prompt_tokens = 40
        first_response.usage.completion_tokens = 20
        first_response.usage.total_tokens = 60
        
        # Fallback response
        fallback_response = MagicMock()
        fallback_response.choices[0].message.content = json.dumps(SAMPLE_VALID_RESPONSE)
        fallback_response.usage.prompt_tokens = 30
        fallback_response.usage.completion_tokens = 15
        fallback_response.usage.total_tokens = 45
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [first_response, fallback_response]
        
        # Call the function
        response, metrics = process_query("test query", client=mock_client)
        
        # Assertions
        assert response == SAMPLE_VALID_RESPONSE
        # Should use tokens from both calls
        assert metrics["tokens_prompt"] == 40 + 30
        assert metrics["tokens_completion"] == 20 + 15
        assert metrics["total_tokens"] == 60 + 45
    
    @patch('app.endpoint.OpenAI')
    def test_api_error_handling(self, mock_openai):
        """Test that API errors are handled gracefully."""
        # Setup mock to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Call the function
        response, metrics = process_query("test query", client=mock_client)
        
        # Assertions
        assert response["answer"] == "An error occurred while processing your request."
        assert response["confidence"] == 0
        assert response["actions"] == ["Contact support"]
        assert "API Error" in metrics.get("error", "")
        assert "latency_ms" in metrics


class TestEndToEnd:
    """End-to-end tests using the actual implementation with mocked API calls."""
    
    @patch('app.endpoint.OpenAI')
    def test_full_flow(self, mock_openai, tmp_path):
        """Test the full flow with a mock API response."""
        # Setup test prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "main_prompt.txt"
        prompt_file.write_text("You are a helpful assistant.")
        
        # Setup metrics directory
        metrics_dir = tmp_path / "metrics"
        
        # Create the metrics file path
        metrics_file = metrics_dir / "metrics.json"
        
        # Mock the file operations to use our temp directory
        with patch('app.endpoint.open') as mock_open, \
             patch('os.makedirs') as mock_makedirs, \
             patch('app.endpoint.PROMPT_PATH', str(prompt_file)), \
             patch('app.endpoint.METRICS_PATH', str(metrics_file)) as mock_metrics_path:
            
            # Setup mock response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(SAMPLE_VALID_RESPONSE)
            mock_response.usage.prompt_tokens = 50
            mock_response.usage.completion_tokens = 30
            mock_response.usage.total_tokens = 80
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Call the function
            response, metrics = process_query("test query", client=mock_client)
            
            # Assertions
            assert response == SAMPLE_VALID_RESPONSE
            assert response["confidence"] == 95
            assert response["actions"] == ["Provide payment options", "Process return"]
            assert metrics["estimated_cost_usd"] == calculate_cost(MODEL, 50, 30)
            
            # Verify the prompt was read
            mock_open.assert_called_with(str(prompt_file), 'r')
            
            # Verify metrics directory was created and metrics were written
            # The actual implementation uses os.path.dirname(os.path.abspath(METRICS_PATH))
            expected_metrics_dir = os.path.dirname(os.path.abspath(str(metrics_file)))
            
            # Check if any call to makedirs matches our expected directory
            makedirs_called = False
            for call_args in mock_makedirs.call_args_list:
                if not call_args[0] or not call_args[0]:
                    continue
                    
                # Get the called path and normalize it for comparison
                called_path = call_args[0][0]
                if isinstance(called_path, str):
                    called_path = os.path.normpath(os.path.abspath(called_path))
                else:
                    called_path = os.path.normpath(os.path.abspath(str(called_path)))
                
                # Compare normalized paths
                if called_path == os.path.normpath(expected_metrics_dir):
                    makedirs_called = True
                    break
                    
            # If not found, print debug information
            if not makedirs_called:
                print("\nDebug - makedirs calls:")
                for i, call_args in enumerate(mock_makedirs.call_args_list):
                    if call_args[0]:
                        print(f"Call {i}: {call_args[0][0]} (type: {type(call_args[0][0])})")
                print(f"Expected: {os.path.normpath(expected_metrics_dir)}")
                    
            assert makedirs_called, f"Expected makedirs to be called with {os.path.normpath(expected_metrics_dir)}"
            
            # Verify the metrics file was written to
            # We need to check if any call to open was made with the metrics file
            metrics_file_str = str(metrics_file)
            mock_open_calls = [
                call[0][0] for call in mock_open.call_args_list
                if call[0] and (str(call[0][0]) == metrics_file_str or call[0][0] == metrics_file)
            ]
            assert len(mock_open_calls) > 0, f"Expected open to be called with {metrics_file}"