"""Metrics tracking for the system."""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AgentMetrics(BaseModel):
    """Metrics for agent performance and resource usage."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success_rate": 0.95,
                "average_latency": 0.234,
                "token_usage": {
                    "gemini": 1000,
                    "gpt4_mini": 500
                },
                "last_updated": "2024-02-16T16:10:04-03:00"
            }
        }
    )

    success_rate: float = Field(default=0.0, description="Success rate of operations")
    average_latency: float = Field(default=0.0, description="Average operation latency in seconds")
    token_usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Token usage by model"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last time metrics were updated"
    )
    total_operations: int = Field(
        default=0,
        description="Total number of operations performed"
    )


class SystemMetrics(BaseModel):
    """System-wide metrics."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_analyses": 100,
                "total_duration": 123.45,
                "average_duration": 1.23,
                "cache_hits": 50,
                "cache_misses": 50
            }
        }
    )

    total_analyses: int = Field(default=0, description="Total number of analyses performed")
    total_duration: float = Field(default=0.0, description="Total duration of all analyses")
    average_duration: float = Field(default=0.0, description="Average duration per analysis")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    cache_misses: int = Field(default=0, description="Number of cache misses")
