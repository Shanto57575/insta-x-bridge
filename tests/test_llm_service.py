import pytest
from unittest.mock import patch, MagicMock
from llm_service import analyze_with_llm

@pytest.fixture
def mock_groq():
    with patch('llm_service.Groq') as mock_groq:
        # Create mock response structure
        mock_message = MagicMock()
        mock_message.content = "Generated tweet text"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Configure Groq client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        yield mock_groq

def test_analyze_with_llm_success(mock_groq):
    post_data = {
        "caption": "Test Instagram caption",
        "timestamp": "2023-04-01T12:00:00Z",
        "likes": 1000,
        "comments": 50
    }
    
    with patch('os.getenv', return_value='fake-api-key'):
        result = analyze_with_llm(post_data)
        
        assert result == "Generated tweet text"
        
        # Verify correct model and system prompt usage
        call_args = mock_groq.return_value.chat.completions.create.call_args[1]
        assert call_args['model'] == "llama-3.3-70b-versatile"
        assert any("social media assistant" in msg['content'] for msg in call_args['messages'] if msg['role'] == 'system')

def test_analyze_with_llm_empty_data():
    result = analyze_with_llm({})
    assert result == "No data available to analyze."

def test_analyze_with_llm_api_error(mock_groq):
    # Configure API error
    mock_groq.return_value.chat.completions.create.side_effect = Exception("API error")
    
    with patch('os.getenv', return_value='fake-api-key'):
        result = analyze_with_llm({"caption": "Test"})
        assert "Error during analysis: API error" in result

def test_analyze_with_llm_long_output(mock_groq):
    # Configure long output that needs truncation
    mock_groq.return_value.chat.completions.create.return_value.choices[0].message.content = "X" * 300
    
    with patch('os.getenv', return_value='fake-api-key'):
        result = analyze_with_llm({"caption": "Test"})
        assert len(result) == 280  # Twitter character limit
        assert result.endswith("...")