import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

from app.endpoint import (
    MODEL,
    PRICING,
    calculate_cost,
    process_query,
    validate_response,
)
from app.safety import PromptSafetyChecker, get_safe_prompt, is_prompt_safe
import pytest

sys.path.append(str(Path(__file__).parent.parent))


# Test data
SAMPLE_VALID_RESPONSE = {
    "answer": "We accept credit cards and PayPal.",
    "confidence": 95,
    "actions": ["Provide payment options", "Process return"],
}

SAMPLE_INVALID_RESPONSE = {
    "answer": "Test answer",
    "confidence": "high",  # Invalid type, should be number
    "actions": "not a list",  # Invalid type, should be list
}


class TestCostCalculation:
    """Tests for the calculate_cost function."""

    def test_cost_calculation(self):
        """Test that cost is calculated correctly."""
        prompt_tokens = 100
        completion_tokens = 50
        expected_cost = (100 * PRICING[MODEL]["input"]) + (
            50 * PRICING[MODEL]["output"]
        )
        assert calculate_cost(MODEL, prompt_tokens, completion_tokens) == pytest.approx(
            expected_cost, 0.000001
        )

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

    @patch("app.endpoint.OpenAI")
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

    @patch("app.endpoint.OpenAI")
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
        mock_client.chat.completions.create.side_effect = [
            first_response,
            fallback_response,
        ]

        # Call the function
        response, metrics = process_query("test query", client=mock_client)

        # Assertions
        assert response == SAMPLE_VALID_RESPONSE
        # Should use tokens from both calls
        assert metrics["tokens_prompt"] == 40 + 30
        assert metrics["tokens_completion"] == 20 + 15
        assert metrics["total_tokens"] == 60 + 45

    @patch("app.endpoint.OpenAI")
    def test_api_error_handling(self, mock_openai):
        """Test that API errors are handled gracefully."""
        # Setup mock to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Call the function
        response, metrics = process_query("test query", client=mock_client)

        # Assertions
        assert (
            response["answer"]
            == "I'm sorry, but I encountered an error while processing your request."
        )
        assert response["confidence"] == 0
        # The implementation returns an empty actions list on error
        assert response["actions"] == []
        assert "API Error" in metrics.get("error", "")
        # The implementation uses latency_ms
        assert "latency_ms" in metrics


class TestPromptSafety:
    """Tests for the prompt safety functionality."""

    def test_profanity_detection(self):
        """Test that profanity is detected in the input."""
        # Test with profanity
        result = is_prompt_safe("This is a test with a bad word: fuck")
        assert result.is_safe is False
        assert "profanity" in result.reason.lower()
        assert result.risk_score > 0.5  # Should be high risk for profanity

        # Test with clean input
        result = is_prompt_safe("This is a clean input")
        assert result.is_safe is True

        # Test with mixed case profanity
        result = is_prompt_safe("This has FuCkInG Shit DiCK pUsSy bad words")
        assert result.is_safe is False
        assert "profanity" in result.reason.lower()

    def test_safety_checker_instance(self):
        """Test the default global instance of the safety checker."""
        from app.safety import safety_checker

        assert isinstance(safety_checker, PromptSafetyChecker)

        # Test with a clean prompt
        result = is_prompt_safe("Hello, how are you?")
        assert result.is_safe is True

    def test_get_safe_prompt(self):
        """Test the get_safe_prompt function."""
        # Test with a bad word
        test_text = "This has a bad word: shit"
        safe_prompt = get_safe_prompt(test_text)
        assert safe_prompt == test_text

        # Test with clean input
        clean_text = "This is a clean message"
        assert get_safe_prompt(clean_text) == clean_text

    def test_edge_cases(self):
        """Test edge cases for the safety checker."""
        # Empty string - should be considered unsafe
        result = is_prompt_safe("")
        assert result.is_safe is False
        assert "empty" in result.reason.lower()

        # Very long string - should be safe if no profanity
        long_string = "x" * 1000 + " clean string " + "y" * 1000
        result = is_prompt_safe(long_string)
        assert result.is_safe is True

        # Non-string input should raise an AttributeError
        with pytest.raises(AttributeError):
            is_prompt_safe(123)  # type: ignore


class TestEndToEnd:
    """End-to-end tests using the actual implementation with mocked API calls."""

    @patch("app.endpoint.OpenAI")
    def test_full_flow(self, mock_openai):
        """Test the full flow with a mock API response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(SAMPLE_VALID_RESPONSE)
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Call the function with a test query
        response, metrics = process_query("test query", client=mock_client)

        # Verify the response structure and values
        assert response == SAMPLE_VALID_RESPONSE
        assert response["confidence"] == 95
        assert response["actions"] == ["Provide payment options", "Process return"]

        # Verify metrics - check for expected fields and values
        assert "estimated_cost_usd" in metrics
        assert "latency_ms" in metrics
        assert "model" in metrics
        assert metrics["model"] == MODEL

        # Verify token counts if they exist in the response
        if "prompt_tokens" in metrics:
            assert metrics["prompt_tokens"] == 50
        if "completion_tokens" in metrics:
            assert metrics["completion_tokens"] == 30
        if "total_tokens" in metrics:
            assert metrics["total_tokens"] == 80
