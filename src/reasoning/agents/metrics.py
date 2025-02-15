"""Metrics analysis agent for evaluating code quality and complexity."""

import os
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext, CodeMetrics


class MetricsAnalyzer(BaseAgent):
    """Analyzes code for quality metrics and complexity."""

    def get_system_prompt(self) -> str:
        return (
            "You are an expert in code quality and metrics analysis. "
            "Your analysis should:\n"
            "1. Leverage the rich metadata provided\n"
            "2. Consider the full context from Gemini retrieval\n"
            "3. Calculate and evaluate:\n"
            "   - Code complexity metrics\n"
            "   - Maintainability indices\n"
            "   - Code quality indicators\n"
            "   - Testing coverage needs\n"
            "   - Technical debt indicators\n"
            "4. Provide concrete examples and evidence\n"
            "5. Consider behavioral implications"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze(self, code_context: CodeContext) -> CodeMetrics:
        """Analyze code for quality metrics."""
        # Enrich context with metadata and related information
        enriched_context = await self._enrich_context(code_context)
        
        deps = AgentDependencies(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            code_context=enriched_context,
            retrieval_results=[]  # Will be populated by _enrich_context
        )
        
        result = await self.agent.run(
            f"Calculate metrics for this code:\n{enriched_context.code_snippet}",
            deps=deps
        )
        return CodeMetrics(**result.data.findings.get("metrics", {}))
