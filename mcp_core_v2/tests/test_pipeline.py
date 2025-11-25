"""Tests for the design pipeline."""

import pytest
from datetime import datetime
from models.contracts import (
    DesignRequest, ElectricalLoad, PanelSpecification,
    Location, VoltageType, LoadType
)
from pipeline import get_design_pipeline


@pytest.fixture
def sample_loads():
    """Create sample electrical loads for testing."""
    return [
        ElectricalLoad(
            id="test_load_001",
            name="Test Lighting",
            load_type=LoadType.LIGHTING,
            voltage=VoltageType.SINGLE_PHASE_120V,
            power_watts=1000,
            quantity=5,
            location=Location(room="Test Room", floor="1"),
            is_continuous=True
        ),
        ElectricalLoad(
            id="test_load_002",
            name="Test Receptacle",
            load_type=LoadType.RECEPTACLE,
            voltage=VoltageType.SINGLE_PHASE_120V,
            power_watts=180,
            quantity=10,
            location=Location(room="Test Room", floor="1"),
            is_continuous=False
        ),
        ElectricalLoad(
            id="test_load_003",
            name="Test HVAC",
            load_type=LoadType.HVAC,
            voltage=VoltageType.SINGLE_PHASE_240V,
            power_watts=3000,
            quantity=1,
            location=Location(room="Mechanical", floor="Roof"),
            is_continuous=True
        ),
    ]


@pytest.fixture
def sample_panel(sample_loads):
    """Create a sample panel specification."""
    return PanelSpecification(
        id="test_panel_001",
        name="TP-1",
        voltage=VoltageType.SINGLE_PHASE_120V,
        main_breaker_rating=200,
        number_of_circuits=42,
        location=Location(room="Electrical Room", floor="1"),
        feeds=[load.id for load in sample_loads]
    )


@pytest.fixture
def sample_request(sample_loads, sample_panel):
    """Create a sample design request."""
    return DesignRequest(
        session_id="test_session_001",
        project_name="Test Project",
        project_number="TEST-001",
        loads=sample_loads,
        panels=[sample_panel],
        service_voltage=VoltageType.SINGLE_PHASE_240V,
        utility_service_size=200
    )


