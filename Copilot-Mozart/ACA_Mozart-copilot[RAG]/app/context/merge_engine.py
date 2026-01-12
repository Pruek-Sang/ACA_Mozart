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

Created: 2025-12-28
Updated: 2025-12-28 - Full flexibility: all devices, rooms, VD
"""

import logging
from typing import Dict, Any, Optional, List

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
        
        logger.info(f"[MERGE] Loaded session with {len(session.loads)} loads, {len(session.rooms)} rooms")
        
        # =====================================================================
        # STEP 2: Parse edit command using Hybrid Parser (LLM-First for flexibility)
        # =====================================================================
        cmd = await parse_edit_command(edit_request, use_llm_fallback=True)
        
        if not cmd or not cmd.is_valid():
            logger.warning(f"[MERGE] Failed to parse edit command: '{edit_request[:50]}...'")
            return None
        
        logger.info(f"[MERGE] Parsed: {cmd.action.value} {cmd.target_type.value} - {cmd.device_type or cmd.device_code or cmd.room_type}")
        
        # =====================================================================
        # STEP 3: Apply change based on target_type (DEVICE or ROOM)
        # =====================================================================
        updated_loads = list(session.loads) if session.loads else []
        updated_rooms = list(session.rooms) if session.rooms else []
        
        if cmd.target_type == TargetType.ROOM:
            # ROOM operations
            if cmd.action == EditAction.ADD:
                updated_rooms = apply_add_room(updated_rooms, cmd)
            elif cmd.action == EditAction.REMOVE:
                updated_rooms = apply_remove_room(updated_rooms, updated_loads, cmd)
            else:
                logger.warning(f"[MERGE] CHANGE action not supported for rooms")
                return None
        else:
            # DEVICE operations
            target_indices = find_target_loads(updated_loads, cmd)
            
            if not target_indices and cmd.action != EditAction.ADD:
                logger.warning(f"[MERGE] No matching load found for {cmd.device_type or cmd.device_code}")
                return None
            
            if cmd.action == EditAction.CHANGE:
                updated_loads = apply_change(updated_loads, target_indices, cmd)
            elif cmd.action == EditAction.ADD:
                updated_loads = apply_add(updated_loads, cmd, updated_rooms)
            elif cmd.action == EditAction.REMOVE:
                updated_loads = apply_remove(updated_loads, target_indices)
        
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
            await log_edit_action(
                session_id=session_id,
                action=cmd.action.value,
                target=cmd.device_type or cmd.device_code or cmd.room_type or "unknown",
                before_count=len(session.loads) if session.loads else 0,
                after_count=len(updated_loads)
            )
        except Exception as audit_err:
            logger.warning(f"[MERGE] Audit log failed (non-blocking): {audit_err}")
        
        # =====================================================================
        # STEP 5: Return merged design for re-calculation
        # =====================================================================
        return {
            "rooms": updated_rooms,
            "loads": updated_loads,
            "site_context": session.site_context,
            "edit_applied": cmd.to_dict(),
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


def apply_change(loads: List[Dict], indices: List[int], cmd: EditCommand) -> List[Dict]:
    """
    Apply CHANGE action to matching loads.
    Supports: new_value, quantity, branch_distance_m
    """
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
            logger.info(f"[MERGE] Changed device: {old_device} → {new_device}")
        
        # Change quantity if specified
        if cmd.quantity is not None:
            old_qty = loads[i].get("quantity", 1)
            loads[i]["quantity"] = cmd.quantity
            logger.info(f"[MERGE] Changed quantity: {old_qty} → {cmd.quantity}")
        
        # Change branch_distance_m if specified (for VD)
        if cmd.branch_distance_m is not None:
            old_dist = loads[i].get("branch_distance_m")
            loads[i]["branch_distance_m"] = cmd.branch_distance_m
            logger.info(f"[MERGE] Changed distance: {old_dist} → {cmd.branch_distance_m}m")
    
    return loads


def apply_add(loads: List[Dict], cmd: EditCommand, rooms: List[Dict]) -> List[Dict]:
    """
    Apply ADD action - add new load.
    Supports any device via device_code or device_type.
    """
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
    
    new_load = {
        "room_name": target_room or "ห้องนั่งเล่น",
        "device": device,
        "quantity": cmd.quantity or 1,
        "floor": cmd.target_floor or 1,
    }
    
    if cmd.branch_distance_m:
        new_load["branch_distance_m"] = cmd.branch_distance_m
    
    loads.append(new_load)
    logger.info(f"[MERGE] Added: {device} x{cmd.quantity or 1} in {target_room}")
    
    return loads


def apply_remove(loads: List[Dict], indices: List[int]) -> List[Dict]:
    """
    Apply REMOVE action - delete matching loads.
    """
    for i in sorted(indices, reverse=True):
        removed = loads.pop(i)
        logger.info(f"[MERGE] Removed: {removed.get('device')} from {removed.get('room_name')}")
    
    return loads


def apply_add_room(rooms: List[Dict], cmd: EditCommand) -> List[Dict]:
    """
    Apply ADD ROOM action.
    """
    room_type = cmd.room_type or "bedroom"
    quantity = cmd.quantity or 1
    
    # Generate room names
    existing_count = sum(1 for r in rooms if room_type in r.get("type", ""))
    
    type_to_name = {
        "bedroom": "ห้องนอน",
        "bathroom": "ห้องน้ำ",
        "kitchen": "ห้องครัว",
        "living": "ห้องนั่งเล่น",
        "storage": "ห้องเก็บของ",
        "exterior": "พื้นที่ภายนอก",
        "garage": "โรงรถ",
    }
    
    base_name = type_to_name.get(room_type, room_type)
    
    for i in range(quantity):
        room_num = existing_count + i + 1
        room_name = f"{base_name} {room_num}" if room_num > 1 else base_name
        
        new_room = {
            "name": room_name,
            "type": room_type,
            "floor": cmd.target_floor or 1,
        }
        rooms.append(new_room)
        logger.info(f"[MERGE] Added room: {room_name} (type={room_type})")
    
    return rooms


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
