"""
Specialized agent for generating rich code metadata using GPT-4-mini.
"""

import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

from ...llm.gpt4_mini import GPT4MiniClient, GPT4MiniModel
from ..types import (
    AgentAnalysis,
    CodeContext,
    CodeUnderstandingLevel,
    MetadataRequest,
    MetadataExtractionLevel,
    CodeMetadata
)
from .base import BaseAgent
from ...retrieval.gemini import GeminiRetriever


class MetadataGenerationAgent(BaseAgent):
    """Agent for generating rich metadata about code."""
    
    def __init__(
        self,
        model: Optional[GPT4MiniModel] = None,
        gemini_retriever: Optional[GeminiRetriever] = None
    ):
        """Initialize the metadata generation agent.
        
        Args:
            model: Optional GPT4Mini model for analysis
            gemini_retriever: Optional Gemini retriever for similar code examples
        """
        super().__init__(model=model, gemini_retriever=gemini_retriever)
        
        # Set up logging
        self.logger = logging.getLogger("agent.metadata")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for metadata generation."""
        return """You are a specialized code analysis agent focused on generating rich metadata.
        Your task is to analyze code snippets and produce detailed metadata about their:
        1. Structure (imports, functions, classes, types)
        2. Behavior (side effects, complexity, performance)
        3. Relationships (dependencies, patterns, architectural impact)
        4. Quality (maintainability, security, best practices)
        
        Respond with structured metadata that can be directly parsed into the CodeMetadata type.
        Focus on being precise and concise in your analysis."""
    
    def get_metadata_requirements(self) -> MetadataRequest:
        """Get metadata extraction requirements."""
        return MetadataRequest(
            extraction_level=MetadataExtractionLevel.DEEP,
            include_types=True,
            include_dependencies=True,
            max_dependency_depth=2,
            include_docstrings=True,
            include_comments=True
        )
    
    async def extract_metadata(self, code_context: CodeContext, window_size: Optional[int] = None) -> CodeMetadata:
        """Extract metadata from code context.
        
        Args:
            code_context: Context containing code to analyze
            window_size: Optional window size for context
            
        Returns:
            Extracted metadata
        """
        # Get metadata requirements
        requirements = self.get_metadata_requirements()
        
        # Initialize metadata with empty values
        metadata = CodeMetadata()
        
        try:
            # Extract basic metadata
            metadata.imports = self._extract_imports(code_context.code_snippet)
            metadata.functions = self._extract_functions(code_context.code_snippet)
            metadata.classes = self._extract_classes(code_context.code_snippet)
            
            # Extract additional metadata based on requirements
            if requirements.include_types:
                metadata.types = self._extract_types(code_context.code_snippet)
            
            if requirements.include_dependencies:
                metadata.dependencies = self._extract_dependencies(
                    code_context.code_snippet,
                    requirements.max_dependency_depth
                )
            
            if requirements.include_docstrings:
                metadata.docstrings = self._extract_docstrings(code_context.code_snippet)
            
            if requirements.include_comments:
                metadata.comments = self._extract_comments(code_context.code_snippet)
            
            metadata.success = True
            
        except Exception as e:
            metadata.success = False
            metadata.error = str(e)
        
        return metadata
    
    async def analyze(self, context: CodeContext) -> AgentAnalysis:
        """Analyze code and generate rich metadata.
        
        Args:
            context: Context about the code being analyzed
            
        Returns:
            Agent analysis containing generated metadata
        """
        try:
            # First use Gemini for context retrieval
            relevant_context = await self.gemini_retriever.get_context(
                context.code_snippet,
                max_tokens=2_000_000  # Use full 2M token window
            )
            
            # Generate metadata from the context
            metadata = CodeMetadata(
                imports=relevant_context.get("imports", []),
                functions=relevant_context.get("functions", []),
                classes=relevant_context.get("classes", []),
                types=relevant_context.get("types", {}),
                dependencies=relevant_context.get("dependencies", {}),
                docstrings=relevant_context.get("docstrings", {}),
                comments=relevant_context.get("comments", []),
                success=True
            )
            
            return AgentAnalysis(
                agent_name=self.name,
                understanding_level=CodeUnderstandingLevel.SEMANTIC,
                findings=metadata.model_dump(),
                confidence=0.95,
                supporting_evidence=[
                    f"Analyzed {len(context.code_snippet)} lines of code",
                    f"Incorporated {len(str(relevant_context))} tokens of context",
                    "Generated comprehensive metadata structure"
                ]
            )
            
        except Exception as e:
            # Handle errors gracefully
            return AgentAnalysis(
                agent_name=self.name,
                understanding_level=CodeUnderstandingLevel.SURFACE,
                findings={"error": str(e)},
                confidence=0.1,
                supporting_evidence=[
                    "Error occurred during metadata generation",
                    f"Error type: {type(e).__name__}"
                ],
                warnings=[str(e)]
            )
    
    def _build_analysis_prompt(
        self,
        context: CodeContext,
        relevant_context: str
    ) -> str:
        """Build the prompt for GPT-4-mini analysis."""
        return f"""Analyze this code and generate rich metadata:

        Code Context:
        - File: {context.file_path}
        - Language: {context.language}
        - Lines: {context.start_line}-{context.end_line}
        
        Relevant Context:
        {relevant_context}
        
        Code to Analyze:
        {context.code_snippet}
        
        Generate metadata following this structure:
        {{
            "imports": ["list of imports"],
            "functions": [
                {{
                    "name": "function name",
                    "params": ["param names"],
                    "return_type": "return type",
                    "complexity": int,
                    "side_effects": ["list of side effects"]
                }}
            ],
            "classes": [
                {{
                    "name": "class name",
                    "bases": ["base classes"],
                    "methods": ["method names"],
                    "attributes": ["attribute names"]
                }}
            ],
            "types": {{"variable": "type"}},
            "dependencies": {{"file": ["dependent files"]}},
            "patterns": ["identified patterns"],
            "security_issues": ["potential issues"],
            "performance_notes": ["performance characteristics"]
        }}
        """
