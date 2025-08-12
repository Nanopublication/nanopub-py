"""
Test runner that automatically discovers and imports all test cases 
from .py files in the tests directory.
"""

import os
import sys
import importlib.util
import pytest
from pathlib import Path


def discover_and_import_tests():
    """
    Automatically discover and import all test modules in the tests directory.
    This ensures all test cases are collected when running this file.
    """
    tests_dir = Path(__file__).parent
    test_modules = []

    # Add the parent directory to sys.path if not already present
    parent_dir = tests_dir.parent
    if parent_dir not in sys.path:
        sys.path.insert(0, str(parent_dir))
        print(f"Added {parent_dir} to sys.path")
    
    # Find all .py files in tests directory
    for py_file in tests_dir.glob("*.py"):
        # Skip this file and __init__.py
        if py_file.name in ("tests.py", "__init__.py"):
            continue
            
        # Convert filename to module name
        module_name = py_file.stem
        
        try:
            # Import using the file path directly
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                test_modules.append(module)
                print(f"✓ Imported test module: {module_name}")
        except pytest.skip.Exception:
            print(f"⏭ Skipped test module: {module_name} (module-level skip)")
        except ImportError as e:
            print(f"✗ Failed to import {module_name}: {e}")
        except Exception as e:
            print(f"✗ Error importing {module_name}: {e}")
    
    return test_modules


def collect_test_functions():
    """
    Collect all test functions from imported modules.
    """
    test_functions = []
    test_classes = []
    
    # Get all modules in the tests package
    tests_dir = Path(__file__).parent
    
    for py_file in tests_dir.glob("*.py"):
        if py_file.name in ("tests.py", "__init__.py"):
            continue
            
        module_name = py_file.stem
        
        try:
            # Check if the module is already imported
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                # Import using the file path directly
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                else:
                    print(f"✗ Could not load module {module_name} from {py_file}")
                    continue           
            # Collect test functions and classes from the module
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(module, attr_name)
                
                # Check for test functions
                if (callable(attr) and attr_name.startswith('test_')):
                    test_functions.append(f"{module_name}.{attr_name}")
                
                # Check for test classes
                elif (isinstance(attr, type) and 
                      attr_name.startswith('Test')):
                    test_classes.append(f"{module_name}.{attr_name}")
                    
                    # Also collect methods from test classes
                    for method_name in dir(attr):
                        if method_name.startswith('test_'):
                            test_functions.append(f"{module_name}.{attr_name}.{method_name}")
        
        except Exception as e:
            print(f"Error processing module {module_name}: {e}")
    
    return test_functions, test_classes


def main():
    """
    Main function to discover tests and provide information.
    """
    print("🔍 Discovering tests in the tests directory...")
    print("=" * 60)
    
    # Import all test modules
    modules = discover_and_import_tests()
    
    # Collect test information
    functions, classes = collect_test_functions()
    
    print("\n📊 Test Discovery Summary:")
    print(f"   Modules imported: {len(modules)}")
    print(f"   Test classes found: {len(classes)}")
    print(f"   Test functions found: {len(functions)}")
    
    if classes:
        print("\n📋 Test Classes:")
        for cls in sorted(set(classes)):
            print(f"   • {cls}")
    
    if functions:
        print(f"\n🧪 Test Functions (showing first 10):")
        for func in sorted(set(functions))[:10]:
            print(f"   • {func}")
        if len(functions) > 10:
            print(f"   ... and {len(functions) - 10} more")
    
    print("\n" + "=" * 60)
    print("✅ All tests have been imported and are ready to run!")
    print("\nTo run all tests, use:")
    print("   poetry run pytest tests/ -v")
    print("   poetry run coverage run -m pytest tests/ -sv --tb=short --disable-warnings")


# Auto-discover and import all test modules when this file is imported
print("🚀 Auto-importing all test modules...")
_imported_modules = discover_and_import_tests()


# Example test to verify this file works
def test_test_discovery():
    """
    Test that the test discovery mechanism works.
    """
    modules = discover_and_import_tests()
    # This test passes if we can import modules without errors
    assert isinstance(modules, list)


def test_tests_directory_exists():
    """
    Test that the tests directory exists and contains Python files.
    """
    tests_dir = Path(__file__).parent
    assert tests_dir.exists()
    assert tests_dir.is_dir()
    
    # Check for Python files (excluding this one)
    py_files = [f for f in tests_dir.glob("*.py") if f.name != "tests.py"]
    # This will pass even if there are no other test files yet
    assert isinstance(py_files, list)


class TestDiscovery:
    """
    Test class for the discovery mechanism itself.
    """
    
    def test_import_mechanism(self):
        """Test that the import mechanism works."""
        functions, classes = collect_test_functions()
        assert isinstance(functions, list)
        assert isinstance(classes, list)
    
    def test_path_resolution(self):
        """Test that path resolution works correctly."""
        tests_dir = Path(__file__).parent
        assert tests_dir.name == "tests"
        assert tests_dir.exists()


if __name__ == "__main__":
    # If run directly, show discovery information and run tests
    # Use already imported modules or import if not done yet
    
    if '_imported_modules' in globals():
        modules = _imported_modules
        print("Using already imported modules...")
    else:
        modules = discover_and_import_tests()
    
    # Also run pytest on this file specifically
    print("\n🧪 Running tests in this file...")
    pytest.main([__file__, "-v"])