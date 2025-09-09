#!/usr/bin/env python3
"""
Simple validation script to verify fixes without external dependencies
Run this with any Python interpreter to validate the codebase
"""

import sys
import os
import importlib.util

def test_import(module_path, module_name):
    """Test if a module can be imported"""
    try:
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, module
        else:
            return False, f"File not found: {module_path}"
    except Exception as e:
        return False, str(e)

def validate_codebase():
    """Validate the codebase structure and imports"""
    print("🔍 Validating MyTypist Backend Codebase")
    print("=" * 50)

    # Add current directory to path
    current_dir = os.path.dirname(__file__)
    sys.path.insert(0, current_dir)

    validation_results = []

    # Test 1: Configuration
    print("\n1. Testing Configuration...")
    success, result = test_import(os.path.join(current_dir, "config.py"), "config")
    if success:
        print("   ✅ Configuration module loads successfully")
        try:
            settings = result.settings
            print(f"   ✅ Settings loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
            validation_results.append(("Configuration", True, "OK"))
        except Exception as e:
            print(f"   ⚠️  Settings object issue: {e}")
            validation_results.append(("Configuration", False, str(e)))
    else:
        print(f"   ❌ Configuration failed: {result}")
        validation_results.append(("Configuration", False, result))

    # Test 2: Database
    print("\n2. Testing Database Module...")
    success, result = test_import(os.path.join(current_dir, "database.py"), "database")
    if success:
        print("   ✅ Database module loads successfully")
        try:
            db_manager = result.DatabaseManager
            print("   ✅ DatabaseManager class available")
            validation_results.append(("Database", True, "OK"))
        except Exception as e:
            print(f"   ⚠️  DatabaseManager issue: {e}")
            validation_results.append(("Database", False, str(e)))
    else:
        print(f"   ❌ Database failed: {result}")
        validation_results.append(("Database", False, result))

    # Test 3: User Model
    print("\n3. Testing User Model...")
    user_model_path = os.path.join(current_dir, "app", "models", "user.py")
    success, result = test_import(user_model_path, "user_model")
    if success:
        print("   ✅ User model loads successfully")
        try:
            user_role = result.UserRole
            user_status = result.UserStatus
            print(f"   ✅ UserRole enum: {[role.value for role in user_role]}")
            print(f"   ✅ UserStatus enum: {[status.value for status in user_status]}")
            validation_results.append(("User Model", True, "OK"))
        except Exception as e:
            print(f"   ⚠️  User model enums issue: {e}")
            validation_results.append(("User Model", False, str(e)))
    else:
        print(f"   ❌ User model failed: {result}")
        validation_results.append(("User Model", False, result))

    # Test 4: Main Application
    print("\n4. Testing Main Application...")
    success, result = test_import(os.path.join(current_dir, "main.py"), "main_app")
    if success:
        print("   ✅ Main application module loads successfully")
        try:
            app = result.app
            print("   ✅ FastAPI app instance created")
            validation_results.append(("Main App", True, "OK"))
        except Exception as e:
            print(f"   ⚠️  FastAPI app issue: {e}")
            validation_results.append(("Main App", False, str(e)))
    else:
        print(f"   ❌ Main application failed: {result}")
        validation_results.append(("Main App", False, result))

    # Test 5: Test Files
    print("\n5. Testing Test Files...")
    test_files = [
        "app/tests/test_basic.py",
        "app/tests/test_models.py",
        "app/tests/test_api.py",
        "app/tests/test_performance.py"
    ]

    test_results = []
    for test_file in test_files:
        test_path = os.path.join(current_dir, test_file)
        success, result = test_import(test_path, f"test_{os.path.basename(test_file)}")
        if success:
            print(f"   ✅ {test_file} loads successfully")
            test_results.append(True)
        else:
            print(f"   ❌ {test_file} failed: {result}")
            test_results.append(False)

    all_tests_ok = all(test_results)
    validation_results.append(("Test Files", all_tests_ok, "OK" if all_tests_ok else "Some test files have issues"))

    # Test 6: Enhanced Services
    print("\n6. Testing Enhanced Services...")
    enhanced_services = [
        "app/services/performance_document_engine.py",
        "app/services/batch_processing_engine.py",
        "app/services/signature_canvas_service.py",
        "app/services/smart_template_processor.py",
        "app/services/realtime_drafts_service.py",
        "app/services/advanced_caching_service.py"
    ]

    enhanced_results = []
    for service_file in enhanced_services:
        service_path = os.path.join(current_dir, service_file)
        if os.path.exists(service_path):
            print(f"   ✅ {service_file} exists")
            enhanced_results.append(True)
        else:
            print(f"   ❌ {service_file} missing")
            enhanced_results.append(False)

    all_enhanced_ok = all(enhanced_results)
    validation_results.append(("Enhanced Services", all_enhanced_ok, "OK" if all_enhanced_ok else "Some services missing"))

    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)

    all_passed = True
    for component, success, message in validation_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component:20} | {status} | {message}")
        if not success:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("The codebase is ready for testing once Python environment is set up.")
    else:
        print("⚠️  SOME VALIDATIONS FAILED")
        print("Please review the issues above before proceeding.")

    return all_passed

if __name__ == "__main__":
    success = validate_codebase()
    sys.exit(0 if success else 1)
