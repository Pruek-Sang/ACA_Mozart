# 🔧 Implementation Plan - MCP Core v2 Calculation Fixes

**Created by**: Laplacia  
**Date**: 2025-11-27  
**Principle**: **ZERO REGRESSION (non-calculation)** + **100% ACCURACY (calculation)**

---

## 🎯 Core Principles

### **1. Calculation Code** (เปลี่ยนได้):
- ✅ สูตรคำนวณ (Load, VD, Ampacity, Derating)
- ✅ ค่า Constants ตามมาตรฐาน (NEC, มอก., IEC)
- ✅ Validation Rules
- ✅ Correction Factors

**Reason**: ต้องการ **ความถูกต้อง 100%**

### **2. Non-Calculation Code** (ห้ามแตะ):
- ❌ File structure
- ❌ Import statements (ยกเว้น missing imports)
- ❌ Function signatures (ยกเว้นเพิ่ม parameters)
- ❌ Global instances
- ❌ Logging logic

**Reason**: **ห้าม Regression** เด็ดขาด

### **3. Need Approval** (บอกเหตุผลก่อน):
- ⚠️ เปลี่ยน data models
- ⚠️ เพิ่ม dependencies
- ⚠️ แก้ pipeline flow

---

## 📋 Calculation Rules from Catalog

### **VALIDATION_RULE** (11 รายการ):

#### **VR001: Voltage Drop - Single Phase**
```json
{
  "rule_id": "VR004",
  "rule_name": "Voltage drop limit 3%",
  "logic": {
    "max_voltage_drop_pct": 3,
    "base_voltage_v": 230,
    "validation_type": "voltage_drop_check"
  },
  "standard_reference": "IEC 60364-5-52 / Voltage drop"
}
```
**Formula Requirements**:
```
VD% = (VD_volt / V_nominal) × 100 ≤ 3%

Single Phase:
VD_volt = 2 × L_m × I_a × (R × cosθ + X × sinθ) / 1000

Where:
- L_m: ความยาวสาย (เมตร, one-way)
- I_a: กระแสไฟฟ้า (Ampere)
- R: ความต้านทาน (Ω/km @ operating temperature)
- X: รีแอคแตนซ์ (Ω/km)
- cosθ: Power factor
- sinθ: √(1 - cos²θ)
```

#### **VR002: Voltage Drop - Three Phase**
```json
{
  "rule_id": "VAL-VD-400V-3P",
  "logic": {
    "max_voltage_drop_pct": 5,
    "validation_type": "voltage_drop_check"
  },
  "formula": {
    "type": "VOLTAGE_DROP_3P",
    "requires": ["I_a", "L_m", "R_ohm_per_km_20C", "alpha_per_C", "delta_T_C", "V_ll"]
  }
}
```
**Formula**:
```
VD_volt = √3 × L_m × I_a × (R × cosθ + X × sinθ) / 1000
```

#### **VR003: Circuit Loading ≤ 80%**
```json
{
  "rule_id": "VR005",
  "logic": {
    "max_load_pct_of_breaker": 80,
    "error_level": "WARNING"
  }
}
```

#### **VR004: Temperature-Dependent Resistance**
**Required Parameters**:
- `R_ohm_per_km_20C`: ความต้านทานที่ 20°C
- `alpha_per_C`: Temperature coefficient (copper = 0.00393 /°C)
- `delta_T_C`: ΔT = Operating temp - 20°C

**Formula**:
```python
R_operating = R_20C × (1 + alpha × ΔT)

# Example:
# R_20C = 7.41 Ω/km (THW 2.5mm²)
# Operating temp = 75°C
# ΔT = 75 - 20 = 55°C
# R_75C = 7.41 × (1 + 0.00393 × 55) = 7.41 × 1.216 = 9.01 Ω/km
```

---

### **DERATING_FACTOR** (4 ชนิด):

#### **DF001: Conductor Grouping**
```json
{
  "factor_id": "DF001",
  "derating_type": "conductor_grouping",
  "standard_reference": "IEC 60364-5-52 / EIT",
  "table": [
    {"min_conductors": 1, "max_conductors": 3, "factor": 1.0},
    {"min_conductors": 4, "max_conductors": 6, "factor": 0.8},
    {"min_conductors": 7, "max_conductors": 9, "factor": 0.7},
    {"min_conductors": 10, "max_conductors": 20, "factor": 0.5},
    {"min_conductors": 21, "max_conductors": 30, "factor": 0.4}
  ]
}
```

