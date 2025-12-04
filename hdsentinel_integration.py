"""
HDSentinel Integration Module

Integrates actual HDSentinel Linux binary for comprehensive drive health testing.
"""

import subprocess
import os
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, Optional, List
from pathlib import Path


class HDSentinelIntegration:
    """
    Wrapper for HDSentinel Linux binary.
    
    HDSentinel Linux can be downloaded from:
    https://www.hdsentinel.com/hard_disk_sentinel_linux.php
    """
    
    def __init__(self, hdsentinel_path: Optional[str] = None):
        """
        Initialize HDSentinel integration.
        
        Args:
            hdsentinel_path: Path to HDSentinel binary. If None, searches common locations.
        """
        self.hdsentinel_path = self._find_hdsentinel(hdsentinel_path)
        self.xml_output_path = None
        
        if not self.hdsentinel_path:
            raise FileNotFoundError(
                "HDSentinel binary not found. "
                "Please download from https://www.hdsentinel.com/hard_disk_sentinel_linux.php "
                "and place it in /usr/local/bin/hdsentinel or ./tools/hdsentinel"
            )
    
    def _find_hdsentinel(self, custom_path: Optional[str] = None) -> Optional[str]:
        """Find HDSentinel binary in common locations"""
        if custom_path and os.path.exists(custom_path):
            return custom_path
        
        base_dir = os.path.dirname(__file__)
        
        # Common locations - check files first (various name spellings)
        search_paths = [
            '/usr/local/bin/hdsentinel',
            '/usr/bin/hdsentinel',
            '/opt/hdsentinel/hdsentinel',
            os.path.join(base_dir, 'HDSentinal'),  # User's actual file name
            os.path.join(base_dir, 'hdsentinel'),
            os.path.join(base_dir, 'HDSentinel'),
            os.path.join(base_dir, 'tools', 'hdsentinel'),
            './HDSentinal',  # User's actual file name
            './hdsentinel',
            './HDSentinel',
            './tools/hdsentinel',
        ]
        
        # Also check inside folders named "hdsentinel" or "HDSentinal" (various spellings)
        folder_paths = [
            os.path.join(base_dir, 'HDSentinal'),  # User's actual folder name
            os.path.join(base_dir, 'hdsentinel'),
            './HDSentinal',  # User's actual folder name
            './hdsentinel',
            './HDSentinel',
            './HDSENTINEL',
        ]
        
        # Check for binary files inside folders
        for folder_path in folder_paths:
            if os.path.isdir(folder_path):
                # Check common binary names inside folder
                for bin_name in ['hdsentinel', 'HDSentinel', 'HDSENTINEL', 'hdsentinel-linux', 'HDSentinel-linux']:
                    bin_path = os.path.join(folder_path, bin_name)
                    if os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
                        search_paths.append(bin_path)
        
        for path in search_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def check_health(self, device_path: str) -> Dict:
        """
        Run HDSentinel health check on a drive.
        
        Args:
            device_path: Path to device (e.g., '/dev/sdb')
        
        Returns:
            Dictionary with health information
        """
        # HDSentinel command-line options vary by version
        # Common options: -r (report), -html (HTML output), -txt (text output)
        
        # Try to get text report
        result = subprocess.run(
            [self.hdsentinel_path, '-r', device_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            # Try alternative command format
            result = subprocess.run(
                [self.hdsentinel_path, device_path],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        health_data = self._parse_hdsentinel_output(result.stdout)
        health_data['raw_output'] = result.stdout
        health_data['return_code'] = result.returncode
        
        return health_data
    
    def get_detailed_report(self, device_path: str, output_format: str = 'txt') -> Dict:
        """
        Get detailed HDSentinel report.
        
        Args:
            device_path: Path to device
            output_format: 'txt', 'html', or 'xml'
        
        Returns:
            Dictionary with report data
        """
        format_flags = {
            'txt': '-txt',
            'html': '-html',
            'xml': '-xml'
        }
        
        flag = format_flags.get(output_format, '-txt')
        
        result = subprocess.run(
            [self.hdsentinel_path, flag, device_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        report_data = {
            'format': output_format,
            'output': result.stdout,
            'return_code': result.returncode
        }
        
        if output_format == 'xml' and result.returncode == 0:
            try:
                root = ET.fromstring(result.stdout)
                report_data['parsed'] = self._parse_xml_report(root)
            except ET.ParseError:
                report_data['parse_error'] = 'Failed to parse XML'
        
        return report_data
    
    def run_surface_test(self, device_path: str, test_type: str = 'quick') -> Dict:
        """
        Run HDSentinel surface test.
        
        Args:
            device_path: Path to device
            test_type: 'quick', 'complete', or 'repair'
        
        Returns:
            Dictionary with test results
        """
        test_flags = {
            'quick': '-quicktest',
            'complete': '-completetest',
            'repair': '-repair'
        }
        
        flag = test_flags.get(test_type, '-quicktest')
        
        result = subprocess.run(
            [self.hdsentinel_path, flag, device_path],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )
        
        return {
            'test_type': test_type,
            'output': result.stdout,
            'return_code': result.returncode,
            'results': self._parse_test_results(result.stdout)
        }
    
    def get_all_drives_info(self) -> List[Dict]:
        """
        Get information about all detected drives.
        
        Returns:
            List of drive information dictionaries
        """
        result = subprocess.run(
            [self.hdsentinel_path, '-r'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            # Try without flag
            result = subprocess.run(
                [self.hdsentinel_path],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        return self._parse_drive_list(result.stdout)
    
    def _parse_hdsentinel_output(self, output: str) -> Dict:
        """Parse HDSentinel text output"""
        health_data = {
            'health_percent': None,
            'temperature': None,
            'power_on_hours': None,
            'power_cycle_count': None,
            'reallocated_sectors': None,
            'pending_sectors': None,
            'uncorrectable_sectors': None,
            'status': None,
            'model': None,
            'serial': None,
            'capacity': None,
        }
        
        lines = output.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Health percentage
            if 'health' in line_lower and '%' in line:
                try:
                    health_match = re.search(r'(\d+)%', line)
                    if health_match:
                        health_data['health_percent'] = int(health_match.group(1))
                except:
                    pass
            
            # Temperature
            if 'temperature' in line_lower or 'temp' in line_lower:
                try:
                    temp_match = re.search(r'(\d+)\s*°?c', line, re.IGNORECASE)
                    if temp_match:
                        health_data['temperature'] = int(temp_match.group(1))
                except:
                    pass
            
            # Power-on hours
            if 'power' in line_lower and 'hour' in line_lower:
                try:
                    poh_match = re.search(r'(\d+)', line)
                    if poh_match:
                        health_data['power_on_hours'] = int(poh_match.group(1))
                except:
                    pass
            
            # Model
            if 'model' in line_lower:
                model_match = re.search(r'model[:\s]+(.+)', line, re.IGNORECASE)
                if model_match:
                    health_data['model'] = model_match.group(1).strip()
            
            # Serial
            if 'serial' in line_lower:
                serial_match = re.search(r'serial[:\s]+(.+)', line, re.IGNORECASE)
                if serial_match:
                    health_data['serial'] = serial_match.group(1).strip()
            
            # Capacity
            if 'capacity' in line_lower or 'size' in line_lower:
                cap_match = re.search(r'(\d+\.?\d*)\s*(gb|tb|mb)', line, re.IGNORECASE)
                if cap_match:
                    health_data['capacity'] = line.strip()
        
        return health_data
    
    def _parse_xml_report(self, root: ET.Element) -> Dict:
        """Parse HDSentinel XML report"""
        data = {}
        
        # Navigate XML structure (structure may vary by HDSentinel version)
        for disk in root.findall('.//Disk'):
            disk_data = {}
            for child in disk:
                disk_data[child.tag] = child.text
            data[disk.get('id', 'unknown')] = disk_data
        
        return data
    
    def _parse_test_results(self, output: str) -> Dict:
        """Parse surface test results"""
        results = {
            'bad_sectors': 0,
            'tested_sectors': 0,
            'status': 'unknown'
        }
        
        lines = output.split('\n')
        for line in lines:
            if 'bad' in line.lower() and 'sector' in line.lower():
                bad_match = re.search(r'(\d+)', line)
                if bad_match:
                    results['bad_sectors'] = int(bad_match.group(1))
            
            if 'tested' in line.lower() or 'scanned' in line.lower():
                tested_match = re.search(r'(\d+)', line)
                if tested_match:
                    results['tested_sectors'] = int(tested_match.group(1))
            
            if 'passed' in line.lower():
                results['status'] = 'passed'
            elif 'failed' in line.lower():
                results['status'] = 'failed'
        
        return results
    
    def _parse_drive_list(self, output: str) -> List[Dict]:
        """Parse list of all drives"""
        drives = []
        lines = output.split('\n')
        
        current_drive = {}
        for line in lines:
            if not line.strip():
                if current_drive:
                    drives.append(current_drive)
                    current_drive = {}
                continue
            
            # Parse drive information
            if ':' in line:
                key, value = line.split(':', 1)
                current_drive[key.strip().lower()] = value.strip()
        
        if current_drive:
            drives.append(current_drive)
        
        return drives

