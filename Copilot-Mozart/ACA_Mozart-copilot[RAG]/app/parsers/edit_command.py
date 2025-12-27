"""
Edit Command - Data Structure for Edit Operations

Defines the EditCommand dataclass that represents a parsed edit request.
This is the shared contract between parser components.

Created: 2025-12-28
Updated: 2025-12-28 - Added full flexibility fields
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class EditAction(str, Enum):
    """Possible edit actions."""
    CHANGE = "CHANGE"
    ADD = "ADD"
    REMOVE = "REMOVE"
    UNKNOWN = "UNKNOWN"


class TargetType(str, Enum):
    """What type of object is being edited."""
    DEVICE = "DEVICE"
    ROOM = "ROOM"
    UNKNOWN = "UNKNOWN"


@dataclass
class EditCommand:
    """
    Represents a parsed edit command from user input.
    
    Supports:
    - Device operations: CHANGE/ADD/REMOVE any device type
    - Room operations: ADD/REMOVE rooms
    - VD adjustments: Set branch_distance_m for wire sizing
    
    Examples:
        "เปลี่ยนแอร์เป็น 18000 BTU" → EditCommand(action=CHANGE, device_type="AC", new_value=18000)
        "เพิ่มห้องนอน" → EditCommand(action=ADD, target_type=ROOM, room_type="bedroom")
        "สายแอร์ยาว 25 เมตร" → EditCommand(action=CHANGE, device_type="AC", branch_distance_m=25)
    """
    
    # Required fields
    action: EditAction = EditAction.UNKNOWN
    target_type: TargetType = TargetType.DEVICE  # DEVICE or ROOM
    
    # Device targeting
    device_type: str = ""          # AC, HEATER, PUMP, etc.
    device_code: Optional[str] = None  # Full code: AC-18000BTU, REFRIG-300W
    
    # Room targeting (for device placement or room operations)
    room_name: Optional[str] = None     # "ห้องนอน 1", "ห้องครัว" (target or new room name)
    room_type: Optional[str] = None     # living, bedroom, kitchen, bathroom, etc.
    target_floor: Optional[int] = None  # 1, 2
    
    # Legacy alias (for backward compatibility)
    @property
    def target_room(self) -> Optional[str]:
        return self.room_name
    
    @target_room.setter
    def target_room(self, value: Optional[str]):
        self.room_name = value
    
    # Value for CHANGE/ADD
    new_value: Optional[int] = None          # 18000, 4500, etc.
    unit: Optional[str] = None               # BTU, W, m
    quantity: Optional[int] = None           # For ADD count
    
    # VD (Voltage Drop) - wire distance
    branch_distance_m: Optional[float] = None  # Cable length in meters
    
    # Metadata
    confidence: float = 0.0                # 0.0-1.0
    parse_method: str = "unknown"          # "regex", "llm", "failed"
    raw_input: str = ""                    # Original user input
    normalized_input: str = ""             # After typo normalization
    
    def is_valid(self) -> bool:
        """Check if command has minimum required data."""
        if self.action == EditAction.UNKNOWN:
            return False
        
        # For ROOM operations
        if self.target_type == TargetType.ROOM:
            if self.action == EditAction.ADD and not self.room_type:
                return False
            if self.action == EditAction.REMOVE and not self.room_name:
                return False
            return True
        
        # For DEVICE operations
        if not self.device_type and not self.device_code:
            return False
        
        # CHANGE requires either new_value or branch_distance_m
        if self.action == EditAction.CHANGE:
            if self.new_value is None and self.branch_distance_m is None and self.quantity is None:
                return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "action": self.action.value,
            "target_type": self.target_type.value,
            "device_type": self.device_type,
            "device_code": self.device_code,
            "room_name": self.room_name,
            "room_type": self.room_type,
            "target_floor": self.target_floor,
            "new_value": self.new_value,
            "unit": self.unit,
            "quantity": self.quantity,
            "branch_distance_m": self.branch_distance_m,
            "confidence": self.confidence,
            "parse_method": self.parse_method,
            "raw_input": self.raw_input,
            "normalized_input": self.normalized_input,
            "is_valid": self.is_valid(),
        }