#### **DF002: Ambient Temperature**
```json
{
  "factor_id": "DF002",
  "derating_type": "ambient_temperature",
  "standard_reference": "NEC Table 310.15(B)(2)(a)",
  "base_temperature_c": 30,
  "table": [
    {"ambient_temp_c": 30, "derating_factor_75c": 1.0},
    {"ambient_temp_c": 35, "derating_factor_75c": 0.94},
    {"ambient_temp_c": 40, "derating_factor_75c": 0.88},
    {"ambient_temp_c": 45, "derating_factor_75c": 0.82},
    {"ambient_temp_c": 50, "derating_factor_75c": 0.75}
  ]
}
```

#### **DF003: Soil Thermal Resistivity**
```json
{
  "factor_id": "DF003",
  "derating_type": "soil_burial",
  "table": [
    {"soil_resistivity_km_per_w": 1.0, "factor": 1.0},
    {"soil_resistivity_km_per_w": 1.5, "factor": 0.9},
    {"soil_resistivity_km_per_w": 2.0, "factor": 0.8},
    {"soil_resistivity_km_per_w": 2.5, "factor": 0.7}
  ]
}
```

#### **DF004: Thermal Insulation**
```json
{
  "factor_id": "DF004",
  "derating_type": "thermal_insulation",
  "table": [
    {"insulation_thickness_mm": 0, "derating_factor": 1.0},
    {"insulation_thickness_mm": 50, "derating_factor": 0.85},
    {"insulation_thickness_mm": 100, "derating_factor": 0.75},
    {"insulation_thickness_mm": 200, "derating_factor": 0.6}
  ]
}
```

---

## 🔍 Current Code Analysis

### **File 1: `core/load_calculator.py`**

#### **Issues Found**:

1. **❌ Missing `Optional` import** (Line 24)
   ```python
   def calculate_load_current(
       self, 
       load: ElectricalLoad,
       power_factor: Optional[float] = None  # ← Optional not imported
   )
   ```

2. **⚠️ Simplified demand current** (Line 136)
   ```python
   demand_current = demand_va / 120  # ← ใช้ 120V แทนที่จะใช้ voltage จริง
   ```
   **Should be**:
   ```python
   # Get actual voltage from load/panel
   voltage = self._get_voltage_from_type(panel.voltage)
   demand_current = demand_va / voltage
   ```

#### **Calculation Rules to Add**:
- ✅ Load demand factors ตาม NEC 220.42
- ✅ Receptacle demand factors ตาม NEC 220.44
- ⚠️ ต้องใช้ voltage จริง ไม่ใช่ hardcoded 120V

---

### **File 2: `core/wire_sizer.py`**

#### **Issues Found**:

1. **❌ Missing temperature correction**
   - ใช้ resistance ที่ temperature คงที่
   - ไม่มีการคำนวณ `R_operating = R_20C × (1 + α × ΔT)`

2. **❌ Missing derating factors**
   - ไม่มี ambient temperature correction (DF002)
   - ไม่มี conductor grouping correction (DF001)
   - Code มีตัวแปร `temperature_rating` และ `adjust ampacity` แต่ไม่ได้ใช้งาน

3. **⚠️ Voltage drop ใช้ R อย่างเดียว**
   ```python
   # Line 146-147
   total_resistance = (resistance_per_1000 * distance_feet * 2) / 1000
   voltage_drop = current * total_resistance
   ```
   **Should include reactance**:
   ```python
   Z_effective = R * cos(θ) + X * sin(θ)
   voltage_drop = current * Z_effective * 2 * distance / 1000
   ```

#### **Calculation Rules to Implement**:

**Rule 1: Temperature-Dependent Resistance**
```python
def _calculate_resistance_at_temp(
    self,
    r_20c: float,
    operating_temp_c: float,
    conductor_material: str = 'copper'
) -> float:
    """คำนวณความต้านทานที่อุณหภูมิใช้งาน"""
    alpha = 0.00393 if conductor_material == 'copper' else 0.00403  # aluminum
    delta_t = operating_temp_c - 20
    return r_20c * (1 + alpha * delta_t)
```

