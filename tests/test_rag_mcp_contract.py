"""
RAG ↔ MCP Contract Test - Verify API schemas match
Catches: Field mismatches between RAG and MCP

This test verifies:
1. RAG McpDesignRequest fields match MCP DesignRequestInput
2. MCP DesignResultOutput fields match RAG McpDesignResponse  
3. Core required fields exist in both
"""
import sys
import os
import pytest

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Copilot-Mozart', 'ACA_Mozart-copilot[RAG]'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_core_v2'))


class TestRAGToMCPContract:
    """Test RAG → MCP request contract."""
    
    def test_request_core_fields_exist(self):
        """Core request fields must exist in both RAG and MCP."""
        from app.mcp_adapter import McpDesignRequest
        from api import DesignRequestInput
        
        # Get field names
        rag_fields = set(McpDesignRequest.__dataclass_fields__.keys())
        mcp_fields = set(DesignRequestInput.model_fields.keys())
        
        # Core fields that MUST match
        required_fields = {
            "session_id",
            "project_name", 
            "loads",
            "panels",
        }
        
        for field in required_fields:
            assert field in rag_fields, f"RAG McpDesignRequest missing: {field}"
            assert field in mcp_fields, f"MCP DesignRequestInput missing: {field}"
    
    def test_site_context_field_exists(self):
        """site_context field must exist for installation parameters."""
        from app.mcp_adapter import McpDesignRequest
        from api import DesignRequestInput
        
        rag_fields = set(McpDesignRequest.__dataclass_fields__.keys())
        mcp_fields = set(DesignRequestInput.model_fields.keys())
        
        assert "site_context" in rag_fields, "RAG missing site_context"
        assert "site_context" in mcp_fields, "MCP missing site_context"


class TestMCPToRAGContract:
    """Test MCP → RAG response contract."""
    
    def test_response_core_fields_exist(self):
        """Core response fields must exist in MCP output."""
        from api import DesignResultOutput
        
        mcp_fields = set(DesignResultOutput.model_fields.keys())
        
        # Core fields that RAG expects
        expected_fields = {
            "session_id",
            "calculations",
            "wire_sizing",
            "breaker_selections",
            "grouped_circuits",
            "readable_report",
        }
        
        for field in expected_fields:
            assert field in mcp_fields, f"MCP DesignResultOutput missing: {field}"
    
    def test_grouped_circuits_type(self):
        """grouped_circuits must be List type (not Dict)."""
        from api import DesignResultOutput
        import typing
        
        field_info = DesignResultOutput.model_fields.get("grouped_circuits")
        assert field_info is not None, "grouped_circuits field not found"
        
        # Should be Optional[List[...]]
        annotation = field_info.annotation
        # Check it's not a Dict
        origin = typing.get_origin(annotation)
        if origin is not None:
            assert origin is not dict, "grouped_circuits should be List, not Dict"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
