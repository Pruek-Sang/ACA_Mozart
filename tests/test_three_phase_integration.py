"""
3-Phase Integration Tests (Sprint 9)
=====================================

Test all 3-phase features implemented in Sprints 1-8:
1. Threshold Detection (>25kW → 3-phase required)
2. Phase Balance Algorithm (LFD)
3. Wire Sizing for 3-Phase
4. Display Layer (compute.py)
5. SLD Renderer (3P breaker, CT meter)
6. BOQ Renderer (3P pricing)
7. MDB & Grounding
8. CT Meter Logic

NO MOCKS - Real service calls only!
Author: Estrella 🌟
Date: 2025-01 (Production-3Phase branch)
"""
import sys
import os
import pytest
import math

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Copilot-Mozart', 'ACA_Mozart-copilot[RAG]'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_core_v2'))


# =============================================================================
# Sprint 1: Threshold Detection Tests
# =============================================================================

class TestThreePhaseThreshold:
    """Test 3-phase detection based on 25kW threshold (วสท. 2564)."""
    
    def test_check_three_phase_required_over_threshold(self):
        """Load >25kW should require 3-phase."""
        from core.circuit_grouper import check_three_phase_required
        
        circuits = [
            {'circuit_name': 'AC1', 'total_watts': 15000},
            {'circuit_name': 'AC2', 'total_watts': 12000},  # Total = 27kW > 25kW
        ]
        
        result = check_three_phase_required(circuits)
        assert result['requires_three_phase'] is True
        assert result['total_connected_load_kw'] > 25.0
        assert '3PH-001' in result.get('reason', '')
    
    def test_check_three_phase_required_under_threshold(self):
        """Load ≤25kW should NOT require 3-phase."""
        from core.circuit_grouper import check_three_phase_required
        
        circuits = [
            {'circuit_name': 'AC1', 'total_watts': 12000},
            {'circuit_name': 'Lighting', 'total_watts': 5000},  # Total = 17kW < 25kW
        ]
        
        result = check_three_phase_required(circuits)
        assert result['requires_three_phase'] is False
        assert result['total_connected_load_kw'] <= 25.0
    
    def test_calculate_connected_load(self):
        """Test total load calculation in kW."""
        from core.circuit_grouper import calculate_connected_load
        
        circuits = [
            {'total_watts': 10000},
            {'total_watts': 5000},
            {'total_watts': 8000},
        ]
        
        total_kw = calculate_connected_load(circuits)
        assert total_kw == 23.0


# =============================================================================
# Sprint 2: Phase Balance Tests
# =============================================================================

class TestPhaseBalanceInjector:
    """Test LFD (Largest First Decreasing) phase balance algorithm."""
    
    def test_phase_balance_inject(self):
        """Test circuit assignment to L1/L2/L3."""
        from context.phase_balance_injector import PhaseBalanceInjector
        
        injector = PhaseBalanceInjector()
        
        circuits = [
            {'circuit_name': 'AC1', 'total_kw': 3.6},
            {'circuit_name': 'AC2', 'total_kw': 3.6},
            {'circuit_name': 'AC3', 'total_kw': 3.6},
            {'circuit_name': 'Light1', 'total_kw': 1.0},
            {'circuit_name': 'Light2', 'total_kw': 1.0},
            {'circuit_name': 'Socket', 'total_kw': 2.0},
        ]
        
        result = injector.inject(circuits)
        
        # Check all circuits assigned
        assert len(result.assignments) == len(circuits)
        
        # Check each circuit has a phase
        for circuit_name, phase in result.assignments.items():
            assert phase in ('L1', 'L2', 'L3')
        
        # Check imbalance is calculated
        assert 'imbalance_percent' in result.summary
        assert result.summary['imbalance_percent'] <= 15.0  # Should be under 15%
    
    def test_phase_balance_imbalance_threshold(self):
        """Test imbalance threshold (15% per วสท.)."""
        from context.phase_balance_injector import PhaseBalanceInjector
        
        injector = PhaseBalanceInjector()
        
        # Unbalanced load (one huge, two small)
        circuits = [
            {'circuit_name': 'Big', 'total_kw': 15.0},
            {'circuit_name': 'Small1', 'total_kw': 0.5},
            {'circuit_name': 'Small2', 'total_kw': 0.5},
        ]
        
        result = injector.inject(circuits)
        
        # Should have warning if imbalance > 15%
        if result.summary['imbalance_percent'] > 15.0:
            assert len(result.warnings) > 0


# =============================================================================
# Sprint 3: Three-Phase Wire Sizing Tests
# =============================================================================