**Rule 2: Derating Factor Application**
```python
def _apply_derating_factors(
    self,
    base_ampacity: float,
    ambient_temp_c: float = 30,
    num_conductors: int = 3,
    thermal_insulation_mm: float = 0
) -> tuple[float, dict]:
    """
    ใช้ Derating Factors ทั้งหมด
    Returns: (derated_ampacity, factors_used)
    """
    # DF002: Ambient Temperature
    temp_factor = self._get_temp_derating(ambient_temp_c)
    
    # DF001: Conductor Grouping
    group_factor = self._get_grouping_derating(num_conductors)
    
    # DF004: Thermal Insulation
    insulation_factor = self._get_insulation_derating(thermal_insulation_mm)
    
    # Apply all factors
    derated_ampacity = base_ampacity * temp_factor * group_factor * insulation_factor
    
    return derated_ampacity, {
        'temperature': temp_factor,
        'grouping': group_factor,
        'insulation': insulation_factor,
        'total': temp_factor * group_factor * insulation_factor
    }
```

**Rule 3: Voltage Drop with Reactance**
```python
def _calculate_voltage_drop_with_reactance(
    self,
    current: float,
    distance_m: float,
    r_ohm_per_km: float,
    x_ohm_per_km: float,
    power_factor: float,
    voltage: float,
    phase_type: str = 'single'
) -> tuple[float, float]:
    """
    คำนวณ Voltage Drop พิจารณา R + jX
    
    Returns: (voltage_drop_volt, voltage_drop_percent)
    """
    cos_theta = power_factor
    sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
    
    # Z effective
    z_eff = r_ohm_per_km * cos_theta + x_ohm_per_km * sin_theta
    
    # Calculate VD
    if phase_type == 'single':
        vd_volt = 2 * distance_m * current * z_eff / 1000
    else:  # three-phase
        vd_volt = math.sqrt(3) * distance_m * current * z_eff / 1000
    
    vd_pct = (vd_volt / voltage) * 100
    
    return vd_volt, vd_pct
```

---

### **File 3: `core/breaker_selector.py`**

#### **Status**: ✅ **Relatively Good**

**No critical calculation errors found**

#### **Enhancements**:
- ⚠️ Could add 80% loading rule check (VR005)
- ⚠️ Could add RCBO requirements for wet areas

---

### **File 4: `core/conduit_sizer.py`**

#### **Status**: ✅ **Good**

**Implements NEC Chapter 9 correctly**:
- ✅ Fill percentage: 53% (1 wire), 31% (2 wires), 40% (3+ wires)
- ✅ Area calculations correct

---

### **File 5: `pipeline.py`**

#### **Issues Found**:

1. **❌ Missing `Optional` import** (Line 251)
   ```python
   from typing import Dict, Any  # ← ต้องเพิ่ม Optional
   ```

2. **❌ Voltage mapping incorrect** (Lines 119-125)
   ```python
   voltage_map = {
       'VoltageType.SINGLE_PHASE_120V': 120,  # ← String keys ผิด!
       # ...
   }
   voltage = voltage_map.get(str(load.voltage), 120)  # ← ไม่ match enum
   ```
   **Should be**:
   ```python
   voltage_map = {
       VoltageType.SINGLE_PHASE_120V: 120,  # ← Enum keys
       VoltageType.SINGLE_PHASE_240V: 240,
       VoltageType.THREE_PHASE_208V: 208,
       VoltageType.THREE_PHASE_480V: 480
   }
   voltage = voltage_map.get(load.voltage, 120)
   ```

3. **❌ Hardcoded distance** (Line 129)
   ```python
   distance_feet=100,  # ← ต้องมาจาก load.location หรือ input
   ```

4. **❌ Hardcoded breaker for ground sizing** (Line 139)
   ```python
   circuit_breaker_rating=20  # ← ต้องใช้จากผลการเลือก breaker
   ```

---

## 📝 Implementation Plan

### **Phase 1: Critical Bug Fixes** (ต้องทำก่อน)

#### **1.1 Fix Missing Imports** ✅ CALCULATION
**Files**: `pipeline.py`, `load_calculator.py`

```python
# At top of file
from typing import Dict, Any, List, Optional  # ← เพิ่ม Optional
```

