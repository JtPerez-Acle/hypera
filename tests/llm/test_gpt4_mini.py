"""Tests for the GPT-4-mini client."""

import pytest
import json
from unittest.mock import AsyncMock, patch
from src.llm.gpt4_mini import GPT4MiniClient, GPT4MiniConfig


@pytest.fixture
def config():
    """Test configuration for GPT-4-mini."""
    return GPT4MiniConfig(
        api_key="test-key",
        model="gpt-4o-mini",
        temperature=0.0
    )


@pytest.fixture
def client(config):
    """Create a test client."""
    return GPT4MiniClient(config)


@pytest.mark.asyncio
async def test_client_initialization(client):
    """Test client initialization."""
    async with client as c:
        assert c.config == client.config
        assert c._session is not None


@pytest.mark.asyncio
async def test_generate_completion(client):
    """Test generating a completion."""
    test_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "imports": ["import os"],
                    "functions": [{
                        "name": "test_func",
                        "params": ["arg1"],
                        "return_type": "str"
                    }]
                })
            }
        }]
    }
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = test_response
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        async with client as c:
            response = await c.generate("Test prompt")
            assert response == test_response
            
            # Verify API call
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert "json" in call_kwargs
            payload = call_kwargs["json"]
            assert "prompt" in payload
            assert payload["prompt"] == "Test prompt"
            assert "temperature" in payload
            assert payload["temperature"] == 0.0


@pytest.mark.asyncio
async def test_extract_completion():
    """Test extracting completion from response."""
    test_metadata = {
        "imports": ["import os"],
        "functions": [{
            "name": "test_func",
            "params": ["arg1"],
            "return_type": "str"
        }]
    }
    
    response = {
        "choices": [{
            "message": {
                "content": json.dumps(test_metadata)
            }
        }]
    }
    
    completion = GPT4MiniClient.extract_completion(response)
    assert json.loads(completion) == test_metadata


@pytest.mark.asyncio
async def test_invalid_response():
    """Test handling invalid API responses."""
    with pytest.raises(ValueError):
        GPT4MiniClient.extract_completion({})
    
    with pytest.raises(ValueError):
        GPT4MiniClient.extract_completion({"choices": []})


@pytest.mark.asyncio
async def test_client_error_handling(client):
    """Test handling API errors."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_post.return_value.__aenter__.return_value = mock_response
        
        async with client as c:
            with pytest.raises(Exception, match="GPT-4 Mini API error: 500 - Internal Server Error"):
                await c.generate("Test prompt")
