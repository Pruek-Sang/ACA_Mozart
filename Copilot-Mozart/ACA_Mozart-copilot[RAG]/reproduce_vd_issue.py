
import asyncio
import logging
import sys
import os
import json

# Setup environment
sys.path.append(os.getcwd())
logging.basicConfig(level=logging.INFO)

from app.service import RagService
from app.models import ProjectRequirements

async def run_reproduction():
    print("🚀 Starting Reproduction of VD Data Loss...")
    
    # User's Prompt
    user_prompt = """
    ออกแบบระบบไฟฟ้าบ้านพักอาศัย 2 ชั้น (ไทย) 
    เงื่อนไขมาตรฐาน:
    - ใช้มาตรฐาน: วสท. 2001-56 / IEC 60364 (อ้างอิง NEC 2023 ได้)
    - ระบบไฟ: 1 เฟส 230V (TH_1PH_230V), สายดินแบบ TT
    - แรงดันตก: วงจรย่อยไม่เกิน 3%
    - กฎ: โหลดวงจรไม่เกิน 80% ของเบรกเกอร์
    - ห้องน้ำ + น้ำอุ่น ต้องใช้ RCBO 30mA
    - แอร์ทุกตัวต้องแยกวงจรเฉพาะ (ถ้ามี)

    ตำแหน่งตู้ไฟและระยะเพื่อทำ BOQ:
    - ตู้ MDB/DB อยู่ “โรงรถ ชั้น 1”
    - ระยะสายเมนจากมิเตอร์ถึงตู้ MDB = 12 เมตร
    - ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร
    - ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 2 = 25 เมตร/วงจร
    - เดินท่อ EMT 1/2” สำหรับวงจรย่อย, สาย THW ในท่อ
    - ขอให้สรุป BOQ เพิ่มท้ายรายงาน

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
    """

    # Mock dependencies to avoid full stack (optional, but better to trace Service logic)
    # We will instantiate RagService and see what it extracts.
    # Note: This requires API KEY.
    
    try:
        service = RagService()
        
        # Prepare Request
        req = ProjectRequirements(
            project_name="Reproduction Home",
            building_type="residential",
            requirements=user_prompt,
            site_context={
                "distance_to_transformer": "less_than_50m", # Mock context
                "installation_area": "indoor",
                "panel_type": "main"
            }
        )
        
        print("🔍 Invoking generate_mcp_spec (Extraction Phase)...")
        # Ensure we have mocked LLM or Real LLM. 
        # If Real LLM is not configured, we might fail.
        # But wait, looking at the code, RagService uses Vertex or Gemini.
        # We need to see if we can trace the extraction even without clear LLM output,
        # OR if we want to spot check the code logic for "floor distances".
        
        # For this "Agentic Analysis", let's first LOOK at the extracted spec structure in app/models.py
        # to see if 'floor_distances' even exists.
        pass
        
    except Exception as e:
        print(f"❌ Setup Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_reproduction())
