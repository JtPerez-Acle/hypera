"""
HyperA Reasoning Module.

This module implements the DeepSeek R1-based reasoning engine that processes
enriched context from the retrieval system (Gemini 1.5 Pro) to perform
deep code analysis and understanding.
"""

from .deepseek import DeepSeekReasoner
from .types import ReasoningRequest, ReasoningResponse

__all__ = ["DeepSeekReasoner", "ReasoningRequest", "ReasoningResponse"]
