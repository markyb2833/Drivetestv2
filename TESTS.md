# Comprehensive Test Suite

## Available Tests

### SMART Tests

1. **SMART Full Health Check** (`smart` / `smart_full`)
   - Comprehensive SMART attributes analysis
   - Checks reallocated sectors, pending sectors, offline uncorrectable
   - Temperature monitoring
   - Power-on hours and power cycle count
   - Overall health status evaluation
   - **Duration**: ~1 minute
   - **HDSentinel-like**: Yes

2. **SMART Short Self-Test** (`smart_short`)
   - Quick SMART self-test
   - **Duration**: ~2 minutes
   - **Use case**: Quick health verification

3. **SMART Extended Self-Test** (`smart_extended`)
   - Full SMART self-test
   - **Duration**: ~1-2 hours
   - **Use case**: Thorough drive validation

4. **SMART Conveyance Test** (`smart_conveyance`)
   - Self-test designed for shipping verification
   - **Duration**: ~5-10 minutes
   - **Use case**: Pre-shipping validation

### Bad Block Tests

5. **Badblocks Read Test** (`badblocks_read`)
   - Non-destructive read-only bad block detection
   - Scans entire drive for bad sectors
   - **Duration**: Varies by drive size (typically 30min - 2 hours)
   - **Safe**: Yes (read-only)

6. **Badblocks Write Test** (`badblocks_write`)
   - **DESTRUCTIVE** write test
   - **WARNING**: Destroys all data on drive
   - Tests drive's ability to write to all sectors
   - **Duration**: Varies by drive size
   - **Use case**: Pre-format validation

### Performance Tests

7. **Sequential Performance** (`performance_seq`)
   - Sequential read speed test
   - Sequential write speed test
   - Uses `dd` for testing
   - **Duration**: ~5-10 minutes
   - **Output**: Read/write speeds in MB/s

8. **Random I/O Performance** (`performance_random`)
   - Random read/write performance
   - Requires `fio` package
   - **Duration**: ~1 minute
   - **Output**: IOPS and latency metrics

### Format/Block Size Tests

9. **Format/Block Size** (`format` / `block_size`)
   - Change drive block size
   - Format drive with specified filesystem
   - Supports fast format option
   - **Parameters**:
     - `block_size`: Block size in bytes (default: 4096)
     - `filesystem`: Filesystem type (default: ext4)
     - `fast_format`: Quick format flag (default: false)
   - **WARNING**: Destroys all data

### Health Check

10. **Comprehensive Health Check** (`health_check`)
    - HDSentinel-like comprehensive health check
    - Checks:
      - SMART health status
      - Temperature
      - Power-on hours
      - Connection type (SATA/SAS)
    - **Duration**: ~1 minute
    - **HDSentinel-like**: Yes

## Test Execution

All tests run in isolated processes, allowing:
- Parallel execution on multiple drives
- No interference between drives
- Independent progress tracking
- Safe cancellation

## Usage Examples

### Python API

```python
from test_executor import TestExecutor

executor = TestExecutor()

# Start SMART full health check
executor.start_test('/dev/sdb', 'smart')

# Start SMART extended test
executor.start_test('/dev/sdb', 'smart_extended')

# Start badblocks read test
executor.start_test('/dev/sdb', 'badblocks_read')

# Start format with custom block size
executor.start_test('/dev/sdb', 'format', test_params={
    'block_size': 4096,
    'filesystem': 'ext4',
    'fast_format': True
})

# Check progress
progress = executor.get_progress('/dev/sdb')
print(f"Progress: {progress.progress_percent}%")
print(f"Status: {progress.current_step}")

# Stop test
executor.stop_test('/dev/sdb')
```

### REST API

```bash
# Start SMART test
curl -X POST http://localhost:5005/api/drives/{serial}/test \
  -H "Content-Type: application/json" \
  -d '{"test_type": "smart"}'

# Start format with parameters
curl -X POST http://localhost:5005/api/drives/{serial}/test \
  -H "Content-Type: application/json" \
  -d '{
    "test_type": "format",
    "test_params": {
      "block_size": 4096,
      "filesystem": "ext4",
      "fast_format": true
    }
  }'

# Get test status
curl http://localhost:5005/api/drives/{serial}/test

# Cancel test
curl -X DELETE http://localhost:5005/api/drives/{serial}/test
```

## HDSentinel Integration

The platform provides HDSentinel-like functionality using Linux native tools:

- **SMART Monitoring**: Uses `smartctl` (smartmontools)
- **Health Checks**: Comprehensive health evaluation
- **Temperature Monitoring**: Real-time temperature tracking
- **Power-on Hours**: Tracks drive usage
- **Connection Detection**: SATA/SAS identification
- **Bad Block Detection**: Comprehensive bad block scanning

All functionality is provided through Linux-native tools, ensuring compatibility and reliability on Ubuntu LTS systems.

## System Requirements

### Required Packages

- `smartmontools` - SMART monitoring
- `hdparm` - Hard disk utilities
- `util-linux` - lsblk, blockdev
- `sg3-utils` - SCSI/SAS utilities
- `badblocks` - Bad block detection (part of e2fsprogs)
- `fio` - Random I/O performance testing (optional)

### Installation

Run the auto-install script:

```bash
./install.sh
```

This will install all required system packages, Python dependencies, and Node.js dependencies.

