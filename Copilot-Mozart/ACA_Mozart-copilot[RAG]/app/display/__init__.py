"""
Display Package - Computed Data Layer

This package implements the "Compute Once, Render Many" pattern.
All display-related calculations are centralized here.

Usage:
    from app.display import compute_display_data, render_markdown
    from app.display import format_audit_for_frontend
    
    display_data = compute_display_data(mcp_result)
    markdown_text = render_markdown(display_data)
    audit_rows = format_audit_for_frontend(audit_results)
"""

from .compute import compute_display_data, DisplayData
from .markdown_renderer import render_markdown
from .audit_document import format_audit_for_frontend, render_audit_document

__all__ = [
    'compute_display_data',
    'DisplayData',
    'render_markdown',
    'format_audit_for_frontend',
    'render_audit_document',
]