class TestThreePhaseWireSizing:
    """Test 3-phase VD formula and calculations."""
    
    def test_3phase_vd_formula(self):
        """Test VD = √3 × I × L × (R cosθ + X sinθ)."""
        from context.three_phase_injector import ThreePhaseInjector
        
        injector = ThreePhaseInjector()
        
        result = injector.calculate_3phase_vd(
            current_a=50,
            distance_m=30,
            wire_size_mm2='10',
            power_factor=0.85
        )
        
        # Should return valid VD values
        assert 'voltage_drop_v' in result
        assert 'voltage_drop_percent' in result
        assert result['voltage_drop_percent'] > 0
        assert result['voltage_drop_percent'] < 10  # Reasonable range
    
    def test_neutral_current_calculation(self):
        """Test neutral current with unbalanced phases."""
        from context.three_phase_injector import ThreePhaseInjector
        
        injector = ThreePhaseInjector()
        
        result = injector.calculate_neutral_current(
            i_l1=50,
            i_l2=45,
            i_l3=40
        )
        
        # Neutral current for unbalanced load
        assert 'neutral_current_a' in result
        assert result['neutral_current_a'] >= 0
        # For slightly unbalanced, neutral should be less than phase currents
        assert result['neutral_current_a'] < 50
    
    def test_3phase_power_calculation(self):
        """Test P = √3 × V × I × cos(θ)."""
        from context.three_phase_injector import ThreePhaseInjector
        
        injector = ThreePhaseInjector()
        
        result = injector.calculate_3phase_power(
            voltage_ll=400,
            current=50,
            power_factor=0.85
        )
        
        # Expected: √3 × 400 × 50 × 0.85 ≈ 29.4 kW
        expected_kw = math.sqrt(3) * 400 * 50 * 0.85 / 1000
        assert abs(result['active_power_kw'] - expected_kw) < 0.1


# =============================================================================
# Sprint 4: Display Layer Tests
# =============================================================================

class TestDisplayLayerThreePhase:
    """Test compute.py 3-phase fields."""
    
    def test_display_data_3phase_fields(self):
        """Test DisplayData includes 3-phase fields."""
        from app.display.compute import compute_display_data
        
        # Mock MCP result with 3-phase data
        mcp_result = {
            'project_name': 'Test 3PH',
            'summary': {
                'total_watts': 35000,
                'demand_current': 55
            },
            'grouped_circuits': [
                {
                    'circuit_name': 'AC1',
                    'total_watts': 12000,
                    'assigned_phase': 'L1'
                },
                {
                    'circuit_name': 'AC2', 
                    'total_watts': 12000,
                    'assigned_phase': 'L2'
                },
                {
                    'circuit_name': 'AC3',
                    'total_watts': 11000,
                    'assigned_phase': 'L3'
                },
            ],
            'three_phase_data': {
                'is_three_phase': True
            },
            'wire_sizing': {},
            'conduit_sizing': {}
        }
        
        display = compute_display_data(mcp_result)
        
        # Check 3-phase fields exist
        assert display.get('is_three_phase') is True
        assert display.get('voltage_system') == '3PH-400V'
        assert display.get('line_voltage_v') == 400
        assert display.get('phase_voltage_v') == 230
    
    def test_ct_meter_sizing_over_30kw(self):
        """Test CT meter selection for loads >30kW."""
        from app.display.compute import _get_meter_sizing
        
        # 3-phase, 40kW load
        meter, wire, breaker = _get_meter_sizing(
            demand_current=60,
            is_three_phase=True,
            total_kw=40
        )
        
        assert 'CT' in meter
        assert '3P' in breaker


# =============================================================================
# Sprint 5: SLD Renderer Tests
# =============================================================================

class TestSLDRenderer3Phase:
    """Test SLD renderer 3-phase features."""
    
    def test_sld_3phase_main_breaker(self):
        """Test 3P main breaker display."""
        from app.display.sld_renderer import render_sld
        
        display_data = {
            'is_three_phase': True,
            'voltage_system': '3PH-400V',
            'main_breaker': '100A',
            'main_wire': '35',
            'meter_size': '50(150)A 3PH',
            'design_current': 55,
            'circuits': [],
            'project_name': 'Test 3PH SLD'
        }
        
        sld = render_sld(display_data)
        
        # Check metadata includes 3-phase info
        assert sld['metadata']['is_three_phase'] is True
        
        # Check main breaker node has 3P
        main_breaker_node = next(
            (n for n in sld['nodes'] if n['id'] == 'main_breaker'),
            None
        )
        assert main_breaker_node is not None
        assert '3P' in main_breaker_node['data'].get('poles', '')
    
    def test_sld_ct_meter_node(self):
        """Test CT meter node display."""
        from app.display.sld_renderer import render_sld
        
        display_data = {
            'is_three_phase': True,
            'meter_size': 'CT Meter (200/5A)',
            'main_breaker': '200A',
            'main_wire': '70',
            'design_current': 180,
            'circuits': [],
            'project_name': 'Test CT Meter'
        }
        
        sld = render_sld(display_data)
        
        meter_node = next(
            (n for n in sld['nodes'] if n['id'] == 'meter'),
            None
        )
        assert meter_node is not None
        assert meter_node['type'] == 'ct_meter'


# =============================================================================
# Sprint 6: BOQ Renderer Tests
# =============================================================================

