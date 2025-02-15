"""Adaptive pipeline for intelligent code processing and vector storage."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .pipeline import Pipeline
from .schema import CodeChunkMetadata
from ..core.coordinator import AgentCoordinator


class ChunkingStrategy(BaseModel):
    """Strategy for code chunking."""
    min_chunk_size: int
    max_chunk_size: int
    overlap: int
    split_on: List[str]
    combine_small: bool
    success_rate: float = 0.0


class EmbeddingStats(BaseModel):
    """Statistics for embeddings."""
    dimension: int
    avg_magnitude: float
    avg_similarity: float
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class ChunkPerformance:
    """Performance metrics for a chunking strategy."""
    retrieval_success: int = 0
    total_retrievals: int = 0
    avg_chunk_size: int = 0
    processing_time: float = 0.0


class AdaptivePipeline(Pipeline):
    """Enhanced pipeline with adaptive processing capabilities."""

    def __init__(
        self,
        coordinator: Optional[AgentCoordinator] = None
    ):
        """Initialize the adaptive pipeline."""
        super().__init__()
        self.coordinator = coordinator
        self.chunking_strategies: Dict[str, ChunkingStrategy] = {
            "small": ChunkingStrategy(
                min_chunk_size=50,
                max_chunk_size=200,
                overlap=10,
                split_on=["class ", "def ", "\n\n"],
                combine_small=True
            ),
            "medium": ChunkingStrategy(
                min_chunk_size=150,
                max_chunk_size=500,
                overlap=20,
                split_on=["class ", "def ", "\n\n", "async "],
                combine_small=True
            ),
            "large": ChunkingStrategy(
                min_chunk_size=400,
                max_chunk_size=1000,
                overlap=50,
                split_on=["class ", "def ", "\n\n", "async ", "if __name__"],
                combine_small=False
            )
        }
        self.performance: Dict[str, ChunkPerformance] = {
            k: ChunkPerformance() for k in self.chunking_strategies
        }
        self.embedding_history: List[EmbeddingStats] = []

    async def process_file(
        self,
        file_path: str,
        agent_id: Optional[str] = None
    ) -> List[str]:
        """
        Process a file with adaptive chunking and embedding.
        
        Args:
            file_path: Path to the file to process
            agent_id: Optional ID of the requesting agent
            
        Returns:
            List of stored point IDs
        """
        # Select best strategy based on file and context
        strategy = await self._select_strategy(file_path, agent_id)
        
        try:
            # Process with selected strategy
            start_time = datetime.now()
            point_ids = await super().process_file(
                file_path,
                chunk_params=strategy.dict()
            )
            
            # Update performance metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._update_performance(
                strategy_name=self._get_strategy_name(strategy),
                success=True,
                chunk_count=len(point_ids),
                duration=duration
            )
            
            # Learn from embeddings
            await self._analyze_embeddings(point_ids)
            
            return point_ids
            
        except Exception as e:
            # Update performance metrics on failure
            self._update_performance(
                strategy_name=self._get_strategy_name(strategy),
                success=False,
                chunk_count=0,
                duration=0
            )
            raise

    async def _select_strategy(
        self,
        file_path: str,
        agent_id: Optional[str]
    ) -> ChunkingStrategy:
        """Select the best chunking strategy."""
        # Get agent context if available
        agent_context = None
        if self.coordinator and agent_id:
            agent_context = await self.coordinator.get_agent_context(agent_id)
        
        # Analyze file characteristics
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Consider file size and complexity
        size = len(content)
        complexity = content.count('def ') + content.count('class ')
        
        # Consider agent's context window if available
        window_size = (
            agent_context.get("window_size", 500_000)
            if agent_context else 500_000
        )
        
        # Select strategy based on characteristics
        if size > 10000 or complexity > 20 or window_size > 1_000_000:
            return self.chunking_strategies["large"]
        elif size > 3000 or complexity > 10 or window_size > 500_000:
            return self.chunking_strategies["medium"]
        else:
            return self.chunking_strategies["small"]

    def _update_performance(
        self,
        strategy_name: str,
        success: bool,
        chunk_count: int,
        duration: float
    ) -> None:
        """Update performance metrics for a strategy."""
        if strategy_name not in self.performance:
            return
            
        perf = self.performance[strategy_name]
        perf.total_retrievals += 1
        if success:
            perf.retrieval_success += 1
            perf.avg_chunk_size = (
                (perf.avg_chunk_size * (perf.total_retrievals - 1) + chunk_count)
                / perf.total_retrievals
            )
            perf.processing_time = (
                (perf.processing_time * (perf.total_retrievals - 1) + duration)
                / perf.total_retrievals
            )

    async def _analyze_embeddings(
        self,
        point_ids: List[str]
    ) -> None:
        """Analyze embedding characteristics."""
        points = await self.qdrant.retrieve_points(point_ids)
        if not points:
            return
            
        # Calculate embedding statistics
        vectors = [p.vector for p in points if p.vector]
        if not vectors:
            return
            
        stats = EmbeddingStats(
            dimension=len(vectors[0]),
            avg_magnitude=sum(
                sum(v[i]**2 for i in range(len(v)))**0.5
                for v in vectors
            ) / len(vectors),
            avg_similarity=self._calculate_avg_similarity(vectors)
        )
        
        self.embedding_history.append(stats)
        
        # Share insights if coordinator exists
        if self.coordinator:
            await self.coordinator.share_knowledge(
                "vector_store",
                {"embedding_stats": stats.dict()}
            )

    def _calculate_avg_similarity(
        self,
        vectors: List[List[float]]
    ) -> float:
        """Calculate average cosine similarity between vectors."""
        if len(vectors) < 2:
            return 1.0
            
        total_sim = 0.0
        count = 0
        
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                sim = sum(
                    vectors[i][k] * vectors[j][k]
                    for k in range(len(vectors[i]))
                )
                total_sim += sim
                count += 1
                
        return total_sim / count if count > 0 else 0.0

    def _get_strategy_name(
        self,
        strategy: ChunkingStrategy
    ) -> str:
        """Get the name of a strategy from its parameters."""
        for name, s in self.chunking_strategies.items():
            if (
                s.min_chunk_size == strategy.min_chunk_size and
                s.max_chunk_size == strategy.max_chunk_size
            ):
                return name
        return "custom"
