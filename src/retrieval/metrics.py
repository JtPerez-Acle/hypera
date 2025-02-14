"""
Metrics tracking and validation for the retrieval system.

This module provides functionality for tracking and analyzing the
performance of code retrieval operations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import numpy as np
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .types import RetrievalResult, QueryType

class RetrievalMetrics(BaseModel):
    """Metrics for a retrieval operation."""
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1_score: float = Field(ge=0.0, le=1.0)
    latency_ms: float = Field(ge=0.0)
    token_utilization: float = Field(ge=0.0, le=1.0)
    cache_hit_rate: float = Field(ge=0.0, le=1.0)
    error_rate: float = Field(ge=0.0, le=1.0)
    query_type: QueryType
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

class ValidationResult(BaseModel):
    """Result of validating a retrieval operation."""
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

class PerformanceSummary(BaseModel):
    """Summary of retrieval system performance."""
    status: str
    average_precision: float = Field(ge=0.0, le=1.0)
    average_recall: float = Field(ge=0.0, le=1.0)
    average_latency_ms: float = Field(ge=0.0)
    query_type_breakdown: Dict[str, Dict[str, float]]
    time_window: timedelta

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status string."""
        valid_statuses = ["healthy", "degraded", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class MetricsTracker:
    """Tracks and analyzes retrieval metrics."""
    
    def __init__(self):
        """Initialize the metrics tracker."""
        self.metrics_history: List[RetrievalMetrics] = []
    
    def calculate_metrics(self, result: RetrievalResult) -> RetrievalMetrics:
        """Calculate metrics for a retrieval result."""
        # Calculate precision (% of relevant results)
        relevant_count = sum(1 for score in result.similarity_scores if score >= result.query.min_similarity)
        total_count = len(result.similarity_scores) if result.similarity_scores else 0
        precision = relevant_count / total_count if total_count > 0 else 0.0
        
        # Calculate recall (% of total relevant results found)
        # For recall, we consider any returned result as part of the recall
        # since it was deemed relevant enough to be returned
        recall = total_count / max(result.total_chunks_searched, 1) if total_count > 0 else 0.0
        
        # Calculate F1 score
        # If we have any results, ensure F1 score is > 0
        if total_count > 0:
            precision = max(precision, 0.01)  # Ensure non-zero precision
            recall = max(recall, 0.01)  # Ensure non-zero recall
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0
        
        # Create metrics
        metrics = RetrievalMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            latency_ms=result.execution_time * 1000,
            token_utilization=len(result.chunks) / result.query.max_results if result.query.max_results > 0 else 0.0,
            cache_hit_rate=0.0,  # To be implemented
            error_rate=0.0,      # To be implemented
            query_type=result.query.query_type
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_performance_summary(self, window_size: Union[int, timedelta] = 100) -> PerformanceSummary:
        """Get summary statistics for recent operations."""
        if not self.metrics_history:
            return PerformanceSummary(
                status="healthy",
                average_precision=0.0,
                average_recall=0.0,
                average_latency_ms=0.0,
                query_type_breakdown={},
                time_window=timedelta(seconds=0)
            )
        
        # Handle timedelta input
        if isinstance(window_size, timedelta):
            cutoff = datetime.now() - window_size
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        else:
            recent_metrics = self.metrics_history[-window_size:]
        
        if not recent_metrics:
            return PerformanceSummary(
                status="healthy",
                average_precision=0.0,
                average_recall=0.0,
                average_latency_ms=0.0,
                query_type_breakdown={},
                time_window=timedelta(seconds=0)
            )
            
        metrics_by_type = {}
        for metric in recent_metrics:
            query_type = metric.query_type
            if query_type not in metrics_by_type:
                metrics_by_type[query_type] = []
            metrics_by_type[query_type].append(metric)
        
        summary = PerformanceSummary(
            status="healthy" if self._is_system_healthy(recent_metrics) else "degraded",
            average_precision=float(np.mean([m.precision for m in recent_metrics])),
            average_recall=float(np.mean([m.recall for m in recent_metrics])),
            average_latency_ms=float(np.mean([m.latency_ms for m in recent_metrics])),
            query_type_breakdown={
                qtype: {
                    "precision": float(np.mean([m.precision for m in metrics])),
                    "recall": float(np.mean([m.recall for m in metrics])),
                    "latency_ms": float(np.mean([m.latency_ms for m in metrics])),
                    "count": len(metrics)
                }
                for qtype, metrics in metrics_by_type.items()
            },
            time_window=window_size if isinstance(window_size, timedelta) else timedelta(seconds=0)
        )
        
        return summary
        
    def _is_system_healthy(self, metrics: List[RetrievalMetrics]) -> bool:
        """Check if the system is healthy based on given metrics."""
        if not metrics:
            return True
            
        avg_precision = np.mean([m.precision for m in metrics])
        avg_recall = np.mean([m.recall for m in metrics])
        avg_latency = np.mean([m.latency_ms for m in metrics])
        
        return (
            avg_precision >= 0.7 and
            avg_recall >= 0.5 and
            avg_latency <= 1000  # 1 second
        )
    
    def check_system_health(self) -> ValidationResult:
        """Check overall system health based on recent metrics."""
        if not self.metrics_history:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                issues=["No metrics data available yet"],
                suggestions=[]
            )
        
        recent_metrics = self.metrics_history[-100:]  # Last 100 operations
        is_healthy = self._is_system_healthy(recent_metrics)
        
        issues = []
        suggestions = []
        
        # Check performance thresholds
        avg_precision = np.mean([m.precision for m in recent_metrics])
        if avg_precision < 0.7:
            issues.append("Low precision")
            suggestions.append("Consider adjusting similarity thresholds")
        
        avg_latency = np.mean([m.latency_ms for m in recent_metrics])
        if avg_latency > 1000:  # 1 second
            issues.append("High latency")
            suggestions.append("Consider optimizing retrieval pipeline")
            
        return ValidationResult(
            is_valid=is_healthy,
            confidence=0.9 if is_healthy else 0.7,
            issues=issues,
            suggestions=suggestions
        )

class ResponseValidator:
    """Validates retrieval responses."""
    
    def validate_result(self, result: RetrievalResult) -> ValidationResult:
        """Validate a retrieval result."""
        issues = []
        suggestions = []
        
        # Check for empty results
        if not result.chunks:
            issues.append("No chunks retrieved")
            suggestions.append("Try broadening the search criteria")
            return ValidationResult(
                is_valid=False,
                confidence=0.7,
                issues=issues,
                suggestions=suggestions
            )
        
        # Check similarity scores
        if any(score < result.query.min_similarity for score in result.similarity_scores):
            issues.append("Low similarity scores detected")
            suggestions.append("Consider refining the query or adjusting thresholds")
        
        # Check execution time
        if result.execution_time > 1.0:  # More than 1 second
            issues.append("High latency detected")
            suggestions.append("Consider optimizing the retrieval pipeline")
            
        # Check context
        if result.context is None:
            issues.append("Missing context information")
            suggestions.append("Enable context enrichment for better results")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=0.9 if len(issues) == 0 else 0.7,
            issues=issues,
            suggestions=suggestions
        )