class TestBOQRenderer3Phase:
    """Test BOQ renderer 3-phase pricing."""
    
    def test_boq_3phase_breaker_pricing(self):
        """Test 3P breaker entries in price catalog."""
        from app.display.boq_renderer import PRICE_CATALOG
        
        # Check 3P MCB entries exist
        assert 'MCB-3P-40AT' in PRICE_CATALOG
        assert 'MCB-3P-63AT' in PRICE_CATALOG
        
        # Check 3P MCCB entries exist
        assert 'MCCB-3P-100AT' in PRICE_CATALOG
        assert 'MCCB-3P-200AT' in PRICE_CATALOG
        
        # Check 3P RCD exists
        assert 'RCCB-4P-63AT-30mA' in PRICE_CATALOG
    
    def test_boq_mdb_pricing(self):
        """Test MDB (Main Distribution Board) pricing."""
        from app.display.boq_renderer import PRICE_CATALOG
        
        # Check MDB entries exist
        assert 'MDB-3PH-12W' in PRICE_CATALOG
        assert 'MDB-3PH-24W' in PRICE_CATALOG
        
        # MDB should have labor cost (installation)
        mdb = PRICE_CATALOG['MDB-3PH-12W']
        assert mdb['labor'] > 0
    
    def test_boq_ct_meter_pricing(self):
        """Test CT meter component pricing."""
        from app.display.boq_renderer import PRICE_CATALOG
        
        assert 'CT-METER-5A' in PRICE_CATALOG
        assert 'CT-200-5A' in PRICE_CATALOG


# =============================================================================
# Sprint 7: MDB & Grounding Tests
# =============================================================================

class TestMDBAndGrounding:
    """Test MDB sizing and grounding calculations."""
    
    def test_size_mdb_panel(self):
        """Test MDB panel sizing."""
        from core.wire_sizer import get_wire_sizer
        
        sizer = get_wire_sizer()
        result = sizer.size_mdb_panel(
            total_load_kw=50,
            circuit_count=12,
            is_three_phase=True,
            voltage_ll=400
        )
        
        assert 'panel_type' in result
        assert 'main_breaker_rating' in result
        assert result['is_three_phase'] is True
        assert result['panel_ways'] >= 12
    
    def test_3phase_ground_sizing(self):
        """Test 3-phase grounding conductor sizing."""
        from core.wire_sizer import get_wire_sizer
        
        sizer = get_wire_sizer()
        result = sizer.size_3phase_ground_wire(
            phase_wire_size='4/0',
            overcurrent_device_rating=200
        )
        
        assert 'equipment_ground' in result
        assert 'electrode_ground' in result
        assert 'main_bonding_jumper' in result


# =============================================================================
# Sprint 8: CT Meter Tests
# =============================================================================

class TestCTMeterIntegration:
    """Test CT meter logic for >30kW loads."""
    
    def test_ct_meter_required_over_30kw(self):
        """Test CT meter required for 3-phase >30kW."""
        from app.display.compute import _get_meter_sizing
        
        # 3-phase, 35kW → CT meter required
        meter, wire, breaker = _get_meter_sizing(
            demand_current=55,
            is_three_phase=True,
            total_kw=35
        )
        
        assert 'CT' in meter
        assert '/5A' in meter  # CT ratio
    
    def test_direct_meter_under_30kw(self):
        """Test direct meter for 3-phase ≤30kW."""
        from app.display.compute import _get_meter_sizing
        
        # 3-phase, 25kW → Direct meter OK
        meter, wire, breaker = _get_meter_sizing(
            demand_current=40,
            is_three_phase=True,
            total_kw=25
        )
        
        assert 'CT' not in meter
        assert '3PH' in meter


# =============================================================================
# Exception Tests
# =============================================================================

class TestThreePhaseExceptions:
    """Test 3-phase specific exceptions."""
    
    def test_three_phase_required_error(self):
        """Test ThreePhaseRequiredError (3PH-001)."""
        from core.exceptions import ThreePhaseRequiredError
        
        error = ThreePhaseRequiredError(
            message="Load exceeds 25kW threshold",
            details={'total_kw': 30}
        )
        
        assert error.code == '3PH-001'
        assert '25kW' in str(error)
    
    def test_phase_balance_warning(self):
        """Test PhaseBalanceWarning (3PH-002)."""
        from core.exceptions import PhaseBalanceWarning
        
        warning = PhaseBalanceWarning(
            message="Phase imbalance exceeds 15%",
            details={'imbalance_percent': 18}
        )
        
        assert warning.code == '3PH-002'


# =============================================================================
# Integration Test - Full Pipeline
# =============================================================================

class TestFullPipelineThreePhase:
    """Test complete 3-phase pipeline flow."""
    
    @pytest.mark.integration
    def test_pipeline_with_3phase_load(self):
        """
        Test full pipeline with 3-phase required load.
        
        This is a real integration test - no mocks!
        Requires MCP Core to be running.
        """
        # This test will be run in CI with actual services
        # For now, mark as integration and skip if services not available
        pytest.skip("Run with integration test suite only")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
