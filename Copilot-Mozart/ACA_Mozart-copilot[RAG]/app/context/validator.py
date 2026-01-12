"""
Edit Validator Module

Validates edit commands against safety limits and business rules.
Mirrors the logic from MCP Core's InputSanitizer but applied to EditCommands.

Created: 2026-01-13
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from app.parsers import EditCommand, EditAction, TargetType

@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None

class EditValidator:
    """
    Validates values in EditCommand before they are applied.
    """
    
    # Safety Limits (matches MCP Core)
    LIMITS = {
        # Device Wattage Limits (Watts)
        "MAX_WATTS": 15000,
        "MAX_WATTS_LIGHT": 500,    # LED/Downlight max
        "MAX_WATTS_APPLIANCE": 5000, # Heater/AC max
        
        # Quantity Limits per Room/Type
        "MAX_QTY_PER_ROOM": 50,
        "MAX_SOCKETS": 40,
        
        # Ranges
        "AC_MIN_BTU": 9000,
        "AC_MAX_BTU": 60000,
    }

    @staticmethod
    def validate(cmd: EditCommand, current_loads: List[Dict]) -> ValidationResult:
        """
        Validate an edit command against defined rules.
        """
        # 1. Negative Value Check
        if cmd.new_value is not None and cmd.new_value < 0:
            return ValidationResult(valid=False, error="ค่าต้องไม่ติดลบ (Must be positive)")
            
        if cmd.quantity is not None and cmd.quantity < 0:
            return ValidationResult(valid=False, error="จำนวนต้องไม่ติดลบ")

        # 2. Add/Change Value Validation
        if cmd.action in [EditAction.ADD, EditAction.CHANGE]:
            return EditValidator._validate_values(cmd)
            
        return ValidationResult(valid=True)

    @staticmethod
    def _validate_values(cmd: EditCommand) -> ValidationResult:
        """Deep validation of specific values based on device type."""
        
        # Validate Quantity Cap
        if cmd.quantity and cmd.quantity > 50:
             return ValidationResult(valid=False, error=f"จำนวนเยอะเกินไป (Max 50) - คุณใส่ {cmd.quantity}")

        # Validate Device specific values
        if cmd.target_type == TargetType.DEVICE and (cmd.device_type or cmd.new_value):
            dtype = (cmd.device_type or "").upper()
            val = cmd.new_value
            
            # If no new value to validate, skip
            if val is None:
                return ValidationResult(valid=True)
                
            # AC BTU Check
            if dtype == "AC" or "BTU" in (cmd.unit or "").upper():
                if val < 3000: # Assuming typo (e.g. 12 instead of 12000)
                     return ValidationResult(valid=False, error=f"BTU น้อยผิดปกติ ({val}) - กรุณาระบุเต็ม เช่น 12000")
                if val > EditValidator.LIMITS["AC_MAX_BTU"]:
                     return ValidationResult(valid=False, error=f"BTU สูงเกินจริง ({val}) - Max {EditValidator.LIMITS['AC_MAX_BTU']}")
            
            # Wattage Check (Generic)
            if dtype in ["HEATER", "SHOWER"] and val > 6000:
                return ValidationResult(valid=False, error=f"วัตต์เครื่องทำน้ำอุ่นสูงเกิน ({val}W) - ปกติไม่เกิน 4500-6000W")
                
            if dtype in ["LED", "LIGHT"] and val > EditValidator.LIMITS["MAX_WATTS_LIGHT"]:
                 return ValidationResult(valid=False, error=f"วัตต์หลอดไฟสูงเกิน ({val}W) - LED ปกติไม่เกิน 50-100W")

        return ValidationResult(valid=True)
