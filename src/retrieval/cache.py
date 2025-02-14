"""
Caching and rate limiting for the retrieval system.

This module provides caching mechanisms and rate limiting to optimize
API usage and improve response times.
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
from functools import lru_cache
from .types import RetrievalQuery, RetrievalResult

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    burst_limit: int = 10
    cooldown_seconds: float = 1.0

@dataclass
class CacheConfig:
    """Configuration for result caching."""
    ttl_seconds: int = 3600  # 1 hour
    max_size: int = 1000
    min_similarity: float = 0.95

class RateLimiter:
    """
    Rate limiter for API requests.
    
    Implements a token bucket algorithm with burst capacity
    to manage API request rates.
    
    Metadata:
        - Performance: Request throttling
        - Optimization: Burst handling
        - Monitoring: Usage tracking
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize the rate limiter."""
        self.config = config or RateLimitConfig()
        self.tokens = self.config.burst_limit
        self.last_update = time.time()
        self.requests = deque(maxlen=self.config.requests_per_minute)
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.config.burst_limit,
            self.tokens + elapsed * (self.config.requests_per_minute / 60.0)
        )
        self.last_update = now
    
    async def acquire(self) -> Tuple[bool, float]:
        """
        Attempt to acquire a rate limit token.
        
        Returns:
            Tuple[bool, float]: (success, wait_time)
        """
        self._refill_tokens()
        
        # Clean old requests
        now = time.time()
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        # Check rate limit
        if len(self.requests) >= self.config.requests_per_minute:
            wait_time = 60 - (now - self.requests[0])
            return False, max(0, wait_time)
        
        # Check burst limit
        if self.tokens < 1:
            wait_time = self.config.cooldown_seconds
            return False, wait_time
        
        # Acquire token
        self.tokens -= 1
        self.requests.append(now)
        return True, 0.0

class ResultCache:
    """
    Cache for retrieval results.
    
    Implements an LRU cache with TTL and similarity-based
    cache hit detection.
    
    Metadata:
        - Performance: Response caching
        - Optimization: Memory management
        - Monitoring: Cache statistics
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize the cache."""
        self.config = config or CacheConfig()
        self.cache: Dict[str, Tuple[RetrievalResult, datetime]] = {}
        self.hits = 0
        self.misses = 0
    
    def _compute_key(self, query: RetrievalQuery) -> str:
        """Compute cache key for a query."""
        # Convert query to a stable string representation
        query_dict = {
            "query": query.query,
            "query_type": query.query_type,
            "filters": query.filters.dict() if query.filters else None,
            "max_results": query.max_results
        }
        query_str = json.dumps(query_dict, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()
    
    def _is_similar_query(
        self,
        cached_query: RetrievalQuery,
        new_query: RetrievalQuery
    ) -> bool:
        """Check if queries are similar enough for cache hit."""
        # For now, simple exact matching
        # TODO: Implement fuzzy matching for queries
        return (
            cached_query.query == new_query.query and
            cached_query.query_type == new_query.query_type
        )
    
    def get(self, query: RetrievalQuery) -> Optional[RetrievalResult]:
        """
        Attempt to get a cached result for a query.
        
        Args:
            query: The retrieval query
            
        Returns:
            Optional[RetrievalResult]: Cached result if available
        """
        key = self._compute_key(query)
        if key in self.cache:
            result, timestamp = self.cache[key]
            
            # Check TTL
            if datetime.now() - timestamp > timedelta(seconds=self.config.ttl_seconds):
                del self.cache[key]
                self.misses += 1
                return None
            
            # Check similarity
            if self._is_similar_query(result.query, query):
                self.hits += 1
                return result
        
        self.misses += 1
        return None
    
    def put(self, query: RetrievalQuery, result: RetrievalResult):
        """
        Cache a retrieval result.
        
        Args:
            query: The retrieval query
            result: The result to cache
        """
        key = self._compute_key(query)
        self.cache[key] = (result, datetime.now())
        
        # Enforce max size
        if len(self.cache) > self.config.max_size:
            # Remove oldest entries
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1][1]
            )
            for old_key, _ in sorted_items[:len(self.cache) - self.config.max_size]:
                del self.cache[old_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.config.max_size,
            "hit_rate": hit_rate,
            "hits": self.hits,
            "misses": self.misses
        }
