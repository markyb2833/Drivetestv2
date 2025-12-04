#!/usr/bin/env python3
"""
Safety Verification Script

Verifies that OS drive detection and isolation work correctly.
Run this before deploying to production.
"""

from os_drive_detector import get_os_drive, is_os_drive, get_all_non_os_drives
from drive_detector import DriveDetector
from test_executor import TestExecutor


def test_os_drive_detection():
    """Test OS drive detection"""
    print("=" * 60)
    print("Testing OS Drive Detection")
    print("=" * 60)
    
    os_name, os_path = get_os_drive()
    
    if os_name and os_path:
        print(f"✓ OS Drive detected: {os_name} -> {os_path}")
    else:
        print("✗ WARNING: Could not detect OS drive!")
        print("  System will be conservative and reject all drives.")
        return False
    
    # Test is_os_drive function
    if is_os_drive(os_path):
        print(f"✓ is_os_drive() correctly identifies OS drive")
    else:
        print(f"✗ ERROR: is_os_drive() failed to identify OS drive!")
        return False
    
    # Test non-OS drive detection
    non_os_drives = get_all_non_os_drives()
    print(f"✓ Found {len(non_os_drives)} non-OS drives")
    
    # Verify OS drive is not in the list
    if os_path in non_os_drives:
        print(f"✗ ERROR: OS drive found in non-OS drives list!")
        return False
    else:
        print(f"✓ OS drive correctly excluded from non-OS drives")
    
    return True


def test_drive_detector():
    """Test drive detector excludes OS drive"""
    print("\n" + "=" * 60)
    print("Testing Drive Detector")
    print("=" * 60)
    
    detector = DriveDetector()
    drives = detector.scan_drives()
    
    print(f"✓ Detected {len(drives)} drives")
    
    # Verify OS drive is not detected
    os_name, os_path = get_os_drive()
    if os_path and os_path in drives:
        print(f"✗ ERROR: OS drive detected by DriveDetector!")
        return False
    
    print(f"✓ OS drive correctly excluded by DriveDetector")
    
    # Print detected drives
    for device_path, drive_info in drives.items():
        print(f"  - {device_path}: Bay {drive_info.bay_number}, "
              f"Serial: {drive_info.serial}, Model: {drive_info.model}")
    
    return True


def test_test_executor():
    """Test test executor rejects OS drive"""
    print("\n" + "=" * 60)
    print("Testing Test Executor Safety")
    print("=" * 60)
    
    executor = TestExecutor()
    os_name, os_path = get_os_drive()
    
    if not os_path:
        print("⚠ Skipping: Could not detect OS drive")
        return True
    
    # Try to start test on OS drive (should fail)
    try:
        executor.start_test(os_path, 'smart')
        print(f"✗ ERROR: Test executor allowed test on OS drive!")
        return False
    except ValueError as e:
        if "OS drive" in str(e) or "forbidden" in str(e).lower():
            print(f"✓ Test executor correctly rejected OS drive test")
            print(f"  Error message: {e}")
        else:
            print(f"✗ ERROR: Wrong error message: {e}")
            return False
    
    return True


def main():
    """Run all safety tests"""
    print("\n" + "=" * 60)
    print("HDD Tester Safety Verification")
    print("=" * 60 + "\n")
    
    tests = [
        ("OS Drive Detection", test_os_drive_detection),
        ("Drive Detector", test_drive_detector),
        ("Test Executor Safety", test_test_executor),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All safety tests passed!")
        return 0
    else:
        print("✗ Some safety tests failed. DO NOT DEPLOY!")
        return 1


if __name__ == '__main__':
    exit(main())

