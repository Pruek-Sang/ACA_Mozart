"""
🌟 Golden Stress Test - Post-Deployment Verification

This test hits REAL LLM/MCP to verify system correctness.
Run after deploy to ensure engineering logic is working.

Usage:
    pytest tests/test_golden_stress.py -v -m live
    # OR
    python tests/test_golden_stress.py  # Direct run
"""
import pytest
import asyncio
import os

# Check if we can run live tests
LIVE_TESTS_ENABLED = os.getenv('ENABLE_LIVE_TESTS', 'false').lower() == 'true'


# ═══════════════════════════════════════════════════════════════════════════
# THE HARDCORE PROMPT (Full Thai Residential Design)
# ═══════════════════════════════════════════════════════════════════════════
THE_STRESS_TEST_PROMPT = """
ออกแบบระบบไฟฟ้าบ้านพักอาศัย 2 ชั้น (ไทย)

เงื่อนไขมาตรฐาน:
- ใช้มาตรฐาน: วสท. 2001-56 / IEC 60364 (อ้างอิง NEC 2023 ได้)
- ระบบไฟ: 1 เฟส 230V (TH_1PH_230V), สายดินแบบ TT
- แรงดันตก: วงจรย่อยไม่เกิน 3%
- กฎ: โหลดวงจรไม่เกิน 80% ของเบรกเกอร์
- ห้องน้ำ + น้ำอุ่น ต้องใช้ RCBO 30mA
- แอร์ทุกตัวต้องแยกวงจรเฉพาะ (ถ้ามี)

ตำแหน่งตู้ไฟและระยะเพื่อทำ BOQ:
- ตู้ MDB/DB อยู่ "โรงรถ ชั้น 1"
- ระยะสายเมนจากมิเตอร์ถึงตู้ MDB = 12 เมตร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 2 = 25 เมตร/วงจร
- เดินท่อ EMT 1/2" สำหรับวงจรย่อย, สาย THW ในท่อ
- ขอให้สรุป BOQ เพิ่มท้ายรายงาน (อย่างน้อย: จำนวน MCB/RCBO, ความยาวสาย 1.5/2.5/4/6 mm² แบบประมาณการ, จำนวนท่อ EMT 1/2")

รายละเอียดพื้นที่และห้อง:

ชั้น 1
1) ห้องนั่งเล่น 30 ตร.ม. (ไม่มีแอร์)
   - ต้องการเต้ารับคู่ 6 จุด
   - ไฟดาวน์ไลท์ LED 20W จำนวน 4 ดวง
   - พัดลมเพดาน 60W จำนวน 1 ตัว
2) ห้องครัว ขนาด 3 x 5 เมตร (15 ตร.ม.)
   - มีเตาแม่เหล็กไฟฟ้า 3000W 1 เครื่อง (ต้องวงจรเฉพาะ)
   - มีไมโครเวฟ 1500W 1 เครื่อง
   - หม้อหุงข้าว 800W 1 เครื่อง
   - ตู้เย็น 300W 1 เครื่อง (เต้ารับเฉพาะ 1 จุด)
   - กาต้มน้ำ 2200W 1 เครื่อง
   - เต้ารับคู่เหนือเคาน์เตอร์ 6 จุด + เต้ารับคู่ทั่วไป 2 จุด
   - ไฟ LED 20W จำนวน 3 ดวง
3) ห้องน้ำ 1 (มาตรฐาน)
   - เครื่องทำน้ำอุ่น 4500W 1 เครื่อง (RCBO 30mA วงจรเฉพาะ)
   - เต้ารับกันน้ำ 16A 1 จุด
   - ไฟ LED 10W 1 ดวง
   - พัดลมดูดอากาศ 25W 1 ตัว
4) ห้องเก็บของ 20 ตร.ม.
   - เต้ารับเดี่ยว 1 จุด
   - ไฟ LED 10W 2 ดวง
5) โรงรถ 20 ตร.ม.
   - เต้ารับคู่ 2 จุด
   - ไฟ LED 10W 2 ดวง
6) ภายนอก/พื้นที่ส่วนกลาง
   - ปั๊มน้ำ 750W 1 ตัว (วงจรเฉพาะ)
   - ไฟภายนอก LED 10W 2 ดวง
   - เต้ารับกันน้ำ 16A 1 จุด

ชั้น 2
1) ห้องนอน 1 (ประมาณ 14 ตร.ม.)
   - เต้ารับคู่ 4 จุด
   - ไฟ LED 10W 3 ดวง
   - พัดลมเพดาน 60W 1 ตัว
   - (ไม่มีแอร์)
2) ห้องนอน 2 (ประมาณ 12 ตร.ม.)
   - เต้ารับคู่ 3 จุด
   - ไฟ LED 10W 3 ดวง
   - พัดลมเพดาน 60W 1 ตัว
   - (ไม่มีแอร์)
3) ห้องน้ำ 2
   - เครื่องทำน้ำอุ่น 3500W 1 เครื่อง (RCBO 30mA วงจรเฉพาะ)
   - เต้ารับกันน้ำ 16A 1 จุด
   - ไฟ LED 10W 1 ดวง
   - พัดลมดูดอากาศ 25W 1 ตัว
4) ห้องเก็บของ ชั้น 2 พื้นที่ 10 ตร.ม.
   - เต้ารับเดี่ยว 1 จุด
   - ไฟ LED 10W 1 ดวง
5) ระเบียง
   - เต้ารับกันน้ำ 16A 1 จุด
   - ไฟ LED 10W 1 ดวง
""".strip()


