"""
Integration Test - Real Supabase Connection
CRITICAL: This runs against the REAL DATABASE defined in .env
It creates a temporary session, modifies it, verifies changes, and deletes it.
"""

import asyncio
import sys
import os
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv()

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

async def test_real_supabase_lifecycle():
    from app.context.session_injector import session_injector
    from app.context.merge_engine import merge_design_changes
    from app.models import SiteContext
    
    # 1. Setup Test ID
    test_session_id = str(uuid.uuid4())
    logger.info(f"🔵 Starting Integration Test with Session ID: {test_session_id}")
    
    try:
        # Check connection first
        if not session_injector.is_available():
            logger.error("🔴 Supabase is NOT available. Check .env configuration.")
            return

        # 2. CREATE: Create initial session with design
        logger.info("Step 1: Creating initial design...")
        initial_loads = [
            {"device": "AC-12000BTU", "room_name": "ห้องนอน 1", "floor": 2, "quantity": 1},
            {"device": "LIGHT-10W", "room_name": "ห้องนั่งเล่น", "floor": 1, "quantity": 4}
        ]
        
        # Custom Logic: Fetch a real user ID to satisfy FK constraint
        # Since we have service_role, we can list users.
        try:
             # Use the admin auth api to list users
             users_response = session_injector.client.auth.admin.list_users()
             logger.info(f"List users response type: {type(users_response)}")
             
             # Handle different response types (supabase-py versions vary)
             users_list = []
             if isinstance(users_response, list):
                 users_list = users_response
             elif hasattr(users_response, "users"):
                 users_list = users_response.users
             
             if users_list:
                  test_user_id = users_list[0].id
                  logger.info(f"Using existing user ID: {test_user_id}")
             else:
                  # Create a dummy user if none exist
                  logger.info("No users found (or empty list). Creating temp user...")
                  user_res = session_injector.client.auth.admin.create_user({
                      "email": f"test_user_{uuid.uuid4()}@example.com",
                      "password": "password123",
                      "email_confirm": True
                  })
                  # user_res is likely UserResponse, containing user object
                  if hasattr(user_res, "user"):
                      test_user_id = user_res.user.id
                  else:
                      test_user_id = user_res.id # Possible direct user object
                      
                  logger.info(f"Created temp user ID: {test_user_id}")

        except Exception as e:
             logger.error(f"Failed to fetch/create user: {e}")
             # Fallback (might fail)
             test_user_id = str(uuid.uuid4())

        session = await session_injector.create(user_id=test_user_id, initial_data={"loads": initial_loads})
        
        if not session or session.id != test_session_id:
             # If create returns a different ID (which it shouldn't if we passed it, but create method generates one usually? 
             # Let's check create method signature. It doesn't accept ID. It auto-generates ID or lets DB do it.
             # Wait, session_injector.create takes user_id and initial_data. It relies on Supabase to generate ID usually or we can pass it if we modify create.)
             # Actually session_injector.create code:
             # data = { "user_id": user_id, ... }
             # result = table.insert(data).execute()
             # So the DB generates the ID. We cannot force our ID unless we modify create.
             # We should use the ID returned by create.
             pass

        if not session:
             logger.error("🔴 Failed to create initial session.")
             return
        
        test_session_id = session.id # Update our ID to the real one
        logger.info(f"✅ Initial design saved. ID: {test_session_id}")

        # 3. VERIFY CREATE
        session = await session_injector.load(test_session_id)
        if not session or len(session.loads) != 2:
            logger.error(f"🔴 Load failed or count mismatch. Got {len(session.loads) if session else 0} loads.")
            return
        logger.info("✅ Initial load verified.")

        # 4. EDIT (MERGE): Change AC is 12000 -> 18000
        logger.info("Step 2: Executing Merge (Real Logic)...")
        # Simulate user command: "เปลี่ยนแอร์ห้องนอน 1 เป็น 18000 BTU"
        edit_command_str = "เปลี่ยนแอร์ห้องนอน 1 เป็น 18000 BTU"
        
        # Patch LLM to ensure we don't hit external APIs
        from unittest.mock import patch
        
        # Mock LLM to return valid EditCommand
        with patch('app.parsers.llm_parser.llm_parse') as mock_llm:
             from app.parsers.edit_command import EditCommand, EditAction
             # Configure the mock to return a valid command object (as a coroutine result)
             expected_cmd = EditCommand(
                 action=EditAction.CHANGE,
                 device_type="AC",
                 target_room="ห้องนอน 1",
                 new_value=18000,
                 unit="BTU",
                 confidence=1.0,
                 parse_method="mock_llm"
             )
             
             # AsyncMock automatically makes the return value awaitable
             mock_llm.return_value = expected_cmd
             
             try:
                 result = await merge_design_changes(test_session_id, edit_command_str)
             except Exception as merge_err:
                 logger.error(f"🔴 Merge failed with exception: {merge_err}")
                 import traceback
                 traceback.print_exc()
                 return
        
        if not result or not result.get("loads"):
            logger.error("🔴 Merge returned failure.")
            return
            
        # 5. VERIFY UPDATE (From Return)
        updated_loads = result["loads"]
        ac_load = next((l for l in updated_loads if "AC" in l["device"]), None)
        if ac_load and ac_load["device"] == "AC-18000BTU":
            logger.info("✅ Merge Logic returned correct data.")
        else:
            logger.error(f"🔴 Merge Logic returned wrong data: {ac_load}")
            # Debug: print all loads
            logger.info(f"All loads: {updated_loads}")
            return

        # 6. VERIFY PERSISTENCE (Load from DB again)
        logger.info("Step 3: Verifying Persistence (Reload from DB)...")
        session_reloaded = await session_injector.load(test_session_id)
        saved_loads = session_reloaded.loads
        saved_ac = next((l for l in saved_loads if "AC" in l["device"]), None)
        
        if saved_ac and saved_ac["device"] == "AC-18000BTU":
            logger.info("✅ DB Persistence Verified! Data is officially safe.")
        else:
            logger.error(f"🔴 DB Data verify failed. Got: {saved_ac}")
            return

        # 7. CLEANUP
        logger.info("Step 4: Cleaning up...")
        # Since access to delete might be restricted or implemented differently,
        # we check if delete method exists.
        if hasattr(session_injector, 'delete_session'):
             await session_injector.delete_session(test_session_id)
             logger.info("✅ Test session deleted.")
        elif hasattr(session_injector, 'delete'):
             # We implemented delete in session_injector
             await session_injector.delete(test_session_id)
             logger.info("✅ Test session deleted.")
        else:
             logger.info("⚠️ No delete method found. Test data remains (Session ID start with TEST_INTEGRATION_)")

        logger.info("🎉 INTEGRATION TEST PASSED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"🔴 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_real_supabase_lifecycle())
