"""Configuration module for the application."""

from typing import Dict, Any
from pydantic import BaseModel, ConfigDict


class ResourceConfig(BaseModel):
    """Resource configuration for the system."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gemini_max_tokens": 2_000_000,
                "gpt4_mini_max_tokens": 1024,
                "max_parallel_agents": 5,
                "cache_size_mb": 1024,
                "enable_retrieval_cache": True
            }
        }
    )

    gemini_max_tokens: int = 2_000_000  # 2M token context window
    gpt4_mini_max_tokens: int = 1024
    max_parallel_agents: int = 5
    cache_size_mb: int = 1024
    enable_retrieval_cache: bool = True


class GeminiConfig(BaseModel):
    """Configuration for Gemini model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": "your-api-key",
                "max_tokens": 2_000_000,
                "model": "gemini-1.5-pro"
            }
        }
    )

    api_key: str
    max_tokens: int = 2_000_000
    model: str = "gemini-1.5-pro"


class GPT4MiniConfig(BaseModel):
    """Configuration for GPT-4-mini model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": "your-api-key",
                "max_tokens": 1024
            }
        }
    )

    api_key: str
    max_tokens: int = 1024
