import asyncio
import uuid
import logging
import sys
import os

sys.path.append(os.getcwd())
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.context.session_injector import session_injector
from app.context.merge_engine import merge_design_changes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyEditPhase2")

async def run_verification():
    # 1. Create Session
    session_data = await session_injector.create(project_name="Phase 2 Validation Test")
    if not session_data:
        logger.error("❌ Failed to create session")
        return
        
    session_id = session_data.id
    logger.info(f"🚀 Starting Phase 2 Verification with Session ID: {session_id}")

    # 2. Seed Data
    initial_loads = [
        {"device": "AC-12000BTU", "room_name": "Bedroom 1", "quantity": 1, "floor": 2},
    ]
    initial_rooms = [
        {"name": "Bedroom 1", "type": "bedroom", "floor": 2},
    ]
    await session_injector.update_design(session_id, loads=initial_loads, rooms=initial_rooms)
    logger.info("✅ Seeded initial data.")
    
    # =================================================================
    # TEST CASE 1: Feature 6 - Merge Duplicate (Add same device to same room)
    # =================================================================
    logger.info("\n--- TEST CASE 1: Feature 6 (Merge Duplicate) ---")
    logger.info("Action: Adding 'AC-12000BTU' to 'Bedroom 1' again via 'เพิ่มแอร์'...")
    
    # Note: Using generic text, but engine should resolve to same device if logic works right 
    # OR we need to be specific. Let's try to trigger the merge logic.
    # The current logic matches exactly "device" string. 
    # If LLM parses "แอร์" -> "AC-12000BTU" (default), it should match.
    
    res1 = await merge_design_changes(session_id, "เพิ่มแอร์ 1 เครื่อง ห้อง Bedroom 1")
    
    sess = await session_injector.load(session_id)
    bedroom_acs = [l for l in sess.loads if l["room_name"] == "Bedroom 1" and "AC" in l["device"]]
    
    if len(bedroom_acs) == 1 and bedroom_acs[0]["quantity"] == 2:
        logger.info(f"✅ PASS: Feature 6 (Merged Quantity). Count: 1, Qty: {bedroom_acs[0]['quantity']}")
    else:
        logger.error(f"❌ FAIL: Feature 6. Count: {len(bedroom_acs)}, Qty: {bedroom_acs[0]['quantity'] if bedroom_acs else 0}")

    # =================================================================
    # TEST CASE 2: Feature 7 - Validation (Negative Watts/Quantity)
    # =================================================================
    logger.info("\n--- TEST CASE 2: Feature 7 (Validation - Negative) ---")
    res2 = await merge_design_changes(session_id, "เพิ่ม Fan -5 ตัว")
    
    if res2 and res2.get("status") == "validation_error":
         logger.info(f"✅ PASS: Feature 7 (Caught Negative). Msg: {res2.get('message')}")
    else:
         logger.error(f"❌ FAIL: Feature 7 (Negative). Result: {res2}")

    # =================================================================
    # TEST CASE 3: Feature 7 - Validation (Crazy Values)
    # =================================================================
    logger.info("\n--- TEST CASE 3: Feature 7 (Validation - Crazy Watts) ---")
    res3 = await merge_design_changes(session_id, "แก้ไขแอร์เป็น 900000 BTU")
    
    if res3 and res3.get("status") == "validation_error":
         logger.info(f"✅ PASS: Feature 7 (Caught High Value). Msg: {res3.get('message')}")
    else:
         # Note: If LLM fails to parse 900000 as value, this might fail differently.
         logger.error(f"❌ FAIL: Feature 7 (High Value). Result: {res3}")

    logger.info("\n🏁 Phase 2 Verification Complete")

if __name__ == "__main__":
    asyncio.run(run_verification())
