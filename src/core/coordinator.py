"""Agent Coordinator for managing cross-module communication and resource optimization."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

from ..retrieval.context import ContextManager
from ..retrieval.gemini import GeminiRetriever
from ..metadata.extractor import MetadataExtractor
from ..vector_store.pipeline import Pipeline


@dataclass
class AgentMetrics:
    """Metrics for agent performance and resource usage."""
    success_rate: float = 0.0
    average_latency: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class ResourceAllocation(BaseModel):
    """Resource allocation for an agent."""
    cpu_share: float
    memory_limit: int
    context_window_size: int
    priority: int


class AgentCoordinator:
    """Coordinates agent activities and resource usage across modules."""

    def __init__(self):
        """Initialize the coordinator with necessary components."""
        self.context_manager = ContextManager()
        self.retriever = GeminiRetriever()
        self.metadata_extractor = MetadataExtractor()
        self.pipeline = Pipeline()
        
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.resource_allocations: Dict[str, ResourceAllocation] = {}
        self.shared_knowledge: Dict[str, Any] = {}

    async def register_agent(
        self,
        agent_id: str,
        initial_resources: ResourceAllocation
    ) -> None:
        """Register a new agent with the coordinator."""
        self.agent_metrics[agent_id] = AgentMetrics()
        self.resource_allocations[agent_id] = initial_resources
        await self._optimize_resources()

    async def update_metrics(
        self,
        agent_id: str,
        success: bool,
        latency: float,
        resources_used: Dict[str, float]
    ) -> None:
        """Update metrics for an agent."""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]
        n = metrics.resource_usage.get("count", 0) + 1
        
        # Update running averages
        metrics.success_rate = (
            (metrics.success_rate * (n - 1) + int(success)) / n
        )
        metrics.average_latency = (
            (metrics.average_latency * (n - 1) + latency) / n
        )
        
        # Update resource usage
        for resource, usage in resources_used.items():
            current = metrics.resource_usage.get(resource, 0)
            metrics.resource_usage[resource] = (current * (n - 1) + usage) / n
            
        metrics.resource_usage["count"] = n
        metrics.last_updated = datetime.now()
        
        # Trigger resource optimization if needed
        if n % 10 == 0:  # Optimize every 10 updates
            await self._optimize_resources()

    async def share_knowledge(
        self,
        agent_id: str,
        knowledge: Dict[str, Any]
    ) -> None:
        """Share knowledge between agents."""
        # Merge new knowledge with existing
        for key, value in knowledge.items():
            if key not in self.shared_knowledge:
                self.shared_knowledge[key] = value
            elif isinstance(value, dict):
                self.shared_knowledge[key].update(value)
            elif isinstance(value, list):
                self.shared_knowledge[key].extend(value)
            else:
                self.shared_knowledge[key] = value

    async def get_agent_context(
        self,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get context for a specific agent."""
        if agent_id not in self.resource_allocations:
            return None
            
        allocation = self.resource_allocations[agent_id]
        return {
            "window_size": allocation.context_window_size,
            "shared_knowledge": self.shared_knowledge,
            "metrics": self.agent_metrics.get(agent_id)
        }

    async def _optimize_resources(self) -> None:
        """Optimize resource allocation based on agent performance."""
        total_success_rate = sum(
            m.success_rate for m in self.agent_metrics.values()
        )
        total_latency = sum(
            m.average_latency for m in self.agent_metrics.values()
        )
        
        # Adjust allocations based on performance
        for agent_id, metrics in self.agent_metrics.items():
            if total_success_rate > 0:
                performance_share = metrics.success_rate / total_success_rate
            else:
                performance_share = 1.0 / len(self.agent_metrics)
                
            if total_latency > 0:
                latency_share = 1 - (metrics.average_latency / total_latency)
            else:
                latency_share = 1.0 / len(self.agent_metrics)
                
            # Update resource allocation
            allocation = self.resource_allocations[agent_id]
            allocation.cpu_share = (performance_share + latency_share) / 2
            allocation.context_window_size = int(
                2_000_000 * performance_share  # 2M tokens total
            )
