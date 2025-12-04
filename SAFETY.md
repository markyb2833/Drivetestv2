# Safety Features

## Critical Safety Requirements

### 1. OS Drive Protection

**NEVER run tests on the OS drive.**

The system implements multiple layers of protection:

- **`os_drive_detector.py`**: Detects OS drive using multiple methods:
  - `/proc/mounts` - Root filesystem mount point
  - `/etc/fstab` - Root partition entry
  - `/boot` device detection
  - `lsblk` root filesystem detection

- **Pre-test checks**: Every test function checks `is_os_drive()` before execution
- **Drive filtering**: `get_all_non_os_drives()` automatically excludes OS drive
- **Conservative approach**: If OS drive cannot be detected, system rejects all drives for safety

### 2. Isolated Test Execution

**All drives run tests in separate processes.**

- **Process isolation**: Each drive test runs in its own `multiprocessing.Process`
- **No interference**: Tests on different drives cannot affect each other
- **Parallel execution**: Multiple drives can be tested simultaneously
- **Resource isolation**: Each process has its own memory space and file handles

### 3. Parallel Processing

**Tests run independently - plugging 1 or 20 drives takes the same time per drive.**

- **Independent processes**: Each drive's test is completely isolated
- **No blocking**: Starting a block size change on one drive doesn't block testing another
- **Concurrent operations**: Format operations and tests can run simultaneously on different drives
- **Progress tracking**: Each drive's progress is tracked independently

## Implementation Details

### OS Drive Detection

```python
from os_drive_detector import get_os_drive, is_os_drive

# Get OS drive
os_name, os_path = get_os_drive()

# Check if device is OS drive
if is_os_drive('/dev/sda'):
    raise ValueError("Cannot test OS drive!")
```

### Test Execution

```python
from test_executor import TestExecutor

executor = TestExecutor()

# Start test (automatically runs in isolated process)
executor.start_test('/dev/sdb', 'smart')

# Multiple drives can run simultaneously
executor.start_test('/dev/sdc', 'badblocks')  # Runs in parallel
executor.start_test('/dev/sdd', 'format')     # Runs in parallel
```

### Drive Detection

```python
from drive_detector import DriveDetector

detector = DriveDetector()
drives = detector.scan_drives()  # Automatically excludes OS drive

# All returned drives are safe to test
for device_path, drive_info in drives.items():
    print(f"Safe to test: {device_path}")
```

## Safety Checklist

- [x] OS drive detection implemented
- [x] Pre-test OS drive checks
- [x] Process isolation for tests
- [x] Parallel execution support
- [x] Drive filtering excludes OS drive
- [x] Error handling for detection failures

## Testing Safety

Before running any tests, verify:

1. OS drive is correctly identified
2. Test executor rejects OS drive attempts
3. Multiple tests can run in parallel
4. Tests don't interfere with each other

