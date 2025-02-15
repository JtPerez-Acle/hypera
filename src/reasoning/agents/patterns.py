"""Pattern analysis agent for identifying design patterns and architectural patterns."""

import os
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext, DesignPattern


class PatternAnalyzer(BaseAgent):
    """Analyzes code for design patterns and architectural patterns."""

    def get_system_prompt(self) -> str:
        return (
            "You are an expert in software design patterns and architecture. "
            "Your analysis should:\n"
            "1. Leverage the rich metadata provided\n"
            "2. Consider the full context from Gemini retrieval\n"
            "3. Identify and analyze:\n"
            "   - Common design patterns\n"
            "   - Architectural patterns\n"
            "   - Code organization principles\n"
            "   - Pattern implementation quality\n"
            "   - Pattern applicability and trade-offs\n"
            "4. Provide concrete examples and evidence\n"
            "5. Consider behavioral implications"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze(self, code_context: CodeContext) -> List[DesignPattern]:
        """Analyze code for design patterns."""
        # Enrich context with metadata and related information
        enriched_context = await self._enrich_context(code_context)
        
        deps = AgentDependencies(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            code_context=enriched_context,
            retrieval_results=[]  # Will be populated by _enrich_context
        )
        
        result = await self.agent.run(
            f"Identify design patterns in this code:\n{enriched_context.code_snippet}",
            deps=deps
        )
        return [DesignPattern(**pattern) for pattern in result.data.findings.get("patterns", [])]
