"""
PDF Formatter - Transforms MCP JSON into PDF reports.

Status: PLANNED (not implemented yet)
Dependencies: reportlab or weasyprint (to be added)

Design Notes:
- Will use same data as MarkdownFormatter
- Template-based approach for consistent branding
- Support for company logo, header/footer
- A4 format for Thai electrical reports
"""

from typing import Dict, Any
from .base_formatter import BaseFormatter


class PdfFormatter(BaseFormatter):
    """
    Formats MCP design results as PDF.
    
    TODO: Implement when PDF export feature is needed.
    Dependencies to add:
    - reportlab (pure Python PDF generation)
    - OR weasyprint (HTML→PDF, requires system libs)
    """
    
    def get_format_type(self) -> str:
        return "pdf"
    
    def format(self, mcp_result: Dict[str, Any]) -> str:
        """
        Transform MCP result into PDF.
        
        Returns:
            Path to generated PDF file (not the content itself)
        """
        raise NotImplementedError(
            "PDF export is planned but not yet implemented. "
            "Use MarkdownFormatter for now."
        )
    
    def generate_pdf(
        self, 
        mcp_result: Dict[str, Any],
        output_path: str,
        template: str = "default"
    ) -> str:
        """
        Generate PDF file from MCP result.
        
        Args:
            mcp_result: Dictionary from MCP Core export_to_dict()
            output_path: Where to save the PDF
            template: Template name (default, minimal, detailed)
            
        Returns:
            Path to generated PDF file
        """
        # TODO: Implement PDF generation
        # 1. Convert to HTML using template
        # 2. Render HTML to PDF
        # 3. Save to output_path
        raise NotImplementedError("PDF generation not yet implemented")


# Placeholder for future implementation
def export_to_pdf(mcp_result: Dict[str, Any], output_path: str) -> str:
    """
    Export MCP result to PDF file.
    
    Args:
        mcp_result: Dictionary from MCP Core
        output_path: Where to save PDF
        
    Returns:
        Path to generated PDF
    """
    formatter = PdfFormatter()
    return formatter.generate_pdf(mcp_result, output_path)
