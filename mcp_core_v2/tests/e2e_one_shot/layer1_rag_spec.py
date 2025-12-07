"""Layer 1: RAG → Spec Validation Tests"""

import json
import requests
from pathlib import Path
from typing import Tuple, Dict, Any


class RagSpecTests:
    """RAG spec generation validation tests."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_endpoint = config["rag_endpoint"]
        self.timeout = config.get("timeout", 30)
        self.fixtures_dir = Path(__file__).parent / "fixtures"
    
    def test_spec_generation(self, test_case: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """
        Test RAG spec generation against golden reference.
        
        Args:
            test_case: Dict with 'id', 'prompt_file', 'spec_file'
        
        Returns:
            (success, message, details)
        """
        test_id = test_case["id"]
        prompt_file = test_case["prompt_file"]
        golden_spec_file = test_case["spec_file"]
        
        # Load prompt
        prompt_path = self.fixtures_dir / "prompts" / prompt_file
        with open(prompt_path) as f:
            prompt_text = f.read().strip()
        
        # Load golden spec
        golden_path = self.fixtures_dir / "golden_specs" / golden_spec_file
        with open(golden_path) as f:
            golden_spec = json.load(f)
        
        # Call RAG
        try:
            response = requests.post(
                self.rag_endpoint,
                json={
                    "query": prompt_text,
                    "interaction_mode": "one_shot"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            actual_spec = response.json()
            
        except requests.exceptions.RequestException as e:
            return False, f"RAG call failed: {e}", {"error": str(e)}
        
        # Validate spec structure
        validation_errors = self._validate_spec_structure(actual_spec)
        if validation_errors:
            return False, f"Spec structure invalid", {"errors": validation_errors}
        
        # Validate device codes
        invalid_codes = self._validate_device_codes(actual_spec)
        if invalid_codes:
            return False, f"Invalid device codes: {invalid_codes}", {"invalid_codes": invalid_codes}
        
        # Compare with golden (key fields only)
        diff = self._compare_specs(golden_spec, actual_spec)
        if diff:
            return False, "Spec differs from golden", {"diff": diff}
        
        return True, "Spec generation passed", {"actual_spec": actual_spec}
    
    def _validate_spec_structure(self, spec: Dict[str, Any]) -> List[str]:
        """Validate that spec has all required fields."""
        errors = []
        
        # Check top-level structure
        if "project_input" not in spec:
            errors.append("Missing 'project_input'")
            return errors
        
        project_input = spec["project_input"]
        
        # Check required sections
        required_sections = ["project_info", "electrical_system", "rooms", "loads", "constraints"]
        for section in required_sections:
            if section not in project_input:
                errors.append(f"Missing section: {section}")
        
        # Check rooms have required fields
        for i, room in enumerate(project_input.get("rooms", [])):
            if not room.get("room_id"):
                errors.append(f"Room {i} missing room_id")
            if not room.get("template_code"):
                errors.append(f"Room {i} missing template_code")
        
        # Check loads have required fields
        for i, load in enumerate(project_input.get("loads", [])):
            if not load.get("load_id"):
                errors.append(f"Load {i} missing load_id")
            if not load.get("device_code"):
                errors.append(f"Load {i} missing device_code")
            if not load.get("room_id"):
                errors.append(f"Load {i} missing room_id")
        
        return errors
    
    def _validate_device_codes(self, spec: Dict[str, Any]) -> List[str]:
        """Validate that all device codes exist in catalog."""
        # Known device codes (should read from DEVICE_CODES.md)
        valid_codes = {
            "AC-12000BTU", "AC-18000BTU", "AC-9000BTU",
            "HEATER-3500W", "INDUCTION-3000W",
            "SOCKET-16A", "SOCKET-13A",
            "LIGHT-LED", "LIGHT-FL", "REFRIG-200W"
        }
        
        invalid = []
        for load in spec.get("project_input", {}).get("loads", []):
            device_code = load.get("device_code")
            if device_code and device_code not in valid_codes:
                invalid.append(device_code)
        
        return invalid
    
    def _compare_specs(self, golden: Dict, actual: Dict) -> Dict[str, Any]:
        """Compare key fields between golden and actual specs."""
        diff = {}
        
        # Compare project_info
        golden_pi = golden.get("project_input", {})
        actual_pi = actual.get("project_input", {})
        
        # Compare voltage system
        if golden_pi.get("electrical_system", {}).get("voltage_system") != \
           actual_pi.get("electrical_system", {}).get("voltage_system"):
            diff["voltage_system"] = {
                "golden": golden_pi.get("electrical_system", {}).get("voltage_system"),
                "actual": actual_pi.get("electrical_system", {}).get("voltage_system")
            }
        
        # Compare number of rooms/loads
        if len(golden_pi.get("rooms", [])) != len(actual_pi.get("rooms", [])):
            diff["room_count"] = {
                "golden": len(golden_pi.get("rooms", [])),
                "actual": len(actual_pi.get("rooms", []))
            }
        
        if len(golden_pi.get("loads", [])) != len(actual_pi.get("loads", [])):
            diff["load_count"] = {
                "golden": len(golden_pi.get("loads", [])),
                "actual": len(actual_pi.get("loads", []))
            }
        
        return diff
