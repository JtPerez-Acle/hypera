"""Agentic metadata manager for adaptive metadata extraction and management."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from .extractor import MetadataExtractor
from ..core.coordinator import AgentCoordinator


class MetadataPattern(BaseModel):
    """Pattern discovered in code metadata."""
    pattern_type: str
    frequency: int
    confidence: float
    last_seen: datetime
    examples: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class ExtractionStrategy:
    """Strategy for metadata extraction."""
    priority: int
    depth: int
    patterns: List[str]
    last_success_rate: float = 0.0
    times_used: int = 0
    last_used: datetime = field(default_factory=datetime.now)


class AdaptiveMetadataManager:
    """Manages metadata extraction with learning capabilities."""

    def __init__(
        self,
        coordinator: Optional[AgentCoordinator] = None,
        extractor: Optional[MetadataExtractor] = None
    ):
        """Initialize the manager."""
        self.coordinator = coordinator
        self.extractor = extractor or MetadataExtractor()
        self.patterns: Dict[str, MetadataPattern] = {}
        self.strategies: Dict[str, ExtractionStrategy] = {
            "quick": ExtractionStrategy(
                priority=1,
                depth=1,
                patterns=["imports", "functions", "classes"]
            ),
            "deep": ExtractionStrategy(
                priority=2,
                depth=2,
                patterns=["imports", "functions", "classes", "calls", "dependencies"]
            ),
            "comprehensive": ExtractionStrategy(
                priority=3,
                depth=3,
                patterns=[
                    "imports", "functions", "classes", "calls",
                    "dependencies", "types", "comments", "metrics"
                ]
            )
        }

    async def extract_metadata(
        self,
        code: str,
        file_path: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata using the best strategy for the context.
        
        Args:
            code: Source code to analyze
            file_path: Path to the source file
            agent_id: Optional ID of the requesting agent
            
        Returns:
            Extracted metadata
        """
        strategy = await self._select_strategy(code, agent_id)
        
        try:
            metadata = await self.extractor.extract(
                code,
                file_path,
                patterns=strategy.patterns,
                depth=strategy.depth
            )
            
            # Update strategy metrics
            strategy.times_used += 1
            strategy.last_used = datetime.now()
            strategy.last_success_rate = 1.0
            
            # Learn from successful extraction
            await self._learn_patterns(metadata)
            
            # Share knowledge if coordinator exists
            if self.coordinator and agent_id:
                await self.coordinator.share_knowledge(
                    agent_id,
                    {"metadata_patterns": self.patterns}
                )
            
            return metadata
            
        except Exception as e:
            # Update strategy metrics on failure
            strategy.last_success_rate = 0.0
            raise

    async def _select_strategy(
        self,
        code: str,
        agent_id: Optional[str] = None
    ) -> ExtractionStrategy:
        """Select the best strategy based on code and context."""
        # Get agent context if available
        agent_context = None
        if self.coordinator and agent_id:
            agent_context = await self.coordinator.get_agent_context(agent_id)
        
        # Estimate code complexity
        complexity = self._estimate_complexity(code)
        
        # Select strategy based on complexity and context
        if complexity > 0.8 or (
            agent_context and
            agent_context.get("window_size", 0) > 1_000_000
        ):
            return self.strategies["comprehensive"]
        elif complexity > 0.4:
            return self.strategies["deep"]
        else:
            return self.strategies["quick"]

    def _estimate_complexity(self, code: str) -> float:
        """Estimate code complexity (0-1)."""
        # Simple complexity estimation
        factors = [
            len(code.split("\n")),  # Lines of code
            code.count("class "),   # Number of classes
            code.count("def "),     # Number of functions
            code.count("import "),  # Number of imports
            code.count("try:"),     # Error handling
            code.count("async ")    # Async code
        ]
        
        # Normalize each factor and combine
        max_values = [1000, 50, 100, 50, 20, 20]
        normalized = [
            min(1.0, f / m) for f, m in zip(factors, max_values)
        ]
        return sum(normalized) / len(normalized)

    async def _learn_patterns(self, metadata: Dict[str, Any]) -> None:
        """Learn patterns from extracted metadata."""
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                pattern_type = f"{key}_structure"
                if pattern_type not in self.patterns:
                    self.patterns[pattern_type] = MetadataPattern(
                        pattern_type=pattern_type,
                        frequency=1,
                        confidence=1.0,
                        last_seen=datetime.now(),
                        examples=[str(value)[:100]]  # Limit example size
                    )
                else:
                    pattern = self.patterns[pattern_type]
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    if len(pattern.examples) < 5:  # Keep up to 5 examples
                        pattern.examples.append(str(value)[:100])
