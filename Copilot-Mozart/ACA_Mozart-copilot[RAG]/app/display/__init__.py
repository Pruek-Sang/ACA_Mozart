"""
Display Package - Computed Data Layer

This package implements the "Compute Once, Render Many" pattern.
All display-related calculations are centralized here.

Usage:
    from app.display import compute_display_data, render_markdown
    
    display_data = compute_display_data(mcp_result)
    markdown_text = render_markdown(display_data)
"""

from .compute import compute_display_data, DisplayData
# from .markdown_renderer import render_markdown  # TODO: Phase 1 later

__all__ = [
    'compute_display_data',
    'DisplayData',
    # 'render_markdown',
]
