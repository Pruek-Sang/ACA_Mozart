"""
Three-Phase Engineering Injector - Advanced 3-Phase Calculations

[CP-3PH-WIRE] Cloud logging prefix for Sprint 3.
[CP-3PH-ENG] Cloud logging prefix for engineering calculations.

📋 PURPOSE:
-----------
คำนวณค่าทางวิศวกรรมไฟฟ้า 3 เฟส ที่ phase_balance_injector.py ทำไม่ได้
(Phase assignment/balancing อยู่ใน phase_balance_injector.py แล้ว)

📊 ENGINEERING FEATURES (Full Roadmap):
=======================================

┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: BASIC (Priority: HIGH) - IMPLEMENTED                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ 3-Phase VD Formula: VD = √3 × I × L × (R cosθ + X sinθ) / V             │
│  ✓ Neutral Current (Unbalanced): In = √(Ia² + Ib² + Ic² - IaIb - IbIc - IcIa)│
│  ✓ Power Calculations: S = √3 × V × I, P = S × cosθ, Q = S × sinθ          │
│  ✓ Suggest 3-Phase Upgrade: when 1-phase load > 15kW                       │
└─────────────────────────────────────────────────────────────────────────────┘

Author: Mozart AI - Sprint 3 Implementation
Date: 2026-01-25
"""

import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

SQRT3 = math.sqrt(3)  # √3 ≈ 1.732

# Voltage levels (Thai standard)
VOLTAGE_3PH_380V = 380  # V line-to-line
VOLTAGE_3PH_400V = 400  # V line-to-line (IEC)
VOLTAGE_1PH_220V = 220  # V line-to-neutral
VOLTAGE_1PH_230V = 230  # V line-to-neutral (Thai standard)

# Upgrade thresholds
SINGLE_PHASE_MAX_KW = 15.0  # Suggest 3-phase above this
MOTOR_VFD_THRESHOLD_KW = 5.5  # Suggest VFD above this

# Power factor targets
TARGET_PF_INDUSTRIAL = 0.95
TARGET_PF_COMMERCIAL = 0.90
TARGET_PF_RESIDENTIAL = 0.85

# Wire resistance/reactance tables (Ohm/km at 75°C for copper)
# Source: IEC 60287, วสท. 2564
WIRE_RESISTANCE_OHM_PER_KM = {
    "1.5": 14.8,
    "2.5": 8.91,
    "4": 5.57,
    "6": 3.71,
    "10": 2.22,
    "16": 1.39,
    "25": 0.889,
    "35": 0.635,
    "50": 0.444,
    "70": 0.317,
    "95": 0.233,
    "120": 0.185,
    "150": 0.148,
    "185": 0.120,
    "240": 0.0922,
}

# Reactance (typical for PVC insulated cables in conduit)
WIRE_REACTANCE_OHM_PER_KM = {
    "1.5": 0.108,
    "2.5": 0.100,
    "4": 0.095,
    "6": 0.090,
    "10": 0.083,
    "16": 0.078,
    "25": 0.075,
    "35": 0.072,
    "50": 0.070,
    "70": 0.068,
    "95": 0.066,
    "120": 0.065,
    "150": 0.064,
    "185": 0.063,
    "240": 0.062,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

class MotorStartingMethod(str, Enum):
    """Motor starting methods."""
    DOL = "DOL"  # Direct On Line
    STAR_DELTA = "STAR_DELTA"  # Y-Δ
    SOFT_STARTER = "SOFT_STARTER"
    VFD = "VFD"  # Variable Frequency Drive


@dataclass
class ThreePhasePowerResult:
    """Result of 3-phase power calculation."""
    apparent_power_kva: float  # S
    active_power_kw: float     # P
    reactive_power_kvar: float  # Q
    power_factor: float        # cosθ
    line_current_a: float      # I_line
    phase_current_a: float     # I_phase (for delta connection)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'apparent_power_kva': round(self.apparent_power_kva, 2),
            'active_power_kw': round(self.active_power_kw, 2),
            'reactive_power_kvar': round(self.reactive_power_kvar, 2),
            'power_factor': round(self.power_factor, 3),
            'line_current_a': round(self.line_current_a, 2),
            'phase_current_a': round(self.phase_current_a, 2),
        }


