"""
Merge Engine - Stateful Intelligence Module

Handles merging user edit requests into existing designs.
Uses the Hybrid Parser (Regex + LLM) for command parsing.

Chain of Thought:
1. Load session from Supabase
2. Parse edit command (Normalizer → Regex → LLM)
3. Find target load/room in existing design
4. Apply change (patch, not replace)
5. Save updated design back to Supabase
6. Return merged design for re-calculation

Undo Logic:
- Snapshots are stored in session.site_context["_undo_stack"]
- Max 10 snapshots allowed
- UNDO action pops the last snapshot and restores loads/rooms

Created: 2025-12-28
Updated: 2026-01-13 - Added Edit Features 1-7 (Not Found, Summary, Qty, Undo, Validation)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json

from app.parsers import parse_edit_command, EditCommand, EditAction
from app.parsers.edit_command import TargetType

logger = logging.getLogger("Aura.Context.MergeEngine")


async def merge_design_changes(
    session_id: str,
    edit_request: str
) -> Optional[Dict[str, Any]]:
    """
    Load existing design from session and merge user's edit request.
    
    Supports:
    - Device CHANGE/ADD/REMOVE (any device type)
    - Room ADD/REMOVE
    - VD adjustments (branch_distance_m)
    - Quantity changes
    
    Args:
        session_id: The current session UUID
        edit_request: User's edit command (e.g., "เปลี่ยนแอร์เป็น 18000 BTU")
        
    Returns:
        Dict with merged design data, or None if merge failed
    """
    try:
        from app.context.session_injector import session_injector
        
        # =====================================================================
        # STEP 1: Load existing session
        # =====================================================================
        session = await session_injector.load(session_id)
        
        if not session:
            logger.warning(f"[MERGE] Session {session_id[:8]}... not found - cannot merge")
            return None
        
        # [CP-3] Merge Start Checkpoint - Log input state
        loads_count = len(session.loads) if session.loads else 0
        rooms_count = len(session.rooms) if session.rooms else 0
        logger.info(f"[CP-3] Merge start: session={session_id[:8]}, loads={loads_count}, rooms={rooms_count}, cmd=\"{edit_request[:50]}\"")
        
        logger.info(f"[MERGE] Loaded session with {len(session.loads)} loads, {len(session.rooms)} rooms")
        
        # =====================================================================
        # STEP 2: Parse edit command using Hybrid Parser (LLM-First for flexibility)
        # =====================================================================
        cmd = await parse_edit_command(edit_request, use_llm_fallback=True)
        
        if not cmd or not cmd.is_valid():
            logger.warning(f"[MERGE] Failed to parse edit command: '{edit_request[:50]}...'")
            return None
            
        # 🟡 Feature 7: Robust Validation
        from app.context.validator import EditValidator
        validation = EditValidator.validate(cmd, session.loads)
        if not validation.valid:
            logger.warning(f"[MERGE] Validation failed: {validation.error}")
            return {
                "status": "validation_error",
                "message": f"❌ {validation.error}",
                "debug_info": {"cmd": str(cmd)}
            }
            
        if cmd.action == EditAction.UNDO:
            # 🟢 Feature 5: Undo Last Action
            undo_res = await _undo_last_action(session, session_id)
            if not undo_res:
                return {
                    "status": "error",
                    "message": "⚠️ ไม่สามารถย้อนกลับได้ (ไม่มีประวัติการแก้ไข)",
                }
            return {
                "status": "success",
                "message": "✅ ย้อนกลับการแก้ไขล่าสุดเรียบร้อย (Undo Successful)",
                "data": undo_res  # {loads, rooms}
            }
            
        logger.info(f"[MERGE] Parsed: {cmd.action.value} {cmd.target_type.value} - {cmd.device_type or cmd.device_code or cmd.room_type}")
        
        # 🟢 Feature 5: Save Snapshot BEFORE applying changes
        # Ensure we don't save snapshot for UNDO action itself
        await _save_snapshot(session, session_id)
        
        # =====================================================================
        # STEP 3: Apply change based on target_type (DEVICE or ROOM)
        # =====================================================================
        updated_loads = list(session.loads) if session.loads else []
        updated_rooms = list(session.rooms) if session.rooms else []
        
        if cmd.target_type == TargetType.ROOM:
            # ROOM operations
            changes_log = []  # Initialize for ROOM operations
            if cmd.action == EditAction.ADD:
                updated_rooms = apply_add_room(updated_rooms, cmd)
                changes_log.append(f"เพิ่มห้อง '{cmd.room_type}' เรียบร้อย")
            elif cmd.action == EditAction.REMOVE:
                updated_rooms = apply_remove_room(updated_rooms, updated_loads, cmd)
                changes_log.append(f"ลบห้อง '{cmd.room_type}' เรียบร้อย")
            else:
                logger.warning(f"[MERGE] CHANGE action not supported for rooms")
                return None
        else:
            # DEVICE operations
            target_indices = find_target_loads(updated_loads, cmd)
            
            # 🔴 Feature 1: Device Not Found handling
            if not target_indices and cmd.action != EditAction.ADD:
                logger.warning(f"[MERGE] No matching load found for {cmd.device_type or cmd.device_code}")
                return {
                    "status": "not_found",
                    "message": f"❌ ไม่พบอุปกรณ์ '{cmd.device_type or cmd.device_code}' ในห้องที่ระบุค่ะ",
                    "debug_info": {"target": cmd.device_type, "room": cmd.room_name}
                }

            # 🔴 Feature 2: Confirmation Mode (Ambiguity Detection)
            if len(target_indices) > 1 and not cmd.room_name and cmd.action in [EditAction.REMOVE, EditAction.CHANGE]:
                # Found multiple items but user didn't specify which one/room
                # Check if they are in different rooms (if all in same room, maybe okay to delete all? No, safer to ask)
                unique_rooms = list(set([updated_loads[i].get("room_name") for i in target_indices]))
                
                logger.info(f"[MERGE] Ambiguous target: {len(target_indices)} matches in {unique_rooms}")
                
                options = []
                for i in target_indices:
                    load = updated_loads[i]
                    options.append(f"{load.get('device')} ใน {load.get('room_name')}")
                
                return {
                    "status": "confirm_required",
                    "message": f"⚠️ พบอุปกรณ์หลายรายการ ({len(target_indices)} รายการ) กรุณาระบุห้องให้ชัดเจน",
                    "options": options,
                    "debug_info": {"unique_rooms": unique_rooms}
                }
            
            if cmd.action == EditAction.CHANGE:
                updated_loads, changes_log = apply_change(updated_loads, target_indices, cmd)
            elif cmd.action == EditAction.ADD:
                updated_loads, changes_log = apply_add(updated_loads, cmd, updated_rooms)
            elif cmd.action == EditAction.REMOVE:
                updated_loads, changes_log = apply_remove(updated_loads, target_indices, cmd.quantity or 1)
        
        # =====================================================================
        # STEP 4: Save updated design back to Supabase
        # =====================================================================
        success = await session_injector.update_design(
            session_id,
            loads=updated_loads,
            rooms=updated_rooms
        )
        
        if not success:
            logger.error("[MERGE] Failed to save updated design to Supabase")
            return None
        
        logger.info(f"[MERGE] ✅ Successfully merged - {len(updated_loads)} loads, {len(updated_rooms)} rooms")
        
        # 🆕 Audit Trail: Log EDIT action
        try:
            from app.context.audit_logger import log_edit_action
            target_name = cmd.device_type or cmd.device_code or cmd.room_type or "unknown"
            await log_edit_action(
                session_id=session_id,
                action=cmd.action.value,
                target=target_name,
                before_count=len(session.loads) if session.loads else 0,
                after_count=len(updated_loads)
            )
        except Exception as audit_err:
            logger.warning(f"[MERGE] Audit log failed (non-blocking): {audit_err}")
            
        # 🔴 Feature 3: Return structured result with summary
        return {
            "status": "success",
            "message": f"✅ {changes_log[0]}" if changes_log else "✅ ปรับปรุงข้อมูลเรียบร้อย",
            "changes": changes_log,
            "data": {
                "loads": updated_loads,
                "rooms": updated_rooms
            }
        }
        
    except Exception as e:
        logger.error(f"[MERGE] Failed to merge design: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_target_loads(loads: List[Dict], cmd: EditCommand) -> List[int]:
    """
    Find indices of loads that match the edit command target.
    Supports matching by device_type, device_code, room_name, and floor.
    """
    matches = []
    
    for i, load in enumerate(loads):
        device = load.get("device", "")
        room = load.get("room_name", "")
        
        # Check device match
        device_match = False
        
        # Match by exact device_code if specified
        if cmd.device_code and cmd.device_code.upper() == device.upper():
            device_match = True
        # Match by device_type prefix
        elif cmd.device_type:
            dtype = cmd.device_type.upper()
            if device.upper().startswith(dtype + "-") or device.upper().startswith(dtype):
                device_match = True
        
        if not device_match:
            continue
        
        # Check room match (if specified)
        if cmd.room_name:
            if cmd.room_name.lower() not in room.lower():
                continue
        
        # Check floor match (if specified)
        if cmd.target_floor:
            load_floor = load.get("floor", 1)
            if load_floor != cmd.target_floor:
                continue
        
        matches.append(i)
    
    logger.debug(f"[MERGE] Found {len(matches)} matching loads")
    return matches


def apply_change(loads: List[Dict], indices: List[int], cmd: EditCommand) -> Tuple[List[Dict], List[str]]:
    """
    Apply CHANGE action to matching loads.
    Supports: new_value, quantity, branch_distance_m
    Returns: (updated_loads, changes_log)
    """
    changes_log = []
    for i in indices:
        old_device = loads[i].get("device", "")
        
        # Change device value if specified
        if cmd.new_value is not None:
            # Use device_code if provided, otherwise build from device_type
            if cmd.device_code:
                new_device = cmd.device_code
            elif cmd.device_type:
                # Build device code based on type
                dtype = cmd.device_type.upper()
                unit = cmd.unit or ("BTU" if dtype == "AC" else "W")
                new_device = f"{dtype}-{cmd.new_value}{unit}"
            else:
                # Just replace numbers in existing device
                import re
                new_device = re.sub(r'\d+', str(cmd.new_value), old_device)
            
            loads[i]["device"] = new_device
            msg = f"เปลี่ยน {old_device} → {new_device}"
            logger.info(f"[MERGE] {msg}")
            changes_log.append(msg)
        
        # Change quantity if specified
        if cmd.quantity is not None:
            old_qty = loads[i].get("quantity", 1)
            loads[i]["quantity"] = cmd.quantity
            msg = f"ปรับจำนวน {old_device}: {old_qty} → {cmd.quantity}"
            logger.info(f"[MERGE] {msg}")
            changes_log.append(msg)
        
        # Change branch_distance_m if specified (for VD)
        if cmd.branch_distance_m is not None:
            old_dist = loads[i].get("branch_distance_m")
            loads[i]["branch_distance_m"] = cmd.branch_distance_m
            msg = f"ปรับระยะสาย {old_device}: {old_dist or 'N/A'}m → {cmd.branch_distance_m}m"
            logger.info(f"[MERGE] {msg}")
            changes_log.append(msg)
    
    return loads, changes_log


def apply_add(loads: List[Dict], cmd: EditCommand, rooms: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Apply ADD action - add new load.
    Supports any device via device_code or device_type.
    Returns: (updated_loads, changes_log)
    """
    changes_log = []
    # Determine target room
    target_room = cmd.room_name
    if not target_room and rooms:
        # Default based on device type
        dtype = cmd.device_type or ""
        if dtype.upper() == "HEATER":
            for r in rooms:
                if "ห้องน้ำ" in r.get("name", ""):
                    target_room = r.get("name")
                    break
        if not target_room:
            target_room = rooms[0].get("name", "ห้องนั่งเล่น")
    
    # Build device code
    if cmd.device_code:
        device = cmd.device_code
    elif cmd.device_type:
        dtype = cmd.device_type.upper()
        val = cmd.new_value
        unit = cmd.unit or ("BTU" if dtype == "AC" else "W")
        
        # Use defaults if no value specified
        defaults = {
            "AC": ("12000", "BTU"),
            "HEATER": ("4500", "W"),
            "PUMP": ("750", "W"),
            "INDUCTION": ("3000", "W"),
            "REFRIG": ("300", "W"),
            "MICROWAVE": ("1500", "W"),
            "KETTLE": ("2200", "W"),
            "RICECOOK": ("800", "W"),
            "FAN-CEILING": ("60", "W"),
            "FAN-EXHAUST": ("25", "W"),
            "LIGHT-LED": ("10", "W"),
            "SOCKET": ("16", "A"),
        }
        
        if val is None:
            default_val, default_unit = defaults.get(dtype, ("0", "W"))
            val = default_val
            unit = default_unit
        
        device = f"{dtype}-{val}{unit}"
    else:
        logger.warning("[MERGE] No device_type or device_code for ADD")
        return loads
    
    # 🟡 Feature 6: Merge Duplicates
    # Check if this exact device already exists in the target room
    # Match criteria: same device string, same room, same floor
    found_existing = False
    add_qty = cmd.quantity or 1
    target_floor = cmd.target_floor or 1
    
    for load in loads:
        is_same_device = load.get("device") == device
        is_same_room = load.get("room_name") == target_room
        # Floor check: strict if provided, loose otherwise (assume 1st floor if not specified in load)
        load_floor = load.get("floor", 1)
        is_same_floor = load_floor == target_floor
        
        if is_same_device and is_same_room and is_same_floor:
            old_qty = load.get("quantity", 1)
            load["quantity"] = old_qty + add_qty
            msg = f"เพิ่มจำนวน {device} ใน{target_room}: {old_qty} → {load['quantity']}"
            logger.info(f"[MERGE] {msg} (Merged Duplicate)")
            changes_log.append(msg)
            found_existing = True
            break
            
    if not found_existing:
        new_load = {
            "room_name": target_room or "ห้องนั่งเล่น",
            "device": device,
            "quantity": add_qty,
            "floor": target_floor,
        }
        
        if cmd.branch_distance_m:
            new_load["branch_distance_m"] = cmd.branch_distance_m
        
        loads.append(new_load)
        msg = f"เพิ่ม {device} x{add_qty} ใน{target_room or 'ห้องนั่งเล่น'}"
        logger.info(f"[MERGE] {msg}")
        changes_log.append(msg)
    
    return loads, changes_log


