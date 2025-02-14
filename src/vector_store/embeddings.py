"""
Embedding generation pipeline for code chunks.

This module handles the generation of embeddings that combine both code content
and rich metadata in a structured format. Uses OpenAI for embedding generation
while preserving compatibility with Gemini 1.5 Pro's context window for retrieval.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import openai
from pydantic import Field
from pydantic_settings import BaseSettings
from .schema import CodeChunkPayload, CodeChunkMetadata

class OpenAIConfig(BaseSettings):
    """Configuration for OpenAI API."""
    api_key: str = Field(..., env='OPENAI_API_KEY')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

def initialize_openai():
    """Initialize OpenAI client with API key."""
    config = OpenAIConfig()
    openai.api_key = config.api_key

def format_chunk_for_embedding(chunk: CodeChunkPayload) -> str:
    """
    Format a code chunk and its metadata for embedding generation.
    
    This function creates a structured text representation that combines
    code content with its metadata in a way that preserves important
    context and relationships.
    
    Args:
        chunk: CodeChunkPayload containing the code and its metadata
        
    Returns:
        str: Formatted text ready for embedding generation
        
    Metadata:
        - Dependencies: CodeChunkPayload, CodeChunkMetadata
        - Format: Structured text with clear section delimiters
        - Context: Preserves code-metadata relationships
    """
    metadata_dict = chunk.metadata.dict()
    
    # Format dependencies and imports for better context
    deps = ", ".join(metadata_dict["dependencies"]) if metadata_dict["dependencies"] else "none"
    imports = ", ".join(metadata_dict["imports"]) if metadata_dict["imports"] else "none"
    
    # Create a structured format that clearly separates different types of information
    formatted_text = f"""
[CODE_METADATA]
Type: {metadata_dict["chunk_type"]}
Language: {metadata_dict["language"]}
Location: {metadata_dict["file_path"]}:{metadata_dict["start_line"]}-{metadata_dict["end_line"]}
Dependencies: {deps}
Imports: {imports}

[DOCUMENTATION]
{metadata_dict["doc_string"] if metadata_dict["doc_string"] else "No documentation available"}

[AST_METADATA]
{json.dumps(metadata_dict["ast_data"], indent=2)}

[CODE_CONTENT]
{chunk.content}
"""
    return formatted_text

def validate_chunk(chunk: Dict[str, Any]) -> bool:
    """Validate a code chunk before embedding."""
    # Check for empty content
    if not chunk.get("content") or not chunk["content"].strip():
        raise ValueError("Empty or whitespace-only content in chunk")
        
    # Check for metadata
    if not chunk.get("metadata"):
        raise ValueError("Missing metadata in chunk")
        
    # Check required metadata fields
    required_metadata = ["chunk_type", "language", "file_path", "start_line", "end_line"]
    missing = [field for field in required_metadata if field not in chunk["metadata"]]
    if missing:
        raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")
        
    # Check for valid line numbers
    start_line = chunk["metadata"]["start_line"]
    end_line = chunk["metadata"]["end_line"]
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        raise ValueError("Line numbers must be integers")
    if start_line < 0 or end_line < start_line:
        raise ValueError("Invalid line number range")
        
    return True

async def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding using OpenAI's text-embedding-3-large model.
    
    Args:
        text: Formatted text to generate embedding for
        
    Returns:
        List[float]: Generated embedding vector
        
    Metadata:
        - Dependencies: OpenAI API
        - Error Handling: API errors, rate limiting
        - Performance: Async operation
    """
    try:
        response = await openai.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    except Exception as e:
        # Log the error and re-raise
        print(f"Error generating embedding: {e}")
        raise

async def generate_embeddings(chunks: List[Dict[str, Any]], client: Any) -> List[List[float]]:
    """Generate embeddings for code chunks."""
    # Validate chunks
    for chunk in chunks:
        validate_chunk(chunk)
        
    # Format chunks for embedding
    texts = [format_chunk_for_embedding(CodeChunkPayload(**chunk)) for chunk in chunks]
    
    try:
        # Generate embeddings
        embeddings = await client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )
        return [e.embedding for e in embeddings.data]
    except Exception as e:
        raise ValueError(f"Error generating embeddings: {str(e)}")

async def process_chunk(chunk: CodeChunkPayload) -> CodeChunkPayload:
    """
    Process a code chunk by generating its embedding.
    
    Args:
        chunk: CodeChunkPayload to process
        
    Returns:
        CodeChunkPayload: Original chunk with embedding added
        
    Metadata:
        - Dependencies: format_chunk_for_embedding, generate_embedding
        - Performance: Async operation
        - Error Handling: Embedding generation errors
    """
    formatted_text = format_chunk_for_embedding(chunk)
    chunk.embedding = await generate_embedding(formatted_text)
    return chunk

async def process_chunks_batch(chunks: List[CodeChunkPayload]) -> List[CodeChunkPayload]:
    """
    Process a batch of code chunks in parallel.
    
    Args:
        chunks: List of CodeChunkPayload objects to process
        
    Returns:
        List[CodeChunkPayload]: Processed chunks with embeddings
        
    Metadata:
        - Dependencies: process_chunk
        - Performance: Parallel async processing
        - Error Handling: Batch processing errors
    """
    # TODO: Implement proper batching with rate limiting
    processed = []
    for chunk in chunks:
        processed_chunk = await process_chunk(chunk)
        processed.append(processed_chunk)
    return processed
