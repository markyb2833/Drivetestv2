"""
Test Execution Engine

Runs comprehensive tests in isolated processes to ensure:
1. Tests on different drives never interfere
2. Block size changes can run in parallel
3. Each drive has its own process space
"""

import subprocess
import multiprocessing
import threading
import time
import json
import re
import os
from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from os_drive_detector import is_os_drive

# Try to import HDSentinel integration
try:
    from hdsentinel_integration import HDSentinelIntegration
    HDSENTINEL_AVAILABLE = True
except ImportError:
    HDSENTINEL_AVAILABLE = False
    HDSentinelIntegration = None


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TestProgress:
    """Progress information for a running test"""
    device_path: str
    test_type: str
    status: TestStatus
    progress_percent: float
    current_step: str
    start_time: datetime
    elapsed_seconds: float
    error_message: Optional[str] = None
    result_data: Optional[Dict] = None


class TestExecutor:
    """
    Executes comprehensive tests in isolated processes.
    
    Each drive gets its own process, allowing parallel execution
    without interference between drives.
    """
    
    def __init__(self):
        self.active_tests: Dict[str, multiprocessing.Process] = {}
        self.test_progress: Dict[str, TestProgress] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
    
    def start_test(self, device_path: str, test_type: str, 
                   progress_callback: Optional[Callable] = None,
                   test_params: Optional[Dict] = None) -> bool:
        """
        Start a test on a drive in an isolated process.
        
        Args:
            device_path: Path to device (e.g., '/dev/sdb')
            test_type: Type of test ('smart', 'smart_short', 'smart_extended', 
                       'smart_conveyance', 'badblocks_read', 'badblocks_write',
                       'performance_seq', 'performance_random', 'format', etc.)
            progress_callback: Optional callback for progress updates
            test_params: Optional test parameters (block_size, fast_format, etc.)
        
        Returns:
            bool: True if test started successfully
        """
        # CRITICAL SAFETY CHECK: Never test OS drive
        if is_os_drive(device_path):
            raise ValueError(f"CRITICAL ERROR: Attempted to test OS drive {device_path}. This is forbidden!")
        
        with self._lock:
            # Check if test already running for this drive
            if device_path in self.active_tests:
                test_proc = self.active_tests[device_path]
                if test_proc.is_alive():
                    print(f"Test already running on {device_path}")
                    return False
            
            # Create progress tracker
            progress = TestProgress(
                device_path=device_path,
                test_type=test_type,
                status=TestStatus.RUNNING,
                progress_percent=0.0,
                current_step="Starting test...",
                start_time=datetime.now(),
                elapsed_seconds=0.0,
                result_data={}
            )
            self.test_progress[device_path] = progress
            
            if progress_callback:
                self.progress_callbacks[device_path] = progress_callback
            
            # Start test in isolated process
            process = multiprocessing.Process(
                target=self._run_test_isolated,
                args=(device_path, test_type, progress, test_params or {})
            )
            process.start()
            
            self.active_tests[device_path] = process
            
            return True
    
    def _run_test_isolated(self, device_path: str, test_type: str, 
                           progress: TestProgress, test_params: Dict):
        """
        Run test in isolated process.
        
        This runs in a separate process, ensuring complete isolation
        from other drive tests.
        """
        try:
            # Update progress
            self._update_progress(device_path, "Initializing test...", 5.0)
            
            # Route to appropriate test function
            if test_type == 'hdsentinel' or test_type == 'hdsentinel_health':
                self._run_hdsentinel_test(device_path, progress)
            elif test_type == 'smart' or test_type == 'smart_full':
                self._run_smart_full_test(device_path, progress)
            elif test_type == 'smart_short':
                self._run_smart_short_test(device_path, progress)
            elif test_type == 'smart_extended':
                self._run_smart_extended_test(device_path, progress)
            elif test_type == 'smart_conveyance':
                self._run_smart_conveyance_test(device_path, progress)
            elif test_type == 'badblocks_read':
                self._run_badblocks_read_test(device_path, progress)
            elif test_type == 'badblocks_write':
                self._run_badblocks_write_test(device_path, progress)
            elif test_type == 'badblocks':
                self._run_badblocks_read_test(device_path, progress)  # Default to read-only
            elif test_type == 'performance_seq':
                self._run_performance_sequential_test(device_path, progress)
            elif test_type == 'performance_random':
                self._run_performance_random_test(device_path, progress)
            elif test_type == 'format' or test_type == 'block_size':
                self._run_format_test(device_path, progress, test_params)
            elif test_type == 'health_check':
                self._run_health_check_test(device_path, progress)
            else:
                raise ValueError(f"Unknown test type: {test_type}")
            
            # Mark as completed
            self._update_progress(device_path, "Test completed", 100.0)
            progress.status = TestStatus.COMPLETED
            
        except Exception as e:
            error_msg = str(e)
            print(f"Test failed on {device_path}: {error_msg}")
            progress.status = TestStatus.FAILED
            progress.error_message = error_msg
            self._update_progress(device_path, f"Error: {error_msg}", progress.progress_percent)
        
        finally:
            # Cleanup
            with self._lock:
                if device_path in self.active_tests:
                    del self.active_tests[device_path]
    
    def _run_hdsentinel_test(self, device_path: str, progress: TestProgress):
        """Run actual HDSentinel health check"""
        if not HDSENTINEL_AVAILABLE:
            raise Exception("HDSentinel not available. Please install HDSentinel Linux binary.")
        
        self._update_progress(device_path, "Initializing HDSentinel...", 5.0)
        
        try:
            hdsentinel = HDSentinelIntegration()
        except FileNotFoundError as e:
            raise Exception(f"HDSentinel binary not found: {e}")
        
        self._update_progress(device_path, "Running HDSentinel health check...", 20.0)
        
        # Run HDSentinel health check
        health_data = hdsentinel.check_health(device_path)
        progress.result_data['hdsentinel_health'] = health_data
        
        self._update_progress(device_path, "Getting detailed HDSentinel report...", 60.0)
        
        # Get detailed report
        detailed_report = hdsentinel.get_detailed_report(device_path, 'txt')
        progress.result_data['hdsentinel_report'] = detailed_report
        
        # Check for failures
        failures = []
        warnings = []
        
        if health_data.get('health_percent'):
            health_pct = health_data['health_percent']
            if health_pct < 50:
                failures.append(f"Critical health: {health_pct}%")
            elif health_pct < 80:
                warnings.append(f"Low health: {health_pct}%")
        
        if health_data.get('reallocated_sectors', 0) > 0:
            failures.append(f"Reallocated sectors: {health_data['reallocated_sectors']}")
        
        if health_data.get('temperature'):
            temp = health_data['temperature']
            if temp > 60:
                warnings.append(f"High temperature: {temp}°C")
        
        progress.result_data['failures'] = failures
        progress.result_data['warnings'] = warnings
        
        if failures:
            raise Exception(f"HDSentinel health check failed: {'; '.join(failures)}")
        
        self._update_progress(device_path, "HDSentinel health check completed", 100.0)
    
    def _run_smart_full_test(self, device_path: str, progress: TestProgress):
        """Run comprehensive SMART health test (HDSentinel-like)"""
        self._update_progress(device_path, "Reading SMART attributes...", 10.0)
        
        # Get full SMART information
        result = subprocess.run(
            ['smartctl', '-a', device_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"SMART test failed: {result.stderr}")
        
        output = result.stdout
        progress.result_data['smart_output'] = output
        
        self._update_progress(device_path, "Parsing SMART attributes...", 30.0)
        
        # Parse critical SMART attributes
        smart_data = self._parse_smart_attributes(output)
        progress.result_data['smart_attributes'] = smart_data
        
        # Check for critical failures
        self._update_progress(device_path, "Checking critical attributes...", 50.0)
        
        failures = []
        warnings = []
        
        # Check reallocated sectors
        if 'Reallocated_Sector_Ct' in smart_data:
            reallocated = smart_data['Reallocated_Sector_Ct'].get('raw_value', 0)
            if reallocated > 0:
                failures.append(f"Reallocated sectors detected: {reallocated}")
        
        # Check pending sectors
        if 'Current_Pending_Sector' in smart_data:
            pending = smart_data['Current_Pending_Sector'].get('raw_value', 0)
            if pending > 0:
                failures.append(f"Pending sectors: {pending}")
        
        # Check offline uncorrectable
        if 'Offline_Uncorrectable' in smart_data:
            uncorrectable = smart_data['Offline_Uncorrectable'].get('raw_value', 0)
            if uncorrectable > 0:
                failures.append(f"Offline uncorrectable sectors: {uncorrectable}")
        
        # Check temperature
        if 'Temperature_Celsius' in smart_data:
            temp = smart_data['Temperature_Celsius'].get('value', 0)
            if temp > 60:
                warnings.append(f"High temperature: {temp}°C")
        
        # Check power-on hours
        if 'Power_On_Hours' in smart_data:
            poh = smart_data['Power_On_Hours'].get('raw_value', 0)
            progress.result_data['power_on_hours'] = poh
        
        # Check power cycle count
        if 'Power_Cycle_Count' in smart_data:
            pcc = smart_data['Power_Cycle_Count'].get('raw_value', 0)
            progress.result_data['power_cycle_count'] = pcc
        
        # Check overall health status
        self._update_progress(device_path, "Evaluating health status...", 80.0)
        
        if 'SMART overall-health self-assessment test result' in output:
            health_match = re.search(r'SMART overall-health self-assessment test result: (\w+)', output)
            if health_match:
                health_status = health_match.group(1)
                progress.result_data['health_status'] = health_status
                if health_status != 'PASSED':
                    failures.append(f"SMART health check: {health_status}")
        
        progress.result_data['failures'] = failures
        progress.result_data['warnings'] = warnings
        
        if failures:
            raise Exception(f"SMART test failed: {'; '.join(failures)}")
        
        self._update_progress(device_path, "SMART test passed", 100.0)
    
    def _run_smart_short_test(self, device_path: str, progress: TestProgress):
        """Run SMART short self-test (typically 2 minutes)"""
        self._update_progress(device_path, "Starting SMART short self-test...", 5.0)
        
        # Start short test
        result = subprocess.run(
            ['smartctl', '-t', 'short', device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to start SMART short test: {result.stderr}")
        
        # Monitor test progress
        self._update_progress(device_path, "Running SMART short self-test...", 20.0)
        
        # Wait and check status periodically
        max_wait = 300  # 5 minutes max
        elapsed = 0
        while elapsed < max_wait:
            time.sleep(10)
            elapsed += 10
            
            # Check test status
            status_result = subprocess.run(
                ['smartctl', '-l', 'selftest', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode == 0:
                status_output = status_result.stdout
                if 'Self-test execution status:' in status_output:
                    if 'completed without error' in status_output.lower():
                        self._update_progress(device_path, "SMART short test completed", 100.0)
                        progress.result_data['test_result'] = 'PASSED'
                        return
                    elif 'self-test in progress' in status_output.lower():
                        progress_pct = min(90.0, 20.0 + (elapsed / max_wait) * 70.0)
                        self._update_progress(device_path, f"SMART short test in progress... ({elapsed}s)", progress_pct)
                    elif 'failed' in status_output.lower() or 'error' in status_output.lower():
                        raise Exception("SMART short test failed")
        
        raise Exception("SMART short test timed out")
    
    def _run_smart_extended_test(self, device_path: str, progress: TestProgress):
        """Run SMART extended self-test (typically 1-2 hours)"""
        self._update_progress(device_path, "Starting SMART extended self-test...", 5.0)
        
        result = subprocess.run(
            ['smartctl', '-t', 'long', device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to start SMART extended test: {result.stderr}")
        
        self._update_progress(device_path, "Running SMART extended self-test (this may take 1-2 hours)...", 10.0)
        
        # Monitor for up to 2.5 hours
        max_wait = 9000  # 2.5 hours
        elapsed = 0
        while elapsed < max_wait:
            time.sleep(30)  # Check every 30 seconds
            elapsed += 30
            
            status_result = subprocess.run(
                ['smartctl', '-l', 'selftest', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode == 0:
                status_output = status_result.stdout
                if 'completed without error' in status_output.lower():
                    self._update_progress(device_path, "SMART extended test completed", 100.0)
                    progress.result_data['test_result'] = 'PASSED'
                    return
                elif 'self-test in progress' in status_output.lower():
                    progress_pct = min(95.0, 10.0 + (elapsed / max_wait) * 85.0)
                    self._update_progress(device_path, f"SMART extended test in progress... ({elapsed//60}m)", progress_pct)
                elif 'failed' in status_output.lower():
                    raise Exception("SMART extended test failed")
        
        raise Exception("SMART extended test timed out")
    
    def _run_smart_conveyance_test(self, device_path: str, progress: TestProgress):
        """Run SMART conveyance self-test (for shipping)"""
        self._update_progress(device_path, "Starting SMART conveyance self-test...", 5.0)
        
        result = subprocess.run(
            ['smartctl', '-t', 'conveyance', device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to start SMART conveyance test: {result.stderr}")
        
        max_wait = 600  # 10 minutes max
        elapsed = 0
        while elapsed < max_wait:
            time.sleep(15)
            elapsed += 15
            
            status_result = subprocess.run(
                ['smartctl', '-l', 'selftest', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode == 0:
                status_output = status_result.stdout
                if 'completed without error' in status_output.lower():
                    self._update_progress(device_path, "SMART conveyance test completed", 100.0)
                    progress.result_data['test_result'] = 'PASSED'
                    return
                elif 'self-test in progress' in status_output.lower():
                    progress_pct = min(90.0, 10.0 + (elapsed / max_wait) * 80.0)
                    self._update_progress(device_path, f"SMART conveyance test in progress... ({elapsed}s)", progress_pct)
        
        raise Exception("SMART conveyance test timed out")
    
    def _run_badblocks_read_test(self, device_path: str, progress: TestProgress):
        """Run badblocks read-only test"""
        self._update_progress(device_path, "Starting badblocks read test...", 5.0)
        
        # Get device size for progress estimation
        size_result = subprocess.run(
            ['blockdev', '--getsize64', device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        device_size = int(size_result.stdout.strip()) if size_result.returncode == 0 else 0
        
        # Run badblocks in read-only mode with progress
        process = subprocess.Popen(
            ['badblocks', '-v', '-s', '-e', '10', device_path],  # -e 10 = stop after 10 errors
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        bad_blocks = []
        last_progress = 5.0
        
        while process.poll() is None:
            # Read output line by line
            line = process.stdout.readline()
            if line:
                # Parse progress from badblocks output
                # Format: "Testing with random pattern: 12.34% done, 0:05 elapsed"
                progress_match = re.search(r'(\d+\.\d+)% done', line)
                if progress_match:
                    progress_pct = float(progress_match.group(1))
                    last_progress = 5.0 + (progress_pct * 0.9)  # 5-95%
                    self._update_progress(device_path, f"Badblocks read test: {progress_pct:.1f}%", last_progress)
                
                # Check for bad blocks
                if 'bad' in line.lower() or 'error' in line.lower():
                    bad_blocks.append(line.strip())
            else:
                time.sleep(1)
        
        process.wait()
        
        if bad_blocks:
            progress.result_data['bad_blocks'] = bad_blocks
            raise Exception(f"Badblocks test found {len(bad_blocks)} bad blocks")
        
        if process.returncode != 0:
            raise Exception(f"Badblocks test failed with return code {process.returncode}")
        
        self._update_progress(device_path, "Badblocks read test completed - no errors found", 100.0)
        progress.result_data['bad_blocks'] = []
    
    def _run_badblocks_write_test(self, device_path: str, progress: TestProgress):
        """Run badblocks destructive write test (WARNING: Destroys data!)"""
        self._update_progress(device_path, "WARNING: Write test will destroy all data!", 5.0)
        time.sleep(2)  # Give user a moment to see warning
        
        # Run badblocks with write mode
        process = subprocess.Popen(
            ['badblocks', '-v', '-w', '-s', '-e', '10', device_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        bad_blocks = []
        last_progress = 10.0
        
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                progress_match = re.search(r'(\d+\.\d+)% done', line)
                if progress_match:
                    progress_pct = float(progress_match.group(1))
                    last_progress = 10.0 + (progress_pct * 0.85)  # 10-95%
                    self._update_progress(device_path, f"Badblocks write test: {progress_pct:.1f}%", last_progress)
                
                if 'bad' in line.lower() or 'error' in line.lower():
                    bad_blocks.append(line.strip())
            else:
                time.sleep(1)
        
        process.wait()
        
        if bad_blocks:
            progress.result_data['bad_blocks'] = bad_blocks
            raise Exception(f"Badblocks write test found {len(bad_blocks)} bad blocks")
        
        self._update_progress(device_path, "Badblocks write test completed", 100.0)
        progress.result_data['bad_blocks'] = []
    
    def _run_performance_sequential_test(self, device_path: str, progress: TestProgress):
        """Run sequential read/write performance test"""
        self._update_progress(device_path, "Running sequential read test...", 10.0)
        
        # Sequential read test using dd
        read_result = subprocess.run(
            ['dd', f'if={device_path}', 'of=/dev/null', 'bs=1M', 'count=1024', 'iflag=direct'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if read_result.returncode != 0:
            raise Exception(f"Sequential read test failed: {read_result.stderr}")
        
        # Parse speed from dd output
        speed_match = re.search(r'(\d+\.?\d*)\s*(MB/s|GB/s)', read_result.stderr)
        read_speed = speed_match.group(1) if speed_match else "N/A"
        
        self._update_progress(device_path, "Running sequential write test...", 60.0)
        
        # Sequential write test (use a temporary file)
        temp_file = f'/tmp/hdd_test_{os.getpid()}.tmp'
        try:
            write_result = subprocess.run(
                ['dd', 'if=/dev/zero', f'of={temp_file}', 'bs=1M', 'count=1024', 'oflag=direct'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if write_result.returncode == 0:
                speed_match = re.search(r'(\d+\.?\d*)\s*(MB/s|GB/s)', write_result.stderr)
                write_speed = speed_match.group(1) if speed_match else "N/A"
            else:
                write_speed = "N/A"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        progress.result_data['sequential_read_speed'] = read_speed
        progress.result_data['sequential_write_speed'] = write_speed
        
        self._update_progress(device_path, "Performance test completed", 100.0)
    
    def _run_performance_random_test(self, device_path: str, progress: TestProgress):
        """Run random I/O performance test"""
        self._update_progress(device_path, "Running random I/O performance test...", 10.0)
        
        # Use fio if available, otherwise skip
        fio_available = subprocess.run(['which', 'fio'], capture_output=True).returncode == 0
        
        if not fio_available:
            self._update_progress(device_path, "fio not available, skipping random I/O test", 100.0)
            progress.result_data['random_io_test'] = 'SKIPPED (fio not installed)'
            return
        
        # Run fio random read/write test
        fio_config = f"""
[global]
filename={device_path}
direct=1
runtime=60
time_based=1

[random-read]
rw=randread
bs=4k
iodepth=16

[random-write]
rw=randwrite
bs=4k
iodepth=16
"""
        
        fio_result = subprocess.run(
            ['fio', '--output-format=json', '-'],
            input=fio_config,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if fio_result.returncode == 0:
            try:
                fio_data = json.loads(fio_result.stdout)
                progress.result_data['random_io'] = fio_data
            except:
                progress.result_data['random_io'] = fio_result.stdout
        
        self._update_progress(device_path, "Random I/O test completed", 100.0)
    
    def _run_format_test(self, device_path: str, progress: TestProgress, test_params: Dict):
        """Run block size change/format operation"""
        self._update_progress(device_path, "Preparing format operation...", 5.0)
        
        block_size = test_params.get('block_size', 4096)
        fast_format = test_params.get('fast_format', False)
        filesystem = test_params.get('filesystem', 'ext4')
        
        # Get current block size
        current_bs_result = subprocess.run(
            ['blockdev', '--getbsz', device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        current_block_size = int(current_bs_result.stdout.strip()) if current_bs_result.returncode == 0 else 0
        progress.result_data['old_block_size'] = current_block_size
        progress.result_data['new_block_size'] = block_size
        
        self._update_progress(device_path, f"Changing block size to {block_size}...", 20.0)
        
        # Unmount if mounted
        subprocess.run(['umount', device_path], capture_output=True)
        
        # Create partition table (if needed)
        self._update_progress(device_path, "Creating partition table...", 30.0)
        
        # Format with specified block size
        self._update_progress(device_path, f"Formatting with {filesystem} (block size: {block_size})...", 40.0)
        
        mkfs_args = ['mkfs', f'-t {filesystem}']
        if fast_format:
            mkfs_args.append('-q')  # Quick format
        
        # Use specific block size if supported
        format_result = subprocess.run(
            ['mkfs', '-t', filesystem, '-b', str(block_size), device_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if format_result.returncode != 0:
            raise Exception(f"Format failed: {format_result.stderr}")
        
        self._update_progress(device_path, "Format completed", 100.0)
        progress.result_data['format_success'] = True
    
    def _run_health_check_test(self, device_path: str, progress: TestProgress):
        """Run comprehensive health check (HDSentinel-like)"""
        self._update_progress(device_path, "Running comprehensive health check...", 5.0)
        
        # Combine multiple checks
        health_data = {}
        
        # SMART check
        self._update_progress(device_path, "Checking SMART health...", 20.0)
        try:
            smart_result = subprocess.run(
                ['smartctl', '-H', device_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            health_data['smart_health'] = smart_result.stdout
        except:
            health_data['smart_health'] = 'ERROR'
        
        # Temperature check
        self._update_progress(device_path, "Checking temperature...", 40.0)
        try:
            temp_result = subprocess.run(
                ['smartctl', '-A', device_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            temp_match = re.search(r'Temperature.*?(\d+)', temp_result.stdout)
            if temp_match:
                health_data['temperature'] = int(temp_match.group(1))
        except:
            pass
        
        # Power-on hours
        self._update_progress(device_path, "Checking power-on hours...", 60.0)
        try:
            attr_result = subprocess.run(
                ['smartctl', '-A', device_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            poh_match = re.search(r'Power_On_Hours.*?(\d+)', attr_result.stdout)
            if poh_match:
                health_data['power_on_hours'] = int(poh_match.group(1))
        except:
            pass
        
        # Connection type
        self._update_progress(device_path, "Checking connection type...", 80.0)
        try:
            info_result = subprocess.run(
                ['smartctl', '-i', device_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if 'SATA' in info_result.stdout:
                health_data['connection_type'] = 'SATA'
            elif 'SAS' in info_result.stdout:
                health_data['connection_type'] = 'SAS'
        except:
            pass
        
        progress.result_data['health_data'] = health_data
        self._update_progress(device_path, "Health check completed", 100.0)
    
    def _parse_smart_attributes(self, smart_output: str) -> Dict:
        """Parse SMART attributes from smartctl output"""
        attributes = {}
        
        # Find the attributes section
        lines = smart_output.split('\n')
        in_attributes = False
        
        for line in lines:
            if 'ID#' in line and 'ATTRIBUTE_NAME' in line:
                in_attributes = True
                continue
            
            if in_attributes:
                if line.strip() == '':
                    break
                
                # Parse attribute line
                # Format: "  1 Raw_Read_Error_Rate     0x002f   200   200   051    Pre-fail  Always       -       0"
                match = re.match(r'\s*(\d+)\s+(\S+)\s+0x\w+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+.*?(\d+)', line)
                if match:
                    attr_id = match.group(1)
                    attr_name = match.group(2)
                    value = int(match.group(3))
                    worst = int(match.group(4))
                    threshold = int(match.group(5))
                    raw_value = int(match.group(8))
                    
                    attributes[attr_name] = {
                        'id': attr_id,
                        'value': value,
                        'worst': worst,
                        'threshold': threshold,
                        'raw_value': raw_value
                    }
        
        return attributes
    
    def _update_progress(self, device_path: str, current_step: str, progress_percent: float):
        """Update progress for a test"""
        with self._lock:
            if device_path in self.test_progress:
                progress = self.test_progress[device_path]
                progress.current_step = current_step
                progress.progress_percent = progress_percent
                progress.elapsed_seconds = (datetime.now() - progress.start_time).total_seconds()
                
                # Call callback if registered
                if device_path in self.progress_callbacks:
                    try:
                        callback = self.progress_callbacks[device_path]
                        callback(asdict(progress))
                    except Exception as e:
                        print(f"Error in progress callback: {e}")
    
    def stop_test(self, device_path: str) -> bool:
        """
        Stop a running test.
        
        Args:
            device_path: Path to device
        
        Returns:
            bool: True if test was stopped
        """
        with self._lock:
            if device_path in self.active_tests:
                process = self.active_tests[device_path]
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
                    if process.is_alive():
                        process.kill()
                    
                    if device_path in self.test_progress:
                        self.test_progress[device_path].status = TestStatus.CANCELLED
                    
                    del self.active_tests[device_path]
                    return True
        return False
    
    def get_progress(self, device_path: str) -> Optional[TestProgress]:
        """Get current progress for a test"""
        with self._lock:
            return self.test_progress.get(device_path)
    
    def get_all_progress(self) -> Dict[str, TestProgress]:
        """Get progress for all active tests"""
        with self._lock:
            return self.test_progress.copy()
    
    def is_test_running(self, device_path: str) -> bool:
        """Check if a test is running on a drive"""
        with self._lock:
            if device_path in self.active_tests:
                return self.active_tests[device_path].is_alive()
            return False


if __name__ == '__main__':
    # Test executor
    executor = TestExecutor()
    
    # Example: Start a test (would need actual device)
    # executor.start_test('/dev/sdb', 'smart')
    
    print("Test executor initialized")
    print("Each drive runs in isolated process for parallel execution")
    print("\nAvailable test types:")
    print("  - smart / smart_full: Comprehensive SMART health check")
    print("  - smart_short: SMART short self-test (~2 min)")
    print("  - smart_extended: SMART extended self-test (~1-2 hours)")
    print("  - smart_conveyance: SMART conveyance test (for shipping)")
    print("  - badblocks_read: Read-only bad block detection")
    print("  - badblocks_write: Destructive write test (WARNING: destroys data)")
    print("  - performance_seq: Sequential read/write performance")
    print("  - performance_random: Random I/O performance (requires fio)")
    print("  - format / block_size: Change block size and format")
    print("  - health_check: Comprehensive health check (HDSentinel-like)")
