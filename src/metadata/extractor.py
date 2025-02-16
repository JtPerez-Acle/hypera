"""Legacy metadata extractor module for backward compatibility."""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetadataExtractor:
    """Legacy metadata extractor class.
    
    This is kept for backward compatibility and will be removed in future versions.
    Use the MetadataGenerationAgent instead.
    """
    
    def __init__(self):
        """Initialize the extractor."""
        import warnings
        warnings.warn(
            "MetadataExtractor is deprecated. Use MetadataGenerationAgent instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    async def extract_metadata(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract metadata from code.
        
        This is a stub implementation that returns empty metadata.
        Use MetadataGenerationAgent for actual metadata extraction.
        """
        return {
            "imports": [],
            "functions": [],
            "classes": [],
            "types": {},
            "dependencies": {}
        }
