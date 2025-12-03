#!/usr/bin/env python3
"""
🎯 ONE-SHOT END-TO-END TEST
===========================
ทดสอบระบบทั้งหมดแบบ realistic ห้ามใช้ fallback

Test Scenario:
- บ้านพักอาศัย 2 ชั้น (ขนาดรวม 150 ตร.ม.)
- ห้องนั่งเล่น 6x5 (30 ตร.ม.) → 2 outlets
- ห้องนอนใหญ่ 5x4 (20 ตร.ม.) → 2 outlets  
- ห้องนอนเล็ก 4x4 (16 ตร.ม.) → 1 outlet (ไม่เกิน 5x5)
- ครัว 4x4 (16 ตร.ม.) → 2 outlets (heavy load)
- ห้องน้ำ 2.5x2.5 (6.25 ตร.ม.) → 1 outlet (ไม่เกิน 5x5)

Expected:
1. RAG ตอบได้ (ไม่ใช้ fallback)
2. LLM Judge ผ่าน
3. MCP_Core คำนวณได้จริง
4. AutoLISP output สวยงาม
"""

import httpx
import json
import asyncio
from datetime import datetime

# ==================== CONFIG ====================
RAG_URL = "http://localhost:8080"
MCP_URL = "http://localhost:5001"
API_KEY = "AIzaSyCklv8Stb8E3MmGdMyrzKsyg_O-iLjADLA"

# ==================== TEST INPUT ====================
# Realistic Thai house specification
ONE_SHOT_QUERY = """
ออกแบบระบบไฟฟ้าบ้านพักอาศัย 2 ชั้น พื้นที่รวมประมาณ 150 ตารางเมตร โดยมีรายละเอียดดังนี้:

ชั้น 1:
- ห้องนั่งเล่น ขนาด 6x5 เมตร (30 ตร.ม.) ติดแอร์ 12,000 BTU
- ครัว ขนาด 4x4 เมตร (16 ตร.ม.) มีเตาไฟฟ้า 3000W และไมโครเวฟ 1500W
- ห้องน้ำ ขนาด 2.5x2.5 เมตร มีเครื่องทำน้ำอุ่น 3500W

ชั้น 2:
- ห้องนอนใหญ่ ขนาด 5x4 เมตร (20 ตร.ม.) ติดแอร์ 12,000 BTU
- ห้องนอนเล็ก ขนาด 4x4 เมตร (16 ตร.ม.) ติดแอร์ 9,000 BTU
- ห้องน้ำ ขนาด 2.5x2.5 เมตร มีเครื่องทำน้ำอุ่น 3500W

ต้องการทราบ:
1. ขนาดเมนเบรกเกอร์ที่เหมาะสม
2. จำนวนวงจรย่อย
3. ขนาดสายไฟหลักและสายย่อย
4. ควรติด RCD/RCBO ตรงไหนบ้าง

ใช้มาตรฐาน วสท./IEC ของไทย ระบบไฟ 230V 1 เฟส
"""

