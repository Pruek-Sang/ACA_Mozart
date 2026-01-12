import asyncio
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyFeat2")

async def verify_feat2():
    logger.info("🚀 Testing Feature 2: Confirmation Mode")
    
    # 1. Create Session
    session_data = await session_injector.create(project_name="Feat2 Test")
    session_id = session_data.id
    
    # 2. Seed Ambiguous Data
    # 2 ACs in different rooms
    initial_rooms = [
        {"name": "Bedroom 1", "type": "bedroom", "floor": 1},
        {"name": "Living Room", "type": "living", "floor": 1}
    ]
    initial_loads = [
        {"device": "AC-12000BTU", "room_name": "Bedroom 1", "quantity": 1},
        {"device": "AC-18000BTU", "room_name": "Living Room", "quantity": 1}
    ]
    await session_injector.update_design(session_id, loads=initial_loads, rooms=initial_rooms)
    
    # 3. Trigger Ambiguity
    logger.info("Command: 'remove AC'")
    res = await merge_design_changes(session_id, "remove AC")
    
    if res and res['status'] == 'confirm_required':
        logger.info(f"✅ PASS: Confirmation Triggered. Options: {res['options']}")
    else:
        logger.error(f"❌ FAIL: Status is {res.get('status') if res else 'None'}")

if __name__ == "__main__":
    asyncio.run(verify_feat2())
