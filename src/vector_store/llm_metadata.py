"""
LLM-based code analysis and metadata generation.

This module leverages Gemini 1.5 Pro's 2M token context window for deep
code analysis and rich metadata generation.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.generativeai import GenerativeModel
from .schema import CodeChunkPayload, CodeChunkMetadata

class LLMMetadataGenerator:
    """Generates rich metadata using Gemini 1.5 Pro."""
    
    def __init__(self, api_key: str):
        """Initialize with Gemini API key."""
        self.model = GenerativeModel(
            model_name="gemini-1.5-pro",
            api_key=api_key
        )
    
    async def analyze_chunks(
        self,
        chunks: List[CodeChunkPayload],
        max_batch_size: int = 1_000_000  # 1M tokens per batch
    ) -> List[CodeChunkPayload]:
        """
        Analyze code chunks using Gemini 1.5 Pro.
        
        Args:
            chunks: List of code chunks to analyze
            max_batch_size: Maximum tokens per batch
            
        Returns:
            List[CodeChunkPayload]: Chunks with enriched metadata
        """
        # Prepare chunks in batches to fit context window
        batches = self._create_batches(chunks, max_batch_size)
        enriched_chunks = []
        
        for batch in batches:
            # Create context for LLM
            context = self._prepare_context(batch)
            
            # Generate analysis
            response = await self.model.generate_content(
                f'''Analyze this code and provide detailed metadata about:
                1. Function and class relationships
                2. Dependencies and imports
                3. Code complexity and patterns
                4. Potential bugs or issues
                5. Performance considerations
                
                Code to analyze:
                {context}
                
                Respond in the following JSON format:
                {{
                    "chunks": [
                        {{
                            "start_line": <int>,
                            "end_line": <int>,
                            "analysis": {{
                                "relationships": [...],
                                "dependencies": [...],
                                "complexity": {{...}},
                                "issues": [...],
                                "performance": [...]
                            }}
                        }}
                    ]
                }}
                ''')
            
            # Parse and apply metadata
            try:
                analysis = json.loads(response.text)
                enriched_chunks.extend(
                    self._apply_analysis(batch, analysis)
                )
            except Exception as e:
                print(f"Error parsing LLM response: {e}")
                enriched_chunks.extend(batch)
        
        return enriched_chunks
    
    def _create_batches(
        self,
        chunks: List[CodeChunkPayload],
        max_size: int
    ) -> List[List[CodeChunkPayload]]:
        """Split chunks into batches that fit context window."""
        batches = []
        current_batch = []
        current_size = 0
        
        for chunk in chunks:
            # Estimate token size (rough approximation)
            chunk_size = len(chunk.content.split())
            
            if current_size + chunk_size > max_size:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            
            current_batch.append(chunk)
            current_size += chunk_size
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _prepare_context(self, chunks: List[CodeChunkPayload]) -> str:
        """Prepare chunks for LLM analysis."""
        context = []
        for chunk in chunks:
            context.append(
                f"--- File: {chunk.metadata.file_path} "
                f"(Lines {chunk.metadata.start_line}-{chunk.metadata.end_line}) ---\n"
                f"{chunk.content}\n"
            )
        return "\n".join(context)
    
    def _apply_analysis(
        self,
        chunks: List[CodeChunkPayload],
        analysis: Dict[str, Any]
    ) -> List[CodeChunkPayload]:
        """Apply LLM analysis to chunks."""
        chunk_map = {
            (c.metadata.start_line, c.metadata.end_line): c
            for c in chunks
        }
        
        enriched_chunks = []
        for chunk_analysis in analysis.get("chunks", []):
            start_line = chunk_analysis["start_line"]
            end_line = chunk_analysis["end_line"]
            chunk = chunk_map.get((start_line, end_line))
            
            if chunk:
                # Update metadata with LLM analysis
                chunk.metadata.dependencies = chunk_analysis["analysis"]["dependencies"]
                # Add any custom fields to metadata model if needed
                enriched_chunks.append(chunk)
            else:
                print(f"Warning: No matching chunk for lines {start_line}-{end_line}")
        
        return enriched_chunks or chunks  # Return original if no enrichment
