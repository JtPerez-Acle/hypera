"""
Core coordinator for managing the analysis pipeline.
"""

from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime, UTC
from zoneinfo import ZoneInfo

from src.config import ResourceConfig, GeminiConfig, GPT4MiniConfig
from src.llm.gpt4_mini import GPT4MiniClient
from src.retrieval.gemini import GeminiRetriever
from src.metadata.metadata_manager import MetadataGenerationAgent
from src.reasoning.agents.system import ReasoningSystem
from src.core.metrics import AgentMetrics, SystemMetrics
from src.reasoning.types import (
    CodeContext,
    ComprehensiveAnalysis,
    AgentAnalysis,
    CodeUnderstandingLevel
)

logger = logging.getLogger(__name__)


class SystemCoordinator:
    """Coordinator for the analysis system."""
    
    def __init__(
        self,
        gpt4_mini_key: str,
        gemini_key: str,
        config: Optional[ResourceConfig] = None
    ):
        """Initialize the system coordinator.
        
        Args:
            gpt4_mini_key: API key for GPT-4-mini
            gemini_key: API key for Gemini 1.5 Pro
            config: Optional resource configuration
        """
        self.config = config or ResourceConfig()
        
        # Initialize core components
        self.gemini = GeminiRetriever(
            GeminiConfig(
                api_key=gemini_key,
                max_tokens=self.config.gemini_max_tokens
            )
        )
        self.gpt4_mini = GPT4MiniClient(
            GPT4MiniConfig(
                api_key=gpt4_mini_key,
                max_tokens=self.config.gpt4_mini_max_tokens
            )
        )
        
        # Initialize reasoning system
        metadata_agent = MetadataGenerationAgent()
        self.reasoning = ReasoningSystem(
            metadata_extractor=metadata_agent,
            gemini_retriever=self.gemini,
            model=self.gpt4_mini
        )
        
        # Initialize metrics and cache
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics = SystemMetrics()
        self.cache: Dict[str, ComprehensiveAnalysis] = {}
    
    async def analyze_code(
        self,
        context: CodeContext,
        query: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> ComprehensiveAnalysis:
        """Analyze code using all available agents.
        
        Args:
            context: Context about the code to analyze
            query: Optional specific query to focus the analysis
            cache_key: Optional key for caching results
            
        Returns:
            Comprehensive analysis from all agents
        """
        # Check cache first
        if (
            self.config.enable_retrieval_cache
            and cache_key
            and cache_key in self.cache
        ):
            self.system_metrics.cache_hits += 1
            return self.cache[cache_key]
        
        self.system_metrics.cache_misses += 1
        
        # Start analysis
        start_time = datetime.now()
        try:
            analysis = await self.reasoning.analyze(
                context=context,
                query=query
            )
            
            # Update metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.system_metrics.total_analyses += 1
            self.system_metrics.total_duration += duration
            self.system_metrics.average_duration = (
                self.system_metrics.total_duration / self.system_metrics.total_analyses
            )
            
            # Update token usage
            token_usage = self._get_token_usage(analysis)
            for agent_analysis in analysis.agent_analyses:
                self._update_metrics(
                    agent_id=agent_analysis.agent_name,
                    success=agent_analysis.success,
                    latency=duration,
                    token_usage=token_usage
                )
            
            # Cache results if enabled
            if cache_key and self.config.enable_retrieval_cache:
                self.cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise
    
    async def batch_analyze(
        self,
        contexts: List[CodeContext],
        query: Optional[str] = None
    ) -> List[ComprehensiveAnalysis]:
        """Analyze multiple code contexts in parallel.
        
        Args:
            contexts: List of code contexts to analyze
            query: Optional query to focus the analysis
            
        Returns:
            List of comprehensive analyses
        """
        tasks = []
        for context in contexts:
            task = asyncio.create_task(
                self.analyze_code(
                    context=context,
                    query=query
                )
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks)
            return results
        except Exception as e:
            logger.error(f"Error during batch analysis: {str(e)}")
            raise
    
    def _update_metrics(
        self,
        agent_id: str,
        success: bool,
        latency: float,
        token_usage: Dict[str, int]
    ) -> None:
        """Update agent metrics.
        
        Args:
            agent_id: ID of the agent
            success: Whether the operation succeeded
            latency: Operation latency in seconds
            token_usage: Token usage by model
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics()
        
        metrics = self.agent_metrics[agent_id]
        metrics.total_operations += 1
        
        # Update running averages
        metrics.success_rate = (
            (metrics.success_rate * (metrics.total_operations - 1) + int(success))
            / metrics.total_operations
        )
        metrics.average_latency = (
            (metrics.average_latency * (metrics.total_operations - 1) + latency)
            / metrics.total_operations
        )
        
        # Update token usage
        for model, tokens in token_usage.items():
            current = metrics.token_usage.get(model, 0)
            metrics.token_usage[model] = current + tokens
        
        metrics.last_updated = datetime.now()
    
    def _get_token_usage(self, analysis: ComprehensiveAnalysis) -> Dict[str, int]:
        """Extract token usage from analysis results.
        
        Args:
            analysis: The comprehensive analysis
            
        Returns:
            Dictionary of model names to token counts
        """
        usage: Dict[str, int] = {}
        for agent_analysis in analysis.agent_analyses:
            if isinstance(agent_analysis.findings, dict) and "token_usage" in agent_analysis.findings:
                token_usage = agent_analysis.findings["token_usage"]
                for model, tokens in token_usage.items():
                    usage[model] = usage.get(model, 0) + tokens
        return usage
    
    def get_metrics(self) -> Dict[str, AgentMetrics]:
        """Get current agent metrics.
        
        Returns:
            Dictionary of agent IDs to their metrics
        """
        return self.agent_metrics.copy()
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self.cache.clear()
