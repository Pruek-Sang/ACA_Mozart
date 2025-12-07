"""
Golden Reference Generator for One-Shot E2E Tests

This script auto-generates golden reference data from:
1. User prompts → RAG specs (via /api/v1/mcp_spec)
2. RAG specs → MCP results (via MCP Core pipeline)

Usage:
    python golden_generator.py --mode all
    python golden_generator.py --mode rag-only
    python golden_generator.py --mode mcp-only
"""

import json
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.contracts import DesignRequest, DesignResult
from pipeline import DesignPipeline


class GoldenGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize generator with configuration."""
        self.config = self._load_config(config_path)
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.prompts_dir = self.fixtures_dir / "prompts"
        self.golden_specs_dir = self.fixtures_dir / "golden_specs"
        self.golden_results_dir = self.fixtures_dir / "golden_results"
        
        # Create directories
        for dir_path in [self.prompts_dir, self.golden_specs_dir, self.golden_results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load test configuration."""
        config_file = Path(__file__).parent / config_path
        if not config_file.exists():
            # Default config
            return {
                "rag_endpoint": "http://localhost:8080/api/v1/mcp_spec",
                "mcp_endpoint": "http://localhost:8001/design",  # TBD
                "timeout": 30,
                "tolerance": {
                    "current_percent": 5.0,
                    "voltage_drop_percent": 0.5,
                    "wire_size_exact": True
                }
            }
        
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def generate_rag_golden(self, prompt_file: str) -> Dict[str, Any]:
        """
        Generate golden RAG spec from user prompt.
        
        Args:
            prompt_file: Name of prompt file (e.g., "OS-1_simple_house.txt")
        
        Returns:
            Golden spec JSON
        """
        prompt_path = self.prompts_dir / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        # Read prompt
        with open(prompt_path) as f:
            prompt_text = f.read().strip()
        
        print(f"🔵 Generating RAG golden for: {prompt_file}")
        print(f"📝 Prompt: {prompt_text[:100]}...")
        
        # Call RAG /mcp_spec endpoint
        try:
            response = requests.post(
                self.config["rag_endpoint"],
                json={
                    "query": prompt_text,
                    "interaction_mode": "one_shot"  # Force one-shot
                },
                timeout=self.config["timeout"]
            )
            response.raise_for_status()
            
            spec_data = response.json()
            
            # Save golden spec
            test_id = prompt_file.replace(".txt", "")
            golden_path = self.golden_specs_dir / f"{test_id}_spec.json"
            
            with open(golden_path, 'w', encoding='utf-8') as f:
                json.dump(spec_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Golden spec saved: {golden_path}")
            return spec_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ RAG call failed: {e}")
            raise
    
    def generate_mcp_golden(self, spec_file: str) -> Dict[str, Any]:
        """
        Generate golden MCP result from RAG spec.
        
        Args:
            spec_file: Name of spec file (e.g., "OS-1_spec.json")
        
        Returns:
            Golden result JSON
        """
        spec_path = self.golden_specs_dir / spec_file
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
        
        # Read spec
        with open(spec_path) as f:
            spec_data = json.load(f)
        
        print(f"🔵 Generating MCP golden for: {spec_file}")
        
        # Convert RAG spec → MCP DesignRequest (via adapter)
        design_request = self._adapt_spec_to_request(spec_data)
        
        # Run MCP pipeline
        try:
            pipeline = DesignPipeline()
            result = pipeline.execute(design_request)
            
            # Convert to dict
            result_dict = result.model_dump()
            
            # Save golden result
            test_id = spec_file.replace("_spec.json", "")
            golden_path = self.golden_results_dir / f"{test_id}_result.json"
            
            with open(golden_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Golden result saved: {golden_path}")
            return result_dict
            
        except Exception as e:
            print(f"❌ MCP pipeline failed: {e}")
            raise
    
    def _adapt_spec_to_request(self, spec_data: Dict[str, Any]) -> DesignRequest:
        """
        Adapter: Convert RAG ProjectInputSpec → MCP DesignRequest.
        
        This is a simplified version. Full implementation should be in mcp_adapter.py
        """
        # Extract project_input from McpSpecResponse
        project_input = spec_data.get("project_input", {})
        
        # Map rooms and loads
        loads = []
        for load in project_input.get("loads", []):
            # Map device_code to load_type and power
            device_mapping = self._get_device_mapping(load["device_code"])
            
            loads.append({
                "id": load["load_id"],
                "name": load.get("notes", load["device_code"]),
                "load_type": device_mapping["load_type"],
                "voltage": self._map_voltage(project_input["electrical_system"]["voltage_system"]),
                "power_watts": device_mapping["power_watts"],
                "quantity": load["qty"],
                "location": {
                    "room": self._find_room_name(load["room_id"], project_input["rooms"]),
                    "floor": None
                },
                "is_continuous": device_mapping.get("is_continuous", False)
            })
        
        # Create DesignRequest
        return DesignRequest(
            session_id=f"golden_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            project_name=project_input["project_info"]["project_name"],
            loads=loads,
            panels=[],  # TBD: Generate from rooms
            service_voltage=self._map_voltage(project_input["electrical_system"]["voltage_system"]),
            utility_service_size=100  # Default for now
        )
    
    def _get_device_mapping(self, device_code: str) -> Dict[str, Any]:
        """Map device_code to MCP format."""
        # This should read from catalog/DEVICE_CODES.md
        mappings = {
            "AC-12000BTU": {"load_type": "HVAC", "power_watts": 1500, "is_continuous": True},
            "AC-18000BTU": {"load_type": "HVAC", "power_watts": 2200, "is_continuous": True},
            "HEATER-3500W": {"load_type": "APPLIANCE", "power_watts": 3500, "is_continuous": True},
            "SOCKET-16A": {"load_type": "RECEPTACLE", "power_watts": 3680, "is_continuous": False},
            "LIGHT-LED": {"load_type": "LIGHTING", "power_watts": 15, "is_continuous": False},
        }
        return mappings.get(device_code, {"load_type": "OTHER", "power_watts": 1000})
    
    def _map_voltage(self, voltage_system: str) -> str:
        """Map Thai voltage to NEC voltage."""
        mapping = {
            "TH_1PH_230V": "SINGLE_PHASE_240V",
            "TH_3PH_400V": "THREE_PHASE_480V"
        }
        return mapping.get(voltage_system, "SINGLE_PHASE_240V")
    
    def _find_room_name(self, room_id: str, rooms: List[Dict]) -> str:
        """Find room name by ID."""
        for room in rooms:
            if room["room_id"] == room_id:
                return room["name"]
        return "Unknown"
    
    def generate_all(self):
        """Generate all golden references."""
        print("🚀 Starting golden reference generation...\n")
        
        # Find all prompt files
        prompt_files = sorted(self.prompts_dir.glob("OS-*.txt"))
        
        if not prompt_files:
            print("⚠️  No prompt files found in fixtures/prompts/")
            print("   Please create prompt files first (OS-1_*.txt, OS-2_*.txt, etc.)")
            return
        
        stats = {"success": 0, "failed": 0}
        
        for prompt_file in prompt_files:
            try:
                # Generate RAG golden
                spec_data = self.generate_rag_golden(prompt_file.name)
                
                # Generate MCP golden
                spec_filename = prompt_file.name.replace(".txt", "_spec.json")
                self.generate_mcp_golden(spec_filename)
                
                stats["success"] += 1
                print(f"✅ Completed: {prompt_file.name}\n")
                
            except Exception as e:
                stats["failed"] += 1
                print(f"❌ Failed: {prompt_file.name} - {e}\n")
        
        print(f"\n📊 Summary:")
        print(f"   Success: {stats['success']}")
        print(f"   Failed: {stats['failed']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate golden references for E2E tests")
    parser.add_argument("--mode", choices=["all", "rag-only", "mcp-only"], default="all")
    parser.add_argument("--test-id", help="Specific test ID (e.g., OS-1)")
    
    args = parser.parse_args()
    
    generator = GoldenGenerator()
    
    if args.mode == "all":
        generator.generate_all()
    elif args.mode == "rag-only":
        if args.test_id:
            generator.generate_rag_golden(f"{args.test_id}_*.txt")
        else:
            print("Please specify --test-id for single test generation")
    # ... similar for mcp-only


if __name__ == "__main__":
    main()
