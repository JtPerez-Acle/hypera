"""Metrics analysis agent for evaluating code quality and complexity."""

import os
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext, CodeMetrics, MetadataExtractionLevel


class MetricsAnalysisAgent(BaseAgent):
    """Analyzes code for quality metrics and complexity."""

    def get_metadata_requirements(self) -> MetadataExtractionLevel:
        """Get metadata requirements for metrics analysis."""
        return MetadataExtractionLevel.FULL

    def get_system_prompt(self) -> str:
        """Get system prompt for metrics analysis."""
        return """You are a code quality expert analyzing code metrics and complexity.
        Focus on identifying:
        1. Cyclomatic complexity
        2. Code duplication
        3. Function/method size
        4. Code maintainability
        5. Performance considerations
        
        Provide detailed analysis of code metrics and suggest improvements."""

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