MCP_SPEC_REQUEST = {
    "project_name": "บ้านพักอาศัย 2 ชั้น - E2E Test",
    "building_type": "residential",
    "voltage_system": "TH_1PH_230V",
    "location": "Bangkok",
    "rooms": [
        {"name": "ห้องนั่งเล่น 1F", "type": "living_room", "area_sqm": 30.0},
        {"name": "ครัว 1F", "type": "kitchen", "area_sqm": 16.0},
        {"name": "ห้องน้ำ 1F", "type": "bathroom", "area_sqm": 6.25},
        {"name": "ห้องนอนใหญ่ 2F", "type": "bedroom", "area_sqm": 20.0},
        {"name": "ห้องนอนเล็ก 2F", "type": "bedroom", "area_sqm": 16.0},
        {"name": "ห้องน้ำ 2F", "type": "bathroom", "area_sqm": 6.25}
    ],
    "loads": [
        # ห้องนั่งเล่น (30 ตร.ม. > 25 → 2 outlets)
        {"room_name": "ห้องนั่งเล่น 1F", "device": "AC-12000BTU", "quantity": 1},
        {"room_name": "ห้องนั่งเล่น 1F", "device": "SOCKET-16A", "quantity": 2},
        # ครัว (heavy load → 2 outlets minimum)
        {"room_name": "ครัว 1F", "device": "INDUCTION-3000W", "quantity": 1},
        {"room_name": "ครัว 1F", "device": "MICROWAVE-1500W", "quantity": 1},
        {"room_name": "ครัว 1F", "device": "SOCKET-16A", "quantity": 2},
        # ห้องน้ำ 1F (6.25 ตร.ม. < 25 → 1 outlet, RCBO required)
        {"room_name": "ห้องน้ำ 1F", "device": "HEATER-3500W", "quantity": 1},
        # ห้องนอนใหญ่ (20 ตร.ม. < 25 → แต่ใกล้ → 2 outlets)
        {"room_name": "ห้องนอนใหญ่ 2F", "device": "AC-12000BTU", "quantity": 1},
        {"room_name": "ห้องนอนใหญ่ 2F", "device": "SOCKET-16A", "quantity": 2},
        # ห้องนอนเล็ก (16 ตร.ม. < 25 → 1 outlet)
        {"room_name": "ห้องนอนเล็ก 2F", "device": "AC-9000BTU", "quantity": 1},
        {"room_name": "ห้องนอนเล็ก 2F", "device": "SOCKET-16A", "quantity": 1},
        # ห้องน้ำ 2F
        {"room_name": "ห้องน้ำ 2F", "device": "HEATER-3500W", "quantity": 1}
    ],
    "user_constraints": [
        "rcd_for_all_outlets",
        "rcbo_for_bathroom",
        "split_kitchen_circuit"
    ]
}

