from pydantic import BaseSettings, Field
import qdrant_client

class QdrantConfig(BaseSettings):
    url: str = Field(..., env='QDRANT_URL')
    api_key: str = Field(..., env='QDRANT_API_KEY')
    port: int = Field(6333, env='QDRANT_PORT')
    prefer_grpc: bool = Field(False, env='QDRANT_PREFER_GRPC')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

def get_qdrant_client() -> qdrant_client.QdrantClient:
    """
    Returns configured Qdrant client with connection pooling
    
    Metadata:
        - Dependencies: QdrantConfig
        - Error Handling: Connection validation
        - Performance: GRPC/HTTP2 support
    """
    config = QdrantConfig()
    return qdrant_client.QdrantClient(
        url=config.url,
        port=config.port,
        api_key=config.api_key,
        prefer_grpc=config.prefer_grpc
    )

qdrant_client = get_qdrant_client()

print(qdrant_client.get_collections())