def apply_remove(loads: List[Dict], indices: List[int], remove_qty: int = 1) -> Tuple[List[Dict], List[str]]:
    """
    Apply REMOVE action - reduce quantity or delete if quantity becomes 0.
    Returns: (updated_loads, changes_log)
    """
    remaining_to_remove = remove_qty
    removed_items_log = []
    
    for i in sorted(indices, reverse=True):
        if remaining_to_remove <= 0:
            break
            
        load = loads[i]
        device_name = load.get('device', 'Unknown')
        room = load.get('room_name', 'Unknown')
        current_qty = load.get("quantity", 1)
        
        if current_qty <= remaining_to_remove:
            # Remove entire entry
            removed = loads.pop(i)
            msg = f"ลบ {device_name} x{current_qty} จาก{room}"
            removed_items_log.append(msg)
            remaining_to_remove -= current_qty
            logger.info(f"[MERGE] Removed entire entry: {device_name} from {room}")
        else:
            # Reduce quantity
            loads[i]["quantity"] = current_qty - remaining_to_remove
            msg = f"ลดจำนวน {device_name} จาก {current_qty} เหลือ {loads[i]['quantity']} ใน{room}"
            removed_items_log.append(msg)
            logger.info(f"[MERGE] Reduced: {device_name} {current_qty} → {loads[i]['quantity']}")
            remaining_to_remove = 0
    
    if remaining_to_remove > 0:
        msg = f"⚠️ ต้องการลบ {remove_qty} แต่เจอแค่ {remove_qty - remaining_to_remove}"
        removed_items_log.append(msg)
        logger.warning(f"[MERGE] {msg}")
    
    return loads, removed_items_log


