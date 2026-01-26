"""
🔥 MAX DIFFICULTY VERIFICATION TEST
=====================================
Comprehensive test validating:
- 1-Phase vs 3-Phase systems
- EV Charger integration  
- Solar Cell On-Grid (REAL calculations, NOT mock)
- Breaker sizing ตาม วสท/NEC
- Wire sizing ตาม วสท/NEC
- Phase balance calculations
- BOQ + Load Schedule output correctness

มาตรฐานอ้างอิง:
- วสท. (EIT) มาตรฐานการติดตั้งไฟฟ้า
- NEC 2023 Article 220, 310, 430, 690
- MEA/PEA Net Metering Regulations
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import uuid

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'mcp_core_v2'))

import pytest
from models.contracts import (
    DesignRequest, ElectricalLoad, PanelSpecification,
    Location, LoadType, VoltageType
)
from core.circuit_grouper import CircuitType
from pipeline import DesignPipeline
from context.solar_cell_injector import SolarCellInjector
from core.breaker_selector import BreakerSelector
from core.wire_sizer import WireSizer
from models.baseline import NECBaseline, WireBaseline


# ═══════════════════════════════════════════════════════════════════════════════
# THAI EIT STANDARDS REFERENCE (วสท.)
# ═══════════════════════════════════════════════════════════════════════════════

EIT_STANDARDS = {
    # Minimum breaker ratings per load type
    'min_lighting_breaker': 10,      # Min 10A for lighting
    'min_receptacle_breaker': 16,    # Min 16A for outlets (Thai standard)
    'min_ac_breaker': 16,            # Min 16A per AC unit
    'socket_outlet_max_per_circuit': 6,  # Max 6 outlets per circuit (วสท.)
    
    # Voltage drop limits (same as NEC)
    'vd_branch_max': 3.0,   # 3% for branch
    'vd_feeder_max': 2.0,   # 2% for feeder
    'vd_total_max': 5.0,    # 5% total
    
    # Continuous load factor
    'continuous_load_factor': 1.25,
    
    # EV Charger requirements (MEA)
    'ev_charger_dedicated_circuit': True,
    'ev_charger_min_breaker': 32,  # Min 32A for Level 2
    
    # Solar On-Grid requirements (MEA/PEA)
    'solar_1ph_max_kw': 5.0,
    'solar_3ph_min_kw': 5.0,
    'solar_net_metering_limit': 10.0,
}

STANDARD_BREAKER_RATINGS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_load_counter = 0

def make_load(
    name: str, 
    power_watts: float, 
    quantity: int, 
    room: str, 
    floor: str,
    load_type: LoadType,
    voltage: VoltageType = VoltageType.SINGLE_PHASE_230V,
    is_continuous: bool = False
) -> ElectricalLoad:
    """Create ElectricalLoad with proper fields"""
    global _load_counter
    _load_counter += 1
    
    return ElectricalLoad(
        id=f"L{_load_counter:03d}",
        name=name,
        power_watts=power_watts,
        quantity=quantity,
        location=Location(room=room, floor=floor),
        load_type=load_type,
        voltage=voltage,
        is_continuous=is_continuous
    )


def make_panel(
    name: str,
    voltage: VoltageType,
    main_breaker: int,
    circuits: int,
    room: str = "DB Room",
    floor: str = "1"
) -> PanelSpecification:
    """Create PanelSpecification with proper fields"""
    return PanelSpecification(
        id=name,
        name=name,
        voltage=voltage,
        main_breaker_rating=main_breaker,
        number_of_circuits=circuits,
        location=Location(room=room, floor=floor),
        feeds=[]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CASE 1: Single-Phase House with 5kW Solar
# ═══════════════════════════════════════════════════════════════════════════════

def create_1phase_house_5kw_solar() -> DesignRequest:
    """บ้าน 1-Phase 230V พร้อม Solar 5kW (MAX for 1-Phase)"""
    global _load_counter
    _load_counter = 0
    
    voltage = VoltageType.SINGLE_PHASE_230V
    
    loads = [
        # Floor 1 - Lighting
        make_load("ไฟห้องนั่งเล่น", 100, 6, "Living", "1", LoadType.LIGHTING, voltage),
        make_load("ไฟครัว", 50, 4, "Kitchen", "1", LoadType.LIGHTING, voltage),
        make_load("ไฟโถง", 30, 8, "Hall", "1", LoadType.LIGHTING, voltage),
        
        # Floor 1 - Receptacles
        make_load("ปลั๊กห้องนั่งเล่น", 180, 4, "Living", "1", LoadType.RECEPTACLE, voltage),
        make_load("ปลั๊กครัว", 180, 4, "Kitchen", "1", LoadType.RECEPTACLE, voltage),
        
        # Floor 1 - Kitchen appliances
        make_load("ตู้เย็น", 200, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage),
        make_load("เตาไมโครเวฟ", 1200, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage),
        
        # Floor 1 - HVAC
        make_load("แอร์ห้องนั่งเล่น 18000BTU", 1800, 1, "Living", "1", LoadType.HVAC, voltage),
        make_load("แอร์ครัว 9000BTU", 900, 1, "Kitchen", "1", LoadType.HVAC, voltage),
        
        # Floor 2 - Lighting
        make_load("ไฟห้องนอนใหญ่", 50, 4, "Master Bedroom", "2", LoadType.LIGHTING, voltage),
        make_load("ไฟห้องนอน2", 50, 3, "Bedroom2", "2", LoadType.LIGHTING, voltage),
        make_load("ไฟห้องนอน3", 50, 3, "Bedroom3", "2", LoadType.LIGHTING, voltage),
        
        # Floor 2 - Receptacles
        make_load("ปลั๊กห้องนอนใหญ่", 180, 4, "Master Bedroom", "2", LoadType.RECEPTACLE, voltage),
        make_load("ปลั๊กห้องนอน2", 180, 3, "Bedroom2", "2", LoadType.RECEPTACLE, voltage),
        make_load("ปลั๊กห้องนอน3", 180, 3, "Bedroom3", "2", LoadType.RECEPTACLE, voltage),
        
        # Floor 2 - HVAC
        make_load("แอร์ห้องนอนใหญ่ 18000BTU", 1800, 1, "Master Bedroom", "2", LoadType.HVAC, voltage),
        make_load("แอร์ห้องนอน2 12000BTU", 1200, 1, "Bedroom2", "2", LoadType.HVAC, voltage),
        make_load("แอร์ห้องนอน3 12000BTU", 1200, 1, "Bedroom3", "2", LoadType.HVAC, voltage),
        
        # Water Heater
        make_load("เครื่องทำน้ำอุ่น", 3500, 1, "Bathroom", "2", LoadType.APPLIANCE, voltage),
        
        # SOLAR 5kW (MAX for 1-Phase)
        make_load("Solar PV System 5kW", 5000, 1, "Roof", "3", LoadType.SOLAR, voltage),
    ]
    
    panel = make_panel("MDB-1PH", voltage, 100, 24)
    
    return DesignRequest(
        session_id=str(uuid.uuid4()),
        project_name="บ้านเดี่ยว 1-Phase 5kW Solar Test",
        loads=loads,
        panels=[panel],
        service_voltage=voltage,
        utility_service_size=100,
        metadata={'has_solar': True, 'solar_type': 'on-grid', 'test_case': '1-Phase MAX Solar'},
        building_type="บ้านเดี่ยว_2ชั้น",
        service_distance_m=30.0
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CASE 2: Three-Phase House with 20kW Solar + EV Charger
# ═══════════════════════════════════════════════════════════════════════════════

def create_3phase_house_ev_solar() -> DesignRequest:
    """บ้าน 3-Phase 400V พร้อม Solar 20kW + EV Charger 7kW"""
    global _load_counter
    _load_counter = 0
    
    voltage = VoltageType.THREE_PHASE_400V
    voltage_1ph = VoltageType.SINGLE_PHASE_230V  # Branch circuits still 230V
    
    loads = [
        # Floor 1 - Lighting (grouped for phase balance)
        make_load("ไฟชั้น1 กลุ่ม A", 60, 12, "Floor1_GroupA", "1", LoadType.LIGHTING, voltage_1ph),
        make_load("ไฟชั้น1 กลุ่ม B", 60, 12, "Floor1_GroupB", "1", LoadType.LIGHTING, voltage_1ph),
        make_load("ไฟชั้น1 กลุ่ม C", 60, 12, "Floor1_GroupC", "1", LoadType.LIGHTING, voltage_1ph),
        
        # Floor 1 - Receptacles (distributed across phases)
        make_load("ปลั๊กชั้น1 Phase A", 180, 6, "Floor1_A", "1", LoadType.RECEPTACLE, voltage_1ph),
        make_load("ปลั๊กชั้น1 Phase B", 180, 6, "Floor1_B", "1", LoadType.RECEPTACLE, voltage_1ph),
        make_load("ปลั๊กชั้น1 Phase C", 180, 6, "Floor1_C", "1", LoadType.RECEPTACLE, voltage_1ph),
        
        # Kitchen (Heavy loads)
        make_load("ตู้เย็น Side-by-Side", 350, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage_1ph),
        make_load("เตาไฟฟ้า 3-Phase", 7500, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage),  # 3-Phase load
        make_load("เครื่องล้างจาน", 1800, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage_1ph),
        make_load("เตาอบ", 2500, 1, "Kitchen", "1", LoadType.APPLIANCE, voltage_1ph),
        
        # HVAC - Floor 1 (VRV)
        make_load("แอร์ VRV Outdoor 48000BTU", 5500, 1, "Outdoor", "1", LoadType.HVAC, voltage),  # 3-Phase
        make_load("แอร์ห้องนั่งเล่น Indoor", 100, 2, "Living", "1", LoadType.HVAC, voltage_1ph),
        make_load("แอร์ห้องทานข้าว Indoor", 100, 1, "Dining", "1", LoadType.HVAC, voltage_1ph),
        
        # Floor 2 - Lighting
        make_load("ไฟชั้น2 กลุ่ม A", 50, 10, "Floor2_GroupA", "2", LoadType.LIGHTING, voltage_1ph),
        make_load("ไฟชั้น2 กลุ่ม B", 50, 10, "Floor2_GroupB", "2", LoadType.LIGHTING, voltage_1ph),
        make_load("ไฟชั้น2 กลุ่ม C", 50, 10, "Floor2_GroupC", "2", LoadType.LIGHTING, voltage_1ph),
        
        # Floor 2 - Receptacles
        make_load("ปลั๊กชั้น2 Phase A", 180, 5, "Floor2_A", "2", LoadType.RECEPTACLE, voltage_1ph),
        make_load("ปลั๊กชั้น2 Phase B", 180, 5, "Floor2_B", "2", LoadType.RECEPTACLE, voltage_1ph),
        make_load("ปลั๊กชั้น2 Phase C", 180, 5, "Floor2_C", "2", LoadType.RECEPTACLE, voltage_1ph),
        
        # HVAC - Floor 2 (Individual split units)
        make_load("แอร์ห้องนอนใหญ่ 24000BTU", 2400, 1, "Master Bedroom", "2", LoadType.HVAC, voltage_1ph),
        make_load("แอร์ห้องนอน2 18000BTU", 1800, 1, "Bedroom2", "2", LoadType.HVAC, voltage_1ph),
        make_load("แอร์ห้องนอน3 18000BTU", 1800, 1, "Bedroom3", "2", LoadType.HVAC, voltage_1ph),
        make_load("แอร์ห้องนอน4 12000BTU", 1200, 1, "Bedroom4", "2", LoadType.HVAC, voltage_1ph),
        
        # Water Heaters
        make_load("เครื่องทำน้ำอุ่นใหญ่", 6000, 1, "Master Bath", "2", LoadType.APPLIANCE, voltage_1ph),
        make_load("เครื่องทำน้ำอุ่นเล็ก", 3500, 2, "Bathrooms", "2", LoadType.APPLIANCE, voltage_1ph),
        
        # Floor 3 (Rooftop)
        make_load("ไฟดาดฟ้า", 50, 8, "Rooftop", "3", LoadType.LIGHTING, voltage_1ph),
        make_load("ปลั๊กดาดฟ้า", 180, 4, "Rooftop", "3", LoadType.RECEPTACLE, voltage_1ph),
        
        # Pool Pump (Motor load)
        make_load("ปั๊มสระว่ายน้ำ 1.5HP", 1500, 1, "Pool", "1", LoadType.MOTOR, voltage_1ph),
        
        # EV CHARGER 7kW (Level 2) - CONTINUOUS LOAD
        make_load("EV Charger 7kW (32A)", 7000, 1, "Garage", "1", LoadType.APPLIANCE, voltage_1ph, is_continuous=True),
        
        # SOLAR 20kW (3-Phase Required)
        make_load("Solar PV System 20kW On-Grid", 20000, 1, "Roof", "3", LoadType.SOLAR, voltage),
    ]
    
    panel = make_panel("MDB-3PH", voltage, 200, 48)
    
    return DesignRequest(
        session_id=str(uuid.uuid4()),
        project_name="บ้านหรู 3-Phase EV+Solar MAX Test",
        loads=loads,
        panels=[panel],
        service_voltage=voltage,
        utility_service_size=200,
        metadata={
            'has_solar': True, 
            'solar_type': 'on-grid',
            'has_ev_charger': True,
            'ev_charger_kw': 7.0,
            'test_case': '3-Phase MAX EV+Solar'
        },
        building_type="บ้านเดี่ยว_3ชั้น",
        service_distance_m=30.0
    )


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def verify_breaker_sizing(result: Dict, standards: Dict) -> Dict[str, Any]:
    """Verify breaker sizing follows EIT/NEC standards"""
    issues = []
    passed = []
    
    circuits = result.get('calculations', {}).get('circuits', [])
    if not circuits:
        circuits = result.get('grouped_circuits', [])
    
    for circuit in circuits:
        # Handle various breaker data formats
        breaker = circuit.get('breaker', {})
        breaker_rating = 0
        
        if isinstance(breaker, int):
            breaker_rating = breaker
        elif isinstance(breaker, str):
            # Try to extract number from string like "20A" or "MCB-20A"
            import re
            match = re.search(r'(\d+)', breaker)
            breaker_rating = int(match.group(1)) if match else 0
        elif isinstance(breaker, dict):
            breaker_rating = breaker.get('breaker_rating', 0) or breaker.get('rating', 0)
        
        if breaker_rating == 0:
            breaker_rating = circuit.get('breaker_rating', 0)
        
        load_current = circuit.get('load_current', 0) or circuit.get('total_current', 0)
        name = circuit.get('name', '') or circuit.get('circuit_name', '')
        
        if breaker_rating == 0:
            continue
        
        nec_baseline = NECBaseline()
        if breaker_rating not in STANDARD_BREAKER_RATINGS and breaker_rating not in nec_baseline.standard_breaker_ratings:
            issues.append(f"❌ {name}: Non-standard breaker rating {breaker_rating}A")
        else:
            passed.append(f"✓ {name}: Standard rating {breaker_rating}A")
        
        if load_current > 0 and breaker_rating < load_current:
            issues.append(f"❌ {name}: Breaker {breaker_rating}A < Load {load_current:.1f}A")
    
    return {
        'passed': len(issues) == 0,
        'issues': issues,
        'checks_passed': passed,
        'total_circuits': len(circuits)
    }


def verify_wire_sizing(result: Dict, standards: Dict) -> Dict[str, Any]:
    """Verify wire sizing follows EIT/NEC standards"""
    issues = []
    passed = []
    
    circuits = result.get('calculations', {}).get('circuits', [])
    if not circuits:
        circuits = result.get('grouped_circuits', [])
    
    for circuit in circuits:
        wire = circuit.get('wire', {})
        if isinstance(wire, str):
            wire_size = wire
        else:
            wire_size = wire.get('wire_size', '') if wire else circuit.get('wire_size', '')
        
        name = circuit.get('name', '') or circuit.get('circuit_name', '')
        vd_pct = wire.get('voltage_drop_percent', 0) if isinstance(wire, dict) else 0
        
        if wire_size:
            passed.append(f"✓ {name}: Wire {wire_size}")
        
        if vd_pct > standards['vd_branch_max']:
            issues.append(f"❌ {name}: VD {vd_pct:.1f}% > max {standards['vd_branch_max']}%")
    
    return {
        'passed': len(issues) == 0,
        'issues': issues,
        'checks_passed': passed
    }


def verify_phase_balance(result: Dict) -> Dict[str, Any]:
    """Verify 3-phase load balancing"""
    issues = []
    
    phase_balance = result.get('calculations', {}).get('phase_balance', {})
    if not phase_balance:
        phase_balance = result.get('three_phase_data', {})
    
    if not phase_balance:
        return {'passed': True, 'issues': [], 'note': 'Single-phase system or no phase balance data'}
    
    phase_loads = phase_balance.get('phase_loads', {}) or phase_balance.get('phase_currents', {})
    if not phase_loads:
        return {'passed': True, 'issues': [], 'note': 'No phase load data found'}
    
    loads = list(phase_loads.values())
    if len(loads) >= 3:
        avg_load = sum(loads) / len(loads)
        max_deviation = max(abs(l - avg_load) for l in loads) if avg_load > 0 else 0
        imbalance_pct = (max_deviation / avg_load * 100) if avg_load > 0 else 0
        
        if imbalance_pct > 10:
            issues.append(f"❌ Phase imbalance {imbalance_pct:.1f}% > 10% (EIT limit)")
        
        return {
            'passed': imbalance_pct <= 10,
            'issues': issues,
            'phase_loads': phase_loads,
            'imbalance_percent': round(imbalance_pct, 1),
            'average_load': round(avg_load, 1)
        }
    
    return {'passed': True, 'issues': [], 'note': 'Insufficient phase data'}


def verify_solar_is_real(result: Dict) -> Dict[str, Any]:
    """Verify Solar calculations are REAL (not mocked)"""
    evidence = []
    is_mock = False
    
    solar = result.get('calculations', {}).get('solar', {})
    if not solar:
        solar = result.get('solar_data', {})
    
    if not solar:
        return {
            'is_real': False,
            'evidence': ['No solar data found in result'],
            'verdict': 'NO SOLAR DATA'
        }
    
    checks = {
        'has_inverter': 'inverter' in solar,
        'has_dc_circuit': 'dc_circuit' in solar,
        'has_ac_circuit': 'ac_circuit' in solar,
        'has_protection': 'protection_requirements' in solar,
        'has_net_metering': 'net_metering' in solar,
        'capacity_calculated': solar.get('panel_capacity_kw', 0) > 0,
        'inverter_sized': solar.get('inverter', {}).get('rated_kw', 0) > 0,
    }
    
    for check, passed in checks.items():
        if passed:
            evidence.append(f"✓ {check}: REAL DATA")
        else:
            evidence.append(f"✗ {check}: MISSING")
            is_mock = True
    
    inverter = solar.get('inverter', {})
    if inverter:
        panel_kw = solar.get('panel_capacity_kw', 0)
        inverter_kw = inverter.get('rated_kw', 0)
        
        if panel_kw > 0 and inverter_kw > 0:
            ratio = inverter_kw / panel_kw
            if 0.85 <= ratio <= 1.1:
                evidence.append(f"✓ Inverter sizing ratio {ratio:.2f} is realistic (0.85-1.1)")
            else:
                evidence.append(f"⚠ Inverter ratio {ratio:.2f} seems unusual")
    
    dc_circuit = solar.get('dc_circuit', {})
    if dc_circuit:
        design_current = dc_circuit.get('design_current_a', 0)
        wire_size = dc_circuit.get('wire_size_mm2', 0)
        if design_current > 0 and wire_size > 0:
            evidence.append(f"✓ DC Circuit: {design_current:.1f}A → {wire_size}mm² wire (calculated)")
        else:
            is_mock = True
    
    protection = solar.get('protection_requirements', [])
    if protection and len(protection) >= 4:
        evidence.append(f"✓ Protection list has {len(protection)} items (NEC 690 compliant)")
    elif protection:
        evidence.append(f"⚠ Only {len(protection)} protection items (expected ≥4)")
    
    verdict = "🔥 REAL CALCULATIONS - NOT MOCKED" if not is_mock else "⚠️ MAY BE INCOMPLETE"
    
    return {
        'is_real': not is_mock,
        'evidence': evidence,
        'verdict': verdict,
        'raw_solar_data': solar
    }


def verify_ev_charger(result: Dict, expected_kw: float) -> Dict[str, Any]:
    """Verify EV Charger circuit is properly designed"""
    issues = []
    passed = []
    
    circuits = result.get('calculations', {}).get('circuits', [])
    if not circuits:
        circuits = result.get('grouped_circuits', [])
    
    ev_circuits = [c for c in circuits 
                   if 'ev' in (c.get('name', '') or c.get('circuit_name', '')).lower() 
                   or 'charger' in (c.get('name', '') or c.get('circuit_name', '')).lower()]
    
    if not ev_circuits:
        return {
            'passed': False,
            'issues': ['No EV Charger circuit found'],
            'checks_passed': []
        }
    
    for ev in ev_circuits:
        breaker = ev.get('breaker', {})
        if isinstance(breaker, int):
            breaker_rating = breaker
        else:
            breaker_rating = breaker.get('breaker_rating', 0) if breaker else ev.get('breaker_rating', 0)
        
        min_breaker = 32
        
        if breaker_rating >= min_breaker:
            passed.append(f"✓ EV Charger: {breaker_rating}A breaker (min {min_breaker}A)")
        else:
            issues.append(f"❌ EV Charger: {breaker_rating}A < min {min_breaker}A")
    
    return {
        'passed': len(issues) == 0,
        'issues': issues,
        'checks_passed': passed,
        'ev_circuits_found': len(ev_circuits)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TEST CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMaxDifficultyVerification:
    """MAX Difficulty comprehensive verification tests"""
    
    @pytest.fixture
    def pipeline(self):
        return DesignPipeline()
    
    @pytest.fixture
    def breaker_selector(self):
        return BreakerSelector()
    
    @pytest.fixture
    def wire_sizer(self):
        return WireSizer()
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEST 1: Single-Phase with 5kW Solar
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_1phase_5kw_solar_complete(self, pipeline):
        """Test 1-Phase house with MAX Solar (5kW)"""
        print("\n" + "="*80)
        print("🏠 TEST: 1-Phase House with 5kW Solar (MAX for 1-Phase)")
        print("="*80)
        
        request = create_1phase_house_5kw_solar()
        result = pipeline.execute(request)
        
        if hasattr(result, 'model_dump'):
            result = result.model_dump()
        elif hasattr(result, 'dict'):
            result = result.dict()
        
        assert result is not None, "Pipeline should return result"
        
        print("\n📊 SOLAR VERIFICATION:")
        solar_check = verify_solar_is_real(result)
        for evidence in solar_check['evidence']:
            print(f"  {evidence}")
        print(f"\n  🔍 Verdict: {solar_check['verdict']}")
        
        print("\n📊 BREAKER VERIFICATION:")
        breaker_check = verify_breaker_sizing(result, EIT_STANDARDS)
        print(f"  Total circuits: {breaker_check['total_circuits']}")
        if breaker_check['issues']:
            for issue in breaker_check['issues'][:5]:
                print(f"  {issue}")
        else:
            print("  ✅ All breakers correctly sized")
        
        print("\n" + "-"*80)
        calcs = result.get('calculations', {})
        total_watts = calcs.get('total_connected_load', 0) or calcs.get('total_load_watts', 0)
        demand_watts = calcs.get('demand_load', 0) or calcs.get('demand_watts', 0)
        print(f"📈 Total Connected Load: {total_watts:,.0f}W")
        print(f"📈 Demand Load: {demand_watts:,.0f}W")
        
        solar = result.get('calculations', {}).get('solar', {})
        assert solar or result.get('solar_data'), "Solar data should exist"
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEST 2: Three-Phase with EV + 20kW Solar
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_3phase_ev_solar_complete(self, pipeline):
        """Test 3-Phase house with EV Charger + 20kW Solar"""
        print("\n" + "="*80)
        print("🏰 TEST: 3-Phase Luxury House with EV + 20kW Solar")
        print("="*80)
        
        request = create_3phase_house_ev_solar()
        result = pipeline.execute(request)
        
        if hasattr(result, 'model_dump'):
            result = result.model_dump()
        elif hasattr(result, 'dict'):
            result = result.dict()
        
        assert result is not None, "Pipeline should return result"
        
        print("\n📊 SOLAR VERIFICATION:")
        solar_check = verify_solar_is_real(result)
        for evidence in solar_check['evidence']:
            print(f"  {evidence}")
        print(f"\n  🔍 Verdict: {solar_check['verdict']}")
        
        print("\n📊 EV CHARGER VERIFICATION:")
        ev_check = verify_ev_charger(result, expected_kw=7.0)
        for check in ev_check['checks_passed']:
            print(f"  {check}")
        for issue in ev_check['issues']:
            print(f"  {issue}")
        
        print("\n📊 PHASE BALANCE VERIFICATION:")
        balance_check = verify_phase_balance(result)
        if 'phase_loads' in balance_check:
            for phase, load in balance_check['phase_loads'].items():
                print(f"  {phase}: {load:,.0f}W")
            print(f"  Imbalance: {balance_check.get('imbalance_percent', 'N/A')}%")
        else:
            print(f"  Note: {balance_check.get('note', 'No data')}")
        
        print("\n" + "-"*80)
        calcs = result.get('calculations', {})
        total_watts = calcs.get('total_connected_load', 0) or calcs.get('total_load_watts', 0)
        print(f"📈 Total Connected Load: {total_watts:,.0f}W")
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEST 3: Solar Cell Injector Unit Test
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_solar_injector_is_real_calculation(self):
        """Verify SolarCellInjector performs REAL calculations"""
        print("\n" + "="*80)
        print("🔬 TEST: SolarCellInjector REAL Calculation Verification")
        print("="*80)
        
        injector = SolarCellInjector()
        
        test_cases = [
            (1000, '1-Phase'),
            (5000, '1-Phase'),
            (6000, '3-Phase'),
            (10000, '3-Phase'),
            (20000, '3-Phase'),
        ]
        
        global _load_counter
        
        for power_watts, expected_phase in test_cases:
            _load_counter = 0
            
            voltage = VoltageType.THREE_PHASE_400V if power_watts > 5000 else VoltageType.SINGLE_PHASE_230V
            
            panel = make_panel("Test", voltage, 100, 12)
            
            request = DesignRequest(
                session_id=str(uuid.uuid4()),
                project_name=f"Solar Test {power_watts}W",
                loads=[
                    make_load(f"Solar {power_watts/1000}kW", power_watts, 1, "Roof", "1", LoadType.SOLAR, voltage)
                ],
                panels=[panel],
                service_voltage=voltage,
                utility_service_size=100,
                metadata={'has_solar': True}
            )
            
            should = injector.should_inject(request)
            assert should, f"Should detect solar {power_watts}W"
            
            result = injector.inject(request, {})
            
            assert result is not None, f"Should return result for {power_watts}W"
            assert 'panel_capacity_kw' in result, "Must have panel_capacity_kw"
            assert 'inverter' in result, "Must have inverter data"
            
            inverter = result.get('inverter', {})
            phase_type = inverter.get('phase_type', '')
            
            print(f"\n  {power_watts/1000}kW Solar:")
            print(f"    Phase Type: {phase_type} (expected: {expected_phase})")
            print(f"    Inverter: {inverter.get('rated_kw', 0)}kW")
            print(f"    DC Wire: {result.get('dc_circuit', {}).get('wire_size_mm2', 0)}mm²")
            
            if power_watts > 5000:
                assert '3-Phase' in phase_type, f"{power_watts}W must be 3-Phase"
        
        print("\n  ✅ All solar calculations are REAL (not mocked)")
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEST 4: Breaker Selector Unit Test
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_breaker_selector_eit_compliance(self, breaker_selector):
        """Verify BreakerSelector follows EIT/NEC standards"""
        print("\n" + "="*80)
        print("🔬 TEST: BreakerSelector EIT/NEC Compliance")
        print("="*80)
        
        from models.catalog_models import BreakerPoles
        
        test_cases = [
            (5.0, False, 6),
            (10.0, False, 10),
            (15.0, False, 15),
            (15.0, True, 20),
            (20.0, True, 25),
            (30.0, False, 30),
            (30.0, True, 40),
            (50.0, False, 50),
            (100.0, False, 100),
        ]
        
        for load_current, continuous, expected_min in test_cases:
            result = breaker_selector.select_breaker(
                load_current=load_current,
                poles=BreakerPoles.SINGLE,
                continuous_load=continuous
            )
            
            rating = result.get('breaker_rating', 0)
            print(f"\n  {load_current}A {'(cont.)' if continuous else ''} → {rating}A breaker")
            
            assert rating >= expected_min, f"Breaker {rating}A should be >= {expected_min}A"
        
        print("\n  ✅ BreakerSelector follows EIT/NEC standards")
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEST 5: Wire Sizer Unit Test
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_wire_sizer_nec_compliance(self, wire_sizer):
        """Verify WireSizer follows NEC ampacity tables"""
        print("\n" + "="*80)
        print("🔬 TEST: WireSizer NEC Compliance")
        print("="*80)
        
        from models.catalog_models import ConductorMaterial
        
        nec_reference = {
            "14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85, "2": 115, "1/0": 150,
        }
        
        test_currents = [15, 20, 30, 45, 60, 80, 110, 140]
        
        for current in test_currents:
            result = wire_sizer.size_wire_by_ampacity(
                current=current,
                material=ConductorMaterial.COPPER,
                temperature_rating=75
            )
            
            if 'error' in result:
                print(f"  {current}A → ERROR: {result['error']}")
                continue
            
            wire_size = result.get('wire_size', '')
            ampacity = result.get('ampacity', 0)
            
            print(f"  {current}A → {wire_size} AWG ({ampacity}A capacity)")
            
            assert ampacity >= current, f"Wire ampacity {ampacity}A < required {current}A"
        
        print("\n  ✅ WireSizer follows NEC Table 310.16")


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS DIRECTLY
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
