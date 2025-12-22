
import requests
import json
import sys

# Usage: python tests/verify_cloud_rag.py [CLOUD_RUN_URL]
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

print(f"🚀 Testing RAG Service at: {URL}")

payload = {
    "project_name": "Debug VD Distance",
    "building_type": "residential",
    "voltage_system": "TH_1PH_230V",
    "rooms": [
        {"name": "Living Room", "type": "living", "floor": 1, "area_sqm": 25},
        {"name": "Bedroom 1", "type": "bedroom", "floor": 2, "area_sqm": 20}
    ],
    "loads": [
        {"room_name": "Living Room", "device": "AC-18000BTU", "quantity": 1},
        {"room_name": "Bedroom 1", "device": "AC-12000BTU", "quantity": 1, "branch_distance_m": 25.5} # Defined distance
    ],
    "service_distance_m": 45.0, # Defined distance
    "site_context": {
        "distance_to_transformer": "less_than_50m",
        "installation_area": "indoor",
        "panel_type": "main",
        "conduit_grouping": "1"
    }
}

try:
    print("📤 Sending design request...")
    resp = requests.post(f"{URL}/api/v1/design", json=payload, timeout=60)
    
    print(f"📥 Response Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        
        # 1. Check RAG Spec Generation
        spec = data.get("spec", {}).get("project_input", {})
        proj_info = spec.get("project_info", {})
        loads = spec.get("loads", [])
        
        print("\n🔍 Verifying RAG Spec (LLM Output):")
        svc_dist = proj_info.get("service_distance_m")
        print(f"   - Service Distance: {svc_dist} m (Expected: 45.0) -> {'✅' if svc_dist == 45.0 else '❌'}")
        
        branch_ok = False
        empty_loads = len(loads) == 0
        if empty_loads:
            print(f"   - Loads: 0 items found! ❌ (CRITICAL ERROR - LLM or Mapper failed)")
        else:
            print(f"   - Loads: {len(loads)} items found ✅")
            for l in loads:
                dist = l.get("branch_distance_m")
                if dist == 25.5:
                    print(f"   - Load {l.get('load_id')} has distance {dist} m ✅")
                    branch_ok = True
            
            if not branch_ok:
                print(f"   - Load with 25.5m distance NOT FOUND ❌")

        # 2. Check MCP Core Result (if available)
        design_result = data.get("design_result")
        if design_result:
            print("\n🔍 Verifying MCP Calculation:")
            print("   - Design Result received ✅")
            # In a real scenario, we would check wire sizes here
        else:
            print("\n⚠️ MCP Result missing (Check MCP connection)")

    else:
        print(f"❌ Error Response: {resp.text}")

except Exception as e:
    print(f"💥 Connection Failed: {e}")
