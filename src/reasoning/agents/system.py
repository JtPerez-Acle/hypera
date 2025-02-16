"""Reasoning system that orchestrates multiple agents for comprehensive code analysis."""

from typing import List, Optional, Dict, Any
from ...metadata.extractor import MetadataExtractor
from ...metadata.types import MetadataRequest, MetadataExtractionLevel
from ..types import (
    AgentAnalysis,
    CodeContext,
    ComprehensiveAnalysis,
    SecurityIssue,
    DesignPattern,
    CodeMetrics,
    DependencyInfo,
    AgentDependencies
)


class ReasoningSystem:
    """Orchestrates multiple agents for comprehensive code analysis."""

    def __init__(
        self,
        metadata_extractor: Optional[MetadataExtractor] = None,
        gemini_retriever: Optional[GeminiRetriever] = None
    ):
        """Initialize the reasoning system.
        
        Args:
            metadata_extractor: Component for extracting rich metadata
            gemini_retriever: Component for retrieving relevant context
        """
        # Initialize shared components
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.gemini_retriever = gemini_retriever or GeminiRetriever()
        
        # Initialize agents with shared components
        self.agents = {
            "behavioral": BehavioralAnalyzer(
                metadata_extractor=self.metadata_extractor,
                gemini_retriever=self.gemini_retriever
            ),
            "security": SecurityAnalyzer(
                metadata_extractor=self.metadata_extractor,
                gemini_retriever=self.gemini_retriever
            ),
            "patterns": PatternAnalyzer(
                metadata_extractor=self.metadata_extractor,
                gemini_retriever=self.gemini_retriever
            ),
            "metrics": MetricsAnalyzer(
                metadata_extractor=self.metadata_extractor,
                gemini_retriever=self.gemini_retriever
            ),
            "dependencies": DependencyAnalyzer(
                metadata_extractor=self.metadata_extractor,
                gemini_retriever=self.gemini_retriever
            ),
        }

    async def analyze(self, query: str, code_context: CodeContext) -> ComprehensiveAnalysis:
        """
        Perform comprehensive code analysis using all agents.

        This method:
        1. Enriches the context with metadata and related information
        2. Runs all agents in parallel for efficiency
        3. Combines their analyses into a comprehensive result
        4. Uses Gemini to generate natural language summaries
        
        Args:
            query: The analysis query from the user
            code_context: Context about the code to analyze

        Returns:
            A comprehensive analysis combining all agent results
        """
        # First, enrich the context once for all agents
        enriched_context = await self.agents["behavioral"]._enrich_context(code_context)
        
        # Run all agents in parallel
        behavioral_analysis = await self.agents["behavioral"].analyze(enriched_context)
        security_issues = await self.agents["security"].analyze(enriched_context)
        design_patterns = await self.agents["patterns"].analyze(enriched_context)
        metrics = await self.agents["metrics"].analyze(enriched_context)
        dependencies = await self.agents["dependencies"].analyze(enriched_context)

        # Use Gemini to generate a natural language summary
        summary = await self._generate_summary_with_gemini(
            query,
            behavioral_analysis,
            security_issues,
            design_patterns,
            metrics,
            dependencies
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations_with_gemini(
            security_issues,
            design_patterns,
            metrics,
            dependencies
        )

        return ComprehensiveAnalysis(
            query=query,
            agent_analyses=[behavioral_analysis],  # Add other agent analyses
            security_issues=security_issues,
            design_patterns=design_patterns,
            metrics=metrics,
            dependencies=dependencies,
            summary=summary,
            recommendations=recommendations
        )

    async def _generate_summary_with_gemini(
        self,
        query: str,
        behavioral: AgentAnalysis,
        security: List[SecurityIssue],
        patterns: List[DesignPattern],
        metrics: CodeMetrics,
        dependencies: DependencyInfo,
    ) -> str:
        """Generate a comprehensive summary using Gemini 1.5 Pro."""
        # Prepare the context for Gemini
        context = {
            "query": query,
            "behavioral_analysis": behavioral.dict(),
            "security_issues": [issue.dict() for issue in security],
            "design_patterns": [pattern.dict() for pattern in patterns],
            "metrics": metrics.dict(),
            "dependencies": dependencies.dict()
        }
        
        # Use Gemini to generate a natural language summary
        return await self.gemini_retriever.generate_summary(context)

    async def _generate_recommendations_with_gemini(
        self,
        security: List[SecurityIssue],
        patterns: List[DesignPattern],
        metrics: CodeMetrics,
        dependencies: DependencyInfo,
    ) -> List[str]:
        """Generate actionable recommendations using Gemini 1.5 Pro."""
        # Prepare the context for Gemini
        context = {
            "security_issues": [issue.dict() for issue in security],
            "design_patterns": [pattern.dict() for pattern in patterns],
            "metrics": metrics.dict(),
            "dependencies": dependencies.dict()
        }
        
        # Use Gemini to generate recommendations
        return await self.gemini_retriever.generate_recommendations(context)
