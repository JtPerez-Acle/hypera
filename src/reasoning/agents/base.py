"""Base agent implementation for the reasoning system."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from pydantic_ai import Agent, RunContext
from tenacity import retry, stop_after_attempt, wait_exponential

from ...metadata.extractor import MetadataExtractor
from ...metadata.types import MetadataRequest, MetadataExtractionLevel
from ..types import (
    AgentAnalysis,
    AgentDependencies,
    CodeContext
)


class BaseAgent(ABC):
    """Base class for all reasoning agents."""

    def __init__(
        self,
        model: str = "deepseek-chat",
        metadata_extractor: Optional[MetadataExtractor] = None,
        gemini_retriever: Optional = None
    ):
        """Initialize the agent with necessary components.
        
        Args:
            model: The model to use for analysis
            metadata_extractor: Component for extracting rich metadata
            gemini_retriever: Component for retrieving relevant context
        """
        self.agent = Agent(
            model,
            deps_type=AgentDependencies,
            result_type=AgentAnalysis,
            system_prompt=self.get_system_prompt()
        )
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.gemini_retriever = gemini_retriever
        self._setup_tools()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    @abstractmethod
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get the metadata extraction requirements for this agent.
        
        Override this method to specify what level of metadata extraction
        your agent needs. By default, uses STANDARD level.
        
        Returns:
            MetadataRequest configuration for this agent's needs
        """
        return MetadataRequest(
            extraction_level=MetadataExtractionLevel.STANDARD,
            include_types=True,
            include_dependencies=True
        )

    def _setup_tools(self) -> None:
        """Set up any tools needed by this agent."""
        pass

    async def _enrich_context(
        self,
        code_context: CodeContext,
        metadata_request: Optional[MetadataRequest] = None
    ) -> CodeContext:
        """Enrich code context with metadata and related information.
        
        This method:
        1. Extracts rich metadata using our metadata extractor
        2. Retrieves relevant context using Gemini's 2M token window
        3. Combines everything into a comprehensive context
        
        Args:
            code_context: The code context to enrich
            metadata_request: Optional override for metadata extraction config
        
        Returns:
            Enriched code context with metadata
        """
        # Use agent's default requirements if not specified
        metadata_request = metadata_request or self.get_metadata_requirements()
        
        # Extract rich metadata with specified configuration
        metadata = await self.metadata_extractor.extract(
            code_context.code_snippet,
            code_context.language,
            metadata_request
        )
        
        # Get relevant context from our codebase
        retrieval_results = await self.gemini_retriever.retrieve(
            code_context.code_snippet,
            metadata,
            window_size=self._calculate_window_size(metadata_request)
        )

        # Enrich the context
        code_context.imports.extend(metadata.get("imports", []))
        code_context.dependencies.extend(
            metadata.get("dependencies", [])[:metadata_request.max_dependency_depth]
        )
        
        return code_context

    def _calculate_window_size(self, request: MetadataRequest) -> int:
        """Calculate appropriate context window size based on extraction level."""
        base_sizes = {
            MetadataExtractionLevel.MINIMAL: 500_000,
            MetadataExtractionLevel.STANDARD: 1_000_000,
            MetadataExtractionLevel.DEEP: 1_500_000,
            MetadataExtractionLevel.COMPREHENSIVE: 2_000_000
        }
        return base_sizes[request.extraction_level]
