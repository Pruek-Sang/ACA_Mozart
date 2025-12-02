"""
Data Access Layer (DAL) for MCP Core v2

File-based catalog system reading from rag_knowledge/db/catalog_rows.csv
No external database required - all data from local CSV files.

Available modules:
- file_catalog_dal: Low-level CSV file reader
- catalog_dal: High-level catalog operations for electrical components
"""

from dal.file_catalog_dal import get_file_catalog, FileCatalogDAL, CatalogRow
from dal.catalog_dal import get_catalog_dal, CatalogDAL

__all__ = [
    'get_file_catalog',
    'FileCatalogDAL', 
    'CatalogRow',
    'get_catalog_dal',
    'CatalogDAL',
]
