"""
Test configuration and fixtures for HyperA.

This module provides shared fixtures and configuration for all tests,
ensuring consistent test environments and reducing code duplication.
"""

import os
import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from pydantic_settings import BaseSettings
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import google.generativeai as genai
import openai

# Mock API keys for testing
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["DEEPSEEK_API_KEY"] = "test-key"

# Test environment configuration
class TestConfig(BaseSettings):
    """Test configuration with mock API keys."""
    OPENAI_API_KEY: str = "test-openai-key"
    GOOGLE_API_KEY: str = "test-google-key"
    QDRANT_URL: str = "http://localhost:6333"
    
    class Config:
        env_file = ".env.test"

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TestConfig()

@pytest.fixture
def mock_qdrant_client(monkeypatch):
    """Provide a mocked Qdrant client."""
    client = Mock(spec=QdrantClient)
    
    # Mock search results
    search_result = Mock(spec=rest.ScoredPoint)
    search_result.payload = {
        "content": "def test_function(): pass",
        "file_path": "/test/file.py",
        "language": "python",
        "chunk_type": "function"
    }
    search_result.score = 0.95
    
    client.search.return_value = [search_result]
    
    return client

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Provide a mocked OpenAI client."""
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536)]
    
    async def mock_create(*args, **kwargs):
        return mock_response
    
    monkeypatch.setattr(openai.embeddings, "create", AsyncMock(side_effect=mock_create))
    return mock_response

@pytest.fixture
def mock_gemini_client(monkeypatch):
    """Provide a mocked Gemini client."""
    mock_model = Mock()
    mock_model.generate_content_async = AsyncMock(return_value=Mock(text="Mocked analysis"))
    
    def mock_get_model(*args, **kwargs):
        return mock_model
    
    monkeypatch.setattr(genai, "GenerativeModel", mock_get_model)
    return mock_model

@pytest.fixture
def sample_code_chunk() -> Dict[str, Any]:
    """Provide a sample code chunk for testing."""
    return {
        "content": """
        def calculate_metrics(data: List[float]) -> Dict[str, float]:
            \"\"\"Calculate statistical metrics for a list of values.\"\"\"
            return {
                "mean": sum(data) / len(data),
                "max": max(data),
                "min": min(data)
            }
        """,
        "file_path": "/src/analysis/metrics.py",
        "language": "python",
        "chunk_type": "function",
        "metadata": {
            "function_name": "calculate_metrics",
            "parameters": ["data"],
            "return_type": "Dict[str, float]",
            "docstring": "Calculate statistical metrics for a list of values."
        }
    }

@pytest.fixture
def test_files_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create Python test file
    py_file = tmp_path / "test.py"
    py_file.write_text("""
    def hello_world():
        \"\"\"A simple test function.\"\"\"
        return "Hello, World!"
    
    class TestClass:
        def method(self):
            return 42
    """)
    
    # Create markdown test file
    md_file = tmp_path / "test.md"
    md_file.write_text("""
    # Test Document
    
    This is a test markdown file.
    
    ```python
    def code_block():
        pass
    ```
    """)
    
    return tmp_path

@pytest.fixture
def mock_file_system(tmp_path, monkeypatch):
    """Set up a mock file system for testing."""
    # Create project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()
    
    # Create some test files
    (tmp_path / "src/main.py").touch()
    (tmp_path / "tests/test_main.py").touch()
    (tmp_path / "docs/README.md").touch()
    
    # Update current working directory
    monkeypatch.chdir(tmp_path)
    
    return tmp_path
