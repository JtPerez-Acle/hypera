"""
GPT-4-mini client for efficient metadata generation.
"""

from typing import Dict, Any, Optional
import aiohttp
from pydantic import BaseModel, Field


class GPT4MiniConfig(BaseModel):
    """Configuration for GPT-4-mini API."""
    api_key: str = Field(description="API key for GPT-4-mini")
    endpoint: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        description="API endpoint"
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model identifier"
    )
    max_tokens: int = Field(
        default=1024,
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=0.0,
        description="Sampling temperature"
    )
    top_p: float = Field(
        default=0.95,
        description="Nucleus sampling parameter"
    )
    presence_penalty: float = Field(
        default=0.0,
        description="Presence penalty"
    )
    frequency_penalty: float = Field(
        default=0.0,
        description="Frequency penalty"
    )


class GPT4MiniModel:
    """GPT-4 Mini model for code analysis."""
    
    def __init__(self, config: GPT4MiniConfig):
        """Initialize GPT-4 Mini model."""
        self.config = config
        self.base_url = "https://api.gpt4mini.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

    async def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate completion for prompt."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/completions",
                    headers=self.headers,
                    json={
                        "prompt": prompt,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "top_p": self.config.top_p,
                        "frequency_penalty": self.config.frequency_penalty,
                        "presence_penalty": self.config.presence_penalty,
                        "stop": None
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"GPT-4 Mini API error: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    
                    return data
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating completion: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass  # No cleanup needed


class GPT4MiniClient:
    """Client for interacting with GPT-4-mini."""
    
    def __init__(self, config: GPT4MiniConfig):
        """Initialize the client.
        
        Args:
            config: Configuration for the API
        """
        self.config = config
        self._session = None
    
    async def __aenter__(self):
        """Enter async context."""
        self._session = GPT4MiniModel(self.config)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a completion from GPT-4-mini.
        
        Args:
            prompt: The prompt to complete
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            API response containing the completion
        """
        if not self._session:
            raise RuntimeError("Client not initialized. Use async with context.")
        
        return await self._session.generate(prompt)
    
    @staticmethod
    def extract_completion(response: Dict[str, Any]) -> str:
        """Extract the completion text from an API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            The generated completion text
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid API response format: {e}")
