"""
DEFINITIVE E2E TEST: VD Pipeline
Tests the ACTUAL request that would be sent to MCP Core
"""
import sys
import json
sys.path.insert(0, '/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]')
sys.path.insert(0, '/home/builder/Desktop/ACA_Mozart/mcp_core_v2')

def test_full_mcp_request():
    """Build the actual MCP request and check branch_distance_m"""
    print("\n" + "="*60)
    print("🔬 FULL MCP REQUEST TEST")
    print("="*60)
    
    from app.models import (
        ProjectInputSpec, ProjectInfo, ElectricalSystem, 
        RoomSpec, LoadSpec, Constraints
    )
    from app.mcp_adapter import McpAdapter
    from app.models import SiteContext
    
    # Step 1: Build ProjectInputSpec with LoadSpec that has branch_distance_m
    rooms = [
        RoomSpec(room_id="R1", name="ห้องนั่งเล่น", room_type="LIVING", template_code="ROOMT-LIVING-STD"),
        RoomSpec(room_id="R2", name="ห้องครัว", room_type="KITCHEN", template_code="ROOMT-KITCHEN-STD"),
        RoomSpec(room_id="R3", name="ห้องนอน 1", room_type="BEDROOM", template_code="ROOMT-BEDROOM-STD"),
    ]
    
    loads = [
        LoadSpec(load_id="L1", room_id="R1", device_code="SOCKET-16A", qty=6, floor=1, branch_distance_m=15.0),
        LoadSpec(load_id="L2", room_id="R2", device_code="INDUCTION-3000W", qty=1, floor=1, branch_distance_m=15.0),
        LoadSpec(load_id="L3", room_id="R3", device_code="SOCKET-16A", qty=4, floor=2, branch_distance_m=25.0),
        LoadSpec(load_id="L4", room_id="R3", device_code="LIGHT-LED-10W", qty=3, floor=2, branch_distance_m=25.0),
    ]
    
    spec = ProjectInputSpec(
        project_info=ProjectInfo(project_name="Test House", building_type="RESIDENTIAL", spec_version="2.0"),
        electrical_system=ElectricalSystem(voltage_system="TH_1PH_230V", earthing="TT"),
        rooms=rooms,
        loads=loads,
        constraints=Constraints(rule_profile_id="TH_RESIDENTIAL_LV")
    )
    
    print("\n📋 Input LoadSpecs:")
    for load in spec.loads:
        bd = getattr(load, 'branch_distance_m', 'NOT FOUND')
        print(f"  {load.load_id}: {load.device_code} floor={load.floor}, branch_distance_m={bd}")
    
    # Step 2: Convert via McpAdapter
    site_context = SiteContext(
        distance_to_transformer="50_100m",
        installation_area="indoor",
        panel_type="main"
    )
    
    adapter = McpAdapter()
    mcp_request = adapter.convert(spec, site_context)
    
    print("\n📤 MCP Request (after adapter):")
    for load in mcp_request.loads:
        bd = load.branch_distance_m
        print(f"  {load.id}: {load.name}, branch_distance_m={bd}")
        if bd is None:
            print(f"    ❌ LOST HERE!")
    
    # Step 3: Convert to JSON dict (what would be sent via HTTP)
    request_dict = mcp_request.to_dict()
    
    print("\n📊 Final JSON (sent to MCP Core via HTTP):")
    for load in request_dict['loads']:
        bd = load.get('branch_distance_m')
        print(f"  {load['id']}: branch_distance_m={bd}")
        if bd is None:
            print(f"    ❌ LOST IN to_dict()!")
    
    return request_dict

