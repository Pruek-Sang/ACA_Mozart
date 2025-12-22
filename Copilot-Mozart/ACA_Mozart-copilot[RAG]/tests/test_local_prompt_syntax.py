#!/usr/bin/env python3
"""
Local Unit Test - Debug Empty Loads Issue

This test can run WITHOUT Cloud Run!
It tests only the extraction prompt to verify f-string syntax is correct.

Usage:
    cd Copilot-Mozart/ACA_Mozart-copilot[RAG]
    python tests/test_local_prompt_syntax.py
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_extraction_prompt_syntax():
    """
    Test that the extraction prompt doesn't have f-string errors.
    This is the bug that caused 'Invalid format specifier' error.
    """
    print("🧪 Testing extraction prompt f-string syntax...")
    
    try:
        # This will fail if there are f-string escape issues
        from app.service import RagService
        print("✅ service.py imported successfully - no f-string syntax errors!")
        return True
    except ValueError as e:
        if "format specifier" in str(e):
            print(f"❌ F-STRING BUG DETECTED: {e}")
            print("\n💡 Fix: Use {{ }} instead of { } in f-string prompts")
            return False
        raise
    except Exception as e:
        print(f"❌ Import failed with unexpected error: {e}")
        return False

def test_prompt_content():
    """
    Test that the prompt content is valid and includes required fields.
    """
    print("\n🧪 Testing prompt content includes required fields...")
    
    try:
        from app.service import RagService
        
        # Create a dummy service (won't call LLM)
        # We just want to check the prompt strings exist
        service = RagService.__new__(RagService)
        
        # Check if extraction prompt has DEVICE_CODES
        import inspect
        source = inspect.getsource(RagService._extract_loads_from_text)
        
        checks = [
            ("DEVICE_CODES list", "AC-9000BTU" in source or "DEVICE_MAPPING" in source),
            ("rooms array", '"rooms"' in source),
            ("loads array", '"loads"' in source),
            ("floor field", '"floor"' in source),
            ("branch_distance_m (new)", "branch_distance_m" in source),
            ("service_distance_m (new)", "service_distance_m" in source),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to check prompt content: {e}")
        return False

def test_models_have_distance_fields():
    """
    Test that models have the new distance fields for VD calculation.
    """
    print("\n🧪 Testing models have distance fields...")
    
    try:
        from app.models import ProjectRequirements, LoadInput, LoadSpec, ProjectInfo
        
        checks = [
            ("ProjectRequirements.service_distance_m", hasattr(ProjectRequirements, 'model_fields') and 'service_distance_m' in ProjectRequirements.model_fields),
            ("LoadInput.branch_distance_m", hasattr(LoadInput, 'model_fields') and 'branch_distance_m' in LoadInput.model_fields),
            ("LoadSpec.branch_distance_m", hasattr(LoadSpec, 'model_fields') and 'branch_distance_m' in LoadSpec.model_fields),
            ("ProjectInfo.service_distance_m", hasattr(ProjectInfo, 'model_fields') and 'service_distance_m' in ProjectInfo.model_fields),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_mcp_adapter_maps_distances():
    """
    Test that MCP adapter includes distance fields in output.
    """
    print("\n🧪 Testing MCP adapter maps distance fields...")
    
    try:
        from app.mcp_adapter import McpElectricalLoad, McpDesignRequest
        
        checks = [
            ("McpElectricalLoad.branch_distance_m", hasattr(McpElectricalLoad, '__dataclass_fields__') and 'branch_distance_m' in McpElectricalLoad.__dataclass_fields__),
            ("McpDesignRequest.service_distance_m", hasattr(McpDesignRequest, '__dataclass_fields__') and 'service_distance_m' in McpDesignRequest.__dataclass_fields__),
            ("McpDesignRequest.building_type", hasattr(McpDesignRequest, '__dataclass_fields__') and 'building_type' in McpDesignRequest.__dataclass_fields__),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
            if not passed:
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 LOCAL DIAGNOSTIC TEST - Empty Loads Debug")
    print("=" * 60)
    print("This test runs locally without Cloud Run.\n")
    
    results = []
    
    # Test 1: F-string syntax (CRITICAL)
    results.append(("F-String Syntax", test_extraction_prompt_syntax()))
    
    # Test 2: Prompt content
    results.append(("Prompt Content", test_prompt_content()))
    
    # Test 3: Models have fields
    results.append(("Model Fields", test_models_have_distance_fields()))
    
    # Test 4: Adapter maps fields
    results.append(("Adapter Mapping", test_mcp_adapter_maps_distances()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All local tests passed!")
        print("💡 If Cloud Run still fails, the issue is in:")
        print("   - LLM response (API/rate limit)")
        print("   - Gateway routing")
        print("   - MCP Core connection")
    else:
        print("🔴 Some tests failed! Fix before deploying.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
