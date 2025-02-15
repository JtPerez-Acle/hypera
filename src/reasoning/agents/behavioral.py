"""Behavioral analysis agent for understanding code behavior and side effects."""

import os
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext


class BehavioralAnalyzer(BaseAgent):
    """Analyzes code behavior, side effects, and runtime characteristics."""

    def get_system_prompt(self) -> str:
        return (
            "You are an expert in analyzing code behavior and side effects. "
            "Your analysis should:\n"
            "1. Leverage the rich metadata provided\n"
            "2. Consider the full context from Gemini retrieval\n"
            "3. Focus on:\n"
            "   - Function side effects and mutations\n"
            "   - State changes and their scope\n"
            "   - Resource usage and lifecycle\n"
            "   - Error handling and edge cases\n"
            "   - Runtime characteristics\n"
            "4. Provide concrete examples and evidence\n"
            "5. Consider security implications"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze(self, code_context: CodeContext) -> AgentAnalysis:
        """Analyze code behavior and side effects."""
        # Enrich context with metadata and related information
        enriched_context = await self._enrich_context(code_context)
        
        deps = AgentDependencies(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            code_context=enriched_context,
            retrieval_results=[]  # Will be populated by _enrich_context
        )
        
        result = await self.agent.run(
            f"Analyze the behavior and side effects of this code:\n{enriched_context.code_snippet}",
            deps=deps
        )
        return result.data
