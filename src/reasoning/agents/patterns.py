"""Pattern analysis agent for code analysis."""

import logging
from typing import Optional, Dict, Any, List

from src.llm.gpt4_mini import GPT4MiniModel
from src.retrieval.gemini import GeminiRetriever
from src.reasoning.types import (
    AgentAnalysis,
    CodeContext,
    MetadataRequest,
    MetadataExtractionLevel,
    CodeUnderstandingLevel
)
from src.reasoning.agents.metadata_agent import MetadataGenerationAgent
from .base import BaseAgent, ResponseData

class PatternAnalysisAgent(BaseAgent):
    """Agent for analyzing code patterns."""
    
    def __init__(
        self,
        model: Optional[GPT4MiniModel] = None,
        gemini_retriever: Optional[GeminiRetriever] = None,
        metadata_extractor: Optional[MetadataGenerationAgent] = None
    ):
        """Initialize the pattern analysis agent.
        
        Args:
            model: Optional GPT4Mini model for analysis
            gemini_retriever: Optional Gemini retriever for similar code examples
            metadata_extractor: Optional metadata generation agent
        """
        super().__init__(
            model=model,
            gemini_retriever=gemini_retriever,
            metadata_extractor=metadata_extractor
        )
    
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get metadata requirements for pattern analysis."""
        return MetadataRequest(
            extraction_level=MetadataExtractionLevel.DEEP,
            include_types=True,
            include_dependencies=True,
            include_docstrings=True,
            include_comments=True
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for pattern analysis."""
        return """You are a specialized code analysis agent focused on identifying patterns.
        Your task is to analyze code and identify:

        1. Design Patterns:
           - Creational patterns
           - Structural patterns
           - Behavioral patterns
           - Architectural patterns

        2. Code Organization:
           - Module structure
           - Class hierarchies
           - Interface definitions
           - Package organization

        3. Implementation Patterns:
           - Error handling
           - Resource management
           - Concurrency patterns
           - State management

        4. Best Practices:
           - Code style
           - Documentation
           - Testing patterns
           - Performance optimization

        Provide your analysis in the following format:
        {
            "agent_name": "pattern_analyzer",
            "understanding_level": "patterns",
            "findings": {
                "design_patterns": [...],
                "organization": [...],
                "implementation": [...],
                "best_practices": [...]
            },
            "confidence": <float between 0 and 1>,
            "supporting_evidence": [<list of specific code patterns>],
            "warnings": [<list of potential issues>]
        }

        Focus on being thorough and precise in your pattern analysis.
        """
    
    async def analyze(self, context: CodeContext) -> AgentAnalysis:
        """Analyze code patterns.
        
        Args:
            context: Code context to analyze
            
        Returns:
            Analysis containing pattern findings
        """
        # Get metadata if available
        if self.metadata_extractor:
            metadata = await self.metadata_extractor.analyze(context)
        else:
            metadata = None
        
        # Get similar code examples for context
        if self.gemini_retriever:
            similar_code = await self.gemini_retriever.get_context(
                context.code,
                max_examples=3
            )
        else:
            similar_code = []
        
        # Run pattern analysis
        response = await self.agent.run(
            {
                "code": context.code,
                "similar_examples": similar_code,
                "metadata": metadata.dict() if metadata else {}
            }
        )
        
        # Convert response to AgentAnalysis
        return AgentAnalysis(
            agent_name=response.agent_name,
            understanding_level=CodeUnderstandingLevel(response.understanding_level),
            findings=response.findings,
            confidence=response.confidence,
            supporting_evidence=response.supporting_evidence,
            warnings=response.warnings
        )
