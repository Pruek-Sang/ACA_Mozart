#!/usr/bin/env python3
"""
🔬 ACA_Mozart LLM Response Explorer
===================================
Interactive script เพื่อดู LLM response จริงๆ ในแต่ละ scenario

Usage:
    python tests/explore_llm_responses.py

Scenarios ที่รองรับ:
1. One-shot complete data (บ้านพื้นฐาน)
2. Minimal data (ข้อมูลน้อยสุด)
3. Incomplete data (ข้อมูลไม่ครบ)
4. Heavy kitchen (ครัวหนัก)
5. QA - ถามมาตรฐาน

Author: Aethelgard
"""

import asyncio
import json
import httpx
from typing import Any
from pprint import pprint

# API Base URL
BASE_URL = "http://localhost:8080"

# Pretty print helper
def pretty_json(data: Any, title: str = "") -> None:
    """Print JSON with title"""
    if title:
        print(f"\n{'='*60}")
        print(f"📋 {title}")
        print('='*60)
    print(json.dumps(data, indent=2, ensure_ascii=False))

# ============================================================================
# TEST SCENARIOS
# ============================================================================

SCENARIOS = {
    "1_oneshot_complete": {
        "name": "🏠 One-shot Complete (บ้านพื้นฐาน 1 ชั้น)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "Test House - Complete",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "location": "Bangkok",
            "rooms": [
                {"name": "ห้องนั่งเล่น", "type": "living_room", "area_sqm": 25.0},
                {"name": "ห้องนอนใหญ่", "type": "bedroom", "area_sqm": 15.0},
                {"name": "ห้องน้ำ", "type": "bathroom", "area_sqm": 5.0},
                {"name": "ครัว", "type": "kitchen", "area_sqm": 10.0}
            ],
            "loads": [
                {"room_name": "ห้องนั่งเล่น", "device": "AC-12000BTU", "quantity": 1},
                {"room_name": "ห้องนั่งเล่น", "device": "SOCKET-16A", "quantity": 4},
                {"room_name": "ห้องนอนใหญ่", "device": "AC-9000BTU", "quantity": 1},
                {"room_name": "ห้องน้ำ", "device": "HEATER-3500W", "quantity": 1},
                {"room_name": "ครัว", "device": "SOCKET-16A", "quantity": 4}
            ],
            "user_constraints": ["rcd_for_all_outlets"]
        }
    },
    
    "2_minimal": {
        "name": "📦 Minimal Data (ข้อมูลน้อยสุดที่ยอมรับได้)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "Minimal House",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "rooms": [
                {"name": "ห้องนั่งเล่น", "type": "living_room"}
            ],
            "loads": [
                {"room_name": "ห้องนั่งเล่น", "device": "SOCKET-16A", "quantity": 2}
            ]
        }
    },
    
    "3_incomplete": {
        "name": "⚠️ Incomplete Data (ข้อมูลไม่ครบ - ควร error)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "Broken House",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "rooms": [
                {"name": "ห้องนั่งเล่น"},  # ❌ ไม่มี type
                {"name": "ห้องนอน", "type": "bedroom"}
            ],
            "loads": [
                {"room_name": "ห้องที่ไม่มี", "device": "SOCKET-16A", "quantity": 2}  # ❌ room ไม่มี
            ]
        }
    },
    
    "4_heavy_kitchen": {
        "name": "🍳 Heavy Kitchen (ครัวเครื่องใช้ไฟฟ้าหนัก)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "House with Heavy Kitchen",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "location": "Bangkok",
            "rooms": [
                {"name": "ห้องนั่งเล่น", "type": "living_room", "area_sqm": 20.0},
                {"name": "ครัวหนัก", "type": "kitchen", "area_sqm": 15.0}
            ],
            "loads": [
                {"room_name": "ห้องนั่งเล่น", "device": "AC-12000BTU", "quantity": 1},
                {"room_name": "ครัวหนัก", "device": "COOKTOP-INDUCTION-7KW", "quantity": 1},
                {"room_name": "ครัวหนัก", "device": "OVEN-ELECTRIC-3KW", "quantity": 1},
                {"room_name": "ครัวหนัก", "device": "SOCKET-16A", "quantity": 6}
            ],
            "user_constraints": ["split_kitchen_circuit", "dedicated_circuit_for_cooktop"]
        }
    },
    
    "5_qa_standard": {
        "name": "📚 QA - ถามมาตรฐาน วสท.",
        "endpoint": "/api/v1/ask",
        "payload": {
            "query": "สายไฟ THW ขนาด 2.5 ตร.มม. รับกระแสได้กี่แอมป์?",
            "context_hint": ["standard"],
            "language": "th"
        }
    },
    
    "6_qa_device": {
        "name": "🔌 QA - ถามเรื่องอุปกรณ์",
        "endpoint": "/api/v1/ask",
        "payload": {
            "query": "เครื่องทำน้ำอุ่น 3500W ต้องใช้ breaker กี่แอมป์?",
            "context_hint": ["db", "standard"],
            "language": "th"
        }
    },
    
    "7_progressive_step1": {
        "name": "🚶 Progressive Step 1 (แค่บอกชื่อโปรเจค)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "บ้านคุณสมชาย",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "rooms": [],
            "loads": []
        }
    },
    
    "8_progressive_step2": {
        "name": "🚶 Progressive Step 2 (บอกห้องแล้ว แต่ยังไม่บอก load)",
        "endpoint": "/api/v1/mcp_spec",
        "payload": {
            "project_name": "บ้านคุณสมชาย",
            "building_type": "residential",
            "voltage_system": "TH_1PH_230V",
            "rooms": [
                {"name": "ห้องนั่งเล่น", "type": "living_room", "area_sqm": 30.0},
                {"name": "ห้องนอนใหญ่", "type": "bedroom", "area_sqm": 20.0},
                {"name": "ห้องครัว", "type": "kitchen", "area_sqm": 12.0}
            ],
            "loads": []
        }
    }
}

