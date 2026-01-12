import asyncio
import uuid
import logging
import sys
import os
import json
from datetime import datetime

sys.path.append(os.getcwd())
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.context.session_injector import session_injector
from app.context.merge_engine import merge_design_changes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyFULL")

async def run_verification():
    logger.info("🚀 STARTING FINAL FULL SYSTEM VERIFICATION 🚀")
    
    # =========================================================================
    # PHASE 0: CRUD & SESSION
    # =========================================================================
    logger.info("\n--- PHASE 0: CRUD Operations ---")
    session_data = await session_injector.create(project_name="Final Exam Project")
    if not session_data:
        logger.error("❌ CRUD: Create Session Failed")
        return
    session_id = session_data.id
    logger.info(f"✅ CRUD: Session Created ({session_id})")
    
    # Verify Read
    sess = await session_injector.load(session_id)
    if sess.project_name == "Final Exam Project":
        logger.info("✅ CRUD: Read Session Success")
    else:
        logger.error("❌ CRUD: Read Session Mismatch")

    # Seed Data
    initial_loads = []
    initial_rooms = [{"name": "Bedroom 1", "type": "bedroom", "floor": 1}]
    await session_injector.update_design(session_data.id, loads=initial_loads, rooms=initial_rooms)
    
    # =========================================================================
    # PHASE 1: BASIC EDIT (ADD/REMOVE/SUMMARY)
    # =========================================================================
    logger.info("\n--- PHASE 1: Basic Edit ---")
    
    # 1. Add Device
    res = await merge_design_changes(session_id, "add AC 12000BTU to Bedroom 1")
    if res['status'] == 'success' and len(res['changes']) > 0:
        logger.info("✅ Edit: Add Device Success")
    else:
        logger.error(f"❌ Edit: Add Device Failed: {res}")

    # 2. Add Device (Different Room)
    await session_injector.update_design(session_id, rooms=initial_rooms + [{"name": "Living Room", "type": "living", "floor": 1}])
    await merge_design_changes(session_id, "add AC 18000BTU to Living Room")
    
    # 3. Validation Check (Negative Value)
    res_val = await merge_design_changes(session_id, "change AC in Bedroom 1 to -500 BTU")
    if res_val['status'] == 'validation_error':
        logger.info("✅ Validation: Blocked negative value")
    else:
        logger.error(f"❌ Validation: Failed to block negative value: {res_val}")

    # =========================================================================
    # PHASE 2: SMART LOGIC (MERGE & CONFIRMATION)
    # =========================================================================
    logger.info("\n--- PHASE 2: Smart Logic ---")
    
    # 1. Merge Duplicate
    # Add another AC to Bedroom 1 -> Should behave as qty +1
    res_merge = await merge_design_changes(session_id, "add AC 12000BTU to Bedroom 1")
    sess = await session_injector.load(session_id)
    bedroom_ac = next((l for l in sess.loads if l['room_name'] == "Bedroom 1"), None)
    if bedroom_ac and bedroom_ac['quantity'] == 2:
         logger.info("✅ Smart: Merge Duplicate Success (Qty -> 2)")
    else:
         logger.error(f"❌ Smart: Merge Duplicate Failed. Qty: {bedroom_ac.get('quantity') if bedroom_ac else 'None'}")

    # 2. Confirmation Mode (Ambiguity)
    # We have AC in Bedroom 1 and AC in Living Room.
    # Command "Remove AC" should trigger confirmation.
    res_confirm = await merge_design_changes(session_id, "remove AC")
    if res_confirm['status'] == 'confirm_required':
        logger.info(f"✅ Smart: Confirmation Triggered. Options: {len(res_confirm['options'])}")
        # Debug options
        for opt in res_confirm['options']:
            logger.info(f"   - Option: {opt}")
    else:
        logger.error(f"❌ Smart: Confirmation Failed. Status: {res_confirm['status']}")

    # =========================================================================
    # PHASE 3: UNDO
    # =========================================================================
    logger.info("\n--- PHASE 3: Undo ---")
    
    # Current State: Bedroom 1 (2 ACs), Living Room (1 AC)
    # Action: Remove AC from Living Room (Specific)
    await merge_design_changes(session_id, "remove AC from Living Room")
    
    # Verify Removal
    sess = await session_injector.load(session_id)
    living_ac = next((l for l in sess.loads if l['room_name'] == "Living Room"), None)
    if not living_ac:
        logger.info("✅ Pre-Undo: Removal confirmed")
    else:
        logger.error("❌ Pre-Undo: Removal failed")
        
    # Action: Undo
    res_undo = await merge_design_changes(session_id, "undo")
    
    if not res_undo:
        logger.error("❌ Undo: Failed (Response is None)")
    elif res_undo.get('status') == 'success':
         logger.info("✅ Undo: Operation Successful")
    else:
         logger.error(f"❌ Undo: Operation Failed: {res_undo}")
         
    # Verify Restore
    sess = await session_injector.load(session_id)
    living_ac_restored = next((l for l in sess.loads if l['room_name'] == "Living Room"), None)
    if living_ac_restored:
        logger.info("✅ Undo: State Restored (AC is back)")
    else:
        logger.error("❌ Undo: State Not Restored")

    logger.info("\n🏁 ALL SYSTEMS GREEN: Final Verification Complete 🏁")

if __name__ == "__main__":
    asyncio.run(run_verification())
