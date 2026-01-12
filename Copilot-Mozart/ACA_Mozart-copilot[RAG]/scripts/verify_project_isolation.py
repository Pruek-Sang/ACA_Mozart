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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("VerifyIsolation")

async def verify_isolation():
    logger.info("🚀 STARTING PROJECT ISOLATION TEST 🚀")
    
    # =========================================================================
    # 1. Create PROJECT A
    # =========================================================================
    logger.info("\n--- Step 1: Create Project A ---")
    session_a = await session_injector.create(project_name="Project A (Old)")
    id_a = session_a.id
    logger.info(f"✅ Created Project A: {id_a}")
    
    # Modify Project A: Add AC
    logger.info("Adding 'AC' to Project A...")
    await merge_design_changes(id_a, "add AC 12000BTU to Bedroom 1")
    
    # Verify State A
    sess_a = await session_injector.load(id_a)
    loads_a = sess_a.loads
    logger.info(f"Project A Loads: {[l['device'] for l in loads_a]}")
    if len(loads_a) != 1 or loads_a[0]['device'] != "AC-12000BTU":
        logger.error("❌ Project A Initial State Incorrect")
        return
        
    # =========================================================================
    # 2. Create PROJECT B (New Project)
    # =========================================================================
    logger.info("\n--- Step 2: Create Project B (New) ---")
    session_b = await session_injector.create(project_name="Project B (New)")
    id_b = session_b.id
    logger.info(f"✅ Created Project B: {id_b}")
    
    # Modify Project B: Add Fan (Different from A)
    logger.info("Adding 'Fan' to Project B...")
    await merge_design_changes(id_b, "add Fan to Living Room")
    
    # Verify State B
    sess_b = await session_injector.load(id_b)
    loads_b = sess_b.loads
    logger.info(f"Project B Loads: {[l['device'] for l in loads_b]}")
    if len(loads_b) != 1 or "FAN" not in loads_b[0]['device'].upper():
        logger.error("❌ Project B Initial State Incorrect")
        return

    # =========================================================================
    # 3. Verify ISOLATION
    # =========================================================================
    logger.info("\n--- Step 3: Verify Isolation ---")
    
    # Reload Project A and ensure it HAS NOT CHANGED
    logger.info("Reloading Project A...")
    sess_a_reload = await session_injector.load(id_a)
    loads_a_reload = sess_a_reload.loads
    logger.info(f"Project A Loads (Reloaded): {[l['device'] for l in loads_a_reload]}")
    
    # Check A
    if len(loads_a_reload) == 1 and loads_a_reload[0]['device'] == "AC-12000BTU":
        logger.info("✅ Project A is intact (Contains AC, No Fan)")
    else:
        logger.error(f"❌ Project A Corrupted! Found: {loads_a_reload}")
        
    # Reload Project B and ensure it HAS NOT CHANGED
    logger.info("Reloading Project B...")
    sess_b_reload = await session_injector.load(id_b)
    loads_b_reload = sess_b_reload.loads
    logger.info(f"Project B Loads (Reloaded): {[l['device'] for l in loads_b_reload]}")
    
    # Check B
    if len(loads_b_reload) == 1 and "FAN" in loads_b_reload[0]['device'].upper():
        logger.info("✅ Project B is intact (Contains Fan, No AC)")
    else:
        logger.error(f"❌ Project B Corrupted! Found: {loads_b_reload}")
        
    # =========================================================================
    # 4. Verify EDIT/DELETE Isolation (Deep Check)
    # =========================================================================
    logger.info("\n--- Step 4: Verify EDIT/DELETE Isolation ---")
    
    # Setup: Ensure both have an AC, but different values
    logger.info("Setup: Clearing B and adding standard AC-18000BTU...")
    # Reset B loads
    await session_injector.update_design(id_b, loads=[], rooms=[{"name": "Living Room", "type": "living", "floor": 1}])
    await merge_design_changes(id_b, "add AC 18000BTU to Living Room")
    
    # State: A = AC-12000BTU (from before), B = AC-18000BTU
    
    # --- TEST 1: EDIT ISOLATION ---
    logger.info("ACTION: Edit Project A -> Change AC to 9000BTU")
    await merge_design_changes(id_a, "change AC to 9000BTU")
    
    # Reload both
    loads_a = (await session_injector.load(id_a)).loads
    loads_b = (await session_injector.load(id_b)).loads
    
    val_a = loads_a[0]['device']
    val_b = loads_b[0]['device']
    
    logger.info(f"Result A: {val_a} (Expected: AC-9000BTU)")
    logger.info(f"Result B: {val_b} (Expected: AC-18000BTU)")
    
    if "9000" in val_a and "18000" in val_b:
        logger.info("✅ PASS: Edit in A did NOT affect B")
    else:
        logger.error("❌ FAIL: Edit leaked!")

    # --- TEST 2: DELETE ISOLATION ---
    logger.info("ACTION: Delete AC from Project A")
    await merge_design_changes(id_a, "remove AC")
    
    # Reload both
    loads_a = (await session_injector.load(id_a)).loads
    loads_b = (await session_injector.load(id_b)).loads
    
    logger.info(f"Result A Count: {len(loads_a)} (Expected: 0)")
    logger.info(f"Result B Count: {len(loads_b)} (Expected: 1)")
    
    if len(loads_a) == 0 and len(loads_b) == 1:
        logger.info("✅ PASS: Delete in A did NOT affect B")
    else:
        logger.error("❌ FAIL: Delete leaked!")

    # =========================================================================
    # 5. Result
    # =========================================================================
    if id_a != id_b:
        logger.info("\n✅ PASS: Session IDs are unique")
    else:
        logger.error("\n❌ FAIL: Session IDs collide")
        
    logger.info("✨ Isolation Test Complete ✨")

if __name__ == "__main__":
    asyncio.run(verify_isolation())
