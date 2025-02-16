"""
Multi-agent reasoning system for code analysis.
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, UTC
from zoneinfo import ZoneInfo

from ..types import (
    AgentAnalysis,
    CodeContext,
    ComprehensiveAnalysis,
    CodeUnderstandingLevel,
    SecurityIssue,
    DesignPattern,
    CodeMetrics,
    DependencyInfo
)
from .base import BaseAgent
from .metadata_agent import MetadataGenerationAgent
from .patterns import PatternAnalysisAgent
from .security import SecurityAnalysisAgent
from .behavioral import BehavioralAnalysisAgent
from .dependencies import DependencyAnalysisAgent
from .metrics import MetricsAnalysisAgent
from src.retrieval.gemini import GeminiRetriever
from src.reasoning.types import GPT4MiniModel

logger = logging.getLogger(__name__)

class ReasoningSystem:
    """System for coordinating multiple reasoning agents."""
    
    def __init__(
        self,
        metadata_extractor: MetadataGenerationAgent,
        gemini_retriever: GeminiRetriever,
        model: Optional[GPT4MiniModel] = None
    ):
        """Initialize the reasoning system.
        
        Args:
            metadata_extractor: Agent for generating metadata
            gemini_retriever: Retriever for similar code examples
            model: Optional GPT4Mini model for analysis
        """
        self.metadata_extractor = metadata_extractor
        self.gemini_retriever = gemini_retriever
        self.model = model
        
        # Initialize analysis agents
        self.behavioral_agent = BehavioralAnalysisAgent(
            metadata_extractor=metadata_extractor,
            gemini_retriever=gemini_retriever,
            model=model
        )
        self.security_agent = SecurityAnalysisAgent(
            metadata_extractor=metadata_extractor,
            gemini_retriever=gemini_retriever,
            model=model
        )
        self.pattern_agent = PatternAnalysisAgent(
            metadata_extractor=metadata_extractor,
            gemini_retriever=gemini_retriever,
            model=model
        )
        self.metrics_agent = MetricsAnalysisAgent(
            metadata_extractor=metadata_extractor,
            gemini_retriever=gemini_retriever,
            model=model
        )
        self.dependency_agent = DependencyAnalysisAgent(
            metadata_extractor=metadata_extractor,
            gemini_retriever=gemini_retriever,
            model=model
        )
        
        self.agents = {
            "behavioral": self.behavioral_agent,
            "security": self.security_agent,
            "pattern": self.pattern_agent,
            "metrics": self.metrics_agent,
            "dependency": self.dependency_agent
        }
    
    @classmethod
    def create_default(
        cls,
        gpt4_mini_key: Optional[str] = None,
        gemini_key: Optional[str] = None
    ) -> 'ReasoningSystem':
        """Create a default reasoning system.
        
        Args:
            gpt4_mini_key: Optional GPT4Mini API key
            gemini_key: Optional Gemini API key
            
        Returns:
            Configured reasoning system
        """
        model = GPT4MiniModel(api_key=gpt4_mini_key) if gpt4_mini_key else None
        metadata_extractor = MetadataGenerationAgent(model=model)
        gemini_retriever = GeminiRetriever(api_key=gemini_key) if gemini_key else None
        return cls(metadata_extractor, gemini_retriever, model)
    
    async def analyze(
        self,
        context: CodeContext,
        query: Optional[str] = None
    ) -> ComprehensiveAnalysis:
        """Analyze code using all available agents.
        
        Args:
            context: Context about the code being analyzed
            query: Optional query for the analysis
            
        Returns:
            Comprehensive analysis from all agents
        """
        try:
            # Create tasks for each agent
            tasks = [
                asyncio.create_task(self._run_agent_with_timeout(agent, context))
                for agent in self.agents.values()
            ]
            
            # Run tasks with semaphore for parallel control
            sem = asyncio.Semaphore(1)
            async with sem:
                analyses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and collect issues
            valid_analyses = []
            issues = []
            for analysis in analyses:
                if isinstance(analysis, Exception):
                    issues.append(str(analysis))
                else:
                    valid_analyses.append(analysis)
            
            # Extract specific findings
            security_issues: List[SecurityIssue] = []
            design_patterns: List[DesignPattern] = []
            code_metrics: Optional[CodeMetrics] = None
            dependencies: List[DependencyInfo] = []
            recommendations: List[str] = []
            
            for analysis in valid_analyses:
                findings = analysis.findings
                
                # Security findings
                if analysis.agent_name == "security_analyzer":
                    security_issues.extend(findings.get("issues", []))
                    recommendations.extend(findings.get("recommendations", []))
                
                # Pattern findings
                elif analysis.agent_name == "pattern_analyzer":
                    design_patterns.extend(findings.get("patterns", []))
                    recommendations.extend(findings.get("recommendations", []))
                
                # Metrics findings
                elif analysis.agent_name == "metrics_analyzer":
                    metrics = findings.get("metrics")
                    if metrics:
                        code_metrics = CodeMetrics(**metrics)
                
                # Dependency findings
                elif analysis.agent_name == "dependency_analyzer":
                    dependencies.extend(findings.get("dependencies", []))
            
            # Generate summary
            summary = self._generate_summary(
                valid_analyses,
                security_issues,
                design_patterns,
                code_metrics,
                dependencies,
                issues
            )
            
            return ComprehensiveAnalysis(
                query=query or "",  # Empty string instead of None
                code_context=context,
                agent_analyses=valid_analyses,
                summary=summary,
                security_issues=security_issues,
                design_patterns=design_patterns,
                code_metrics=code_metrics,
                dependencies=dependencies[0] if dependencies else DependencyInfo(
                    direct_deps=[],
                    indirect_deps=[],
                    circular_deps=[],
                    external_deps={}
                ),  # Default DependencyInfo with empty values
                recommendations=recommendations,
                warnings=issues,
                timestamp=datetime.now(UTC),
                success=all(a.confidence > 0.5 for a in valid_analyses)
            )
            
        except Exception as e:
            return ComprehensiveAnalysis(
                query="",  # Empty string instead of None
                code_context=context,
                agent_analyses=[],
                summary=f"Error during analysis: {str(e)}",
                security_issues=[],
                design_patterns=[],
                code_metrics=None,
                dependencies=DependencyInfo(
                    direct_deps=[],
                    indirect_deps=[],
                    circular_deps=[],
                    external_deps={}
                ),  # Default DependencyInfo with empty values
                recommendations=[],
                warnings=[str(e)],
                timestamp=datetime.now(UTC),
                success=False
            )
    
    async def _run_agent_with_timeout(
        self,
        agent: BaseAgent,
        context: CodeContext
    ) -> AgentAnalysis:
        """Run an agent's analysis with timeout.
        
        Args:
            agent: Agent to run
            context: Code context to analyze
            
        Returns:
            Agent's analysis or error analysis if timeout
        """
        try:
            return await asyncio.wait_for(
                agent.analyze(context),
                timeout=30
            )
        except asyncio.TimeoutError:
            return AgentAnalysis(
                agent_name=agent.name,
                understanding_level=CodeUnderstandingLevel.SURFACE,
                findings={"error": "Analysis timed out"},
                confidence=0.0,
                warnings=[f"Agent timed out after 30 seconds"]
            )
        except Exception as e:
            return AgentAnalysis(
                agent_name=agent.name,
                understanding_level=CodeUnderstandingLevel.SURFACE,
                findings={"error": str(e)},
                confidence=0.0,
                warnings=[f"Agent failed: {str(e)}"]
            )

    def _generate_summary(
        self,
        analyses: List[Any],
        security_issues: List[SecurityIssue],
        design_patterns: List[DesignPattern],
        code_metrics: Optional[CodeMetrics],
        dependencies: List[DependencyInfo],
        issues: List[str]
    ) -> str:
        """Generate a summary of the analysis results."""
        summary_parts = []
        
        # Add analysis overview
        summary_parts.append(
            f"Analyzed code using {len(analyses)} agents"
        )
        
        # Add security summary
        if security_issues:
            summary_parts.append(
                f"Found {len(security_issues)} security issues"
            )
        
        # Add patterns summary
        if design_patterns:
            summary_parts.append(
                f"Identified {len(design_patterns)} design patterns"
            )
        
        # Add metrics summary
        if code_metrics:
            summary_parts.append(
                f"Code metrics: complexity={code_metrics.complexity:.2f}, "
                f"maintainability={code_metrics.maintainability:.2f}"
            )
        
        # Add dependency summary
        if dependencies:
            summary_parts.append(
                f"Found {len(dependencies)} dependencies"
            )
        
        # Add issues if any
        if issues:
            summary_parts.append(
                f"Encountered {len(issues)} issues during analysis"
            )
        
        return "\n".join(summary_parts)
