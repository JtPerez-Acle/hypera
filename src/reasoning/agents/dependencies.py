"""Dependency analysis agent for understanding code dependencies and relationships."""

import os
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext, DependencyInfo


class DependencyAnalyzer(BaseAgent):
    """Analyzes code dependencies and relationships."""

    def get_system_prompt(self) -> str:
        return (
            "You are an expert in analyzing code dependencies and relationships. "
            "Your analysis should:\n"
            "1. Leverage the rich metadata provided\n"
            "2. Consider the full context from Gemini retrieval\n"
            "3. Focus on:\n"
            "   - Direct dependencies\n"
            "   - Indirect dependencies\n"
            "   - Circular dependencies\n"
            "   - External package usage\n"
            "   - Dependency graph analysis\n"
            "4. Provide concrete examples and evidence\n"
            "5. Consider behavioral implications"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze(self, code_context: CodeContext) -> DependencyInfo:
        """Analyze code dependencies."""
        # Enrich context with metadata and related information
        enriched_context = await self._enrich_context(code_context)
        
        deps = AgentDependencies(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            code_context=enriched_context,
            retrieval_results=[]  # Will be populated by _enrich_context
        )
        
        result = await self.agent.run(
            f"Analyze dependencies in this code:\n{enriched_context.code_snippet}",
            deps=deps
        )
        return DependencyInfo(**result.data.findings.get("dependencies", {}))