**Justification**: Bug fix, ต้องแก้ไม่งั้น code error

---

#### **1.2 Fix Voltage Mapping** ✅ CALCULATION
**File**: `pipeline.py` Lines 119-125

**Current** (ผิด):
```python
voltage_map = {
    'VoltageType.SINGLE_PHASE_120V': 120,
    'VoltageType.SINGLE_PHASE_240V': 240,
    # ...
}
voltage = voltage_map.get(str(load.voltage), 120)
```

**Fixed** (ถูก):
```python
voltage_map = {
    VoltageType.SINGLE_PHASE_120V: 120,
    VoltageType.SINGLE_PHASE_240V: 240,
    VoltageType.THREE_PHASE_208V: 208,
    VoltageType.THREE_PHASE_480V: 480
}
voltage = voltage_map.get(load.voltage, 120)
```

**Impact**: ✅ Fixes calculation bug, no regression

---

#### **1.3 Remove Hardcoded Distance** ⚠️ NEED APPROVAL
**File**: `pipeline.py` Line 129

**Issue**: Distance hardcoded to 100 feet

**Proposed Solution**:
```python
# Option A: Use location data (if available)
distance_feet = getattr(load.location, 'distance_feet', 100)

# Option B: Add to ElectricalLoad model
# ต้องแก้ models/contracts.py (NON-CALCULATION)
```

**Question for User**: ต้องการให้:
- A) ใช้ default 100 feet ต่อไป (ไม่ต้องแก้)
- B) เพิ่ม field `distance_feet` ใน ElectricalLoad model (ต้องแก้ model)

---

#### **1.4 Fix Ground Wire Sizing Logic** ✅ CALCULATION
**File**: `pipeline.py` Line 139

**Current** (ผิด):
```python
ground_size = wire_sizer.size_ground_wire(circuit_breaker_rating=20)  # ← hardcoded
```

**Fixed** (ถูก):
```python
# Use actual breaker selected
ground_size = wire_sizer.size_ground_wire(
    circuit_breaker_rating=breaker_selections[load.id]['breaker_rating']
)
```

**Impact**: ✅ Fixes calculation, no structure change

---

### **Phase 2: Implement Derating Factors** ✅ CALCULATION

#### **2.1 Add Derating Tables**
**File**: `models/baseline.py`

**Add New Class**:
```python
class DeratingFactors:
    """Derating factors from catalog (DF001-DF004)"""
    
    # DF001: Conductor Grouping
    grouping_factors = {
        (1, 3): 1.0,
        (4, 6): 0.8,
        (7, 9): 0.7,
        (10, 20): 0.5,
        (21, 30): 0.4
    }
    
    # DF002: Ambient Temperature @ 75°C
    temp_factors_75c = {
        30: 1.0,
        35: 0.94,
        40: 0.88,
        45: 0.82,
        50: 0.75
    }
    
    # DF004: Thermal Insulation
    insulation_factors = {
        0: 1.0,
        50: 0.85,
        100: 0.75,
        200: 0.6
    }
    
    @staticmethod
    def get_temp_factor(ambient_temp_c: float, conductor_temp_rating: int = 75) -> float:
        """Get temperature derating factor"""
        if conductor_temp_rating != 75:
            raise NotImplementedError("Only 75°C rating supported currently")
        
        # Find closest temperature
        temps = sorted(DeratingFactors.temp_factors_75c.keys())
        for temp in temps:
            if ambient_temp_c <= temp:
                return DeratingFactors.temp_factors_75c[temp]
        
        # If higher than max, use lowest factor
        return DeratingFactors.temp_factors_75c[max(temps)]
    
    @staticmethod
    def get_grouping_factor(num_conductors: int) -> float:
        """Get conductor grouping factor"""
        for (min_c, max_c), factor in DeratingFactors.grouping_factors.items():
            if min_c <= num_conductors <= max_c:
                return factor
        
        # If more than 30, use most conservative
        return 0.4
```

**Justification**: ✅ Adding constants from catalog, no regression

---

#### **2.2 Update Wire Sizer**
**File**: `core/wire_sizer.py`

