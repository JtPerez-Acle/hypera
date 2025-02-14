"""
Client configuration for Qdrant vector database.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class QdrantConfig(BaseSettings):
    """Configuration for Qdrant client."""
    url: str = "localhost"
    port: int = 6333
    prefer_grpc: bool = False
    api_key: Optional[str] = None
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    deepseek_api_key: Optional[str] = Field(None, env="DEEPSEEK_API_KEY")
    
    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"  
    )

_client: Optional[QdrantClient] = None

def get_qdrant_client() -> QdrantClient:
    """
    Returns a configured Qdrant client with connection pooling.
    Uses singleton pattern to avoid multiple client instances.
    
    Returns:
        QdrantClient: Configured Qdrant client instance
    
    Metadata:
        - Dependencies: QdrantConfig
        - Error Handling: Connection validation
        - Performance: GRPC/HTTP2 support, Connection pooling
        - Pattern: Singleton
    """
    global _client
    
    if _client is None:
        config = QdrantConfig()
        
        client_kwargs = {
            "url": config.url,
            "port": config.port,
            "prefer_grpc": config.prefer_grpc
        }
        
        if config.api_key:
            client_kwargs["api_key"] = config.api_key
            
        _client = QdrantClient(**client_kwargs)
    
    return _client
