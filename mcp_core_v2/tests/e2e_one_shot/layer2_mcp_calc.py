"""Layer 2: MCP Calculation Validation Tests"""

import json
from pathlib import Path
from typing import Tuple, Dict, Any
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline import DesignPipeline
from models.contracts import DesignRequest


class McpCalcTests:
    """MCP calculation validation tests."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tolerance = config.get("tolerance", {})
        self.fixtures_dir = Path(__file__).parent / "fixtures"
    
    def test_calculation(self, test_case: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """
        Test MCP calculation against golden result.
        
        Args:
            test_case: Dict with 'id', 'spec_file', 'result_file'
        
        Returns:
            (success, message, details)
        """
        test_id = test_case["id"]
        spec_file = test_case["spec_file"]
        golden_result_file = test_case["result_file"]
        
        # Load RAG spec
        spec_path = self.fixtures_dir / "golden_specs" / spec_file
        with open(spec_path) as f:
            rag_spec = json.load(f)
        
        # Load golden MCP result  
        golden_path = self.fixtures_dir / "golden_results" / golden_result_file
        with open(golden_path) as f:
            golden_result = json.load(f)
        
        # Convert RAG spec → MCP DesignRequest (via adapter)
        try:
            design_request = self._adapt_spec_to_request(rag_spec)
        except Exception as e:
            return False, f"Adapter failed: {e}", {"error": str(e)}
        
        # Run MCP pipeline
        try:
            pipeline = DesignPipeline()
            actual_result = pipeline.execute(design_request)
            actual_dict = actual_result.model_dump()
        except Exception as e:
            return False, f"MCP pipeline failed: {e}", {"error": str(e)}
        
        # Compare results
        diff = self._compare_results(golden_result, actual_dict)
        
        if diff:
            return False, "Results differ from golden", {"diff": diff}
        
        return True, "MCP calculation passed", {"actual_result": actual_dict}
    
    def _adapt_spec_to_request(self, rag_spec: Dict[str, Any]) -> DesignRequest:
        """
        Adapter: Convert RAG spec to MCP DesignRequest.
        
        This is a simplified version. Should match golden_generator.py logic.
        """
        from datetime import datetime
        project_input = rag_spec.get("project_input", {})
        
        # Map loads
        loads = []
        for load in project_input.get("loads", []):
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
        
        # Create request
        return DesignRequest(
            session_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            project_name=project_input["project_info"]["project_name"],
            loads=loads,
            panels=[],
            service_voltage=self._map_voltage(project_input["electrical_system"]["voltage_system"]),
            utility_service_size=100
        )
    
    def _get_device_mapping(self, device_code: str) -> Dict[str, Any]:
        """Map device code to MCP format."""
        mappings = {
            "AC-12000BTU": {"load_type": "HVAC", "power_watts": 1500, "is_continuous": True},
            "AC-18000BTU": {"load_type": "HVAC", "power_watts": 2200, "is_continuous": True},
            "AC-9000BTU": {"load_type": "HVAC", "power_watts": 1200, "is_continuous": True},
            "HEATER-3500W": {"load_type": "APPLIANCE", "power_watts": 3500, "is_continuous": True},
            "INDUCTION-3000W": {"load_type": "APPLIANCE", "power_watts": 3000, "is_continuous": False},
            "SOCKET-16A": {"load_type": "RECEPTACLE", "power_watts": 3680, "is_continuous": False},
            "SOCKET-13A": {"load_type": "RECEPTACLE", "power_watts": 2990, "is_continuous": False},
            "LIGHT-LED": {"load_type": "LIGHTING", "power_watts": 15, "is_continuous": False},
            "REFRIG-200W": {"load_type": "APPLIANCE", "power_watts": 200, "is_continuous": True},
        }
        return mappings.get(device_code, {"load_type": "OTHER", "power_watts": 1000})
    
    def _map_voltage(self, voltage_system: str) -> str:
        """Map Thai voltage to NEC."""
        mapping = {
            "TH_1PH_230V": "SINGLE_PHASE_240V",
            "TH_3PH_400V": "THREE_PHASE_480V"
        }
        return mapping.get(voltage_system, "SINGLE_PHASE_240V")
    
    def _find_room_name(self, room_id: str, rooms: list) -> str:
        """Find room name by ID."""
        for room in rooms:
            if room["room_id"] == room_id:
                return room["name"]
        return "Unknown"
    
    def _compare_results(self, golden: Dict, actual: Dict) -> Dict[str, Any]:
        """Compare golden and actual MCP results with tolerance."""
        diff = {}
        
        # Compare wire sizing
        golden_wires = golden.get("wire_sizing", {})
        actual_wires = actual.get("wire_sizing", {})
        
        wire_diff = self._compare_wire_sizing(golden_wires, actual_wires)
        if wire_diff:
            diff["wire_sizing"] = wire_diff
        
        # Compare breakers
        golden_breakers = golden.get("breaker_selections", {})
        actual_breakers = actual.get("breaker_selections", {})
        
        breaker_diff = self._compare_breakers(golden_breakers, actual_breakers)
        if breaker_diff:
            diff["breaker_selections"] = breaker_diff
        
        # Compare voltage drop
        vd_diff = self._compare_voltage_drop(golden_wires, actual_wires)
        if vd_diff:
            diff["voltage_drop"] = vd_diff
        
        return diff
    
    def _compare_wire_sizing(self, golden: Dict, actual: Dict) -> Dict:
        """Compare wire sizes."""
        diff = {}
        tolerance_exact = self.tolerance.get("wire_size_exact", True)
        
        for load_id in golden.keys():
            if load_id not in actual:
                diff[load_id] = {"error": "missing in actual"}
                continue
            
            golden_size = golden[load_id].get("wire_size")
            actual_size = actual[load_id].get("wire_size")
            
            if tolerance_exact and golden_size != actual_size:
                diff[load_id] = {"golden": golden_size, "actual": actual_size}
        
        return diff
    
    def _compare_breakers(self, golden: Dict, actual: Dict) -> Dict:
        """Compare breaker ratings."""
        diff = {}
        
        for load_id in golden.keys():
            if load_id not in actual:
                diff[load_id] = {"error": "missing in actual"}
                continue
            
            golden_rating = golden[load_id].get("breaker_rating")
            actual_rating = actual[load_id].get("breaker_rating")
            
            if golden_rating != actual_rating:
                diff[load_id] = {"golden": golden_rating, "actual": actual_rating}
        
        return diff
    
    def _compare_voltage_drop(self, golden_wires: Dict, actual_wires: Dict) -> Dict:
        """Compare voltage drop percentages."""
        diff = {}
        vd_tolerance = self.tolerance.get("voltage_drop_percent", 0.5)
        
        for load_id in golden_wires.keys():
            if load_id not in actual_wires:
                continue
            
            golden_vd = golden_wires[load_id].get("voltage_drop", 0)
            actual_vd = actual_wires[load_id].get("voltage_drop", 0)
            
            # Handle percentage strings (e.g., "1.2%")
            if isinstance(golden_vd, str):
                golden_vd = float(golden_vd.rstrip('%'))
            if isinstance(actual_vd, str):
                actual_vd = float(actual_vd.rstrip('%'))
            
            if abs(golden_vd - actual_vd) > vd_tolerance:
                diff[load_id] = {"golden": golden_vd, "actual": actual_vd}
        
        return diff