# ============================================================================
# API CALLERS
# ============================================================================

async def call_api(endpoint: str, payload: dict, timeout: float = 60.0) -> dict:
    """Call ACA_Mozart API and return response"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{BASE_URL}{endpoint}",
                json=payload
            )
            return {
                "status_code": response.status_code,
                "body": response.json() if response.text else {},
                "success": response.is_success
            }
        except httpx.TimeoutException:
            return {"status_code": 504, "body": {"error": "Timeout"}, "success": False}
        except httpx.ConnectError:
            return {"status_code": 0, "body": {"error": "Cannot connect to server"}, "success": False}
        except Exception as e:
            return {"status_code": 0, "body": {"error": str(e)}, "success": False}


async def run_scenario(key: str) -> None:
    """Run a single scenario and display results"""
    scenario = SCENARIOS[key]
    
    print(f"\n{'#'*70}")
    print(f"# {scenario['name']}")
    print(f"{'#'*70}")
    
    print("\n📤 INPUT (ส่งไปที่ API):")
    pretty_json(scenario["payload"])
    
    print(f"\n⏳ Calling {scenario['endpoint']}...")
    result = await call_api(scenario["endpoint"], scenario["payload"])
    
    print(f"\n📥 RESPONSE (Status: {result['status_code']}):")
    
    if result["success"]:
        # For mcp_spec, show key parts
        if scenario["endpoint"] == "/api/v1/mcp_spec":
            body = result["body"]
            
            # Show project_input (the main output)
            if "project_input" in body:
                pretty_json(body["project_input"], "Project Input Spec (for MCP)")
            
            # Show LLM metadata
            if "llm_metadata" in body:
                print(f"\n🤖 LLM: {body['llm_metadata'].get('model', 'N/A')}")
                print(f"📚 Docs used: {body['llm_metadata'].get('retrieved_docs', [])}")
        
        # For ask, show answer
        elif scenario["endpoint"] == "/api/v1/ask":
            body = result["body"]
            print(f"\n💬 Answer:\n{body.get('answer', 'N/A')}")
            print(f"\n📊 Confidence: {body.get('confidence', 'N/A')}")
            if body.get("sources"):
                print(f"📎 Sources: {[s.get('file', 'N/A') for s in body['sources']]}")
        
        else:
            pretty_json(result["body"])
    else:
        # Error case
        pretty_json(result["body"], "❌ ERROR")


async def run_all_scenarios() -> None:
    """Run all scenarios"""
    for key in SCENARIOS:
        await run_scenario(key)
        print("\n" + "-"*70)
        input("Press Enter to continue to next scenario...")


def interactive_menu() -> None:
    """Interactive menu"""
    while True:
        print("\n" + "="*70)
        print("🔬 ACA_Mozart LLM Response Explorer")
        print("="*70)
        print("\nเลือก scenario ที่ต้องการทดสอบ:")
        print()
        
        for i, (key, scenario) in enumerate(SCENARIOS.items(), 1):
            print(f"  {i}. {scenario['name']}")
        
        print()
        print("  a. รันทุก scenario")
        print("  q. ออก")
        print()
        
        choice = input("เลือก (1-8, a, q): ").strip().lower()
        
        if choice == 'q':
            print("👋 Bye!")
            break
        elif choice == 'a':
            asyncio.run(run_all_scenarios())
        else:
            try:
                idx = int(choice) - 1
                keys = list(SCENARIOS.keys())
                if 0 <= idx < len(keys):
                    asyncio.run(run_scenario(keys[idx]))
                else:
                    print("❌ ไม่ถูกต้อง")
            except ValueError:
                print("❌ ไม่ถูกต้อง")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  🔬 ACA_Mozart LLM Response Explorer                             ║
║                                                                   ║
║  ใช้ script นี้เพื่อดู LLM response จริงๆ ใน scenarios ต่างๆ      ║
║                                                                   ║
║  ⚠️  ต้อง start server ก่อน:                                      ║
║      uvicorn app.routes:app --reload --port 8080                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check server
    import httpx
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{BASE_URL}/")
            if r.is_success:
                print(f"✅ Server is running at {BASE_URL}")
                print(f"   Service: {r.json().get('service', 'N/A')}")
                print()
                interactive_menu()
            else:
                print(f"❌ Server responded with error: {r.status_code}")
    except httpx.ConnectError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Please start the server first:")
        print("   uvicorn app.routes:app --reload --port 8080")
    except Exception as e:
        print(f"❌ Error: {e}")
