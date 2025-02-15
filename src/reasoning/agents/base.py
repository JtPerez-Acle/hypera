"""Base agent implementation for the reasoning system."""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic_ai import Agent, RunContext
from tenacity import retry, stop_after_attempt, wait_exponential

from ..metadata.extractor import MetadataExtractor
from ..retrieval.gemini import GeminiRetriever
from ..types import AgentAnalysis, AgentDependencies, CodeContext


class BaseAgent(ABC):
    """Base class for all reasoning agents."""

    def __init__(
        self,
        model: str = "deepseek-chat",
        metadata_extractor: Optional[MetadataExtractor] = None,
        gemini_retriever: Optional[GeminiRetriever] = None
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
        self.gemini_retriever = gemini_retriever or GeminiRetriever()
        self._setup_tools()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def _setup_tools(self) -> None:
        """Set up any tools needed by this agent."""
        pass

    async def _enrich_context(self, code_context: CodeContext) -> CodeContext:
        """Enrich code context with metadata and related information.
        
        This method:
        1. Extracts rich metadata using our metadata extractor
        2. Retrieves relevant context using Gemini's 2M token window
        3. Combines everything into a comprehensive context
        """
        # Extract rich metadata
        metadata = await self.metadata_extractor.extract(
            code_context.code_snippet,
            code_context.language
        )
        
        # Get relevant context from our codebase
        retrieval_results = await self.gemini_retriever.retrieve(
            code_context.code_snippet,
            metadata
        )

        # Enrich the context
        code_context.imports.extend(metadata.get("imports", []))
        code_context.dependencies.extend(metadata.get("dependencies", []))
        
        return code_context
