"""Behavioral analysis agent for understanding code behavior and side effects."""

from typing import Optional, Dict, Any, List

from src.reasoning.types import (
    AgentAnalysis,
    CodeContext,
    MetadataRequest,
    GPT4MiniModel,
    CodeUnderstandingLevel,
    MetadataExtractionLevel,
    AnalysisType,
    Severity
)
from src.retrieval.gemini import GeminiRetriever
from .base import BaseAgent, ResponseDataDict

class BehavioralAnalysisAgent(BaseAgent):
    """Agent for analyzing code behavior and side effects."""
    
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get metadata requirements for behavioral analysis."""
        return MetadataRequest(
            extraction_level=MetadataExtractionLevel.DEEP,
            include_types=True,
            include_dependencies=True,
            include_docstrings=True,
            include_comments=True
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for behavioral analysis."""
        return """You are a specialized code analysis agent focused on understanding code behavior and side effects.
        Your task is to analyze code and identify:

        1. Runtime Behavior:
           - Control flow and execution paths
           - Data transformations and state changes
           - Resource usage (memory, CPU, I/O)
           - Asynchronous operations and concurrency

        2. Side Effects:
           - Mutations of input parameters
           - File system operations
           - Network calls and external API usage
           - Database operations
           - Global state modifications

        3. Error Handling:
           - Exception handling patterns
           - Error propagation
           - Recovery mechanisms
           - Edge cases and failure modes

        4. Performance Implications:
           - Algorithmic complexity
           - Resource consumption patterns
           - Potential bottlenecks
           - Scalability considerations

        Provide your analysis in the following format:
        {
            "agent_name": "behavioral_agent",
            "understanding_level": "behavioral",
            "findings": {
                "runtime_behavior": [...],
                "side_effects": [...],
                "error_handling": [...],
                "performance": [...]
            },
            "confidence": <float between 0 and 1>,
            "supporting_evidence": [<list of specific code patterns>],
            "warnings": [<list of potential issues>]
        }

        Focus on being precise and thorough in your analysis.
        """
    
    async def analyze(self, code_context: CodeContext) -> AgentAnalysis:
        """Analyze code behavior and generate behavioral analysis.

        Args:
            code_context: Code context to analyze

        Returns:
            Analysis of code behavior
        """
        try:
            # Enrich context with metadata
            code_context = await self._enrich_context(code_context)
            
            # Run behavioral analysis
            response = await self.agent.run(
                context=code_context,
                query="Analyze the behavior of this code"
            )
            
            # Extract findings
            findings = {
                "runtime_behavior": response.findings.get("runtime_behavior", []),
                "side_effects": response.findings.get("side_effects", []),
                "error_handling": response.findings.get("error_handling", [])
            }
            
            # Create evidence list
            evidence = [code_context.code_snippet]
            if code_context.metadata and code_context.metadata.docstrings:
                evidence.append(f"Docstrings: {code_context.metadata.docstrings}")
            
            return AgentAnalysis(
                agent_name="behavioral_agent",
                understanding_level=code_context.understanding_level,
                findings=findings,
                supporting_evidence=evidence,
                confidence=response.confidence,
                analysis_type=AnalysisType.BEHAVIORAL,
                severity=Severity.INFO
            )
            
        except Exception as e:
            return AgentAnalysis(
                agent_name="behavioral_agent",
                findings={
                    "error": [f"Error analyzing behavior: {str(e)}"]
                },
                supporting_evidence=["Error occurred during analysis"],
                confidence=0.0,
                analysis_type=AnalysisType.BEHAVIORAL,
                severity=Severity.ERROR
            )
