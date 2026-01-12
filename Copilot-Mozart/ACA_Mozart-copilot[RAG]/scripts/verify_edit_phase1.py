import asyncio
import uuid
import logging
import sys
import os

# Ensure app is in path
sys.path.append(os.getcwd())

# Configuration
# Assuming .env is loaded by the app or we need to load it
from dotenv import load_dotenv
load_dotenv()

from app.context.session_injector import session_injector
from app.context.merge_engine import merge_design_changes

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyEdit")

async def run_verification():
    # 1. Create a fresh session ID via API
    # Create with basic initial data
    session_data = await session_injector.create(project_name="Integration Test Project")
    if not session_data:
        logger.error("❌ Failed to create session")
        return
        
    session_id = session_data.id
    logger.info(f"🚀 Starting Verification with Session ID: {session_id}")

    # 2. Seed Initial Data (simulate CREATE results)
    # We cheat a bit and inject directly to test EDIT flow specifically
    initial_loads = [
        {"device": "AC-12000BTU", "room_name": "Bedroom 1", "quantity": 1, "floor": 2},
        {"device": "TV-55Inch", "room_name": "Living Room", "quantity": 1, "floor": 1},
        {"device": "Pump-250W", "room_name": "Garden", "quantity": 1, "floor": 1}
    ]
    initial_rooms = [
        {"name": "Bedroom 1", "type": "bedroom", "floor": 2},
        {"name": "Living Room", "type": "living_room", "floor": 1},
        {"name": "Garden", "type": "outdoor", "floor": 1}
    ]
    
    # Save seed data
    success = await session_injector.update_design(session_id, loads=initial_loads, rooms=initial_rooms)
    if not success:
        logger.error("❌ Failed to seed initial data!")
        return
    logger.info("✅ Seeded initial data successfully.")

    # =================================================================
    # TEST CASE 1: Feature 3 - Edit Summary & ADD
    # =================================================================
    logger.info("\n--- TEST CASE 1: Add Device & Check Summary ---")
    res1 = await merge_design_changes(session_id, "เพิ่มแอร์ 1 เครื่อง ห้อง Living Room")
    if res1 and res1.get("status") == "success":
        msg = res1.get("message", "")
        if "เพิ่ม" in msg and "AC" in msg:
             logger.info(f"✅ PASS: Feature 3 (Summary Reference): {msg}")
        else:
             logger.warning(f"⚠️ WARN: Feature 3 Summary unclear: {msg}")
             
        # Verify Persistence
        sess = await session_injector.load(session_id)
        ac_count = sum(1 for l in sess.loads if "AC" in l["device"] and l["room_name"] == "Living Room")
        if ac_count == 1:
            logger.info("✅ PASS: Persistence (Load added)")
        else:
            logger.error(f"❌ FAIL: Persistence (Found {ac_count} ACs)")
    else:
        logger.error(f"❌ FAIL: Merge failed: {res1}")

    # =================================================================
    # TEST CASE 2: Feature 4 - Quantity Removal
    # =================================================================
    logger.info("\n--- TEST CASE 2: Feature 4 (Quantity Removal) ---")
    # First add a multi-quantity item
    await merge_design_changes(session_id, "เพิ่ม Fan 3 ตัว ห้อง Garden")
    
    # Now remove 1 Fan
    res2 = await merge_design_changes(session_id, "ลบ Fan 1 ตัว จาก Garden")
    msg2 = res2.get("message", "")
    logger.info(f"Result Msg: {msg2}")
    
    sess = await session_injector.load(session_id)
    fans = [l for l in sess.loads if "Fan" in l["device"] and l["room_name"] == "Garden"]
    
    if fans and fans[0]["quantity"] == 2:
        logger.info(f"✅ PASS: Feature 4 (Reduced 3 -> 2). Qty: {fans[0]['quantity']}")
    else:
        qty = fans[0]["quantity"] if fans else 0
        logger.error(f"❌ FAIL: Feature 4 (Expected 2, got {qty})")

    # =================================================================
    # TEST CASE 3: Feature 1 - Device Not Found
    # =================================================================
    logger.info("\n--- TEST CASE 3: Feature 1 (Device Not Found) ---")
    res3 = await merge_design_changes(session_id, "ลบ Heater จาก Bedroom 1")
    
    if res3 and res3.get("status") == "not_found":
        logger.info(f"✅ PASS: Feature 1 (Caught Not Found). Msg: {res3.get('message')}")
    else:
        logger.error(f"❌ FAIL: Feature 1 (Expected 'not_found', got {res3})")
        
    logger.info("\n🏁 Verification Complete")

if __name__ == "__main__":
    asyncio.run(run_verification())
