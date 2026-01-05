
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Adjust path to find app module
sys.path.insert(0, '/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]')

from app.service import RagService

# Mock LLM Response with floor_distances (Trigger the bug path)
MOCK_LLM_RESPONSE = """
{
  "project_name": "Test Project",
  "floor_distances": {"1": 15, "2": 25}, 
  "rooms": [{"name": "Living", "type": "living", "floor": 1}],
  "loads": [{"room_name": "Living", "device": "SOCKET", "quantity": 1}]
}
"""

def reproduce_bug():
    print("🔬 REPRODUCING THE BUG IN RagService...")
    
    service = RagService()
    
    # Mock internal methods to isolate extraction
    service._get_generation_config = MagicMock()
    service._generate_content = MagicMock(return_value=MOCK_LLM_RESPONSE)
    service._extract_floor_distances = MagicMock(return_value={}) # Fallback regex
    
    print("\n1. Calling _extract_loads_from_text with mock LLM response...")
    print(f"   Mock Response includes: floor_distances: {{'1': 15, '2': 25}}")
    
    result = service._extract_loads_from_text("Test Query")
    
    print("\n2. Result received:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Analyze Result
    if "error" in result:
        print("\n❌ CRASH DETECTED! The NameError was caught and returned as error.")
        print(f"   Error message: {result['error']}")
        
        if "name 'llm_floor_distances' is not defined" in str(result['error']):
             print("\n🎯 CONFIRMED: 'llm_floor_distances' NameError is the root cause!")
    else:
        # Check if floor_distances were actually used
        fd = result.get("floor_distances")
        print(f"\n   floor_distances in result: {fd}")
        
        if fd == {"1": 15, "2": 25} or fd == {1: 15, 2: 25}:
            print("\n✅ BUG FIXED (or not present). The code used LLM floor_distances.")
        else:
            print("\n⚠️ BUG ACTIVE (Silent): LLM floor_distances ignored! (Fallback used)")

if __name__ == "__main__":
    reproduce_bug()