class TestDesignPipeline:
    """Test suite for the design pipeline."""
    
    def test_pipeline_initialization(self):
        """Test that pipeline initializes correctly."""
        pipeline = get_design_pipeline()
        assert pipeline is not None
        assert pipeline.template_resolver is not None
        assert pipeline.load_calculator is not None
        assert pipeline.wire_sizer is not None
        assert pipeline.breaker_selector is not None
        assert pipeline.conduit_sizer is not None
        assert pipeline.compliance_checker is not None
        assert pipeline.autolisp_generator is not None
        assert pipeline.result_builder is not None
    
    def test_pipeline_execute(self, sample_request):
        """Test complete pipeline execution."""
        pipeline = get_design_pipeline()
        result = pipeline.execute(sample_request)
        
        # Verify result structure
        assert result is not None
        assert result.session_id == sample_request.session_id
        assert result.request == sample_request
        assert result.calculations is not None
        assert result.wire_sizing is not None
        assert result.breaker_selections is not None
        assert result.conduit_sizing is not None
        assert result.compliance_report is not None
        
        # Verify calculations exist for the panel
        assert "test_panel_001" in result.calculations
        panel_calc = result.calculations["test_panel_001"]
        assert "total_va" in panel_calc
        assert "total_current" in panel_calc
        assert "demand_current" in panel_calc
    
    def test_template_resolution(self, sample_request):
        """Test template resolution step."""
        pipeline = get_design_pipeline()
        templates = pipeline._resolve_templates(sample_request)
        
        assert templates is not None
        assert len(templates) > 0
        
        # Check that templates were resolved for each load
        for load in sample_request.loads:
            assert load.id in templates
    
    def test_load_calculations(self, sample_request):
        """Test load calculation step."""
        pipeline = get_design_pipeline()
        calculations = pipeline._calculate_loads(sample_request)
        
        assert calculations is not None
        assert "test_panel_001" in calculations
        
        panel_calc = calculations["test_panel_001"]
        assert panel_calc["total_va"] > 0
        assert panel_calc["total_current"] > 0
        assert "load_breakdown" in panel_calc
    
    def test_wire_sizing(self, sample_request):
        """Test wire sizing step."""
        pipeline = get_design_pipeline()
        calculations = pipeline._calculate_loads(sample_request)
        wire_sizing = pipeline._size_wires(sample_request, calculations)
        
        assert wire_sizing is not None
        
        # Check wire sizing for each load
        for load in sample_request.loads:
            assert load.id in wire_sizing
            wire_data = wire_sizing[load.id]
            
            # Should have wire size if no errors
            if 'error' not in wire_data:
                assert 'wire_size' in wire_data
                assert 'ampacity' in wire_data
    
    def test_breaker_selection(self, sample_request):
        """Test breaker selection step."""
        pipeline = get_design_pipeline()
        calculations = pipeline._calculate_loads(sample_request)
        breaker_selections = pipeline._select_breakers(sample_request, calculations)
        
        assert breaker_selections is not None
        
        # Check breaker selection for each load
        for load in sample_request.loads:
            assert load.id in breaker_selections
            breaker_data = breaker_selections[load.id]
            
            if 'error' not in breaker_data:
                assert 'breaker_rating' in breaker_data
                assert 'poles' in breaker_data
    
    def test_conduit_sizing(self, sample_request):
        """Test conduit sizing step."""
        pipeline = get_design_pipeline()
        calculations = pipeline._calculate_loads(sample_request)
        wire_sizing = pipeline._size_wires(sample_request, calculations)
        breaker_selections = pipeline._select_breakers(sample_request, calculations)
        conduit_sizing = pipeline._size_conduits(sample_request, wire_sizing, breaker_selections)
        
        assert conduit_sizing is not None
        
        # Check conduit sizing for loads with valid wire sizing
        for load in sample_request.loads:
            if load.id in wire_sizing and 'wire_size' in wire_sizing[load.id]:
                assert load.id in conduit_sizing
    
    def test_compliance_checking(self, sample_request):
        """Test compliance checking step."""
        pipeline = get_design_pipeline()
        compliance_report = pipeline._check_compliance(sample_request)
        
        assert compliance_report is not None
        assert 'compliant' in compliance_report
        assert 'issues' in compliance_report
        assert 'warnings' in compliance_report
        assert 'nec_version' in compliance_report
    
    def test_autolisp_generation(self, sample_request):
        """Test AutoLISP code generation."""
        pipeline = get_design_pipeline()
        calculations = pipeline._calculate_loads(sample_request)
        wire_sizing = pipeline._size_wires(sample_request, calculations)
        breaker_selections = pipeline._select_breakers(sample_request, calculations)
        conduit_sizing = pipeline._size_conduits(sample_request, wire_sizing, breaker_selections)
        
        design_results = {
            'calculations': calculations,
            'wire_sizing': wire_sizing,
            'breaker_selections': breaker_selections,
            'conduit_sizing': conduit_sizing
        }
        
        autolisp_code = pipeline._generate_autolisp(sample_request, design_results)
        
        assert autolisp_code is not None
        assert len(autolisp_code) > 0
        assert "defun" in autolisp_code.lower()
    
    def test_result_building(self, sample_request):
        """Test result building."""
        pipeline = get_design_pipeline()
        result = pipeline.execute(sample_request)
        
        # Test result summary
        summary = pipeline.result_builder.create_summary(result)
        assert summary is not None
        assert summary['session_id'] == sample_request.session_id
        assert summary['project_name'] == sample_request.project_name
        assert 'component_count' in summary
        assert 'status' in summary
        
        # Test load summary
        load_summary = pipeline.result_builder.create_load_summary(result)
        assert load_summary is not None
        assert 'lighting' in load_summary
        assert 'receptacle' in load_summary
        
        # Test panel summary
        panel_summary = pipeline.result_builder.create_panel_summary(result)
        assert panel_summary is not None
        assert 'test_panel_001' in panel_summary


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_loads(self):
        """Test pipeline with no loads."""
        request = DesignRequest(
            session_id="test_empty",
            project_name="Empty Test",
            loads=[],
            panels=[],
            service_voltage=VoltageType.SINGLE_PHASE_240V,
            utility_service_size=100
        )
        
        pipeline = get_design_pipeline()
        result = pipeline.execute(request)
        
        assert result is not None
        assert len(result.request.loads) == 0
    
    def test_high_power_load(self):
        """Test with high power load."""
        high_power_load = ElectricalLoad(
            id="high_power",
            name="Large Motor",
            load_type=LoadType.MOTOR,
            voltage=VoltageType.THREE_PHASE_480V,
            power_watts=50000,  # 50kW
            quantity=1,
            location=Location(room="Plant", floor="1"),
            is_continuous=True
        )
        
        panel = PanelSpecification(
            id="industrial_panel",
            name="MP-1",
            voltage=VoltageType.THREE_PHASE_480V,
            main_breaker_rating=400,
            number_of_circuits=42,
            location=Location(room="Electrical Room"),
            feeds=["high_power"]
        )
        
        request = DesignRequest(
            session_id="test_high_power",
            project_name="High Power Test",
            loads=[high_power_load],
            panels=[panel],
            service_voltage=VoltageType.THREE_PHASE_480V,
            utility_service_size=400
        )
        
        pipeline = get_design_pipeline()
        result = pipeline.execute(request)
        
        assert result is not None
        assert result.wire_sizing is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
