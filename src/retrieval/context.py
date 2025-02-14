"""
Context management for code retrieval.

This module manages the context window utilization of Gemini 1.5 Pro,
ensuring optimal use of its 2-million token capacity.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .types import CodeContext, RetrievalResult

@dataclass
class ContextWindow:
    """
    Represents a context window in Gemini 1.5 Pro.
    
    This class helps track and manage the content within
    Gemini's 2-million token context window.
    """
    max_tokens: int = 2_000_000  # Gemini 1.5 Pro's context window size
    current_tokens: int = 0
    contents: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize the contents list."""
        self.contents = []
    
    def can_add(self, token_count: int) -> bool:
        """Check if more content can be added to the window."""
        return self.current_tokens + token_count <= self.max_tokens
    
    def add_content(self, content: Dict[str, Any], token_count: int):
        """Add content to the window if space allows."""
        if self.can_add(token_count):
            self.contents.append(content)
            self.current_tokens += token_count
            return True
        return False
    
    def clear(self):
        """Clear the context window."""
        self.contents = []
        self.current_tokens = 0

class ContextManager:
    """
    Manages context accumulation and optimization for code retrieval.
    
    This class ensures efficient use of Gemini's context window by:
    1. Tracking token usage
    2. Optimizing content selection
    3. Managing context relevance
    
    Metadata:
        - Dependencies: Gemini 1.5 Pro
        - Context Window: 2 million tokens
        - Optimization: Smart context selection
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self.window = ContextWindow()
        self.context_history: List[RetrievalResult] = []
    
    def _estimate_tokens(self, content: str) -> int:
        """
        Estimate the number of tokens in a piece of content.
        
        This is a simple estimation - in production we'd use a proper
        tokenizer that matches Gemini's tokenization.
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(content) // 4
    
    def _calculate_relevance(self, result: RetrievalResult) -> float:
        """Calculate the relevance score for a retrieval result."""
        if not result.similarity_scores:
            return 0.0
        return sum(result.similarity_scores) / len(result.similarity_scores)
    
    def add_result(self, result: RetrievalResult) -> bool:
        """
        Add a retrieval result to the context window.
        
        Args:
            result: Retrieved code chunks and context
            
        Returns:
            bool: Whether the content was added successfully
            
        Metadata:
            - Context Management: Token tracking
            - Optimization: Relevance-based selection
        """
        # Estimate tokens for the entire result
        total_tokens = sum(
            self._estimate_tokens(chunk["content"])
            for chunk in result.chunks
        )
        
        if result.context:
            total_tokens += self._estimate_tokens(str(result.context.dict()))
        
        # Try to add to the window
        if self.window.can_add(total_tokens):
            self.window.add_content({
                "result": result,
                "relevance": self._calculate_relevance(result)
            }, total_tokens)
            self.context_history.append(result)
            return True
        
        # If we can't add, try to optimize the window
        return self._optimize_window(result, total_tokens)
    
    def _optimize_window(self, new_result: RetrievalResult, required_tokens: int) -> bool:
        """Optimize the context window by removing less relevant content."""
        if not self.window.contents:
            return True

        # Calculate relevance scores for all content
        scores = [(content["result"], content["relevance"]) for content in self.window.contents]
        scores.sort(key=lambda x: x[1], reverse=True)  # Sort by relevance
        
        # Calculate total tokens needed
        total_tokens = required_tokens + sum(len(str(r)) for r in [content["result"] for content in self.window.contents])
        
        # Keep only the most relevant content that fits within token limit
        current_tokens = 0
        optimized_content = []
        min_relevance = 0.7  # Minimum relevance threshold
        
        for result, score in scores:
            if score < min_relevance:
                continue
                
            content_tokens = len(str(result))
            if current_tokens + content_tokens <= self.window.max_tokens - required_tokens:
                optimized_content.append({"result": result, "relevance": score})
                current_tokens += content_tokens
                
        # Clear and update window content
        self.window.clear()
        for content in optimized_content:
            self.window.add_content(content, len(str(content["result"])))
            
        return True
    
    def get_current_context(self) -> List[Dict[str, Any]]:
        """Get the current contents of the context window."""
        return [content["result"] for content in self.window.contents]
    
    def clear_context(self):
        """Clear the entire context window."""
        self.window.clear()
        self.context_history = []
