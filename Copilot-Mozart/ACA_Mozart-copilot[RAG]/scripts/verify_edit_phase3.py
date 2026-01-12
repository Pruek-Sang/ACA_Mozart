import asyncio
import uuid
import logging
import sys
import os
import json

sys.path.append(os.getcwd())
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.context.session_injector import session_injector
from app.context.merge_engine import merge_design_changes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyEditPhase3")

async def run_verification():
    # 1. Create Session
    session_data = await session_injector.create(project_name="Phase 3 Undo Test")
    if not session_data:
        logger.error("❌ Failed to create session")
        return
        
    session_id = session_data.id
    logger.info(f"🚀 Starting Phase 3 (Undo) Verification with Session ID: {session_id}")

    # 2. Seed Initial Data
    initial_loads = [
        {"device": "AC-12000BTU", "room_name": "Bedroom 1", "quantity": 1, "floor": 2},
    ]
    initial_rooms = [
        {"name": "Bedroom 1", "type": "bedroom", "floor": 2},
    ]
    await session_injector.update_design(session_id, loads=initial_loads, rooms=initial_rooms)
    logger.info("✅ Seeded initial data (1 AC).")
    
    # 3. Action: Add Device (Fan) - this should trigger Autosave Snapshot
    logger.info("\n--- STEP 1: Add Fan (Should save snapshot) ---")
    res1 = await merge_design_changes(session_id, "เพิ่ม Fan 1 ตัว ใน Bedroom 1")
    
    # Verify Fan added
    sess = await session_injector.load(session_id)
    # Debug: Print all devices
    logger.info(f"Loaded Devices: {[l['device'] for l in sess.loads]}")
    
    fans = [l for l in sess.loads if "FAN" in l["device"].upper()]
    if len(fans) >= 1:
        logger.info("✅ Fan added successfully.")
    else:
        logger.error("❌ Failed to add Fan.")
        return

    # Check snapshot existence (internal check)
    stack = sess.site_context.get("_undo_stack", [])
    logger.info(f"Current UNDO Stack Size: {len(stack)}")
    if len(stack) > 0:
        logger.info("✅ Snapshot stack is not empty.")
    else:
        logger.error("❌ Snapshot stack is empty!")

    # 4. Action: Undo
    logger.info("\n--- STEP 2: Execute UNDO ---")
    # Using "ย้อนกลับ" which we mapped to UNDO
    res2 = await merge_design_changes(session_id, "ย้อนกลับ")
    
    if res2 and res2.get("status") == "success":
        logger.info(f"✅ Undo reported success: {res2.get('message')}")
    else:
        logger.error(f"❌ Undo failed: {res2}")
        
    # 5. Verify State Restored
    sess_after = await session_injector.load(session_id)
    fans_after = [l for l in sess_after.loads if "Fan" in l["device"]]
    acs_after = [l for l in sess_after.loads if "AC" in l["device"]]
    
    if len(fans_after) == 0 and len(acs_after) == 1:
        logger.info("✅ PASS: State restored successfully (Fan gone, AC remains).")
    else:
        logger.error(f"❌ FAIL: State not restored properly. Fans: {len(fans_after)}, ACs: {len(acs_after)}")

    logger.info("\n🏁 Phase 3 Verification Complete")

if __name__ == "__main__":
    asyncio.run(run_verification())