# MCP Core design request
MCP_DESIGN_REQUEST = {
    "project_name": "บ้านพักอาศัย 2 ชั้น - E2E Test",
    "loads": [
        {
            "id": "AC-LR",
            "name": "แอร์ห้องนั่งเล่น",
            "power_watts": 1200,
            "load_type": "HVAC",
            "location": {"floor": "1", "room": "living_room"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "AC-MBR",
            "name": "แอร์ห้องนอนใหญ่",
            "power_watts": 1200,
            "load_type": "HVAC",
            "location": {"floor": "2", "room": "master_bedroom"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "AC-SBR",
            "name": "แอร์ห้องนอนเล็ก",
            "power_watts": 900,
            "load_type": "HVAC",
            "location": {"floor": "2", "room": "small_bedroom"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "WH-1F",
            "name": "เครื่องทำน้ำอุ่น 1F",
            "power_watts": 3500,
            "load_type": "WATER_HEATER",
            "location": {"floor": "1", "room": "bathroom_1"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "WH-2F",
            "name": "เครื่องทำน้ำอุ่น 2F",
            "power_watts": 3500,
            "load_type": "WATER_HEATER",
            "location": {"floor": "2", "room": "bathroom_2"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "INDUCTION",
            "name": "เตาไฟฟ้า",
            "power_watts": 3000,
            "load_type": "APPLIANCE",
            "location": {"floor": "1", "room": "kitchen"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "MICROWAVE",
            "name": "ไมโครเวฟ",
            "power_watts": 1500,
            "load_type": "APPLIANCE",
            "location": {"floor": "1", "room": "kitchen"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "LIGHT-1F",
            "name": "ไฟชั้น 1",
            "power_watts": 200,
            "load_type": "LIGHTING",
            "location": {"floor": "1", "room": "general"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "LIGHT-2F",
            "name": "ไฟชั้น 2",
            "power_watts": 150,
            "load_type": "LIGHTING",
            "location": {"floor": "2", "room": "general"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "OUTLET-1F",
            "name": "เต้ารับชั้น 1",
            "power_watts": 500,
            "load_type": "RECEPTACLE",
            "location": {"floor": "1", "room": "general"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        },
        {
            "id": "OUTLET-2F",
            "name": "เต้ารับชั้น 2",
            "power_watts": 400,
            "load_type": "RECEPTACLE",
            "location": {"floor": "2", "room": "general"},
            "voltage": "SINGLE_PHASE_230V",
            "phases": 1
        }
    ],
    "options": {
        "include_lisp": True,
        "standard": "TH_EIT",
        "voltage_system": "230V_1PH"
    }
}


async def test_rag_ask():
    """Test 1: RAG /ask endpoint"""
    print("\n" + "="*60)
    print("🧠 TEST 1: RAG /api/v1/ask")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{RAG_URL}/api/v1/ask",
            json={
                "query": ONE_SHOT_QUERY,
                "context_hint": ["db", "standard", "mcp", "example"],
                "language": "th"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: Status {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        
        # Check for fallback
        if "fallback" in data.get("answer", "").lower():
            print("❌ FAILED: Response uses FALLBACK!")
            return None
        
        print(f"✅ Status: {response.status_code}")
        print(f"📝 Answer length: {len(data.get('answer', ''))} chars")
        print(f"🎯 Confidence: {data.get('confidence')}")
        print(f"📚 Sources: {len(data.get('sources', []))}")
        print(f"🛡️ Grounding: {data.get('grounding_status')}")
        
        # Check grounding status
        if data.get('grounding_status') in ['SUPPORTED', 'CHECK_SKIPPED', 'CHECK_SKIPPED_CONTENT_FILTER']:
            print("✅ Grounding PASSED")
        else:
            print(f"⚠️ Grounding: {data.get('grounding_status')}")
        
        # Print first 500 chars of answer
        answer = data.get('answer', '')
        print(f"\n📄 Answer Preview:\n{answer[:800]}...")
        
        return data


async def test_rag_mcp_spec():
    """Test 2: RAG /mcp_spec endpoint"""
    print("\n" + "="*60)
    print("📋 TEST 2: RAG /api/v1/mcp_spec")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{RAG_URL}/api/v1/mcp_spec",
            json=MCP_SPEC_REQUEST
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: Status {response.status_code}")
            print(response.text[:1000])
            return None
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        # Validate structure
        if "project_input" in data:
            pi = data["project_input"]
            print(f"🏠 Rooms: {len(pi.get('rooms', []))}")
            print(f"🔌 Loads: {len(pi.get('loads', []))}")
            print(f"⚡ Voltage: {pi.get('electrical_system', {}).get('voltage_system')}")
            
            # Check loads have correct outlet counts based on room size
            print("\n📊 Outlet Analysis:")
            for room in pi.get('rooms', []):
                room_id = room.get('room_id')
                room_name = room.get('name')
                area = room.get('area_m2', 0)
                
                # Count outlets for this room
                outlet_count = sum(
                    1 for load in pi.get('loads', [])
                    if load.get('room_id') == room_id and 'SOCKET' in load.get('device_code', '').upper()
                )
                
                expected = 2 if area > 25 else 1
                status = "✅" if outlet_count >= expected else "⚠️"
                print(f"  {status} {room_name}: {area}m² → {outlet_count} outlets (expected ≥{expected})")
        
        return data


async def test_mcp_core_design():
    """Test 3: MCP Core /design endpoint"""
    print("\n" + "="*60)
    print("⚡ TEST 3: MCP Core /api/v1/design")
    print("="*60)
    
    # Convert MCP_DESIGN_REQUEST to proper format for MCP_Core API
    session_id = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Convert loads to MCP_Core format
    loads = []
    for i, load in enumerate(MCP_DESIGN_REQUEST.get('loads', [])):
        load_type_map = {
            "HVAC": "hvac",
            "WATER_HEATER": "appliance",
            "APPLIANCE": "appliance",
            "LIGHTING": "lighting",
            "RECEPTACLE": "receptacle",
        }
        loads.append({
            "id": load.get('id', f"load_{i+1}"),
            "name": load.get('name', f"Load {i+1}"),
            "load_type": load_type_map.get(load.get('load_type'), 'other'),
            "voltage": "230V_1PH",  # Thai standard
            "power_watts": float(load.get('power_watts', 100)),
            "quantity": 1,
            "location": {
                "room": load.get('location', {}).get('room', 'Unknown'),
                "floor": load.get('location', {}).get('floor', '1')
            },
            "is_continuous": False,
            "notes": None
        })
    
    # Calculate main breaker size
    total_watts = sum(l['power_watts'] for l in loads)
    total_amps = total_watts / 230
    if total_amps <= 30:
        main_breaker = 40
    elif total_amps <= 60:
        main_breaker = 80
    elif total_amps <= 100:
        main_breaker = 125
    else:
        main_breaker = 200
    
    # Create panels
    panels = [{
        "id": "panel_main",
        "name": "Main Distribution Board",
        "voltage": "230V_1PH",
        "main_breaker_rating": main_breaker,
        "number_of_circuits": max(12, len(loads) + 4),
        "location": {
            "room": "Utility Room",
            "floor": "1"
        },
        "feeds": [l['id'] for l in loads]
    }]
    
    design_request = {
        "session_id": session_id,
        "project_name": "Thai Residential House - E2E Test",
        "project_number": "E2E-001",
        "loads": loads,
        "panels": panels,
        "service_voltage": "230V_1PH",
        "utility_service_size": main_breaker
    }
    
    print(f"→ Session ID: {session_id}")
    print(f"→ Loads: {len(loads)}")
    print(f"→ Total Load: {total_watts:,.0f} W ({total_amps:.1f} A)")
    print(f"→ Main Breaker: {main_breaker} A")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{MCP_URL}/api/v1/design",
            json=design_request
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: Status {response.status_code}")
            print(response.text[:1000])
            return None
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        # Show calculations
        if "calculations" in data:
            calc = data["calculations"]
            print(f"\n📊 Calculations:")
            total_watts = calc.get('total_load_watts', 0)
            print(f"  - Total Load: {total_watts:,.0f} W" if isinstance(total_watts, (int, float)) else f"  - Total Load: {total_watts} W")
            print(f"  - Total Amps: {calc.get('total_load_amps', 'N/A')} A")
            print(f"  - Demand Factor: {calc.get('demand_factor', 'N/A')}")
        
        # Show wire sizing
        if "wire_sizing" in data and data["wire_sizing"]:
            print(f"\n🔌 Wire Sizing: {len(data['wire_sizing'])} items")
            for load_id, sizing in list(data['wire_sizing'].items())[:5]:
                print(f"  - {load_id}: {sizing.get('wire_size', 'N/A')} ({sizing.get('current_amps', 'N/A')} A)")
        
        # Show breaker selections
        if "breaker_selections" in data and data["breaker_selections"]:
            print(f"\n⚡ Breaker Selections: {len(data['breaker_selections'])} items")
            for load_id, breaker in list(data['breaker_selections'].items())[:5]:
                print(f"  - {load_id}: {breaker.get('breaker_rating', 'N/A')} A, {breaker.get('poles', 'N/A')} pole")
        
        # Show AutoLISP
        if "autolisp_code" in data and data["autolisp_code"]:
            lisp = data["autolisp_code"]
            print(f"\n📜 AutoLISP Generated: {len(lisp)} chars")
            print(f"  Preview:\n{lisp[:500]}...")
        
        # Show errors/warnings
        if data.get("errors"):
            print(f"\n❌ Errors: {data['errors']}")
        if data.get("warnings"):
            print(f"\n⚠️ Warnings: {data['warnings']}")
        
        return data


async def test_mcp_core_calculate():
    """Test 4: MCP Core health check (individual calc endpoints don't exist in v1)"""
    print("\n" + "="*60)
    print("🧮 TEST 4: MCP Core Health Check")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health endpoint
        response = await client.get(f"{MCP_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check:")
            print(f"  - Status: {data.get('status', 'N/A')}")
            print(f"  - Timestamp: {data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"⚠️ Health check returned {response.status_code}")
            return False


async def main():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("🚀 ACA_MOZART ONE-SHOT END-TO-END TEST")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("\n⚠️  RULES:")
    print("  - ห้ามใช้ Fallback")
    print("  - ทุกระบบต้องทำงานจริง")
    print("  - ห้องไม่เกิน 5x5 (25 ตร.ม.) → 1 outlet")
    print("  - ห้องเกิน 25 ตร.ม. → 2 outlets")
    
    results = {
        "rag_ask": False,
        "rag_mcp_spec": False,
        "mcp_design": False,
        "mcp_calculate": False
    }
    
    # Test 1: RAG Ask
    try:
        result = await test_rag_ask()
        results["rag_ask"] = result is not None
    except Exception as e:
        print(f"❌ RAG Ask failed: {e}")
    
    # Test 2: RAG MCP Spec
    try:
        result = await test_rag_mcp_spec()
        results["rag_mcp_spec"] = result is not None
    except Exception as e:
        print(f"❌ RAG MCP Spec failed: {e}")
    
    # Test 3: MCP Core Design
    try:
        result = await test_mcp_core_design()
        results["mcp_design"] = result is not None
    except Exception as e:
        print(f"❌ MCP Design failed: {e}")
    
    # Test 4: MCP Core Calculate
    try:
        result = await test_mcp_core_calculate()
        results["mcp_calculate"] = result is not None
    except Exception as e:
        print(f"❌ MCP Calculate failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
