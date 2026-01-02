"""
Revision Diff Module

Calculates differences between versions of a project.

Author: Fixia
Date: 2026-01-03
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("Aura.RevisionDiff")


class FieldChange(TypedDict):
    """A single field change"""
    field: str
    label: str
    before: Optional[Any]
    after: Optional[Any]
    change_type: str  # 'added', 'removed', 'modified'


class RevisionDiff(TypedDict):
    """Diff between two versions"""
    from_version: int
    to_version: int
    timestamp: str
    summary: str
    changes: List[FieldChange]
    change_count: int


def diff_projects(
    old_version: Dict[str, Any],
    new_version: Dict[str, Any]
) -> RevisionDiff:
    """
    Calculate diff between two project versions.
    
    Args:
        old_version: Previous project data
        new_version: Current project data
        
    Returns:
        RevisionDiff with all changes
    """
    changes: List[FieldChange] = []
    
    # Fields to track with Thai labels
    TRACKED_FIELDS = {
        "building_type": "ประเภทอาคาร",
        "num_floors": "จำนวนชั้น",
        "total_area_sqm": "พื้นที่รวม (ตร.ม.)",
        "main_breaker": "Main Breaker",
        "service_distance_m": "ระยะ Service",
    }
    
    # Check simple fields
    for field, label in TRACKED_FIELDS.items():
        old_val = old_version.get(field)
        new_val = new_version.get(field)
        
        if old_val != new_val:
            if old_val is None and new_val is not None:
                change_type = "added"
            elif old_val is not None and new_val is None:
                change_type = "removed"
            else:
                change_type = "modified"
            
            changes.append({
                "field": field,
                "label": label,
                "before": old_val,
                "after": new_val,
                "change_type": change_type,
            })
    
    # Check rooms
    old_rooms = {r.get("name"): r for r in old_version.get("rooms", [])}
    new_rooms = {r.get("name"): r for r in new_version.get("rooms", [])}
    
    # Added rooms
    for room_name in set(new_rooms.keys()) - set(old_rooms.keys()):
        changes.append({
            "field": f"rooms.{room_name}",
            "label": f"ห้อง: {room_name}",
            "before": None,
            "after": new_rooms[room_name],
            "change_type": "added",
        })
    
    # Removed rooms
    for room_name in set(old_rooms.keys()) - set(new_rooms.keys()):
        changes.append({
            "field": f"rooms.{room_name}",
            "label": f"ห้อง: {room_name}",
            "before": old_rooms[room_name],
            "after": None,
            "change_type": "removed",
        })
    
    # Modified rooms
    for room_name in set(old_rooms.keys()) & set(new_rooms.keys()):
        old_room = old_rooms[room_name]
        new_room = new_rooms[room_name]
        
        # Check room fields
        for field in ["area_sqm", "floor"]:
            if old_room.get(field) != new_room.get(field):
                changes.append({
                    "field": f"rooms.{room_name}.{field}",
                    "label": f"ห้อง {room_name}: {field}",
                    "before": old_room.get(field),
                    "after": new_room.get(field),
                    "change_type": "modified",
                })
        
        # Check devices in room
        old_devices = {d.get("name"): d for d in old_room.get("devices", [])}
        new_devices = {d.get("name"): d for d in new_room.get("devices", [])}
        
        for device_name in set(new_devices.keys()) - set(old_devices.keys()):
            changes.append({
                "field": f"rooms.{room_name}.devices.{device_name}",
                "label": f"เพิ่มอุปกรณ์ใน {room_name}: {device_name}",
                "before": None,
                "after": new_devices[device_name],
                "change_type": "added",
            })
        
        for device_name in set(old_devices.keys()) - set(new_devices.keys()):
            changes.append({
                "field": f"rooms.{room_name}.devices.{device_name}",
                "label": f"ลบอุปกรณ์จาก {room_name}: {device_name}",
                "before": old_devices[device_name],
                "after": None,
                "change_type": "removed",
            })
    
    # Generate summary
    added = sum(1 for c in changes if c["change_type"] == "added")
    removed = sum(1 for c in changes if c["change_type"] == "removed")
    modified = sum(1 for c in changes if c["change_type"] == "modified")
    
    summary_parts = []
    if added > 0:
        summary_parts.append(f"+{added} เพิ่ม")
    if removed > 0:
        summary_parts.append(f"-{removed} ลบ")
    if modified > 0:
        summary_parts.append(f"~{modified} แก้ไข")
    
    return {
        "from_version": old_version.get("version", 0),
        "to_version": new_version.get("version", 1),
        "timestamp": datetime.now().isoformat(),
        "summary": " | ".join(summary_parts) if summary_parts else "ไม่มีการเปลี่ยนแปลง",
        "changes": changes,
        "change_count": len(changes),
    }


def format_diff_for_display(diff: RevisionDiff) -> str:
    """Format diff as human-readable text."""
    lines = [
        f"## Revision v{diff['from_version']} → v{diff['to_version']}",
        f"_{diff['timestamp']}_",
        "",
        f"**สรุป:** {diff['summary']}",
        "",
    ]
    
    if diff["changes"]:
        lines.append("### รายการเปลี่ยนแปลง")
        lines.append("")
        
        for change in diff["changes"]:
            icon = {"added": "➕", "removed": "➖", "modified": "✏️"}.get(change["change_type"], "•")
            
            if change["change_type"] == "modified":
                lines.append(f"- {icon} **{change['label']}**: `{change['before']}` → `{change['after']}`")
            elif change["change_type"] == "added":
                lines.append(f"- {icon} **{change['label']}**: {change['after']}")
            else:
                lines.append(f"- {icon} **{change['label']}** (ลบ)")
    
    return "\n".join(lines)