**Add Methods**:
```python
from models.baseline import DeratingFactors

class WireSizer:
    
    def size_wire_with_voltage_drop(
        self,
        current: float,
        distance_feet: float,
        voltage: float,
        max_voltage_drop_percent: float = 3.0,
        material: ConductorMaterial = ConductorMaterial.COPPER,
        temperature_rating: int = 75,
        # NEW PARAMETERS
        ambient_temp_c: float = 30,
        num_conductors: int = 3,
        power_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Enhanced wire sizing with derating factors
        """
        # 1. Apply derating to required ampacity
        temp_factor = DeratingFactors.get_temp_factor(ambient_temp_c, temperature_rating)
        group_factor = DeratingFactors.get_grouping_factor(num_conductors)
        
        required_ampacity = current / (temp_factor * group_factor)
        
        # 2. Size by derated ampacity
        ampacity_result = self.size_wire_by_ampacity(
            required_ampacity, material, temperature_rating
        )
        
        if 'error' in ampacity_result:
            return ampacity_result
        
        wire_size = ampacity_result['wire_size']
        
        # 3. Get resistance and reactance
        r_20c = self.wire_baseline.copper_resistance.get(wire_size, 0)
        x = 0.089  # Default reactance for THW (could be from table)
        
        # 4. Calculate R at operating temperature
        operating_temp = temperature_rating  # Assume worst case
        r_operating = self._calc_resistance_at_temp(r_20c, operating_temp)
        
        # 5. Calculate VD with R + jX
        vd, vd_pct = self._calculate_vd_with_reactance(
            current, distance_feet, r_operating, x, voltage, power_factor
        )
        
        # 6. Check if VD acceptable
        if vd_pct <= max_voltage_drop_percent:
            return {
                **ampacity_result,
                'voltage_drop': vd,
                'voltage_drop_percent': vd_pct,
                'temp_factor': temp_factor,
                'group_factor': group_factor,
                'derated_ampacity': ampacity_result['ampacity'] * temp_factor * group_factor,
                'sized_for': 'ampacity_with_derating'
            }
        
        # 7. If VD too high, try larger sizes
        # ... (existing logic to upsize)
    
    def _calc_resistance_at_temp(
        self,
        r_20c: float,
        operating_temp_c: float,
        material: str = 'copper'
    ) -> float:
        """Calculate resistance at operating temperature"""
        alpha = 0.00393 if material == 'copper' else 0.00403
        delta_t = operating_temp_c - 20
        return r_20c * (1 + alpha * delta_t)
    
    def _calculate_vd_with_reactance(
        self,
        current: float,
        distance_feet: float,
        r_ohm_per_km: float,
        x_ohm_per_km: float,
        voltage: float,
        power_factor: float
    ) -> Tuple[float, float]:
        """Calculate voltage drop with R + jX"""
        import math
        
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - cos_theta**2) if cos_theta < 1.0 else 0.0
        
        z_eff = r_ohm_per_km * cos_theta + x_ohm_per_km * sin_theta
        
        # Convert feet to meters to km
        distance_km = distance_feet * 0.3048 / 1000
        
        # VD = 2 × I × L × Z (single phase, round trip)
        vd_volt = 2 * current * distance_km * z_eff
        vd_pct = (vd_volt / voltage) * 100
        
        return vd_volt, vd_pct
```

**Impact**: ✅ Calculation enhancement, backward compatible (default parameters)

---

### **Phase 3: Update Pipeline Integration** ✅ CALCULATION

**File**: `pipeline.py`

**Update wire sizing call**:
```python
def _size_wires(self, request, calculations):
    """Enhanced with derating factors"""
    wire_sizing = {}
    
    for load in request.loads:
        current = calculations[load.id]['current']
        voltage = self._get_voltage(load)
        
        # Get distance (TODO: from load.location or input)
        distance_feet = getattr(load.location, 'distance_feet', 100)
        
        # Get ambient conditions (TODO: from request or config)
        ambient_temp = getattr(request, 'ambient_temp_c', 30)
        
        # Size wire with all factors
        result = self.wire_sizer.size_wire_with_voltage_drop(
            current=current,
            distance_feet=distance_feet,
            voltage=voltage,
            max_voltage_drop_percent=3.0,
            ambient_temp_c=ambient_temp,
            num_conductors=3,  # TODO: from circuit config
            power_factor=load.power_factor or 0.9
        )
        
        wire_sizing[load.id] = result
    
    return wire_sizing
```

---

## 📊 Summary of Changes

