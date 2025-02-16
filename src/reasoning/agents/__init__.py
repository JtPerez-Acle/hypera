"""
Multi-agent system for advanced code reasoning.

This package implements a sophisticated multi-agent system that combines:
1. GPT-4-mini for efficient metadata generation
2. DeepSeek R1's reasoning capabilities
3. Gemini 1.5 Pro's 2M token context window
4. Rich metadata integration for deep code understanding

The system uses specialized agents that work together to analyze different
aspects of code, from behavior to architecture, while maintaining a shared
context and metadata store.
"""

from typing import List, Type

from .base import BaseAgent
from .behavioral import BehavioralAnalysisAgent as BehavioralAnalyzer
from .security import SecurityAnalysisAgent as SecurityAnalyzer
from .patterns import PatternAnalysisAgent as PatternAnalyzer
from .metrics import MetricsAnalysisAgent as MetricsAnalyzer
from .dependencies import DependencyAnalysisAgent as DependencyAnalyzer
from .system import ReasoningSystem

__all__ = [
    "BaseAgent",
    "BehavioralAnalyzer",
    "SecurityAnalyzer",
    "PatternAnalyzer",
    "MetricsAnalyzer",
    "DependencyAnalyzer",
    "ReasoningSystem"
]
