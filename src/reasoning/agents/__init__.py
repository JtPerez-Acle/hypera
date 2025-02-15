"""
Multi-agent system for advanced code reasoning.

This package implements a sophisticated multi-agent system that combines:
1. DeepSeek R1's reasoning capabilities
2. Gemini 1.5 Pro's 2M token context window
3. Rich metadata integration for deep code understanding

The system uses specialized agents that work together to analyze different
aspects of code, from behavior to architecture, while maintaining a shared
context and metadata store.
"""

from .base import BaseAgent
from .behavioral import BehavioralAnalyzer
from .security import SecurityAnalyzer
from .patterns import PatternAnalyzer
from .metrics import MetricsAnalyzer
from .dependencies import DependencyAnalyzer
from .system import ReasoningSystem

__all__ = [
    'BaseAgent',
    'BehavioralAnalyzer',
    'SecurityAnalyzer',
    'PatternAnalyzer',
    'MetricsAnalyzer',
    'DependencyAnalyzer',
    'ReasoningSystem',
]
