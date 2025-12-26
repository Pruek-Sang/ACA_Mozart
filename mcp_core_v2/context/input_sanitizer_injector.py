"""
Input Sanitizer Injector
========================
PRE-pipeline validator for sanity checking user inputs.
Blocks impossible values, warns on unusual values.

Follows วสท. 2564 / IEC 60364 standards.
Designed for Thai residential (บ้านพักอาศัย 1-3 ชั้น).

Author: Mozart AI Team
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input sanitization."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    error_count: int = 0


class InputSanitizerInjector:
    """
    PRE-pipeline validator for sanity checking inputs.
    Configurable limits stored as class constants.
    
    Usage:
        sanitizer = InputSanitizerInjector()
        result = sanitizer.sanitize(request)
        if result.errors:
            return early with errors
    """
    
    # ════════════════════════════════════════════════════════════════════════
    # CONFIGURABLE DEVICE LIMITS (Wattage by Type)
    # Format: "DEVICE_TYPE": (min_watts, max_watts, warn_watts)
    # ════════════════════════════════════════════════════════════════════════
    DEVICE_LIMITS = {
        # Lighting
        "LED": (3, 500, 50),
        "DOWNLIGHT": (5, 100, 30),
        "LIGHTING": (3, 500, 100),
        "NEON": (18, 72, 36),
        
        # Appliances
        "HEATER": (3500, 10000, 6000),
        "WATER_HEATER": (3500, 10000, 6000),
        "น้ำอุ่น": (3500, 10000, 6000),
        "INDUCTION": (1000, 5000, 3500),
        "เตาไฟฟ้า": (1000, 5000, 3500),
        "MICROWAVE": (700, 1500, 1200),
        "ไมโครเวฟ": (700, 1500, 1200),
        "REFRIGERATOR": (100, 500, 300),
        "ตู้เย็น": (100, 500, 300),
        "KETTLE": (1500, 3000, 2500),
        "กาต้มน้ำ": (1500, 3000, 2500),
        "RICE_COOKER": (500, 1500, 1000),
        "หม้อหุงข้าว": (500, 1500, 1000),
        
        # HVAC
        "AC": (800, 7000, 4000),
        "แอร์": (800, 7000, 4000),
        "FAN": (30, 150, 100),
        "พัดลม": (30, 150, 100),
        "EXHAUST_FAN": (15, 50, 30),
        "พัดลมดูดอากาศ": (15, 50, 30),
        
        # Motors
        "PUMP": (250, 2000, 1500),
        "ปั๊มน้ำ": (250, 2000, 1500),
        
        # Receptacles
        "RECEPTACLE": (180, 3600, 2000),
        "SOCKET": (180, 3600, 2000),
        "เต้ารับ": (180, 3600, 2000),
        
        # EV (for future)
        "EV_CHARGER": (1800, 7400, 3700),
    }
    
    # ════════════════════════════════════════════════════════════════════════
    # DISTANCE LIMITS (meters)
    # Format: (min_m, max_m, warn_m)
    # ════════════════════════════════════════════════════════════════════════
    DISTANCE_LIMITS = {
        "service_distance_m": (1, 100, 30),        # มิเตอร์ → MDB
        "branch_distance_m": (1, 100, 50),         # MDB → วงจรย่อย
        "distance_to_transformer": (1, 1000, 200), # หม้อแปลง → บ้าน
    }
    
    # ════════════════════════════════════════════════════════════════════════
    # PROJECT LIMITS
    # ════════════════════════════════════════════════════════════════════════
    MAX_POWER_WATTS_PER_LOAD = 45_000    # 45kW per single load
    MAX_QUANTITY_PER_LOAD = 100          # per load item
    MAX_TOTAL_LOAD_1PH = 50_000          # 50kW for 1 phase (200A)
    MAX_TOTAL_LOAD_3PH = 150_000         # 150kW for 3 phase
    MAX_LOADS_COUNT = 200                # total loads in project
    MAX_OUTLETS_PER_ROOM = 30            # เต้ารับต่อห้อง
    MAX_LIGHTS_PER_ROOM = 30             # ดวงไฟต่อห้อง
    MAX_FLOORS = 10                      # จำนวนชั้น
    MAX_ROOM_SQM = 500                   # ขนาดห้อง
    MAX_CIRCUITS = 50                    # วงจรทั้งหมด
    
    # ════════════════════════════════════════════════════════════════════════
    # PERSONALITY MESSAGES 🎭
    # ════════════════════════════════════════════════════════════════════════
    ERROR_MESSAGES_FUN = {
        "nuclear_load": [
            "❌ สร้างบ้านนะเจ้าค่ะ ไม่ใช่โรงงานนิวเคลียร์ค่า! 🏠☢️",
            "❌ โหลดขนาดนี้... ต้องขอสัมปทานจาก กฟผ. ก่อนค่ะ ⚡",
        ],
        "too_many_outlets": [
            "❌ เต้ารับ {n} จุด!? นี่บ้านหรือสถานีอวกาศค่ะ? 🚀",
            "❌ จำนวนนี้เกินจริงไปหน่อยนะเจ้าค่ะ 🤔",
        ],
        "long_distance": [
            "❌ ระยะ {n}m!? บ้านอยู่บนดาวอังคารหรือค่ะ? 🪐",
            "❌ ระยะไกลขนาดนี้ ต้องใช้สาย MV แล้วค่ะ 📏",
        ],
        "negative_value": [
            "❌ ค่าติดลบ? ฟิสิกส์ไม่ทำงานแบบนั้นค่ะ 🧪",
            "❌ ค่าติดลบใช้ไม่ได้ค่ะ ลองใส่ใหม่นะเจ้าค่ะ",
        ],
        "led_too_big": [
            "❌ LED {n}W!? ไม่มี LED ขนาดนี้ในจักรวาลค่ะ 💡😅",
        ],
    }
    
    MULTI_ERROR_MESSAGES = [
        "😅 พักดื่มเบียร์เย็นๆ หน่อยมั้ยค่ะนายท่าน? 🍺🍺🍺",
        "😓 ลองพักสักครู่แล้วค่อยกลับมาใหม่นะเจ้าค่ะ ☕",
        "🤯 Input เยอะจัง... ช้าๆ ได้เปรียบค่ะ",
    ]
    
    WARN_MESSAGES = {
        "high_load": "⚠️ กำลังไฟ {name} สูงผิดปกติ ({n}W) ตรวจสอบอีกครั้งนะเจ้าค่ะ",
        "long_wire": "⚠️ ระยะ {n}m ยาวมาก VD อาจสูง ควรใช้สายขนาดใหญ่ขึ้น",
    }
    
    # ════════════════════════════════════════════════════════════════════════
    # MAIN SANITIZE METHOD
    # ════════════════════════════════════════════════════════════════════════
    def sanitize(self, request: Any) -> ValidationResult:
        """
        Validate all inputs before pipeline processing.
        
        Args:
            request: DesignRequest object
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        loads = getattr(request, 'loads', [])
        site_context = getattr(request, 'site_context', {}) or {}
        
        # 1. Per-load validation
        for load in loads:
            self._validate_load(load, errors, warnings)
        
        # 2. Total project validation
        self._validate_project_totals(loads, request, errors, warnings)
        
        # 3. Distance validation
        self._validate_distances(request, site_context, errors, warnings)
        
        # 4. Sanity checks
        self._validate_sanity(loads, errors)
        
        # 5. Multi-error message
        if len(errors) >= 3:
            errors.append(random.choice(self.MULTI_ERROR_MESSAGES))
        
        logger.info(f"InputSanitizer: {len(errors)} errors, {len(warnings)} warnings")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            error_count=len(errors)
        )
    
    # ════════════════════════════════════════════════════════════════════════
    # PRIVATE VALIDATION METHODS
    # ════════════════════════════════════════════════════════════════════════
    def _validate_load(self, load: Any, errors: List[str], warnings: List[str]):
        """Validate individual load."""
        name = getattr(load, 'name', 'Unknown')
        power = getattr(load, 'power_watts', 0)
        quantity = getattr(load, 'quantity', 1)
        
        # Type check
        if not isinstance(power, (int, float)):
            errors.append(f"❌ {name}: กำลังไฟต้องเป็นตัวเลข ไม่ใช่ '{power}'")
            return
        
        # Negative check
        if power <= 0:
            errors.append(random.choice(self.ERROR_MESSAGES_FUN["negative_value"]))
            return
        
        # Quantity check
        if quantity <= 0 or quantity > self.MAX_QUANTITY_PER_LOAD:
            errors.append(f"❌ {name}: จำนวน {quantity} ไม่ถูกต้อง (1-{self.MAX_QUANTITY_PER_LOAD})")
            return
        
        # Device-specific limits
        device_type = self._detect_device_type(name)
        limits = self.DEVICE_LIMITS.get(device_type)
        
        if limits:
            _, max_w, warn_w = limits
            if power > max_w:
                if device_type in ("LED", "DOWNLIGHT", "LIGHTING"):
                    errors.append(random.choice(self.ERROR_MESSAGES_FUN["led_too_big"]).format(n=power))
                else:
                    errors.append(f"❌ {name}: {power}W เกินขีดจำกัด {max_w}W")
            elif power > warn_w:
                warnings.append(self.WARN_MESSAGES["high_load"].format(name=name, n=power))
        
        # Absolute max check
        total_power = power * quantity
        if total_power > self.MAX_POWER_WATTS_PER_LOAD:
            errors.append(random.choice(self.ERROR_MESSAGES_FUN["nuclear_load"]))
    
    def _validate_project_totals(self, loads: List, request: Any, errors: List[str], warnings: List[str]):
        """Validate project-wide totals."""
        # Load count
        if len(loads) > self.MAX_LOADS_COUNT:
            errors.append(f"❌ จำนวนโหลด {len(loads)} เกินขีดจำกัด {self.MAX_LOADS_COUNT}")
        
        # Total power
        total_power = sum(
            getattr(l, 'power_watts', 0) * getattr(l, 'quantity', 1)
            for l in loads
        )
        
        voltage = getattr(request, 'service_voltage', '230V_1PH')
        is_3phase = '3PH' in str(voltage)
        max_power = self.MAX_TOTAL_LOAD_3PH if is_3phase else self.MAX_TOTAL_LOAD_1PH
        
        if total_power > max_power:
            msg = random.choice(self.ERROR_MESSAGES_FUN["nuclear_load"])
            errors.append(f"{msg}\n   (โหลดรวม {total_power/1000:.1f}kW เกิน {max_power/1000}kW)")
        
        # Duplicate IDs
        ids = [getattr(l, 'id', '') for l in loads]
        if len(ids) != len(set(ids)):
            errors.append("❌ มี Load ID ซ้ำกัน กรุณาตรวจสอบ")
    
    def _validate_distances(self, request: Any, site_context: Dict, errors: List[str], warnings: List[str]):
        """Validate distance values."""
        # Service distance (meter to MDB)
        service_dist = getattr(request, 'service_distance_m', None)
        if service_dist is not None:
            self._check_distance(service_dist, "service_distance_m", "มิเตอร์→MDB", errors, warnings)
        
        # Transformer distance
        transformer_dist = site_context.get('distance_to_transformer')
        if transformer_dist is not None:
            # Handle string categories like "50_100m"
            if isinstance(transformer_dist, str):
                pass  # Category is OK
            elif isinstance(transformer_dist, (int, float)):
                self._check_distance(transformer_dist, "distance_to_transformer", "หม้อแปลง", errors, warnings)
        
        # Branch distances in loads
        for load in getattr(request, 'loads', []):
            branch_dist = getattr(load, 'branch_distance_m', None)
            if branch_dist is not None:
                self._check_distance(branch_dist, "branch_distance_m", f"วงจร {load.name}", errors, warnings)
    
    def _check_distance(self, value: Any, field: str, label: str, errors: List[str], warnings: List[str]):
        """Check a single distance value."""
        if not isinstance(value, (int, float)):
            errors.append(f"❌ ระยะ {label} ต้องเป็นตัวเลข")
            return
        
        if value <= 0:
            errors.append(random.choice(self.ERROR_MESSAGES_FUN["negative_value"]))
            return
        
        limits = self.DISTANCE_LIMITS.get(field, (1, 1000, 200))
        _, max_m, warn_m = limits
        
        if value > max_m:
            errors.append(random.choice(self.ERROR_MESSAGES_FUN["long_distance"]).format(n=value))
        elif value > warn_m:
            warnings.append(self.WARN_MESSAGES["long_wire"].format(n=value))
    
    def _validate_sanity(self, loads: List, errors: List[str]):
        """Basic sanity checks."""
        # Count outlets per room
        room_outlets = {}
        room_lights = {}
        
        for load in loads:
            location = getattr(load, 'location', None)
            if location:
                room = getattr(location, 'room', 'unknown')
                name = getattr(load, 'name', '').upper()
                qty = getattr(load, 'quantity', 1)
                
                if 'SOCKET' in name or 'RECEPTACLE' in name or 'เต้ารับ' in name:
                    room_outlets[room] = room_outlets.get(room, 0) + qty
                elif 'LED' in name or 'LIGHT' in name or 'ไฟ' in name:
                    room_lights[room] = room_lights.get(room, 0) + qty
        
        for room, count in room_outlets.items():
            if count > self.MAX_OUTLETS_PER_ROOM:
                errors.append(random.choice(self.ERROR_MESSAGES_FUN["too_many_outlets"]).format(n=count))
        
        for room, count in room_lights.items():
            if count > self.MAX_LIGHTS_PER_ROOM:
                errors.append(f"❌ {room}: ดวงไฟ {count} ดวง เกินขีดจำกัด {self.MAX_LIGHTS_PER_ROOM}")
    
    def _detect_device_type(self, name: str) -> str:
        """Detect device type from name."""
        name_upper = name.upper()
        for key in self.DEVICE_LIMITS:
            if key.upper() in name_upper:
                return key
        return "OTHER"


# ════════════════════════════════════════════════════════════════════════════
# IDLE TIMEOUT HANDLER (for RAG service)
# ════════════════════════════════════════════════════════════════════════════
IDLE_MESSAGES = [
    "💤 zzzz... เจ้าค่ะหลับไปแล้วค่ะ... พิมพ์อะไรมาปลุกได้นะ 😴",
    "😴 มีอะไรให้ช่วยมั้ยค่ะ... *หาว* 🥱",
    "💤 ง่วงจังเลยค่ะ... นายท่านยังอยู่มั้ยค่ะ? 😪",
]

def get_idle_message() -> str:
    """Get random idle timeout message."""
    return random.choice(IDLE_MESSAGES)
