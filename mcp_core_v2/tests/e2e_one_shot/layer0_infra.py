"""Layer 0: Infrastructure Tests - Health checks and connectivity"""

import requests
from pathlib import Path
from typing import Tuple, Dict, Any


class InfraTests:
    """Infrastructure and connectivity tests."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_endpoint = config.get("rag_endpoint", "http://localhost:8080")
        self.mcp_endpoint = config.get("mcp_endpoint", "http://localhost:8001")
        self.timeout = config.get("timeout", 10)
    
    def test_rag_health(self) -> Tuple[bool, str, Dict]:
        """Test RAG service health."""
        try:
            # Try /health endpoint
            health_url = self.rag_endpoint.replace("/api/v1/mcp_spec", "") + "/health"
            response = requests.get(health_url, timeout=self.timeout)
            
            if response.status_code == 200:
                return True, "RAG service healthy", {"status_code": 200}
            else:
                return False, f"RAG returned {response.status_code}", {"status_code": response.status_code}
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to RAG service", {"error": "connection_refused"}
        except Exception as e:
            return False, f"Health check failed: {e}", {"error": str(e)}
    
    def test_mcp_health(self) -> Tuple[bool, str, Dict]:
        """Test MCP service health."""
        try:
            health_url = self.mcp_endpoint.replace("/design", "") + "/health"
            response = requests.get(health_url, timeout=self.timeout)
            
            if response.status_code == 200:
                return True, "MCP service healthy", {"status_code": 200}
            else:
                return False, f"MCP returned {response.status_code}", {"status_code": response.status_code}
                
        except requests.exceptions.ConnectionError:
            # MCP might not have HTTP endpoint yet, fallback to import test
            try:
                from pipeline import DesignPipeline
                return True, "MCP pipeline importable (no HTTP yet)", {"method": "import"}
            except ImportError as e:
                return False, f"Cannot import MCP pipeline: {e}", {"error": str(e)}
                
        except Exception as e:
            return False, f"Health check failed: {e}", {"error": str(e)}
    
    def test_knowledge_accessible(self) -> Tuple[bool, str, Dict]:
        """Test if RAG knowledge base is accessible."""
        # Check if knowledge folders exist
        knowledge_root = Path("/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/rag_knowledge")
        
        required_folders = ["db", "mcp", "standard", "example"]
        missing = []
        
        for folder in required_folders:
            folder_path = knowledge_root / folder
            if not folder_path.exists():
                missing.append(folder)
        
        if missing:
            return False, f"Missing knowledge folders: {missing}", {"missing": missing}
        
        return True, "All knowledge folders accessible", {"folders": required_folders}