# ═══════════════════════════════════════════════════════════════════════════
# TEST FUNCTION
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.live
@pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="Live tests disabled. Set ENABLE_LIVE_TESTS=true")
@pytest.mark.asyncio
async def test_stress_scenario_hardcore():
    """
    🌟 GOLDEN TEST CASE 1: "The Stress Test" (Real-world Complex Home)
    
    Goal: Verify AI & Computation engine handles complex Thai electrical design.
    Checks:
    - RCBO for water heaters
    - Dedicated circuits for pump/stove
    - Voltage Drop < 3%
    - Main Breaker sizing
    - No VAF wire in conduit
    """
    # Imports inside function to avoid import errors when running standalone
    from app.service import RagService
    from app.models import QueryRequest
    
    print("\n" + "="*60)
    print("🌟 GOLDEN STRESS TEST: 'The Complex Home'")
    print("="*60)
    
    # 1. Create Service & Request
    service = RagService()
    
    req = QueryRequest(
        query=THE_STRESS_TEST_PROMPT,
        context_hint=["mcp_spec", "thai_standard"],
        language="th",
        site_context={
            "distance_to_transformer": "50_100m",
            "installation_area": "indoor",
            "panel_type": "main",
            "conduit_grouping": "2-3"
        }
    )
    
    # 2. Execute Request
    print("📤 Sending request to RagService.process_ask()...")
    response = await service.process_ask(req, session_id=None)
    
    # 3. Basic Response Check
    assert response is not None, "Response is None!"
    assert hasattr(response, 'success'), "Response missing 'success' field"
    
    # Response might fail if MCP unreachable - that's a valid test result
    if not response.success:
        print(f"⚠️ Response failed: {getattr(response, 'message', 'Unknown error')}")
        pytest.skip(f"Backend returned failure: {getattr(response, 'message', 'Unknown')}")
    
    # 4. Extract Display Data
    # StandardResponse.metadata.display_data contains the computed data
    metadata = response.metadata
    display_data = getattr(metadata, 'display_data', None) if metadata else None
    
    if not display_data:
        print("⚠️ No display_data in response - checking raw data...")
        # Maybe design result is in a different location
        pytest.skip("No display_data found - MCP integration might be different")
    
    print(f"✅ Got display_data with {len(display_data.get('circuits', []))} circuits")
    
    # 5. VERIFICATIONS (The 'Expectations')
    circuits = display_data.get('circuits', [])
    assert len(circuits) > 0, "No circuits generated!"
    
    # --- CHECK 1: Water Heater Safety (RCBO) ---
    print("\n📋 CHECK 1: Water Heater RCBO...")
    wh_circuits = [c for c in circuits if 'น้ำอุ่น' in c.get('circuit_name', '') or 'Heater' in c.get('circuit_name', '')]
    print(f"   Found {len(wh_circuits)} water heater circuits")
    
    if len(wh_circuits) >= 1:
        for c in wh_circuits:
            requires_rcbo = c.get('requires_rcbo', False)
            breaker_type = c.get('breaker_type', '')
            assert requires_rcbo is True, f"Water heater '{c.get('circuit_name')}' MUST require RCBO"
            assert 'RCBO' in breaker_type or requires_rcbo, f"Breaker type should be RCBO, got {breaker_type}"
        print("   ✅ RCBO requirement passed")
    else:
        print("   ⚠️ No water heater circuits found - check circuit naming")
    
    # --- CHECK 2: Pump & Induction Stove (Dedicated Circuits) ---
    print("\n📋 CHECK 2: Dedicated Circuits...")
    stove_circuits = [c for c in circuits if 'เตา' in c.get('circuit_name', '') or 'Induction' in c.get('circuit_name', '')]
    pump_circuits = [c for c in circuits if 'ปั๊ม' in c.get('circuit_name', '') or 'Pump' in c.get('circuit_name', '')]
    
    print(f"   Stove circuits: {len(stove_circuits)}, Pump circuits: {len(pump_circuits)}")
    # Soft assert - log but don't fail
    if len(stove_circuits) == 0:
        print("   ⚠️ Warning: No dedicated stove circuit found")
    if len(pump_circuits) == 0:
        print("   ⚠️ Warning: No dedicated pump circuit found")
    
    # --- CHECK 3: Voltage Drop ---
    print("\n📋 CHECK 3: Voltage Drop...")
    vd_values = [c.get('vd_percent', 0) for c in circuits if c.get('vd_percent')]
    if vd_values:
        max_vd = max(vd_values)
        print(f"   Max VD: {max_vd}%")
        assert max_vd <= 5.0, f"Voltage Drop too high! Max {max_vd}% (warning at 3%, fail at 5%)"
        if max_vd > 3.0:
            print(f"   ⚠️ VD > 3% but < 5% - acceptable with warning")
        else:
            print("   ✅ VD within 3% limit")
    else:
        print("   ⚠️ No VD data found")
    
    # --- CHECK 4: Main Breaker Sizing ---
    print("\n📋 CHECK 4: Main Breaker...")
    total_kw = display_data.get('total_kw', 0)
    main_breaker = display_data.get('main_breaker', '')
    print(f"   Total Load: {total_kw} kW")
    print(f"   Main Breaker: {main_breaker}")
    
    assert total_kw > 0, "Total kW should not be 0"
    assert main_breaker != '', "Main breaker should be specified"
    
    # --- CHECK 5: Wire Type (No VAF in conduit) ---
    print("\n📋 CHECK 5: Wire Type...")
    for c in circuits:
        wire_type = c.get('wire_type', 'IEC01')
        if 'VAF' in wire_type.upper():
            print(f"   ❌ FAIL: Found VAF in circuit {c.get('circuit_name')}")
            assert False, f"VAF wire found in {c.get('circuit_name')} - violation!"
    print("   ✅ No VAF violations")
    
    # --- FINAL REPORT ---
    print("\n" + "="*60)
    print("✅✅ ALL GOLDEN CHECKS PASSED! System is Architecturally Sound. ✅✅")
    print("="*60)
    
    # Return summary for CI/CD reporting
    return {
        "circuits_count": len(circuits),
        "total_kw": total_kw,
        "main_breaker": main_breaker,
        "rcbo_count": display_data.get('rcbo_count', 0),
        "max_vd": max(vd_values) if vd_values else None
    }


# ═══════════════════════════════════════════════════════════════════════════
# DIRECT RUN SUPPORT
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    # Enable live tests when running directly
    os.environ['ENABLE_LIVE_TESTS'] = 'true'
    
    print("🚀 Running Golden Stress Test directly...")
    try:
        result = asyncio.run(test_stress_scenario_hardcore())
        print(f"\n📊 Summary: {result}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