@dataclass
class NeutralCurrentResult:
    """Result of neutral current calculation for unbalanced load."""
    neutral_current_a: float
    imbalance_percent: float
    requires_oversized_neutral: bool
    recommended_neutral_size_mm2: float
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'neutral_current_a': round(self.neutral_current_a, 2),
            'imbalance_percent': round(self.imbalance_percent, 2),
            'requires_oversized_neutral': self.requires_oversized_neutral,
            'recommended_neutral_size_mm2': self.recommended_neutral_size_mm2,
            'warnings': self.warnings,
        }


@dataclass
class ThreePhaseVDResult:
    """Result of 3-phase voltage drop calculation."""
    voltage_drop_v: float
    voltage_drop_percent: float
    wire_size_mm2: str
    distance_m: float
    current_a: float
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'voltage_drop_v': round(self.voltage_drop_v, 2),
            'voltage_drop_percent': round(self.voltage_drop_percent, 3),
            'wire_size_mm2': self.wire_size_mm2,
            'distance_m': self.distance_m,
            'current_a': round(self.current_a, 2),
            'warnings': self.warnings,
        }


@dataclass
class MotorStartingResult:
    """Result of motor starting analysis."""
    recommended_method: MotorStartingMethod
    starting_current_a: float
    running_current_a: float
    voltage_dip_percent: float
    breaker_size_a: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'recommended_method': self.recommended_method.value,
            'starting_current_a': round(self.starting_current_a, 2),
            'running_current_a': round(self.running_current_a, 2),
            'voltage_dip_percent': round(self.voltage_dip_percent, 2),
            'breaker_size_a': self.breaker_size_a,
        }


@dataclass 
class CapacitorBankResult:
    """Result of power factor correction calculation."""
    required_kvar: float
    current_pf: float
    target_pf: float
    capacitor_per_phase_uf: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'required_kvar': round(self.required_kvar, 2),
            'current_pf': round(self.current_pf, 3),
            'target_pf': round(self.target_pf, 3),
            'capacitor_per_phase_uf': round(self.capacitor_per_phase_uf, 1),
        }


# =============================================================================
# MAIN INJECTOR CLASS
# =============================================================================

