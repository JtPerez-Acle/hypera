"""Adaptive retriever with learning capabilities for improved code search."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .gemini import GeminiRetriever
from .types import RetrievalQuery, RetrievalResult
from ..core.coordinator import AgentCoordinator


class QueryPattern(BaseModel):
    """Pattern discovered in queries."""
    pattern_type: str
    frequency: int
    success_rate: float
    last_seen: datetime
    examples: List[str] = Field(default_factory=list)


class SearchStrategy(BaseModel):
    """Strategy for code search."""
    similarity_threshold: float
    max_results: int
    rerank_count: int
    use_metadata: bool
    success_rate: float = 0.0


@dataclass
class QueryPerformance:
    """Performance metrics for queries."""
    total_queries: int = 0
    successful_queries: int = 0
    avg_latency: float = 0.0
    last_updated: datetime = datetime.now()


class AdaptiveRetriever(GeminiRetriever):
    """Enhanced retriever with adaptive search capabilities."""

    def __init__(
        self,
        coordinator: Optional[AgentCoordinator] = None
    ):
        """Initialize the adaptive retriever."""
        super().__init__()
        self.coordinator = coordinator
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.search_strategies: Dict[str, SearchStrategy] = {
            "quick": SearchStrategy(
                similarity_threshold=0.7,
                max_results=5,
                rerank_count=10,
                use_metadata=False
            ),
            "balanced": SearchStrategy(
                similarity_threshold=0.6,
                max_results=10,
                rerank_count=20,
                use_metadata=True
            ),
            "thorough": SearchStrategy(
                similarity_threshold=0.5,
                max_results=20,
                rerank_count=40,
                use_metadata=True
            )
        }
        self.performance: Dict[str, QueryPerformance] = {
            k: QueryPerformance() for k in self.search_strategies
        }

    async def retrieve(
        self,
        query: RetrievalQuery,
        agent_id: Optional[str] = None
    ) -> RetrievalResult:
        """
        Retrieve code chunks with adaptive search.
        
        Args:
            query: The retrieval query
            agent_id: Optional ID of the requesting agent
            
        Returns:
            Retrieved chunks with context
        """
        # Select best strategy based on query and context
        strategy = await self._select_strategy(query, agent_id)
        
        # Enhance query based on learned patterns
        enhanced_query = await self._enhance_query(query)
        
        try:
            # Perform retrieval with selected strategy
            start_time = datetime.now()
            result = await super().retrieve(
                enhanced_query,
                similarity_threshold=strategy.similarity_threshold,
                max_results=strategy.max_results,
                rerank_count=strategy.rerank_count,
                use_metadata=strategy.use_metadata
            )
            
            # Update performance metrics
            duration = (datetime.now() - start_time).total_seconds()
            await self._update_performance(
                strategy_name=self._get_strategy_name(strategy),
                success=True,
                latency=duration,
                result=result
            )
            
            # Learn from successful retrieval
            await self._learn_patterns(query, result)
            
            return result
            
        except Exception as e:
            # Update performance metrics on failure
            await self._update_performance(
                strategy_name=self._get_strategy_name(strategy),
                success=False,
                latency=0.0,
                result=None
            )
            raise

    async def _select_strategy(
        self,
        query: RetrievalQuery,
        agent_id: Optional[str]
    ) -> SearchStrategy:
        """Select the best search strategy."""
        # Get agent context if available
        agent_context = None
        if self.coordinator and agent_id:
            agent_context = await self.coordinator.get_agent_context(agent_id)
        
        # Analyze query characteristics
        query_complexity = self._estimate_query_complexity(query)
        
        # Consider agent's context window if available
        window_size = (
            agent_context.get("window_size", 500_000)
            if agent_context else 500_000
        )
        
        # Select strategy based on characteristics
        if query_complexity > 0.8 or window_size > 1_000_000:
            return self.search_strategies["thorough"]
        elif query_complexity > 0.4 or window_size > 500_000:
            return self.search_strategies["balanced"]
        else:
            return self.search_strategies["quick"]

    def _estimate_query_complexity(
        self,
        query: RetrievalQuery
    ) -> float:
        """Estimate query complexity (0-1)."""
        # Consider various query aspects
        factors = [
            len(query.text.split()),  # Number of words
            len(query.filters or []),  # Number of filters
            query.text.count('"'),     # Exact phrase matches
            bool(query.code_context),  # Has code context
            bool(query.metadata)       # Has metadata
        ]
        
        # Normalize and combine factors
        weights = [0.3, 0.2, 0.1, 0.2, 0.2]
        return sum(
            f * w for f, w in zip(factors, weights)
        ) / sum(weights)

    async def _enhance_query(
        self,
        query: RetrievalQuery
    ) -> RetrievalQuery:
        """Enhance query based on learned patterns."""
        # Clone query for modification
        enhanced = query.model_copy()
        
        # Apply relevant patterns
        for pattern in self.query_patterns.values():
            if pattern.success_rate > 0.7:  # Only use successful patterns
                if pattern.pattern_type == "filter_enhancement":
                    enhanced.filters = self._enhance_filters(
                        enhanced.filters,
                        pattern
                    )
                elif pattern.pattern_type == "context_enhancement":
                    enhanced.code_context = self._enhance_context(
                        enhanced.code_context,
                        pattern
                    )
        
        return enhanced

    async def _update_performance(
        self,
        strategy_name: str,
        success: bool,
        latency: float,
        result: Optional[RetrievalResult]
    ) -> None:
        """Update performance metrics."""
        if strategy_name not in self.performance:
            return
            
        perf = self.performance[strategy_name]
        perf.total_queries += 1
        if success:
            perf.successful_queries += 1
            perf.avg_latency = (
                (perf.avg_latency * (perf.total_queries - 1) + latency)
                / perf.total_queries
            )
        
        perf.last_updated = datetime.now()
        
        # Share insights if coordinator exists
        if self.coordinator:
            await self.coordinator.share_knowledge(
                "retriever",
                {
                    "performance": {
                        strategy_name: {
                            "success_rate": (
                                perf.successful_queries / perf.total_queries
                            ),
                            "avg_latency": perf.avg_latency,
                            "last_updated": perf.last_updated
                        }
                    }
                }
            )

    async def _learn_patterns(
        self,
        query: RetrievalQuery,
        result: RetrievalResult
    ) -> None:
        """Learn patterns from successful retrievals."""
        # Analyze query structure
        if query.filters:
            pattern_type = "filter_enhancement"
            if pattern_type not in self.query_patterns:
                self.query_patterns[pattern_type] = QueryPattern(
                    pattern_type=pattern_type,
                    frequency=1,
                    success_rate=1.0,
                    last_seen=datetime.now(),
                    examples=[str(query.filters)]
                )
            else:
                pattern = self.query_patterns[pattern_type]
                pattern.frequency += 1
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.frequency - 1) + 1.0)
                    / pattern.frequency
                )
                pattern.last_seen = datetime.now()
                if len(pattern.examples) < 5:
                    pattern.examples.append(str(query.filters))

    def _get_strategy_name(
        self,
        strategy: SearchStrategy
    ) -> str:
        """Get the name of a strategy from its parameters."""
        for name, s in self.search_strategies.items():
            if (
                s.similarity_threshold == strategy.similarity_threshold and
                s.max_results == strategy.max_results
            ):
                return name
        return "custom"

    def _enhance_filters(
        self,
        filters: Optional[List[Dict[str, Any]]],
        pattern: QueryPattern
    ) -> Optional[List[Dict[str, Any]]]:
        """Enhance query filters based on pattern."""
        if not filters:
            return filters
        return filters  # Placeholder for actual enhancement

    def _enhance_context(
        self,
        context: Optional[Dict[str, Any]],
        pattern: QueryPattern
    ) -> Optional[Dict[str, Any]]:
        """Enhance code context based on pattern."""
        if not context:
            return context
        return context  # Placeholder for actual enhancement
