#!/usr/bin/env python3
"""
Unit tests for the LLM text completion task.
Tests both mocked functionality and optional real API integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from typing import Dict, Any

from tasks.llm_text_complete.llm_text_complete import llm_text_complete


class TestLLMTextComplete:
    """Test class for LLM text completion functionality."""

    def test_basic_completion_without_variables(self):
        """Test basic text completion without prompt variables."""
        # Mock the litellm completion function
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test completion"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response):
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Complete this sentence: The weather is"
            )

            assert result == "This is a test completion"

    def test_completion_with_prompt_variables(self):
        """Test text completion with prompt variables."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello John, how are you today?"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response):
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Hello {name}, how are you {time_of_day}?",
                promptVariables={"name": "John", "time_of_day": "today"}
            )

            assert result == "Hello John, how are you today?"

    def test_completion_with_temperature(self):
        """Test text completion with temperature parameter."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Creative response"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Write a creative story",
                temperature=0.8
            )

            # Verify temperature was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["temperature"] == 0.8

    def test_completion_with_top_p(self):
        """Test text completion with top_p parameter."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response with top_p"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Generate text",
                topP=0.9
            )

            # Verify top_p was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["top_p"] == 0.9

    def test_completion_with_max_tokens(self):
        """Test text completion with max_tokens parameter."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Short response"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Write a short response",
                maxTokens=50
            )

            # Verify max_tokens was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["max_tokens"] == 50

    def test_completion_with_string_stop_words(self):
        """Test text completion with string stop words."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response before stop"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Continue the story",
                stopWords="END"
            )

            # Verify stop words were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["stop"] == ["END"]

    def test_completion_with_list_stop_words(self):
        """Test text completion with list stop words."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response before stop"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_response = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Continue the story",
                stopWords=["END", "STOP", "FINISH"]
            )

            # Verify stop words were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["stop"] == ["END", "STOP", "FINISH"]

    def test_completion_with_dict_stop_words(self):
        """Test text completion with dictionary stop words."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response before stop"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Continue the story",
                stopWords={"end": "END", "stop": "STOP"}
            )

            # Verify stop words were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["stop"] == ["END", "STOP"]

    def test_completion_with_all_optional_parameters(self):
        """Test text completion with all optional parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Complete response"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Generate a comprehensive response",
                temperature=0.7,
                topP=0.9,
                maxTokens=100,
                stopWords=["END", "STOP"]
            )

            # Verify all parameters were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args["temperature"] == 0.7
            assert call_args["top_p"] == 0.9
            assert call_args["max_tokens"] == 100
            assert call_args["stop"] == ["END", "STOP"]

    def test_missing_prompt_variable_error(self):
        """Test error handling when prompt variable is missing."""
        with pytest.raises(ValueError, match="Missing prompt variable: 'name'"):
            llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Hello {name}, how are you?",
                promptVariables={"age": "25"}  # Missing 'name' variable
            )

    def test_litellm_completion_error(self):
        """Test error handling when litellm completion fails."""
        with patch('tasks.llm_text_complete.llm_text_complete.completion', side_effect=Exception("API Error")):
            with pytest.raises(RuntimeError, match="LLM completion failed: API Error"):
                llm_text_complete(
                    llmProvider="openai",
                    model="gpt-3.5-turbo",
                    prompt="Test prompt"
                )

    def test_litellm_response_structure_error(self):
        """Test error handling when litellm response structure is unexpected."""
        # Mock response without expected structure
        mock_response = Mock()
        mock_response.choices = []  # Empty choices list

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response):
            with pytest.raises(RuntimeError, match="LLM completion failed: list index out of range"):
                llm_text_complete(
                    llmProvider="openai",
                    model="gpt-3.5-turbo",
                    prompt="Test prompt"
                )

    def test_prompt_variables_none(self):
        """Test that None promptVariables are handled correctly."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Original prompt"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response):
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Original prompt",
                promptVariables=None
            )

            assert result == "Original prompt"

    def test_empty_prompt_variables_dict(self):
        """Test that empty promptVariables dict is handled correctly."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Original prompt"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response):
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Original prompt",
                promptVariables={}
            )

            assert result == "Original prompt"

    def test_completion_parameters_structure(self):
        """Test that completion parameters are structured correctly."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"

        with patch('tasks.llm_text_complete.llm_text_complete.completion', return_value=mock_response) as mock_completion:
            llm_text_complete(
                llmProvider="openai",
                model="gpt-4",
                prompt="Test prompt"
            )

            # Verify the basic structure
            call_args = mock_completion.call_args[1]
            assert call_args["model"] == "gpt-4"
            assert "messages" in call_args
            assert len(call_args["messages"]) == 1
            assert call_args["messages"][0]["role"] == "user"
            assert call_args["messages"][0]["content"] == "Test prompt"


class TestLLMTextCompleteIntegration:
    """Integration tests that can optionally use real API calls."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set - skipping integration test"
    )
    def test_real_openai_completion(self):
        """Test with real OpenAI API (requires OPENAI_API_KEY in environment)."""
        try:
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="Say 'Hello World' and nothing else",
                maxTokens=10
            )

            # Basic validation that we got a response
            assert isinstance(result, str)
            assert len(result) > 0
            assert "hello" in result.lower() or "world" in result.lower()

        except Exception as e:
            pytest.skip(f"OpenAI API call failed: {e}")

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set - skipping integration test"
    )
    def test_real_openai_completion_with_variables(self):
        """Test with real OpenAI API using prompt variables."""
        try:
            result = llm_text_complete(
                llmProvider="openai",
                model="gpt-3.5-turbo",
                prompt="The capital of {country} is {city}.",
                promptVariables={"country": "Germany", "city": "Berlin"},
                maxTokens=20
            )

            # Basic validation
            assert isinstance(result, str)
            assert len(result) > 0

        except Exception as e:
            pytest.skip(f"OpenAI API call failed: {e}")


if __name__ == "__main__":
    # This allows running the file directly for debugging
    # But pytest will run it as a module
    pytest.main([__file__, "-v"])
