"""
Report Formatters Module
========================
Transforms MCP JSON results into various output formats.

Available Formatters:
- MarkdownFormatter: Human-readable Markdown reports
- PdfFormatter: PDF export (planned)
"""

from .markdown_formatter import MarkdownFormatter, format_design_report

__all__ = [
    "MarkdownFormatter",
    "format_design_report",
]
