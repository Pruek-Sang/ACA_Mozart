"""
Base Formatter - Abstract base class for all formatters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFormatter(ABC):
    """Abstract base class for report formatters."""
    
    @abstractmethod
    def format(self, mcp_result: Dict[str, Any]) -> str:
        """
        Transform MCP result into formatted output.
        
        Args:
            mcp_result: Dictionary from MCP Core export_to_dict()
            
        Returns:
            Formatted string (Markdown, HTML, etc.)
        """
        pass
    
    @abstractmethod
    def get_format_type(self) -> str:
        """Return the format type identifier (e.g., 'markdown', 'pdf', 'html')."""
        pass