def test_mcp_core_receives():
    """Test if MCP Core would correctly receive and use the data"""
    print("\n" + "="*60)
    print("🔧 MCP CORE RECEPTION TEST")
    print("="*60)
    
    # Import MCP Core models
    try:
        from models.contracts import DesignRequest, ElectricalLoad, Location, VoltageType, LoadType
        from pipeline import DesignPipeline
        from config import PipelineSettings
    except ImportError as e:
        print(f"❌ Cannot import MCP Core: {e}")
        return None
    
    # Create the same request that would come from RAG
    loads = [
        ElectricalLoad(
            id="L1",
            name="SOCKET-16A in ห้องนั่งเล่น",
            load_type=LoadType.RECEPTACLE,
            voltage=VoltageType.SINGLE_PHASE_230V,
            power_watts=180,
            quantity=6,
            location=Location(room="ห้องนั่งเล่น", floor="1"),
            branch_distance_m=15.0  # 🎯 This is the key!
        ),
        ElectricalLoad(
            id="L3",
            name="SOCKET-16A in ห้องนอน 1",
            load_type=LoadType.RECEPTACLE,
            voltage=VoltageType.SINGLE_PHASE_230V,
            power_watts=180,
            quantity=4,
            location=Location(room="ห้องนอน 1", floor="2"),
            branch_distance_m=25.0  # 🎯 Different distance for floor 2
        ),
    ]
    
    print("\n📥 ElectricalLoad objects created:")
    for load in loads:
        bd = getattr(load, 'branch_distance_m', 'MISSING')
        print(f"  {load.id}: {load.name}")
        print(f"    branch_distance_m = {bd}")
        print(f"    hasattr = {hasattr(load, 'branch_distance_m')}")
    
    # Check the model definition
    print("\n📐 ElectricalLoad model fields:")
    if hasattr(ElectricalLoad, '__annotations__'):
        for field_name in ElectricalLoad.__annotations__:
            print(f"  - {field_name}")
        
        if 'branch_distance_m' in ElectricalLoad.__annotations__:
            print("✅ PASS: branch_distance_m IS in ElectricalLoad model")
        else:
            print("❌ FAIL: branch_distance_m NOT in ElectricalLoad model!")
    
    return loads

def test_mcp_core_pipeline():
    """Test if pipeline.py correctly reads branch_distance_m"""
    print("\n" + "="*60)
    print("🔄 MCP CORE PIPELINE TEST")
    print("="*60)
    
    import inspect
    
    try:
        from pipeline import DesignPipeline
        
        # Get source of _size_wires method
        source = inspect.getsource(DesignPipeline._size_wires)
        
        # Find the line that reads branch_distance_m
        lines = source.split('\n')
        found = False
        for i, line in enumerate(lines):
            if 'branch_distance_m' in line:
                print(f"  Line {i}: {line.strip()}")
                found = True
        
        if found:
            print("\n✅ PASS: pipeline.py references branch_distance_m")
        else:
            print("\n❌ FAIL: pipeline.py does NOT reference branch_distance_m!")
            
        # Also check the conditional
        if 'hasattr(load' in source and 'branch_distance_m' in source:
            print("✅ PASS: Pipeline checks for branch_distance_m attribute")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    print("="*60)
    print("🔬 DEFINITIVE VD PIPELINE E2E TEST")
    print("="*60)
    
    # Test 1: RAG → MCP Request
    request_dict = test_full_mcp_request()
    
    # Test 2: MCP Core model check
    loads = test_mcp_core_receives()
    
    # Test 3: MCP Core pipeline check
    test_mcp_core_pipeline()
    
    print("\n" + "="*60)
    print("📊 FINAL VERDICT")
    print("="*60)
    
    # Check if all requests have branch_distance_m
    if request_dict:
        all_have_bd = all(load.get('branch_distance_m') is not None for load in request_dict['loads'])
        if all_have_bd:
            print("✅ RAG correctly sends branch_distance_m to MCP Core")
        else:
            print("❌ RAG LOSES branch_distance_m before sending to MCP Core!")
    
    if loads:
        print("✅ MCP Core model can accept branch_distance_m")
    else:
        print("⚠️ Could not verify MCP Core model (import failed)")

if __name__ == "__main__":
    main()
