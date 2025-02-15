"""Security analysis agent for identifying vulnerabilities and security issues."""

import os
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseAgent
from ..types import AgentAnalysis, AgentDependencies, CodeContext, SecurityIssue


class SecurityAnalyzer(BaseAgent):
    """Analyzes code for security vulnerabilities and best practices."""

    def get_system_prompt(self) -> str:
        return (
            "You are a security expert analyzing code for vulnerabilities. "
            "Your analysis should:\n"
            "1. Leverage the rich metadata provided\n"
            "2. Consider the full context from Gemini retrieval\n"
            "3. Look for:\n"
            "   - Security vulnerabilities\n"
            "   - Input validation issues\n"
            "   - Authentication/authorization gaps\n"
            "   - Data exposure risks\n"
            "   - Secure coding best practices\n"
            "4. Provide concrete examples and evidence\n"
            "5. Consider behavioral implications"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze(self, code_context: CodeContext) -> List[SecurityIssue]:
        """Analyze code for security issues."""
        # Enrich context with metadata and related information
        enriched_context = await self._enrich_context(code_context)
        
        deps = AgentDependencies(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            code_context=enriched_context,
            retrieval_results=[]  # Will be populated by _enrich_context
        )
        
        result = await self.agent.run(
            f"Identify security issues in this code:\n{enriched_context.code_snippet}",
            deps=deps
        )
        return [SecurityIssue(**issue) for issue in result.data.findings.get("issues", [])]
