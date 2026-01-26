"""
Solar Cell Injector - Solar PV System Integration (On-Grid)

[IMPLEMENTED - Civilia's Build Jan 2026]

Supports:
- On-Grid (Net Metering) systems for Thai residential/commercial
- 1-Phase: ≤5kW (MEA/PEA residential)
- 3-Phase: >5kW up to 30kW (CT Meter required >10kW)

วสท. + PEA/MEA Requirements:
- Inverter sizing relative to panel capacity (0.9 ratio typical)
- DC disconnect required (NEC 690.15)
- AC disconnect required at service entrance
- Anti-islanding protection mandatory (IEEE 1547)
- Grounding: Equipment ground + DC system bonding
- Net metering: ≤10kW for MEA residential buyback

Log Checkpoints:
- [CP-SOLAR-START] Entry point
- [CP-SOLAR-DETECT] Solar loads found
- [CP-SOLAR-CALC] Calculation in progress
- [CP-SOLAR-DONE] Complete with result summary
- [CP-SOLAR-SKIP] No solar found
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from models.contracts import DesignRequest, ElectricalLoad, LoadType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants for Thai On-Grid Solar (MEA/PEA Standards + IEC/NEC)
# ═══════════════════════════════════════════════════════════════════════════════

# System voltage configurations
SOLAR_1PH_AC_VOLTAGE = 230   # V (Thai 1-Phase)
SOLAR_3PH_AC_VOLTAGE = 400   # V (Thai 3-Phase Line-Line)
SOLAR_DC_NOMINAL_VOLTAGE = 48  # V (common string voltage for residential)

# Phase threshold (MEA regulation)
SOLAR_1PH_MAX_KW = 5.0  # Max for 1-Phase connection
SOLAR_3PH_MIN_KW = 5.0  # Requires 3-Phase above this

# Net metering limits (MEA Residential Program)
NET_METERING_RESIDENTIAL_LIMIT_KW = 10.0  # Standard residential limit
NET_METERING_CT_THRESHOLD_KW = 10.0       # Above this requires CT meter

# Inverter efficiency assumptions (grid-tie string inverter)
INVERTER_EFFICIENCY = 0.97  # 97% typical
INVERTER_SIZING_RATIO = 0.90  # Panel:Inverter ratio (slightly undersize inverter)

# DC Circuit Safety Factors (NEC 690.8)
VOC_SAFETY_FACTOR = 1.25  # Open circuit voltage factor
ISC_SAFETY_FACTOR = 1.25  # Short circuit current factor

# Wire sizing tables (simplified - mm²)
DC_WIRE_SIZING = {
    # Current range (A) → Wire size (mm²)
    (0, 15): 2.5,
    (15, 25): 4.0,
    (25, 40): 6.0,
    (40, 60): 10.0,
    (60, 100): 16.0,
}

AC_WIRE_SIZING = {
    (0, 16): 2.5,
    (16, 25): 4.0,
    (25, 32): 6.0,
    (32, 50): 10.0,
    (50, 70): 16.0,
    (70, 100): 25.0,
}


class SolarCellInjector:
    """
    Injects Solar PV On-Grid system calculations into design pipeline.
    
    Features:
    - Inverter sizing (string inverter based on panel capacity)
    - DC circuit sizing (panels → inverter) with Voc/Isc safety factors
    - AC circuit sizing (inverter → panel/grid)
    - Protection requirements (DC disconnect, AC breaker, SPD)
    - Net metering capacity check and warnings
    - 1-Phase vs 3-Phase requirement detection
    
    Usage:
        injector = SolarCellInjector()
        if injector.should_inject(request):
            solar_data = injector.inject(request, calculations)
    """
    
    # Solar keywords for auto-detection (Thai + English)
    SOLAR_KEYWORDS = [
        'solar', 'pv', 'photovoltaic',
        'โซลาร์', 'แผงโซลาร์', 'แผงโซล่า', 'พลังงานแสงอาทิตย์',
        'inverter', 'อินเวอร์เตอร์', 'กริดไท', 'grid-tie', 'ongrid', 'on-grid'
    ]
    
    def __init__(self):
        """Initialize Solar Cell Injector."""
        logger.debug("[CP-SOLAR-INIT] SolarCellInjector initialized")
    
    def should_inject(self, request: DesignRequest) -> bool:
        """Determine if Solar PV calculations should be performed.
        
        Checks:
        1. metadata.has_solar flag
        2. LoadType.SOLAR in any load
        3. Solar keywords in load names
        
        Args:
            request: Design request with load info
            
        Returns:
            True if Solar PV calculations should be applied
        """
        # Check 1: Explicit flag in metadata
        metadata = getattr(request, 'metadata', None)
        if metadata and isinstance(metadata, dict) and metadata.get('has_solar'):
            logger.info("[CP-SOLAR-DETECT] Enabled via metadata.has_solar")
            return True
        
        # Check 2: LoadType.SOLAR in any load
        for load in request.loads:
            if hasattr(load, 'load_type') and load.load_type == LoadType.SOLAR:
                logger.info(f"[CP-SOLAR-DETECT] Found LoadType.SOLAR: {load.name}")
                return True
        
        # Check 3: Solar keywords in load names
        for load in request.loads:
            load_name_lower = load.name.lower()
            for keyword in self.SOLAR_KEYWORDS:
                if keyword in load_name_lower:
                    logger.info(f"[CP-SOLAR-DETECT] Keyword '{keyword}' found in '{load.name}'")
                    return True
        
        return False
    
    def _extract_solar_loads(self, request: DesignRequest) -> List[ElectricalLoad]:
        """Extract all solar-related loads from request.
        
        Returns:
            List of loads identified as solar components
        """
        solar_loads = []
        for load in request.loads:
            # Check by LoadType
            if hasattr(load, 'load_type') and load.load_type == LoadType.SOLAR:
                solar_loads.append(load)
                continue
            
            # Check by keyword
            load_name_lower = load.name.lower()
            for keyword in self.SOLAR_KEYWORDS:
                if keyword in load_name_lower:
                    solar_loads.append(load)
                    break
        
        return solar_loads
    
    def _calculate_panel_capacity(self, solar_loads: List[ElectricalLoad]) -> float:
        """Calculate total panel DC capacity from solar loads.
        
        Args:
            solar_loads: List of solar-related loads
            
        Returns:
            Total panel capacity in kW
        """
        total_watts = 0
        for load in solar_loads:
            # power_watts is the DC capacity of solar panels
            total_watts += load.power_watts * (load.quantity if hasattr(load, 'quantity') else 1)
        
        return total_watts / 1000.0  # Convert to kW
    
    def _determine_phase_requirement(self, capacity_kw: float) -> Tuple[str, int]:
        """Determine phase requirement based on capacity.
        
        Args:
            capacity_kw: Solar panel capacity in kW
            
        Returns:
            Tuple of (phase_type, num_phases)
            - ("1-Phase", 1) for ≤5kW
            - ("3-Phase", 3) for >5kW
        """
        if capacity_kw <= SOLAR_1PH_MAX_KW:
            return ("1-Phase", 1)
        else:
            return ("3-Phase", 3)
    
    def _size_inverter(self, panel_capacity_kw: float) -> Dict[str, Any]:
        """Size grid-tie inverter based on panel capacity.
        
        Inverter is typically sized at 90% of panel DC capacity to:
        - Handle realistic power output (panels rarely hit STC rating)
        - Reduce cost while maintaining efficiency
        - Allow for future panel expansion
        
        Args:
            panel_capacity_kw: Total DC panel capacity in kW
            
        Returns:
            Dict with inverter specifications
        """
        # Calculate nominal size (90% of panel capacity)
        nominal_kw = panel_capacity_kw * INVERTER_SIZING_RATIO
        
        # Round to common commercial sizes
        common_sizes = [1.5, 2.0, 3.0, 3.6, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0]
        selected_size = min([s for s in common_sizes if s >= nominal_kw], default=common_sizes[-1])
        
        phase_type, num_phases = self._determine_phase_requirement(panel_capacity_kw)
        
        # Calculate AC output current
        if num_phases == 1:
            ac_current = (selected_size * 1000) / SOLAR_1PH_AC_VOLTAGE
        else:
            ac_current = (selected_size * 1000) / (SOLAR_3PH_AC_VOLTAGE * 1.732)  # √3
        
        return {
            'rated_kw': selected_size,
            'panel_capacity_kw': panel_capacity_kw,
            'efficiency': INVERTER_EFFICIENCY,
            'phase_type': phase_type,
            'num_phases': num_phases,
            'ac_voltage': SOLAR_1PH_AC_VOLTAGE if num_phases == 1 else SOLAR_3PH_AC_VOLTAGE,
            'ac_current_a': round(ac_current, 1),
            'type': 'Grid-Tie String Inverter'
        }
    
    def _calculate_dc_circuit(self, panel_capacity_kw: float, num_strings: int = 1) -> Dict[str, Any]:
        """Calculate DC circuit specifications (panels to inverter).
        
        Applies NEC 690.8 safety factors:
        - Voc × 1.25 for conductor voltage rating
        - Isc × 1.25 for overcurrent protection
        
        Args:
            panel_capacity_kw: Total panel DC capacity
            num_strings: Number of panel strings (default 1)
            
        Returns:
            Dict with DC circuit specifications
        """
        # Estimate string current (typical 450W panel at ~10A Isc)
        # For residential systems, assume single string or parallel strings
        estimated_string_isc = (panel_capacity_kw * 1000) / (SOLAR_DC_NOMINAL_VOLTAGE * 10) * 10  # A
        
        # Apply safety factor
        design_current = estimated_string_isc * ISC_SAFETY_FACTOR
        
        # Size wire based on current
        wire_size = 4.0  # Default
        for (min_a, max_a), size in DC_WIRE_SIZING.items():
            if min_a <= design_current < max_a:
                wire_size = size
                break
        
        # DC breaker sizing (next standard size above design current × 1.25)
        dc_breaker_sizes = [10, 15, 20, 25, 32, 40, 50, 63]
        dc_breaker = min([s for s in dc_breaker_sizes if s >= design_current], default=63)
        
        return {
            'string_isc_a': round(estimated_string_isc, 1),
            'design_current_a': round(design_current, 1),
            'wire_size_mm2': wire_size,
            'wire_type': 'PV1-F (Solar Cable)',  # UV resistant, double insulated
            'dc_breaker_a': dc_breaker,
            'dc_disconnect': True,  # Required per NEC 690.15
            'num_strings': num_strings
        }
    
    def _calculate_ac_circuit(self, inverter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate AC circuit specifications (inverter to panel/grid).
        
        Args:
            inverter_data: Inverter specifications from _size_inverter
            
        Returns:
            Dict with AC circuit specifications
        """
        ac_current = inverter_data['ac_current_a']
        design_current = ac_current * 1.25  # NEC 690.8
        
        # Size wire
        wire_size = 4.0
        for (min_a, max_a), size in AC_WIRE_SIZING.items():
            if min_a <= design_current < max_a:
                wire_size = size
                break
        
        # AC breaker (dedicated solar breaker in panel)
        ac_breaker_sizes = [10, 16, 20, 25, 32, 40, 50, 63]
        ac_breaker = min([s for s in ac_breaker_sizes if s >= design_current], default=63)
        
        return {
            'ac_current_a': ac_current,
            'design_current_a': round(design_current, 1),
            'wire_size_mm2': wire_size,
            'wire_type': 'THW' if inverter_data['num_phases'] == 1 else 'THW (3C+N+G)',
            'ac_breaker_a': ac_breaker,
            'breaker_type': 'RCBO 30mA' if inverter_data['rated_kw'] <= 10 else 'MCCB',
            'ac_disconnect': True  # Required at service entrance
        }
    
    def _check_net_metering(self, panel_capacity_kw: float) -> Dict[str, Any]:
        """Check net metering eligibility and requirements.
        
        MEA/PEA Net Metering Program:
        - Residential: ≤10kW standard program
        - >10kW: Requires CT meter installation
        - >30kW: Commercial/industrial program
        
        Args:
            panel_capacity_kw: Total panel capacity
            
        Returns:
            Dict with net metering status and requirements
        """
        eligible = panel_capacity_kw <= NET_METERING_RESIDENTIAL_LIMIT_KW
        requires_ct = panel_capacity_kw > NET_METERING_CT_THRESHOLD_KW
        
        program = "residential"
        if panel_capacity_kw > 30:
            program = "commercial"
        elif requires_ct:
            program = "residential_ct"
        
        return {
            'eligible_residential': eligible,
            'requires_ct_meter': requires_ct,
            'program': program,
            'capacity_kw': panel_capacity_kw,
            'limit_kw': NET_METERING_RESIDENTIAL_LIMIT_KW,
            'notes': []
        }
    
    def _generate_protection_requirements(self, inverter_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate list of required protection devices.
        
        Returns:
            List of protection requirements with item and spec
        """
        requirements = [
            {
                'item': 'DC Disconnect Switch',
                'spec': f"600V DC, {inverter_data['rated_kw'] * 2}A",
                'location': 'Near inverter',
                'mandatory': True
            },
            {
                'item': 'AC Disconnect Switch',
                'spec': f"{inverter_data['ac_voltage']}V AC, {int(inverter_data['ac_current_a'] * 1.5)}A",
                'location': 'At service entrance',
                'mandatory': True
            },
            {
                'item': 'DC Surge Protector (SPD)',
                'spec': 'Type 2, 600V DC',
                'location': 'DC combiner box',
                'mandatory': True
            },
            {
                'item': 'AC Surge Protector (SPD)',
                'spec': f"Type 2, {inverter_data['ac_voltage']}V AC",
                'location': 'Main panel',
                'mandatory': True
            },
            {
                'item': 'Equipment Grounding',
                'spec': 'Per NEC 690.43 - all exposed metal',
                'location': 'Panels, inverter, racking',
                'mandatory': True
            }
        ]
        
        # Anti-islanding is built into grid-tie inverters
        requirements.append({
            'item': 'Anti-Islanding Protection',
            'spec': 'IEEE 1547 compliant (inverter built-in)',
            'location': 'Inverter firmware',
            'mandatory': True
        })
        
        return requirements
    
    def inject(self, request: DesignRequest, calculations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Inject Solar PV calculations into design.
        
        Args:
            request: Original design request
            calculations: Current calculation results
            
        Returns:
            Dict with complete solar system data, or None if no solar
        """
        logger.info("[CP-SOLAR-CALC] Starting solar PV calculation...")
        
        # Extract solar loads
        solar_loads = self._extract_solar_loads(request)
        if not solar_loads:
            logger.warning("[CP-SOLAR-CALC] No solar loads found despite should_inject=True")
            return None
        
        # Calculate panel capacity
        panel_capacity_kw = self._calculate_panel_capacity(solar_loads)
        logger.info(f"[CP-SOLAR-CALC] Panel capacity: {panel_capacity_kw:.2f} kW")
        
        if panel_capacity_kw <= 0:
            logger.warning("[CP-SOLAR-CALC] Panel capacity is 0, skipping")
            return None
        
        # Size inverter
        inverter_data = self._size_inverter(panel_capacity_kw)
        logger.info(f"[CP-SOLAR-CALC] Inverter sized: {inverter_data['rated_kw']} kW ({inverter_data['phase_type']})")
        
        # Calculate circuits
        dc_circuit = self._calculate_dc_circuit(panel_capacity_kw)
        ac_circuit = self._calculate_ac_circuit(inverter_data)
        
        # Check net metering
        net_metering = self._check_net_metering(panel_capacity_kw)
        
        # Generate protection requirements
        protection = self._generate_protection_requirements(inverter_data)
        
        # Build warnings
        warnings = []
        if not net_metering['eligible_residential']:
            warnings.append(f"⚠️ Solar capacity {panel_capacity_kw:.1f}kW exceeds residential net metering limit ({NET_METERING_RESIDENTIAL_LIMIT_KW}kW)")
        if net_metering['requires_ct_meter']:
            warnings.append("📋 CT meter required for systems >10kW - contact MEA/PEA for installation")
        if inverter_data['num_phases'] == 3 and panel_capacity_kw <= SOLAR_1PH_MAX_KW:
            warnings.append("ℹ️ 3-Phase inverter selected but capacity could use 1-Phase")
        
        # Calculate energy metrics (simplified)
        # Thailand average: ~4.5 peak sun hours/day, 0.8 system efficiency
        daily_kwh = panel_capacity_kw * 4.5 * 0.80
        monthly_kwh = daily_kwh * 30
        annual_kwh = daily_kwh * 365
        
        # Net load impact (negative = generation)
        net_impact_watts = -int(panel_capacity_kw * 1000 * 0.8)  # Average output
        
        solar_data = {
            'panel_capacity_kw': panel_capacity_kw,
            'system_type': 'On-Grid (Net Metering)',
            'inverter': inverter_data,
            'dc_circuit': dc_circuit,
            'ac_circuit': ac_circuit,
            'net_metering': net_metering,
            'protection': protection,
            'warnings': warnings,
            'energy_estimate': {
                'daily_kwh': round(daily_kwh, 1),
                'monthly_kwh': round(monthly_kwh, 1),
                'annual_kwh': round(annual_kwh, 1),
                'peak_sun_hours': 4.5,
                'system_efficiency': 0.80
            },
            'net_impact': {
                'load_reduction_watts': net_impact_watts,
                'description': f"Solar generation reduces net load by ~{abs(net_impact_watts)}W average"
            }
        }
        
        logger.info(f"[CP-SOLAR-DONE] Solar calculation complete: {panel_capacity_kw:.1f}kW, {inverter_data['phase_type']}")
        return solar_data


# ═══════════════════════════════════════════════════════════════════════════════
# Global Singleton Instance
# ═══════════════════════════════════════════════════════════════════════════════

_solar_cell_injector: Optional[SolarCellInjector] = None


def get_solar_cell_injector() -> SolarCellInjector:
    """Get the global Solar Cell Injector instance (singleton)."""
    global _solar_cell_injector
    if _solar_cell_injector is None:
        _solar_cell_injector = SolarCellInjector()
        logger.debug("[CP-SOLAR-INIT] Created SolarCellInjector singleton")
    return _solar_cell_injector
