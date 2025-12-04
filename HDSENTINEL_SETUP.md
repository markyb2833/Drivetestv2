# HDSentinel Linux Setup

## Overview

This platform integrates **actual HDSentinel Linux** for comprehensive drive health testing, not just HDSentinel-like functionality.

## Installation

### Step 1: Download HDSentinel Linux

1. Visit: https://www.hdsentinel.com/hard_disk_sentinel_linux.php
2. Download the Linux version (usually a `.tar.gz` archive)
3. Extract the archive

### Step 2: Install HDSentinel Binary

Place the HDSentinel binary in one of these locations (in order of preference):

1. `/usr/local/bin/hdsentinel` (recommended)
2. `/usr/bin/hdsentinel`
3. `/opt/hdsentinel/hdsentinel`
4. `./tools/hdsentinel` (project directory)
5. `./hdsentinel` (project root)

Make it executable:
```bash
sudo chmod +x /usr/local/bin/hdsentinel
```

### Step 3: Verify Installation

Test that HDSentinel works:
```bash
hdsentinel --version
# or
hdsentinel -h
```

### Step 4: Run Auto-Install Script

The `install.sh` script will detect HDSentinel if it's already installed:
```bash
./install.sh
```

## Usage

### Python API

```python
from hdsentinel_integration import HDSentinelIntegration

# Initialize
hdsentinel = HDSentinelIntegration()

# Check drive health
health = hdsentinel.check_health('/dev/sdb')
print(f"Health: {health['health_percent']}%")
print(f"Temperature: {health['temperature']}°C")

# Get detailed report
report = hdsentinel.get_detailed_report('/dev/sdb', 'txt')

# Run surface test
test_results = hdsentinel.run_surface_test('/dev/sdb', 'quick')
```

### Test Executor Integration

HDSentinel is integrated into the test executor:

```python
from test_executor import TestExecutor

executor = TestExecutor()

# Run HDSentinel health check
executor.start_test('/dev/sdb', 'hdsentinel')
# or
executor.start_test('/dev/sdb', 'hdsentinel_health')
```

### REST API

```bash
# Start HDSentinel test
curl -X POST http://localhost:5005/api/drives/{serial}/test \
  -H "Content-Type: application/json" \
  -d '{"test_type": "hdsentinel"}'
```

## Available Test Types

- **`hdsentinel`** or **`hdsentinel_health`**: Full HDSentinel health check
  - Health percentage
  - Temperature monitoring
  - Power-on hours
  - Reallocated sectors
  - Pending sectors
  - Overall status

## HDSentinel Command-Line Options

HDSentinel Linux supports various command-line options. Common ones:

- `-r` or `-report`: Generate report
- `-txt`: Text output format
- `-html`: HTML output format
- `-xml`: XML output format
- `-quicktest`: Quick surface test
- `-completetest`: Complete surface test
- `-repair`: Repair bad sectors (use with caution!)

## Integration Details

The `hdsentinel_integration.py` module provides:

1. **HDSentinelIntegration Class**: Wrapper for HDSentinel binary
2. **Automatic Binary Detection**: Searches common installation paths
3. **Output Parsing**: Parses HDSentinel text/XML output
4. **Error Handling**: Graceful fallback if HDSentinel not available

## Troubleshooting

### HDSentinel Not Found

If you get "HDSentinel binary not found":
1. Verify HDSentinel is installed: `which hdsentinel`
2. Check file permissions: `ls -l /usr/local/bin/hdsentinel`
3. Try specifying path explicitly:
   ```python
   hdsentinel = HDSentinelIntegration('/path/to/hdsentinel')
   ```

### Permission Errors

HDSentinel may need root/sudo access for some operations:
```bash
sudo hdsentinel /dev/sdb
```

### License/Registration

HDSentinel may require registration/license for full functionality. Check HDSentinel documentation for licensing requirements.

## Notes

- HDSentinel Linux is a commercial product - ensure you have proper licensing
- Some features may require the registered/professional version
- The integration module attempts to work with both free and registered versions
- Command-line options may vary by HDSentinel version

