"""
CAD Generation Module for MCP Core v2

This module provides AutoLISP generation capabilities for electrical drawings.
Completely isolated from core calculations to ensure zero regression.

Architecture:
- standards/: Electrical standards (NEC, IEC, EIT) loaded from catalog
- drawing/: Drawing generators (E-101, E-201, E-301, E-401, E-501)
- validators/: Syntax and semantic validation
- test_dxf/: Mock DXF files for testing

Zero Regression Guarantee:
- No imports from core/* modules
- Uses only DesignResult interface (read-only)
- Completely optional (can be disabled)
"""

__version__ = '1.0.0-alpha'
__author__ = 'ACA_Mozart Team'
