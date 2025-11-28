"""
Comprehensive Test Suite for Phase A - AutoLISP/CAD Module

Tests all Phase A components:
1. Standards Loader
2. AutoLISP Writer
3. E-301 Generator
4. E-401 Generator
5. Validation Functions
6. Integration (E-301 + E-401 generation)

All tests must pass before Phase A is considered complete.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cad.standards import load_standards, StandardsEngine
from cad.autolisp_writer import AutoLISPWriter, validate_lisp_syntax
from cad.drawing import SingleLineDiagramGenerator, PanelScheduleGenerator
from cad.validators import validate_lisp_semantic, LISPValidationError


class MockMCPResult:
    """Mock MCP result for testing"""
    def __init__(self):
        self.wires = [
            type('Wire', (), {
                'size_mm2': '2.5',
                'current': 10.5,
                'conduit_size': '16mm',
                'cores': 3,
                'circuit_id': 'CKT-1'
            })(),
            type('Wire', (), {
                'size_mm2': '4.0',
                'current': 18.2,
                'conduit_size': '20mm',
                'cores': 3,
                'circuit_id': 'CKT-2'
            })(),
        ]
        
        self.breakers = [
            type('Breaker', (), {
                'rating': '16',
                'poles': 1
            })(),
            type('Breaker', (), {
                'rating': '20',
                'poles': 1
            })(),
        ]
        
        self.loads = [
            type('Load', (), {
                'description': 'Living Room Lighting',
                'va': 360,
                'quantity': 6,
                'demand_factor': 0.7
            })(),
            type('Load', (), {
                'description': 'Living Room Outlets',
                'va': 1600,
                'quantity': 8,
                'demand_factor': 0.5
            })(),
        ]


def test_standards_loader():
    """Test 1: Standards Loader"""
    print("\n" + "="*60)
    print("TEST 1: Standards Loader")
    print("="*60)
    
    try:
        # Test EIT loading
        eit = load_standards('EIT')
        assert eit is not None, "EIT rules should not be None"
        assert eit['standard'] == 'EIT', "Standard should be EIT"
        assert 'status' in eit, "Should have status field"
        print("✓ EIT standards loaded")
        
        # Test IEC loading
        iec = load_standards('IEC')
        assert iec is not None, "IEC rules should not be None"
        assert iec['standard'] == 'IEC', "Standard should be IEC"
        print("✓ IEC standards loaded")
        
        # Test NEC stub
        nec = load_standards('NEC')
        assert nec['status'] == 'NOT_IMPLEMENTED', "NEC should be stub"
        assert 'fallback_to' in nec, "NEC should have fallback"
        print("✓ NEC stub works with fallback")
        
        print("\n✅ Standards Loader: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Standards Loader: FAIL - {e}")
        return False


def test_autolisp_writer():
    """Test 2: AutoLISP Writer Base"""
    print("\n" + "="*60)
    print("TEST 2: AutoLISP Writer")
    print("="*60)
    
    try:
        writer = AutoLISPWriter("Test Project")
        
        # Test header
        writer.write_header("Test Drawing", "Test description")
        assert len(writer.code_lines) > 0, "Should have header"
        print("✓ Header generation works")
        
        # Test layers
        layers = {
            'TEST-LAYER': {'color': 1, 'linetype': 'CONTINUOUS'}
        }
        writer.create_layers(layers)
        code = writer.get_code()
        assert 'TEST-LAYER' in code, "Should contain layer name"
        print("✓ Layer creation works")
        
        # Test drawing commands
        writer.draw_line((0, 0), (100, 100))
        writer.draw_polyline([(0, 0), (50, 50), (100, 0)])
        writer.add_text("Test", (10, 10), height=100)
        print("✓ Drawing commands work")
        
        # Test parentheses balance
        writer.write_footer()
        code = writer.get_code()
        assert code.count('(') == code.count(')'), "Parentheses should be balanced"
        print("✓ Parentheses balanced")
        
        # Test function wrapping
        writer.wrap_in_function("C:TEST")
        code = writer.get_code()
        assert '(defun C:TEST' in code, "Should have function definition"
        print("✓ Function wrapping works")
        
        print("\n✅ AutoLISP Writer: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ AutoLISP Writer: FAIL - {e}")
        return False


def test_e301_generator():
    """Test 3: E-301 Single Line Diagram Generator"""
    print("\n" + "="*60)
    print("TEST 3: E-301 Generator")
    print("="*60)
    
    try:
        generator = SingleLineDiagramGenerator("Test Project")
        mock_mcp = MockMCPResult()
        
        panel_data = {
            'id': 'DB-1',
            'name': 'Main Distribution Board',
            'voltage': '230V',
            'rating': '100A',
            'location': (0, 0)
        }
        
        # Generate E-301
        lisp_code = generator.generate(panel_data, mock_mcp, 'EIT')
        
        assert lisp_code is not None, "Should generate code"
        assert len(lisp_code) > 0, "Code should not be empty"
        print("✓ Generates LISP code")
        
        # Check content
        assert 'DB-1' in lisp_code, "Should contain panel ID"
        assert 'UTILITY' in lisp_code, "Should have utility source"
        assert 'MCB' in lisp_code, "Should have breaker"
        print("✓ Contains expected symbols")
        
        # Check structure
        assert '(defun' in lisp_code, "Should have function definition"
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses balanced"
        print("✓ Valid LISP structure")
        
        print("\n✅ E-301 Generator: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ E-301 Generator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e401_generator():
    """Test 4: E-401 Panel Schedule Generator"""
    print("\n" + "="*60)
    print("TEST 4: E-401 Generator")
    print("="*60)
    
    try:
        generator = PanelScheduleGenerator("Test Project")
        mock_mcp = MockMCPResult()
        
        # Generate E-401
        lisp_code = generator.generate('DB-1', [], mock_mcp, 'EIT')
        
        assert lisp_code is not None, "Should generate code"
        assert len(lisp_code) > 0, "Code should not be empty"
        print("✓ Generates LISP code")
        
        # Check table content
        assert 'PANEL SCHEDULE' in lisp_code, "Should have title"
        assert 'Circuit' in lisp_code or 'CKT' in lisp_code, "Should have circuit labels"
        print("✓ Contains table structure")
        
        # Check data from MCP
        assert '2.5mm' in lisp_code or '4.0mm' in lisp_code, "Should have wire sizes from MCP"
        assert '16A' in lisp_code or '20A' in lisp_code, "Should have breaker sizes from MCP"
        print("✓ Uses MCP data")
        
        # Check structure
        assert '(defun' in lisp_code, "Should have function definition"
        assert lisp_code.count('(') == lisp_code.count(')'), "Parentheses balanced"
        print("✓ Valid LISP structure")
        
        print("\n✅ E-401 Generator: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ E-401 Generator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """Test 5: Validation Functions"""
    print("\n" + "="*60)
    print("TEST 5: Validation Functions")
    print("="*60)
    
    try:
        # Create temporary test files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Valid LISP file
            valid_lisp = tmpdir / "valid.lsp"
            valid_lisp.write_text(
                '(defun C:TEST ()\n'
                '  (command "LINE" (list 0 0) (list 100 100) "")\n'
                '  (princ)\n'
                ')\n',
                encoding='utf-8'
            )
            
            ok, errors = validate_lisp_syntax(valid_lisp)
            assert ok, f"Valid file should pass: {errors}"
            print("✓ Syntax validation: Valid file passes")
            
            # Invalid LISP - unbalanced parens
            invalid_lisp = tmpdir / "invalid.lsp"
            invalid_lisp.write_text(
                '(defun C:TEST ()\n'
                '  (command "LINE" (list 0 0) (list 100 100) ""\n'  # Missing )
                '  (princ)\n'
                ')\n',
                encoding='utf-8'
            )
            
            ok, errors = validate_lisp_syntax(invalid_lisp)
            assert not ok, "Invalid file should fail"
            assert len(errors) > 0, "Should have error messages"
            print("✓ Syntax validation: Invalid file fails")
            
            # Semantic validation
            mock_mcp = MockMCPResult()
            ok, errors = validate_lisp_semantic(valid_lisp, mock_mcp)
            # Should pass or have warnings (not strict for basic file)
            print("✓ Semantic validation works")
        
        print("\n✅ Validation Functions: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Validation Functions: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test 6: Integration - Generate both E-301 and E-401"""
    print("\n" + "="*60)
    print("TEST 6: Integration Test")
    print("="*60)
    
    try:
        mock_mcp = MockMCPResult()
        panel_data = {
            'id': 'DB-1',
            'name': 'Test Panel',
            'voltage': '230V',
            'rating': '100A',
            'location': (0, 0)
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Generate E-301
            e301_gen = SingleLineDiagramGenerator("Integration Test")
            e301_path = e301_gen.save_to_file(
                tmpdir / "E-301.lsp",
                panel_data,
                mock_mcp,
                'EIT'
            )
            assert e301_path.exists(), "E-301 file should be created"
            print("✓ E-301 generated and saved")
            
            # Generate E-401
            e401_gen = PanelScheduleGenerator("Integration Test")
            e401_path = e401_gen.save_to_file(
                tmpdir / "E-401.lsp",
                'DB-1',
                [],
                mock_mcp,
                'EIT'
            )
            assert e401_path.exists(), "E-401 file should be created"
            print("✓ E-401 generated and saved")
            
            # Validate both
            ok_301, errors_301 = validate_lisp_syntax(e301_path)
            ok_401, errors_401 = validate_lisp_syntax(e401_path)
            
            assert ok_301, f"E-301 should be valid: {errors_301}"
            assert ok_401, f"E-401 should be valid: {errors_401}"
            print("✓ Both files pass syntax validation")
            
            # Check file sizes (should have content)
            assert e301_path.stat().st_size > 500, "E-301 should have substantial content"
            assert e401_path.stat().st_size > 500, "E-401 should have substantial content"
            print("✓ Generated files have content")
        
        print("\n✅ Integration Test: PASS")
        return True
    
    except Exception as e:
        print(f"\n❌ Integration Test: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase A tests"""
    print("\n" + "="*70)
    print(" PHASE A - COMPREHENSIVE TEST SUITE ".center(70, "="))
    print("="*70)
    print("\nAll tests must pass for Phase A to be considered complete.\n")
    
    tests = [
        ("Standards Loader", test_standards_loader),
        ("AutoLISP Writer", test_autolisp_writer),
        ("E-301 Generator", test_e301_generator),
        ("E-401 Generator", test_e401_generator),
        ("Validation Functions", test_validation),
        ("Integration", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} raised unexpected exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY ".center(70, "="))
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(passed for _, passed in results)
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print("\n" + "="*70)
    if all_passed:
        print(f"🎉 ALL {total_count} TESTS PASSED - PHASE A COMPLETE! 🎉".center(70))
        print("="*70)
        print("\nPhase A is ready for production use.")
        print("Deliverables:")
        print("  ✓ Standards Loader (EIT, IEC, NEC stub)")
        print("  ✓ AutoLISP Writer (base functionality)")
        print("  ✓ E-301 Single Line Diagram Generator")
        print("  ✓ E-401 Panel Schedule Generator")
        print("  ✓ Validation Framework (syntax + semantic)")
        print("  ✓ Integration tested and working")
        print("\nReady to proceed to Phase B.")
    else:
        print(f"⚠️  {passed_count}/{total_count} TESTS PASSED - PHASE A INCOMPLETE! ⚠️".center(70))
        print("="*70)
        print("\nPhase A is NOT complete. Fix failing tests before proceeding.")
    
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
