"""Circuit Grouping Module for Residential Electrical Design.

This module groups individual loads into circuits following Thai residential standards.

Philosophy:
- AC units: Always dedicated circuit per unit
- Water heaters: Dedicated RCBO circuit per unit
- Lighting: Group by floor (all bedroom lights → 1 circuit)
- Receptacles: Group by floor
- Kitchen appliances: Dedicated circuits for high-power items
- Switches: No dedicated circuit (part of lighting circuit)

Standards Reference:
- Thai EIT Standard (วสท.)
- NEC Article 210, 220
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from models.contracts import ElectricalLoad, LoadType, VoltageType
import logging
import math

logger = logging.getLogger(__name__)


class CircuitType(str, Enum):
    """Types of electrical circuits."""
    DEDICATED = "dedicated"      # Single load, own breaker
    LIGHTING = "lighting"        # Grouped lighting
    RECEPTACLE = "receptacle"    # Grouped receptacles
    HVAC = "hvac"               # AC dedicated
    WATER_HEATER = "water_heater"  # RCBO required
    KITCHEN = "kitchen"         # Kitchen dedicated
    MOTOR = "motor"             # Motor starter required
    GENERAL = "general"         # Other grouped loads


@dataclass
class GroupedCircuit:
    """A circuit containing one or more loads."""
    circuit_id: str
    circuit_name: str
    circuit_type: CircuitType
    floor: str
    loads: List[ElectricalLoad] = field(default_factory=list)
    total_watts: float = 0.0
    total_current: float = 0.0
    breaker_rating: int = 0
    breaker_poles: int = 1
    wire_size: str = "2.5"
    requires_rcbo: bool = False
    requires_gfci: bool = False
    notes: List[str] = field(default_factory=list)
    
    def add_load(self, load: ElectricalLoad):
        """Add a load to this circuit."""
        self.loads.append(load)
        self.total_watts += load.power_watts * load.quantity
    
    def calculate_current(self, voltage: float = 230.0, pf: float = 0.85) -> float:
        """Calculate total current for this circuit.
        
        Formula: I = P / (V × PF)  [Single phase]
        Thai Standard: 230V nominal
        
        Diversity Factor (วสท.):
        - RECEPTACLE: 0.4 (เต้ารับไม่ได้ใช้พร้อมกันทั้งหมด)
        - Others: 1.0 (dedicated circuits use full load)
        """
        if voltage <= 0:
            voltage = 230.0  # Default Thai residential
        
        # Apply diversity factor for receptacles
        if self.circuit_type == CircuitType.RECEPTACLE:
            diversity = 0.4  # 40% diversity for general outlets
            effective_watts = self.total_watts * diversity
        else:
            effective_watts = self.total_watts
        
        self.total_current = effective_watts / (voltage * pf)
        return self.total_current


class CircuitGrouper:
    """Groups individual loads into circuits following residential standards."""
    
    # Thai residential voltage (EIT Standard)
    VOLTAGE_1PH = 230.0   # 1-phase residential
    VOLTAGE_3PH = 400.0   # 3-phase commercial
    
    # Maximum loads per circuit
    MAX_LIGHTING_WATTS = 1500       # ~6.5A @ 230V
    MAX_RECEPTACLE_WATTS = 3000     # ~13A @ 230V
    MAX_OUTLETS_PER_CIRCUIT = 10    # NEC guideline
    
    # Dedicated circuit thresholds (watts)
    DEDICATED_THRESHOLD = 1500      # >1500W gets dedicated circuit
    
    # Load types that always need dedicated circuits
    DEDICATED_LOAD_TYPES = {
        'AC', 'HVAC', 'AIR', 'แอร์',                    # AC units
        'WATER_HEATER', 'น้ำอุ่น', 'HEATER',           # Water heaters
        'INDUCTION', 'เตา', 'RANGE', 'OVEN',           # Kitchen cooking
        'DRYER', 'อบผ้า',                              # Dryer
        'WASHER', 'ซัก',                               # Washer
        'PUMP', 'ปั๊ม',                                # Pumps (motor)
    }
    
    # Load types that need RCBO (wet location)
    RCBO_REQUIRED = {
        'WATER_HEATER', 'น้ำอุ่น', 'HEATER',
    }
    
    def __init__(self, default_voltage: float = 230.0):
        """Initialize circuit grouper.
        
        Args:
            default_voltage: Default voltage (230V for Thai residential)
        """
        self.voltage = default_voltage
        self.circuits: Dict[str, GroupedCircuit] = {}
        self._circuit_counter = 0
    
    def group_loads(
        self,
        loads: List[ElectricalLoad],
        project_floors: List[str] = None
    ) -> Dict[str, GroupedCircuit]:
        """Group loads into circuits following Thai residential standards.
        
        หลักการออกแบบที่ถูกต้อง (วสท.):
        1. แสงสว่าง+เต้ารับ ในห้องเดียวกัน = 1 วงจร (ใช้ switch ธรรมดา)
        2. แสงสว่างรวมทั้งชั้น = 1 breaker 
        3. Load ที่ต้องมี breaker แยก: แอร์, ปั๊มน้ำ, น้ำอุ่น, เตา Induction
        4. Load อื่นๆ (TV, ตู้เย็น, หม้อหุงข้าว) = ไม่มี breaker (ใช้ switch)
        5. ชั้น 1 และ ชั้น 2 แยก CT กัน
        
        Args:
            loads: List of individual loads
            project_floors: List of floor names (e.g., ["1", "2"])
            
        Returns:
            Dictionary of circuit_id -> GroupedCircuit
        """
        if project_floors is None:
            project_floors = self._detect_floors(loads)
        
        self.circuits = {}
        self._circuit_counter = 0
        
        # Step 1: Classify loads
        # Load ที่ต้องมี dedicated breaker (แอร์, ปั๊มน้ำ, น้ำอุ่น, เตา Induction)
        dedicated_breaker_loads = []
        # Load แสงสว่าง (รวมเป็น 1 breaker ต่อชั้น)
        lighting_loads = []
        # Load อื่นๆ (ไม่มี breaker - ใช้ switch)
        general_loads = []
        
        for load in loads:
            if self._needs_dedicated_breaker(load):
                dedicated_breaker_loads.append(load)
            elif load.load_type == LoadType.LIGHTING:
                lighting_loads.append(load)
            else:
                # TV, ตู้เย็น, หม้อหุงข้าว, เต้ารับ ฯลฯ = ไม่มี breaker แยก
                general_loads.append(load)
        
        # Step 2: Create dedicated breaker circuits (แอร์, ปั๊มน้ำ, น้ำอุ่น)
        for load in dedicated_breaker_loads:
            self._create_dedicated_circuit(load)
        
        # Step 3: Group ALL lighting per floor → 1 breaker per floor
        for floor in project_floors:
            floor_lighting = [l for l in lighting_loads 
                           if self._get_floor(l) == floor]
            if floor_lighting:
                self._create_lighting_circuit(floor_lighting, floor)
        
        # Step 4: Group ALL receptacles/general per floor → 1 breaker per floor
        # ตามมาตรฐาน วสท.: เต้ารับรวมทั้งชั้น ถ้าเกิน 15A ค่อยแยก
        for floor in project_floors:
            floor_general = [l for l in general_loads 
                           if self._get_floor(l) == floor]
            if floor_general:
                self._create_receptacle_circuit(floor_general, floor)
        
        # Step 5: Calculate all circuit parameters
        self._finalize_circuits()
        
        logger.info(f"Grouped {len(loads)} loads into {len(self.circuits)} circuits")
        return self.circuits
    
    def _needs_dedicated_breaker(self, load: ElectricalLoad) -> bool:
        """Check if load needs dedicated breaker.
        
        เฉพาะ Load เหล่านี้ต้องมี breaker แยก:
        - แอร์ (HVAC)
        - ปั๊มน้ำ (Motor)
        - เครื่องทำน้ำอุ่น (Water Heater) 
        - เตา Induction (>3000W)
        
        Load อื่นๆ ใช้ switch ธรรมดา ไม่มี breaker
        """
        # HVAC (แอร์) - always dedicated
        if load.load_type == LoadType.HVAC:
            return True
        
        # Motor (ปั๊มน้ำ) - always dedicated
        if load.load_type == LoadType.MOTOR:
            return True
        
        # Check by keywords
        load_name_upper = load.name.upper()
        
        # Water heater
        for keyword in ['WATER_HEATER', 'น้ำอุ่น', 'HEATER']:
            if keyword in load_name_upper:
                return True
        
        # Induction stove (>3000W)
        for keyword in ['INDUCTION', 'เตา']:
            if keyword in load_name_upper and load.power_watts >= 3000:
                return True
        
        # Pump
        for keyword in ['PUMP', 'ปั๊ม']:
            if keyword in load_name_upper:
                return True
        
        return False
        if load.power_watts * load.quantity >= self.DEDICATED_THRESHOLD:
            return True
        
        # Check by type keywords
        load_name_upper = load.name.upper()
        for keyword in self.DEDICATED_LOAD_TYPES:
            if keyword in load_name_upper:
                return True
        
        # HVAC and Motor types always dedicated
        if load.load_type in [LoadType.HVAC, LoadType.MOTOR]:
            return True
        
        return False
    
    def _needs_rcbo(self, load: ElectricalLoad) -> bool:
        """Check if load needs RCBO (wet location)."""
        load_name_upper = load.name.upper()
        for keyword in self.RCBO_REQUIRED:
            if keyword in load_name_upper:
                return True
        return False
    
    def _get_floor(self, load: ElectricalLoad) -> str:
        """Extract floor from load location."""
        if hasattr(load, 'location') and load.location:
            return load.location.floor or "1"
        return "1"  # Default to floor 1
    
    def _get_room(self, load: ElectricalLoad) -> str:
        """Extract room from load location."""
        if hasattr(load, 'location') and load.location:
            return load.location.room or "Unknown"
        return "Unknown"
    
    def _detect_floors(self, loads: List[ElectricalLoad]) -> List[str]:
        """Detect all floors from loads."""
        floors = set()
        for load in loads:
            floors.add(self._get_floor(load))
        return sorted(list(floors)) or ["1"]
    
    def _next_circuit_id(self, prefix: str = "CKT") -> str:
        """Generate next circuit ID."""
        self._circuit_counter += 1
        return f"{prefix}-{self._circuit_counter:02d}"
    
    def _create_dedicated_circuit(self, load: ElectricalLoad):
        """Create dedicated circuit for a single load."""
        circuit_id = self._next_circuit_id("DED")
        
        # Determine circuit type
        if load.load_type == LoadType.HVAC:
            circuit_type = CircuitType.HVAC
            breaker_poles = 2  # AC needs 2-pole
        elif self._needs_rcbo(load):
            circuit_type = CircuitType.WATER_HEATER
            breaker_poles = 2  # Water heater 2-pole with RCBO
        elif load.load_type == LoadType.MOTOR:
            circuit_type = CircuitType.MOTOR
            breaker_poles = 2
        else:
            circuit_type = CircuitType.DEDICATED
            # 2-pole for high power (>2000W), 1-pole otherwise
            breaker_poles = 2 if load.power_watts > 2000 else 1
        
        circuit = GroupedCircuit(
            circuit_id=circuit_id,
            circuit_name=f"{load.name}",
            circuit_type=circuit_type,
            floor=self._get_floor(load),
            breaker_poles=breaker_poles,
            requires_rcbo=self._needs_rcbo(load)
        )
        circuit.add_load(load)
        
        # Add notes
        if circuit.requires_rcbo:
            circuit.notes.append("ต้องใช้ RCBO 30mA (ป้องกันไฟดูด)")
        if load.load_type == LoadType.MOTOR:
            circuit.notes.append("ต้องใช้ Motor Starter + Overload")
        
        self.circuits[circuit_id] = circuit
    
    def _create_lighting_circuit(self, loads: List[ElectricalLoad], floor: str):
        """Create grouped lighting circuit for a floor."""
        if not loads:
            return
        
        circuit_id = self._next_circuit_id("LT")
        circuit = GroupedCircuit(
            circuit_id=circuit_id,
            circuit_name=f"ไฟแสงสว่าง ชั้น {floor}",
            circuit_type=CircuitType.LIGHTING,
            floor=floor,
            breaker_poles=1
        )
        
        for load in loads:
            circuit.add_load(load)
        
        # Check if need to split
        if circuit.total_watts > self.MAX_LIGHTING_WATTS:
            circuit.notes.append(
                f"⚠️ โหลดสูง ({circuit.total_watts}W) พิจารณาแยกวงจร"
            )
        
        circuit.notes.append(f"รวม {len(loads)} จุดไฟ")
        self.circuits[circuit_id] = circuit
    
    def _create_receptacle_circuit(self, loads: List[ElectricalLoad], floor: str):
        """Create grouped receptacle circuit for a floor.
        
        Auto-splits into multiple circuits if total outlets > 10.
        Thai residential standard: max 10 outlets per 20A circuit.
        """
        if not loads:
            return
        
        # Split loads into chunks of max 10 outlets each
        MAX_PER_CIRCUIT = self.MAX_OUTLETS_PER_CIRCUIT  # 10
        chunks = []
        current_chunk = []
        current_count = 0
        
        for load in loads:
            qty = load.quantity if hasattr(load, 'quantity') else 1
            if current_count + qty > MAX_PER_CIRCUIT and current_chunk:
                # Current chunk is full, start new one
                chunks.append(current_chunk)
                current_chunk = [load]
                current_count = qty
            else:
                current_chunk.append(load)
                current_count += qty
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Create separate circuits for each chunk
        for i, chunk in enumerate(chunks):
            circuit_id = self._next_circuit_id("RC")
            suffix = f" ({i+1})" if len(chunks) > 1 else ""
            
            circuit = GroupedCircuit(
                circuit_id=circuit_id,
                circuit_name=f"เต้ารับ ชั้น {floor}{suffix}",
                circuit_type=CircuitType.RECEPTACLE,
                floor=floor,
                breaker_poles=1
            )
            
            for load in chunk:
                circuit.add_load(load)
            
            total_outlets = sum(l.quantity for l in chunk)
            circuit.notes.append(f"รวม {total_outlets} จุด")
            
            if len(chunks) > 1:
                circuit.notes.append(f"แยกวงจร {i+1}/{len(chunks)}")
            
            self.circuits[circuit_id] = circuit
    
    def _create_room_circuit(self, loads: List[ElectricalLoad], room: str, floor: str):
        """Create circuit for general loads in a room (no dedicated breaker).
        
        วงจรนี้ไม่มี breaker แยก - ใช้ switch ธรรมดา
        เป็นการรวมเต้ารับ + เครื่องใช้ไฟฟ้าทั่วไปในห้องเดียวกัน
        """
        if not loads:
            return
        
        circuit_id = self._next_circuit_id("RM")
        circuit = GroupedCircuit(
            circuit_id=circuit_id,
            circuit_name=f"วงจรทั่วไป {room}",
            circuit_type=CircuitType.GENERAL,
            floor=floor,
            breaker_poles=0  # 0 = ไม่มี breaker (ใช้ switch)
        )
        
        for load in loads:
            circuit.add_load(load)
        
        circuit.notes.append(f"ใช้ switch ธรรมดา (ไม่มี breaker แยก)")
        circuit.notes.append(f"รวม {len(loads)} อุปกรณ์")
        self.circuits[circuit_id] = circuit

    def _add_to_general_circuit(self, load: ElectricalLoad):
        """Add load to general circuit."""
        floor = self._get_floor(load)
        general_id = f"GEN-{floor}"
        
        if general_id not in self.circuits:
            self.circuits[general_id] = GroupedCircuit(
                circuit_id=general_id,
                circuit_name=f"วงจรทั่วไป ชั้น {floor}",
                circuit_type=CircuitType.GENERAL,
                floor=floor,
                breaker_poles=1
            )
        
        self.circuits[general_id].add_load(load)
    
    def _finalize_circuits(self):
        """Calculate final parameters for all circuits."""
        for circuit in self.circuits.values():
            # Calculate current (Thai 230V standard)
            circuit.calculate_current(voltage=self.VOLTAGE_1PH)
            
            # Select breaker rating
            circuit.breaker_rating = self._select_breaker_rating(
                circuit.total_current,
                circuit.circuit_type
            )
            
            # Select wire size (ส่ง circuit_type เพื่อกำหนดขนาดต่ำสุด)
            circuit.wire_size = self._select_wire_size(
                circuit.total_current,
                circuit.breaker_rating,
                circuit.circuit_type
            )
    
    def _select_breaker_rating(
        self,
        current: float,
        circuit_type: CircuitType
    ) -> int:
        """Select appropriate breaker rating.
        
        Standard ratings (NEC 240.6): 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100
        
        Thai Residential Rules (วสท.):
        - RECEPTACLE: 16A or 20A max (เต้ารับบ้านพัก)
        - LIGHTING: 15A or 20A max
        - Others: select based on load current
        """
        standard_ratings = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
        
        # Rule: Receptacle circuits use 16A or 20A only
        if circuit_type == CircuitType.RECEPTACLE:
            allowed_ratings = [16, 20]  # Thai standard: 16A preferred
            for rating in allowed_ratings:
                if rating >= current:
                    return rating
            return 20  # Max for receptacle
        
        # Apply continuous load factor (125%) if applicable
        if circuit_type in [CircuitType.LIGHTING, CircuitType.HVAC]:
            required = current * 1.25
        else:
            required = current
        
        # Find next standard rating
        for rating in standard_ratings:
            if rating >= required:
                return rating
        
        return 100  # Maximum
    
    def _select_wire_size(
        self,
        current: float,
        breaker_rating: int,
        circuit_type: CircuitType = None
    ) -> str:
        """Select appropriate wire size (mm²).
        
        Thai standard wire sizes: 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50
        
        ตารางเลือกสายไฟตามกระแส (มาตรฐาน วสท.):
        - THW 1.5 mm² = 15A max (เฉพาะวงจรไฟฟ้าแสงสว่างเท่านั้น)
        - THW 2.5 mm² = 21A max (วงจรปลั๊ก/แอร์/ทั่วไป ขั้นต่ำ)
        - THW 4.0 mm² = 28A max (ใช้กับ breaker 25A)
        - THW 6.0 mm² = 36A max (ใช้กับ breaker 30-35A)
        - THW 10 mm² = 50A max (ใช้กับ breaker 40-50A)
        - THW 16 mm² = 68A max (ใช้กับ breaker 60A)
        - THW 25 mm² = 89A max (ใช้กับ breaker 70-80A)
        - THW 35 mm² = 111A max (ใช้กับ breaker 100A)
        
        หลักเกณฑ์:
        - วงจรไฟฟ้าแสงสว่าง (Lighting): 1.5mm² ได้
        - วงจรอื่นๆ (ปลั๊ก, แอร์, น้ำอุ่น): ขั้นต่ำ 2.5mm²
        """
        # Minimum wire size based on circuit type
        # วงจรปลั๊ก/เครื่องใช้ไฟฟ้า ต้องใช้ 2.5mm² ขั้นต่ำ (มาตรฐาน วสท.)
        is_lighting_only = circuit_type == CircuitType.LIGHTING
        min_wire_size = "1.5" if is_lighting_only else "2.5"
        
        # Wire size by current (Thai EIT standard)
        if current <= 15:
            wire = "1.5"
        elif current <= 21:
            wire = "2.5"
        elif current <= 28:
            wire = "4"
        elif current <= 36:
            wire = "6"
        elif current <= 50:
            wire = "10"
        elif current <= 68:
            wire = "16"
        elif current <= 89:
            wire = "25"
        else:
            wire = "35"
        
        # Apply minimum (ใช้ค่าที่ใหญ่กว่า)
        wire_sizes = ["1.5", "2.5", "4", "6", "10", "16", "25", "35"]
        min_idx = wire_sizes.index(min_wire_size)
        wire_idx = wire_sizes.index(wire)
        
        return wire_sizes[max(min_idx, wire_idx)]
    
    def get_circuit_summary(self) -> Dict[str, Any]:
        """Get summary of all circuits."""
        summary = {
            "total_circuits": len(self.circuits),
            "dedicated_circuits": 0,
            "grouped_circuits": 0,
            "total_watts": 0,
            "total_current": 0,
            "by_type": {},
            "by_floor": {},
            "circuits": []
        }
        
        for circuit in self.circuits.values():
            summary["total_watts"] += circuit.total_watts
            summary["total_current"] += circuit.total_current
            
            if circuit.circuit_type == CircuitType.DEDICATED:
                summary["dedicated_circuits"] += 1
            else:
                summary["grouped_circuits"] += 1
            
            # Count by type
            type_name = circuit.circuit_type.value
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = 0
            summary["by_type"][type_name] += 1
            
            # Count by floor
            if circuit.floor not in summary["by_floor"]:
                summary["by_floor"][circuit.floor] = 0
            summary["by_floor"][circuit.floor] += 1
            
            # Add circuit details
            summary["circuits"].append({
                "circuit_id": circuit.circuit_id,
                "id": circuit.circuit_id,  # Keep for backwards compatibility
                "name": circuit.circuit_name,
                "circuit_type": circuit.circuit_type.value,
                "type": circuit.circuit_type.value,  # Keep for backwards compatibility
                "floor": circuit.floor,
                "total_watts": circuit.total_watts,
                "watts": circuit.total_watts,  # Keep for backwards compatibility
                "total_current": round(circuit.total_current, 2),
                "current": round(circuit.total_current, 2),  # Keep for backwards compatibility
                "breaker_rating": circuit.breaker_rating,
                "breaker_poles": circuit.breaker_poles,
                "breaker": f"{circuit.breaker_rating}A/{circuit.breaker_poles}P",
                "wire_size": circuit.wire_size,
                "wire": f"THW {circuit.wire_size}mm²",
                "loads": len(circuit.loads),
                "rcbo": circuit.requires_rcbo,
                "notes": circuit.notes
            })
        
        return summary


# Global instance
_circuit_grouper: Optional[CircuitGrouper] = None


def get_circuit_grouper() -> CircuitGrouper:
    """Get the global circuit grouper instance."""
    global _circuit_grouper
    if _circuit_grouper is None:
        _circuit_grouper = CircuitGrouper()
    return _circuit_grouper