def apply_add_room(rooms: List[Dict], cmd: EditCommand) -> List[Dict]:
    """
    Apply ADD ROOM action.
    """
    # Check duplicate
    for r in rooms:
        if r.get("name") == cmd.room_name:
            logger.warning(f"[MERGE] Room already exists: {cmd.room_name}")
            return rooms
            
    new_room = {
        "name": cmd.room_name,
        "type": cmd.room_type or "bedroom",
        "floor": cmd.target_floor or 1
    }
    rooms.append(new_room)
    logger.info(f"[MERGE] Added room: {cmd.room_name}")
    
    return rooms


# =============================================================================
# UNDO / SNAPSHOT LOGIC
# =============================================================================

async def _save_snapshot(session, session_id: str):
    """
    Save current loads/rooms to session.undo_history.
    Max 10 snapshots.
    
    🆕 Phase 5: Now uses session.undo_history instead of site_context['_undo_stack']
    """
    try:
        from app.context.session_injector import session_injector
        from datetime import datetime
        
        # 1. Get current stack from session field (not site_context!)
        undo_stack = session.undo_history if hasattr(session, 'undo_history') else []
        if undo_stack is None:
            undo_stack = []
        
        # 2. Create snapshot
        snapshot = {
            "loads": session.loads,
            "rooms": session.rooms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 3. Push and Limit
        undo_stack.append(snapshot)
        if len(undo_stack) > 10:
            undo_stack.pop(0)  # Remove oldest
            
        # 4. Save undo_history to DB (separate field, not in site_context)
        await session_injector.update(session_id, {"undo_history": undo_stack})
        logger.info(f"[UNDO] Snapshot saved. Stack size: {len(undo_stack)}")
        
    except Exception as e:
        logger.error(f"[UNDO] Failed to save snapshot: {e}")


async def _undo_last_action(session, session_id: str) -> Optional[Dict]:
    """
    Pop last snapshot and restore loads/rooms.
    Returns restored {loads, rooms} or None if empty.
    
    🆕 Phase 5: Now uses session.undo_history instead of site_context['_undo_stack']
    """
    try:
        from app.context.session_injector import session_injector
        
        # Get undo_history from session field (not site_context!)
        undo_stack = session.undo_history if hasattr(session, 'undo_history') else []
        if not undo_stack:
            logger.info("[UNDO] Stack empty, nothing to undo.")
            return None
            
        # 1. Pop last snapshot
        last_snap = undo_stack.pop()
        
        # 2. Extract data
        restored_loads = last_snap.get("loads", [])
        restored_rooms = last_snap.get("rooms", [])
        
        # 3. Update DB (Restore data + Update undo_history)
        success = await session_injector.update_design(
            session_id,
            loads=restored_loads,
            rooms=restored_rooms
        )
        # Also save the reduced undo_history
        await session_injector.update(session_id, {"undo_history": undo_stack})
        
        if success:
            logger.info(f"[UNDO] Restored snapshot. Stack remaining: {len(undo_stack)}")
            return {"loads": restored_loads, "rooms": restored_rooms}
            
        return None
        
    except Exception as e:
        logger.error(f"[UNDO] Failed to undo: {e}")
        return None


def apply_remove_room(rooms: List[Dict], loads: List[Dict], cmd: EditCommand) -> List[Dict]:
    """
    Apply REMOVE ROOM action.
    Also removes all loads in that room.
    """
    target_name = cmd.room_name
    if not target_name:
        logger.warning("[MERGE] No room_name specified for REMOVE")
        return rooms
    
    # Find and remove room
    room_indices = [i for i, r in enumerate(rooms) if target_name.lower() in r.get("name", "").lower()]
    
    for i in sorted(room_indices, reverse=True):
        removed = rooms.pop(i)
        logger.info(f"[MERGE] Removed room: {removed.get('name')}")
    
    # Also remove loads in that room
    load_indices = [i for i, l in enumerate(loads) if target_name.lower() in l.get("room_name", "").lower()]
    for i in sorted(load_indices, reverse=True):
        removed = loads.pop(i)
        logger.info(f"[MERGE] Removed load from deleted room: {removed.get('device')}")
    
    return rooms
