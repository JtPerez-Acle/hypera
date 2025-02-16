"""Base agent implementation for the reasoning system."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TypedDict
import os
import logging

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from src.reasoning.types import (
    AgentAnalysis,
    CodeContext,
    MetadataRequest,
    GPT4MiniModel,
    MetadataExtractionLevel,
    AgentDependencies,
    CodeUnderstandingLevel
)
from src.retrieval.gemini import GeminiRetriever

logger = logging.getLogger(__name__)

class ResponseDataDict(TypedDict):
    """Response data type for agent output."""
    agent_name: str
    understanding_level: str
    findings: Dict[str, Any]
    confidence: float
    supporting_evidence: List[str]
    warnings: Optional[List[str]]

class ResponseData(BaseModel):
    """Pydantic model for agent response data."""
    agent_name: str = Field(..., description="Name of the agent providing the response")
    understanding_level: str = Field(..., description="Level of code understanding achieved")
    findings: Dict[str, Any] = Field(..., description="Analysis findings")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    supporting_evidence: List[str] = Field(..., description="Evidence supporting the findings")
    warnings: Optional[List[str]] = Field(None, description="Optional warnings or issues")

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        model: Optional[GPT4MiniModel] = None,
        metadata_extractor: Optional['MetadataGenerationAgent'] = None,
        gemini_retriever: Optional[GeminiRetriever] = None
    ):
        """Initialize the agent.
        
        Args:
            model: Optional GPT4Mini model
            metadata_extractor: Optional metadata extraction agent
            gemini_retriever: Optional Gemini retriever
        """
        from src.reasoning.agents.metadata_agent import MetadataGenerationAgent
        
        self.metadata_extractor = metadata_extractor
        self.gemini_retriever = gemini_retriever
        self.model = model or OpenAIModel(
            "deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        
        # Initialize pydantic-ai agent
        self.agent = Agent(
            self.model,
            deps_type=AgentDependencies,
            result_type=ResponseData,
            system_prompt=self.get_system_prompt()
        )
        
        # Set up logging
        name = self.__class__.__name__.lower()
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get metadata requirements for this agent."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent."""
        pass
    
    @abstractmethod
    async def analyze(self, context: CodeContext) -> AgentAnalysis:
        """Analyze code context."""
        pass


class BaseAnalysisAgent(BaseAgent):
    """Base class for analysis agents."""
    
    def __init__(
        self,
        metadata_extractor: 'MetadataGenerationAgent',
        gemini_retriever: GeminiRetriever,
        model: Optional[GPT4MiniModel] = None
    ):
        """Initialize the analysis agent.
        
        Args:
            metadata_extractor: Agent for generating metadata
            gemini_retriever: Retriever for similar code examples
            model: Optional GPT4Mini model for analysis
        """
        super().__init__(model=model)
        self.metadata_extractor = metadata_extractor
        self.gemini_retriever = gemini_retriever
    
    @abstractmethod
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get metadata requirements for analysis."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for analysis."""
        pass
    
    @abstractmethod
    async def analyze(self, context: CodeContext) -> AgentAnalysis:
        """Analyze code context."""
        pass


class BaseAgent(ABC):
    """Base class for all reasoning agents."""

    def __init__(
        self,
        model: str = "deepseek-chat",
        metadata_extractor: Optional['MetadataGenerationAgent'] = None,
        gemini_retriever: Optional = None
    ):
        """Initialize the agent with necessary components.
        
        Args:
            model: The model to use for analysis
            metadata_extractor: Component for extracting rich metadata
            gemini_retriever: Component for retrieving relevant context
        """
        from pydantic_ai import Agent, RunContext
        from tenacity import retry, stop_after_attempt, wait_exponential
        from pydantic_ai.models.openai import OpenAIModel
        
        model = OpenAIModel(
            model,
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        self.agent = Agent(
            model,
            deps_type='AgentDependencies',
            result_type=ResponseData,
            system_prompt=self.get_system_prompt()
        )
        self.metadata_extractor = metadata_extractor or self._get_original_metadata_extractor()
        self.gemini_retriever = gemini_retriever
        self._setup_tools()
        name = self.__class__.__name__.lower()
        self._name = name.replace('agent', '').replace('generation', '_generator')

    @property
    def name(self) -> str:
        """Get the name of this agent."""
        return self._name

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

    async def _enrich_context(self, code_context: CodeContext) -> CodeContext:
        """Enrich code context with metadata."""
        try:
            metadata = await self.metadata_extractor.extract_metadata(
                code_context,
                window_size=self._calculate_window_size(self.get_metadata_requirements())
            )
            
            # Update imports and dependencies from metadata
            if metadata.imports:
                code_context.imports.extend(metadata.imports)
            if metadata.dependencies:
                code_context.dependencies.extend(list(metadata.dependencies.keys()))
            
            # Set the metadata field
            code_context.metadata = metadata
            
            return code_context
        except Exception as e:
            logging.error(f"Failed to enrich context: {e}")
            return code_context

    def _calculate_window_size(self, request: MetadataRequest) -> int:
        """Calculate appropriate context window size based on extraction level."""
        base_sizes = {
            MetadataExtractionLevel.MINIMAL: 500_000,
            MetadataExtractionLevel.STANDARD: 1_000_000,
            MetadataExtractionLevel.DEEP: 1_500_000,
            MetadataExtractionLevel.COMPREHENSIVE: 2_000_000
        }
        return base_sizes.get(request.extraction_level, 1_000_000)  # Default to STANDARD size

    def _get_original_metadata_extractor(self):
        from src.metadata.metadata_manager import MetadataGenerationAgent as OriginalMetadataGenerationAgent
        return OriginalMetadataGenerationAgent()