### **✅ CALCULATION Changes** (อนุญาต):

| File | Change | Reason | Regression Risk |
|------|--------|--------|-----------------|
| `pipeline.py` L251 | Add `Optional` import | Bug fix | ❌ None |
| `pipeline.py` L119-125 | Fix voltage mapping | Calculation bug | ❌ None |
| `pipeline.py` L139 | Use actual breaker rating | Calculation fix | ❌ None |
| `models/baseline.py` | Add `DeratingFactors` class | New calculations | ❌ None (new code) |
| `wire_sizer.py` | Add derating methods | Calculation enhancement | ⚠️ Low (optional params) |
| `wire_sizer.py` | Add VD with reactance | Calculation accuracy | ⚠️ Low (internal method) |
| `load_calculator.py` L24 | Add `Optional` import | Bug fix | ❌ None |
| `load_calculator.py` L136 | Use actual voltage | Calculation fix | ⚠️ Low (same logic, better value) |

**Total Calculation Changes**: 8 items

---

### **⚠️ NEED APPROVAL**:

| File | Change | Reason | Impact |
|------|--------|--------|--------|
| `models/contracts.py` | Add `distance_feet` to ElectricalLoad | Need distance data | ⚠️ Model change |
| `pipeline.py` L129 | Use distance from load | Remove hardcode | Depends on model change |

**Questions for User**:
1. ต้องการให้เพิ่ม `distance_feet` field ใน ElectricalLoad model หรือไม่?
2. หรือใช้ default 100 feet ต่อไปจนกว่าจะมีข้อมูลจริง?

---

### **❌ NO CHANGES** (ไม่แตะ):

- ✅ File structure
- ✅ `dal/` layer
- ✅ `main.py`
- ✅ `requirements.txt`
- ✅ Test files

---

## 🧪 Testing Strategy

### **Test Case 1: Wire Sizing with Derating**

**Input**:
```python
current = 20.0  # A
distance_feet = 100  # ft
voltage = 230  # V
ambient_temp_c = 40  # °C (hot climate)
num_conductors = 6  # bundled
power_factor = 0.85  # inductive load
```

**Expected**:
```
Base ampacity required: 20.0 A
Temp factor @ 40°C: 0.88
Group factor (6 conductors): 0.8
Total derating: 0.88 × 0.8 = 0.704
Required ampacity: 20.0 / 0.704 = 28.4 A

Selected wire: THW 4mm² (35A @ 75°C)
Derated ampacity: 35 × 0.704 = 24.6 A ✓

VD calculation:
R_20C = 4.61 Ω/km
R_75C = 4.61 × (1 + 0.00393 × 55) = 5.60 Ω/km
X = 0.085 Ω/km
Z_eff = 5.60 × 0.85 + 0.085 × 0.527 = 4.80 Ω/km
VD = 2 × 20 × 30.48m × 4.80 / 1000 = 5.84V
VD% = 5.84 / 230 × 100 = 2.54% ✓ (< 3%)
```

### **Test Case 2: Voltage Mapping Fix**

**Input**:
```python
load.voltage = VoltageType.SINGLE_PHASE_240V
```

**Before (Bug)**:
```python
voltage_map.get(str(load.voltage), 120)  
# → str(VoltageType.SINGLE_PHASE_240V) = "VoltageType.SINGLE_PHASE_240V"
# → Not in keys → Default to 120V ❌
```

**After (Fixed)**:
```python
voltage_map.get(load.voltage, 120)
# → Direct enum lookup → 240V ✓
```

---

## ✅ Final Checklist

### **Before Starting**:
- [ ] Get approval for distance_feet field (or use default)
- [ ] Confirm derating factor tables match catalog
- [ ] Review formulas with user

### **During Implementation**:
- [ ] Fix missing imports
- [ ] Fix voltage mapping
- [ ] Add DeratingFactors class
- [ ] Update wire_sizer methods
- [ ] Update pipeline integration
- [ ] Add unit tests

### **After Completion**:
- [ ] Run existing tests (ensure no regression)
- [ ] Run new calculation tests
- [ ] Compare results with Guideline examples
- [ ] Document all changes

---

**Prepared by**: Laplacia  
**Status**: ✅ **READY FOR APPROVAL**  
**Awaiting Decision**: Distance field in model (or use default 100 feet)