class ThreePhaseInjector:
    """
    Advanced 3-phase engineering calculations.
    
    [CP-3PH-WIRE] Cloud logging prefix for wire sizing.
    [CP-3PH-ENG] Cloud logging prefix for engineering calculations.
    
    NOTE: Phase assignment/balancing is handled by phase_balance_injector.py
    This injector focuses on calculations AFTER phase assignment.
    """
    
    def __init__(self):
        """Initialize Three-Phase Injector."""
        logger.info("[CP-3PH-ENG] ThreePhaseInjector initialized")
    
    # =========================================================================
    # PHASE 1: BASIC CALCULATIONS (IMPLEMENTED - Sprint 3)
    # =========================================================================
    
    def calculate_3phase_vd(
        self,
        current_a: float,
        distance_m: float,
        wire_size_mm2: str,
        voltage_v: float = VOLTAGE_3PH_380V,
        power_factor: float = 0.85,
        conductor_material: str = "copper"
    ) -> ThreePhaseVDResult:
        """Calculate Voltage Drop for 3-phase circuit.
        
        [CP-3PH-WIRE] Cloud logging checkpoint.
        
        Formula: VD = √3 × I × L × (R × cosθ + X × sinθ)
        
        Args:
            current_a: Line current in Amps
            distance_m: One-way distance in meters
            wire_size_mm2: Wire cross-section in mm² (as string)
            voltage_v: Line-to-line voltage
            power_factor: Load power factor
            conductor_material: "copper" or "aluminum"
            
        Returns:
            ThreePhaseVDResult with voltage drop values
        """
        logger.info(
            f"[CP-3PH-WIRE] Calculating 3-phase VD: {current_a}A, {distance_m}m, "
            f"{wire_size_mm2}mm², {voltage_v}V, PF={power_factor}"
        )
        
        warnings = []
        
        # Get wire resistance and reactance
        wire_r = WIRE_RESISTANCE_OHM_PER_KM.get(wire_size_mm2, 1.0)
        wire_x = WIRE_REACTANCE_OHM_PER_KM.get(wire_size_mm2, 0.08)
        
        # Adjust for aluminum (1.64x resistance of copper)
        if conductor_material.lower() == "aluminum":
            wire_r *= 1.64
        
        # Convert distance to km
        distance_km = distance_m / 1000.0
        
        # Calculate power factor components
        cos_theta = power_factor
        sin_theta = math.sqrt(1 - power_factor ** 2)
        
        # 3-Phase VD formula: VD = √3 × I × L × (R cosθ + X sinθ)
        vd_v = SQRT3 * current_a * distance_km * (wire_r * cos_theta + wire_x * sin_theta)
        vd_percent = (vd_v / voltage_v) * 100
        
        # Warnings
        if vd_percent > 5.0:
            warnings.append(
                f"⚠️ Voltage drop {vd_percent:.2f}% exceeds 5% limit (วสท. 2564: service + branch ≤ 5%)"
            )
        elif vd_percent > 3.0:
            warnings.append(
                f"⚠️ Voltage drop {vd_percent:.2f}% exceeds 3% branch limit (วสท. 2564)"
            )
        
        logger.info(f"[CP-3PH-WIRE] VD result: {vd_v:.2f}V ({vd_percent:.3f}%)")
        
        return ThreePhaseVDResult(
            voltage_drop_v=vd_v,
            voltage_drop_percent=vd_percent,
            wire_size_mm2=wire_size_mm2,
            distance_m=distance_m,
            current_a=current_a,
            warnings=warnings
        )
    
    def calculate_neutral_current(
        self,
        i_a: float,
        i_b: float,
        i_c: float,
        angle_a: float = 0,
        angle_b: float = -120,
        angle_c: float = 120
    ) -> NeutralCurrentResult:
        """Calculate neutral current for unbalanced 3-phase load.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        For balanced load: In = 0
        For unbalanced: In = |Ia∠0° + Ib∠-120° + Ic∠120°|
        
        Simplified formula (assuming resistive loads, same angle shift):
        In = √(Ia² + Ib² + Ic² - Ia×Ib - Ib×Ic - Ic×Ia)
        
        Args:
            i_a, i_b, i_c: Phase currents in Amps
            angle_a, angle_b, angle_c: Phase angles in degrees
            
        Returns:
            NeutralCurrentResult with current and sizing recommendation
        """
        logger.info(f"[CP-3PH-ENG] Calculating neutral current: Ia={i_a}A, Ib={i_b}A, Ic={i_c}A")
        
        warnings = []
        
        # Convert angles to radians
        rad_a = math.radians(angle_a)
        rad_b = math.radians(angle_b)
        rad_c = math.radians(angle_c)
        
        # Phasor calculation
        # I = I∠θ = I(cosθ + j·sinθ)
        i_a_real = i_a * math.cos(rad_a)
        i_a_imag = i_a * math.sin(rad_a)
        
        i_b_real = i_b * math.cos(rad_b)
        i_b_imag = i_b * math.sin(rad_b)
        
        i_c_real = i_c * math.cos(rad_c)
        i_c_imag = i_c * math.sin(rad_c)
        
        # Neutral current = vector sum
        i_n_real = i_a_real + i_b_real + i_c_real
        i_n_imag = i_a_imag + i_b_imag + i_c_imag
        
        # Magnitude
        i_neutral = math.sqrt(i_n_real**2 + i_n_imag**2)
        
        # Calculate imbalance
        avg_current = (i_a + i_b + i_c) / 3
        if avg_current > 0:
            max_current = max(i_a, i_b, i_c)
            min_current = min(i_a, i_b, i_c)
            imbalance_percent = ((max_current - min_current) / avg_current) * 100
        else:
            imbalance_percent = 0.0
        
        # Determine if oversized neutral needed
        # Rule: If neutral > 50% of phase, consider oversizing
        max_phase = max(i_a, i_b, i_c)
        requires_oversized = i_neutral > (max_phase * 0.5)
        
        # Recommend neutral size based on current
        # This is simplified - in reality, match to phase wire size
        if i_neutral <= 20:
            neutral_size = "4"
        elif i_neutral <= 32:
            neutral_size = "6"
        elif i_neutral <= 45:
            neutral_size = "10"
        elif i_neutral <= 60:
            neutral_size = "16"
        elif i_neutral <= 80:
            neutral_size = "25"
        else:
            neutral_size = "35"
        
        if requires_oversized:
            warnings.append(
                f"⚠️ Neutral current {i_neutral:.1f}A > 50% of phase - consider oversized neutral"
            )
        
        if imbalance_percent > 15:
            warnings.append(
                f"⚠️ Phase imbalance {imbalance_percent:.1f}% exceeds 15% (วสท. 2564)"
            )
        
        logger.info(
            f"[CP-3PH-ENG] Neutral current: {i_neutral:.2f}A, imbalance: {imbalance_percent:.1f}%, "
            f"oversized: {requires_oversized}"
        )
        
        return NeutralCurrentResult(
            neutral_current_a=i_neutral,
            imbalance_percent=imbalance_percent,
            requires_oversized_neutral=requires_oversized,
            recommended_neutral_size_mm2=float(neutral_size),
            warnings=warnings
        )
    
    def calculate_3phase_power(
        self,
        line_voltage_v: float,
        line_current_a: float,
        power_factor: float
    ) -> ThreePhasePowerResult:
        """Calculate 3-phase power values.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        S = √3 × V_L × I_L (Apparent Power, kVA)
        P = S × cosθ (Active Power, kW)
        Q = S × sinθ (Reactive Power, kVAR)
        
        Args:
            line_voltage_v: Line-to-line voltage
            line_current_a: Line current
            power_factor: Power factor (cosθ)
            
        Returns:
            ThreePhasePowerResult with all power values
        """
        logger.info(
            f"[CP-3PH-ENG] Calculating 3-phase power: V={line_voltage_v}V, "
            f"I={line_current_a}A, PF={power_factor}"
        )
        
        # Apparent power
        s_va = SQRT3 * line_voltage_v * line_current_a
        s_kva = s_va / 1000.0
        
        # Active power
        p_kw = s_kva * power_factor
        
        # Reactive power
        sin_theta = math.sqrt(1 - power_factor**2)
        q_kvar = s_kva * sin_theta
        
        # Phase current (for star connection, I_phase = I_line)
        # For delta connection: I_phase = I_line / √3
        i_phase = line_current_a  # Assuming star connection
        
        logger.info(
            f"[CP-3PH-ENG] Power result: S={s_kva:.2f}kVA, P={p_kw:.2f}kW, Q={q_kvar:.2f}kVAR"
        )
        
        return ThreePhasePowerResult(
            apparent_power_kva=s_kva,
            active_power_kw=p_kw,
            reactive_power_kvar=q_kvar,
            power_factor=power_factor,
            line_current_a=line_current_a,
            phase_current_a=i_phase
        )
    
    def suggest_upgrade_to_3phase(self, total_load_kw: float) -> Optional[str]:
        """Check if 1-phase system should upgrade to 3-phase.
        
        Args:
            total_load_kw: Total load in kW
            
        Returns:
            Warning message if upgrade recommended, None otherwise
        """
        if total_load_kw > SINGLE_PHASE_MAX_KW:
            return (
                f"ℹ️ โหลดรวม {total_load_kw:.1f}kW เกิน {SINGLE_PHASE_MAX_KW}kW - "
                "พิจารณาใช้ไฟ 3 เฟส (ประหยัดค่าไฟ, สายเล็กลง)"
            )
        return None
    
    # =========================================================================
    # PHASE 2: INTERMEDIATE CALCULATIONS (IMPLEMENTED)
    # =========================================================================
    
    def calculate_capacitor_bank(
        self,
        active_power_kw: float,
        current_pf: float,
        target_pf: float = TARGET_PF_INDUSTRIAL,
        voltage_v: float = VOLTAGE_3PH_380V
    ) -> CapacitorBankResult:
        """Calculate capacitor bank size for power factor correction.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        kVAR = P × (tan(θ1) - tan(θ2))
        where θ1 = arccos(PF_current), θ2 = arccos(PF_target)
        
        Args:
            active_power_kw: Active power in kW
            current_pf: Current power factor
            target_pf: Target power factor (default 0.95)
            voltage_v: System voltage
            
        Returns:
            CapacitorBankResult with kVAR and capacitor sizing
        """
        logger.info(
            f"[CP-3PH-ENG] Calculating capacitor bank: P={active_power_kw}kW, "
            f"PF={current_pf} -> {target_pf}"
        )
        
        # Calculate angles
        theta1 = math.acos(current_pf)
        theta2 = math.acos(target_pf)
        
        # Required kVAR
        required_kvar = active_power_kw * (math.tan(theta1) - math.tan(theta2))
        
        # Capacitance per phase (for star connection)
        # Q = V² × ω × C × 3 (for 3-phase star)
        # C = Q / (3 × V² × ω)
        omega = 2 * math.pi * 50  # 50 Hz
        phase_voltage = voltage_v / SQRT3
        
        # Q in VAR for calculation
        q_var = required_kvar * 1000
        c_farad = q_var / (3 * phase_voltage**2 * omega)
        c_microfarad = c_farad * 1e6
        
        logger.info(
            f"[CP-3PH-ENG] Capacitor bank: {required_kvar:.2f}kVAR, "
            f"{c_microfarad:.1f}µF per phase"
        )
        
        return CapacitorBankResult(
            required_kvar=required_kvar,
            current_pf=current_pf,
            target_pf=target_pf,
            capacitor_per_phase_uf=c_microfarad
        )
    
    def analyze_motor_starting(
        self,
        motor_power_kw: float,
        voltage_v: float = VOLTAGE_3PH_380V,
        transformer_kva: Optional[float] = None,
        motor_type: str = "induction"
    ) -> MotorStartingResult:
        """Analyze motor starting method and requirements.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        Rules of thumb:
        - DOL: OK for motors < 5.5kW (or < 5% of transformer kVA)
        - Star-Delta: Reduces starting current to 33%
        - Soft Starter: Reduces starting current to 40-60%
        - VFD: Best for variable speed, lowest starting current
        
        Args:
            motor_power_kw: Motor power in kW
            voltage_v: System voltage
            transformer_kva: Transformer capacity (for voltage dip check)
            motor_type: "induction" or "synchronous"
            
        Returns:
            MotorStartingResult with recommended method and sizing
        """
        logger.info(
            f"[CP-3PH-ENG] Analyzing motor starting: {motor_power_kw}kW, "
            f"transformer={transformer_kva}kVA"
        )
        
        # Calculate FLA (Full Load Amps)
        # FLA = P / (√3 × V × η × PF)
        efficiency = 0.85
        power_factor = 0.85
        fla = (motor_power_kw * 1000) / (SQRT3 * voltage_v * efficiency * power_factor)
        
        # LRA (Locked Rotor Amps) = FLA × 6 (typical for NEMA B)
        lra_multiplier = 6.0
        lra = fla * lra_multiplier
        
        # Determine recommended starting method
        if motor_power_kw <= 5.5:
            method = MotorStartingMethod.DOL
            starting_current = lra
        elif motor_power_kw <= MOTOR_VFD_THRESHOLD_KW * 2:
            method = MotorStartingMethod.STAR_DELTA
            starting_current = lra / 3  # 33% of DOL
        else:
            method = MotorStartingMethod.VFD
            starting_current = fla * 1.1  # ~110% of FLA
        
        # Check voltage dip if transformer size known
        voltage_dip = 0.0
        if transformer_kva:
            # Simplified: VD% ≈ (Starting kVA / Transformer kVA) × Z%
            # Assume Z% = 5% for distribution transformers
            starting_kva = SQRT3 * voltage_v * starting_current / 1000
            voltage_dip = (starting_kva / transformer_kva) * 5.0
            
            if voltage_dip > 15:
                # Switch to better starting method
                if method == MotorStartingMethod.DOL:
                    method = MotorStartingMethod.STAR_DELTA
                    starting_current = lra / 3
                elif method == MotorStartingMethod.STAR_DELTA:
                    method = MotorStartingMethod.SOFT_STARTER
                    starting_current = lra * 0.4
        
        # Breaker size (125% of FLA for motor, or LRA for DOL)
        if method == MotorStartingMethod.DOL:
            breaker_size = self._get_next_breaker_rating(lra)
        else:
            breaker_size = self._get_next_breaker_rating(fla * 1.25)
        
        logger.info(
            f"[CP-3PH-ENG] Motor analysis: method={method.value}, "
            f"FLA={fla:.1f}A, starting={starting_current:.1f}A, breaker={breaker_size}A"
        )
        
        return MotorStartingResult(
            recommended_method=method,
            starting_current_a=starting_current,
            running_current_a=fla,
            voltage_dip_percent=voltage_dip,
            breaker_size_a=breaker_size
        )
    
    def _get_next_breaker_rating(self, current: float) -> int:
        """Get next standard breaker rating above current."""
        standard_ratings = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
        for rating in standard_ratings:
            if rating >= current:
                return rating
        return 250  # Max
    
    def calculate_transformer_size(
        self,
        total_load_kva: float,
        diversity_factor: float = 0.8,
        growth_factor: float = 1.25,
        efficiency: float = 0.98
    ) -> Dict[str, Any]:
        """Calculate transformer sizing.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        kVA = (total_load × diversity × growth) / efficiency
        
        Then round up to standard size: 50, 100, 160, 250, 315, 400, 500, 630, 800, 1000
        
        Args:
            total_load_kva: Total connected load in kVA
            diversity_factor: Demand factor (0.6-0.9 typical)
            growth_factor: Future growth allowance
            efficiency: Transformer efficiency
            
        Returns:
            Dict with recommended transformer size and details
        """
        logger.info(
            f"[CP-3PH-ENG] Calculating transformer size: load={total_load_kva}kVA, "
            f"diversity={diversity_factor}, growth={growth_factor}"
        )
        
        # Calculate required capacity
        required_kva = (total_load_kva * diversity_factor * growth_factor) / efficiency
        
        # Standard transformer sizes (kVA)
        standard_sizes = [50, 100, 160, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000]
        
        selected_size = None
        for size in standard_sizes:
            if size >= required_kva:
                selected_size = size
                break
        
        if selected_size is None:
            selected_size = standard_sizes[-1]
        
        logger.info(f"[CP-3PH-ENG] Transformer: required={required_kva:.1f}kVA, selected={selected_size}kVA")
        
        return {
            'required_kva': round(required_kva, 2),
            'selected_kva': selected_size,
            'connected_load_kva': total_load_kva,
            'diversity_factor': diversity_factor,
            'growth_factor': growth_factor,
            'utilization_percent': round((required_kva / selected_size) * 100, 1)
        }
    
    # =========================================================================
    # MAIN INJECT METHOD
    # =========================================================================
    
    def inject(self, request: Any, result: Any) -> Any:
        """Main injection point for 3-phase calculations.
        
        [CP-3PH-ENG] Cloud logging checkpoint.
        
        Called POST-pipeline, after phase_balance_injector has assigned loads.
        
        Args:
            request: Original design request
            result: Design result to modify
            
        Returns:
            Modified result with 3-phase calculations
        """
        logger.info("[CP-3PH-ENG] Starting 3-phase engineering injection...")
        
        # Check if 3-phase system
        voltage = getattr(request, 'service_voltage', None)
        if not voltage:
            logger.info("[CP-3PH-ENG] No service voltage, skipping")
            return result
        
        voltage_str = voltage.value if hasattr(voltage, 'value') else str(voltage)
        is_three_phase = '3PH' in voltage_str.upper() or 'THREE' in voltage_str.upper()
        
        if not is_three_phase:
            # Check if should suggest upgrade
            loads = getattr(request, 'loads', [])
            total_kw = sum(
                getattr(l, 'power_watts', 0) * getattr(l, 'quantity', 1) / 1000
                for l in loads
            )
            upgrade_msg = self.suggest_upgrade_to_3phase(total_kw)
            if upgrade_msg:
                warnings = getattr(result, 'warnings', []) or []
                if isinstance(warnings, list):
                    warnings.append(upgrade_msg)
                    try:
                        result.warnings = warnings
                    except AttributeError:
                        object.__setattr__(result, 'warnings', warnings)
            
            logger.info("[CP-3PH-ENG] 1-phase system, injection complete")
            return result
        
        logger.info("[CP-3PH-ENG] Processing 3-phase system...")
        
        # Calculate total 3-phase power
        loads = getattr(request, 'loads', [])
        total_watts = sum(
            getattr(l, 'power_watts', 0) * getattr(l, 'quantity', 1)
            for l in loads
        )
        
        # Assume 400V 3-phase, PF 0.85
        line_current = total_watts / (SQRT3 * 400 * 0.85)
        power_result = self.calculate_3phase_power(400, line_current, 0.85)
        
        # Add 3-phase data to result
        three_phase_data = {
            'is_three_phase': True,
            'power_calculation': power_result.to_dict(),
            'line_voltage_v': 400,
            'line_current_a': round(line_current, 2),
        }
        
        # Attach to result
        try:
            if hasattr(result, 'calculations') and isinstance(result.calculations, dict):
                result.calculations['three_phase'] = three_phase_data
            else:
                object.__setattr__(result, 'three_phase_data', three_phase_data)
        except Exception as e:
            logger.warning(f"[CP-3PH-ENG] Could not attach 3-phase data: {e}")
        
        logger.info(
            f"[CP-3PH-ENG] Injection complete: {power_result.active_power_kw:.2f}kW, "
            f"{line_current:.2f}A"
        )
        
        return result


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_three_phase_injector: Optional[ThreePhaseInjector] = None


def get_three_phase_injector() -> ThreePhaseInjector:
    """Get the global Three-Phase Injector instance."""
    global _three_phase_injector
    if _three_phase_injector is None:
        _three_phase_injector = ThreePhaseInjector()
    return _three_phase_injector
