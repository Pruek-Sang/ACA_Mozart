#!/usr/bin/env python3
"""
Debug Test: LLM Extraction 
Tests if the extraction prompt returns valid data for complex inputs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test input - similar to user's complex request
TEST_INPUT = """ออกแบบระบบไฟฟ้าบ้านพักอาศัย 2 ชั้น

ตำแหน่งตู้ไฟและระยะเพื่อทำ BOQ:
- ตู้ MDB/DB อยู่ "โรงรถ ชั้น 1"
- ระยะสายเมนจากมิเตอร์ถึงตู้ MDB = 12 เมตร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 2 = 25 เมตร/วงจร

ชั้น 1
1) ห้องนั่งเล่น 30 ตร.ม. 
   - ต้องการเต้ารับคู่ 6 จุด
   - ไฟดาวน์ไลท์ LED 20W จำนวน 4 ดวง
   - พัดลมเพดาน 60W จำนวน 1 ตัว
2) ห้องครัว 15 ตร.ม.
   - มีเตาแม่เหล็กไฟฟ้า 3000W 1 เครื่อง
   - มีไมโครเวฟ 1500W 1 เครื่อง
   - ตู้เย็น 300W 1 เครื่อง
3) ห้องน้ำ 1 
   - เครื่องทำน้ำอุ่น 4500W 1 เครื่อง
   - เต้ารับกันน้ำ 16A 1 จุด
   - ไฟ LED 10W 1 ดวง

ชั้น 2
1) ห้องนอน 1 (14 ตร.ม.)
   - เต้ารับคู่ 4 จุด
   - ไฟ LED 10W 3 ดวง
2) ห้องน้ำ 2
   - เครื่องทำน้ำอุ่น 3500W 1 เครื่อง

ระยะหม้อแปลง 10 เมตร, ติดตั้งกลางแดด (Outdoor), เป็นตู้ย่อย (Sub Panel)"""


def test_extraction():
    """Test extraction without full service."""
    print("=" * 60)
    print("🧪 EXTRACTION DEBUG TEST")
    print("=" * 60)
    
    try:
        from app.service import RagService
        
        # Create service instance
        service = RagService()
        
        print(f"\n📝 Input length: {len(TEST_INPUT)} chars")
        print(f"📝 First 200 chars:\n{TEST_INPUT[:200]}...")
        
        # Call extraction
        print("\n⏳ Calling _extract_loads_from_text...")
        result = service._extract_loads_from_text(TEST_INPUT)
        
        print("\n📊 Extraction Result:")
        print("-" * 40)
        
        if result:
            rooms = result.get("rooms", [])
            loads = result.get("loads", [])
            
            print(f"✅ Rooms: {len(rooms)}")
            for r in rooms[:5]:  # Show first 5
                print(f"   - {r.get('name', '?')} (floor: {r.get('floor', '?')}, type: {r.get('type', '?')})")
            
            print(f"\n✅ Loads: {len(loads)}")
            for l in loads[:10]:  # Show first 10
                print(f"   - {l.get('room_name', '?')}: {l.get('device', '?')} x{l.get('quantity', '?')}")
            
            if result.get("error"):
                print(f"\n⚠️ Error: {result.get('error')}")
                
            if len(rooms) == 0:
                print("\n❌ EXTRACTION FAILED: No rooms found!")
            if len(loads) == 0:
                print("\n❌ EXTRACTION FAILED: No loads found!")
        else:
            print("❌ Result is None or empty!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_extraction()
