"""
Drive Detection Service

Detects all drives, maps them to physical bays, and excludes OS drive.
Provides stable device path identification for persistent mapping.
"""

import os
import subprocess
import re
from typing import Dict, Optional, List
from dataclasses import dataclass
from os_drive_detector import get_os_drive, is_os_drive, get_all_non_os_drives


@dataclass
class DriveInfo:
    """Information about a detected drive"""
    device_name: str  # e.g., 'sdb'
    device_path: str  # e.g., '/dev/sdb'
    stable_path: Optional[str] = None  # e.g., 'pci-0000:01:00.0-scsi-0:0:5:0'
    bay_number: Optional[int] = None
    serial: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[str] = None
    connection_type: Optional[str] = None  # 'SATA' or 'SAS'
    sata_version: Optional[str] = None  # 'SATA1', 'SATA2', 'SATA3'
    scsi_host: Optional[int] = None
    scsi_channel: Optional[int] = None
    scsi_target: Optional[int] = None
    scsi_lun: Optional[int] = None


class DriveDetector:
    """Service for detecting and mapping drives"""
    
    def __init__(self):
        self.os_drive_name, self.os_drive_path = get_os_drive()
        self.drives: Dict[str, DriveInfo] = {}
        self.bay_mapping: Dict[int, DriveInfo] = {}  # bay_number -> DriveInfo
        
    def scan_drives(self) -> Dict[str, DriveInfo]:
        """
        Scan for all non-OS drives and extract their information.
        
        Returns:
            dict: Mapping of device_path -> DriveInfo
        """
        self.drives = {}
        self.bay_mapping = {}
        
        # Get all non-OS drives
        drive_paths = get_all_non_os_drives()
        
        for device_path in drive_paths:
            try:
                drive_info = self._get_drive_info(device_path)
                if drive_info:
                    self.drives[device_path] = drive_info
                    
                    # Map to bay if bay number detected
                    if drive_info.bay_number is not None:
                        self.bay_mapping[drive_info.bay_number] = drive_info
                        
            except Exception as e:
                print(f"Error scanning drive {device_path}: {e}")
                continue
        
        return self.drives
    
    def _get_drive_info(self, device_path: str) -> Optional[DriveInfo]:
        """Extract comprehensive information about a drive"""
        device_name = device_path.replace('/dev/', '')
        
        # Skip OS drive (double-check)
        if is_os_drive(device_path):
            print(f"SKIPPING OS DRIVE: {device_path}")
            return None
        
        drive_info = DriveInfo(
            device_name=device_name,
            device_path=device_path
        )
        
        # Get stable path
        drive_info.stable_path = self._get_stable_path(device_path)
        
        # Get SCSI information (for bay mapping)
        scsi_info = self._get_scsi_info(device_name)
        if scsi_info:
            drive_info.scsi_host = scsi_info.get('host')
            drive_info.scsi_channel = scsi_info.get('channel')
            drive_info.scsi_target = scsi_info.get('target')
            drive_info.scsi_lun = scsi_info.get('lun')
            
            # Use SCSI target as bay number (common on backplanes)
            if drive_info.scsi_target is not None:
                drive_info.bay_number = drive_info.scsi_target
        
        # Get drive metadata
        drive_info.serial = self._get_serial(device_path)
        drive_info.model = self._get_model(device_path)
        drive_info.capacity = self._get_capacity(device_path)
        
        # Get connection type
        drive_info.connection_type, drive_info.sata_version = self._get_connection_info(device_path)
        
        return drive_info
    
    def _get_stable_path(self, device_path: str) -> Optional[str]:
        """Get stable device path from /dev/disk/by-path/"""
        device_name = device_path.replace('/dev/', '')
        
        try:
            by_path_dir = '/dev/disk/by-path'
            if not os.path.exists(by_path_dir):
                return None
            
            # Find symlink pointing to this device
            for link_name in os.listdir(by_path_dir):
                link_path = os.path.join(by_path_dir, link_name)
                try:
                    target = os.readlink(link_path)
                    # Check if target matches our device (handle partition numbers)
                    if device_name in target or f'/{device_name}' in target:
                        return link_name
                except Exception:
                    continue
        except Exception as e:
            print(f"Error getting stable path for {device_path}: {e}")
        
        return None
    
    def _get_scsi_info(self, device_name: str) -> Optional[Dict[str, int]]:
        """Get SCSI Host/Channel/Target/LUN from sysfs"""
        scsi_device_path = f'/sys/block/{device_name}/device/scsi_device'
        
        try:
            if os.path.exists(scsi_device_path):
                with open(scsi_device_path, 'r') as f:
                    scsi_str = f.read().strip()
                    # Format: "0:0:5:0" -> host:channel:target:lun
                    parts = scsi_str.split(':')
                    if len(parts) == 4:
                        return {
                            'host': int(parts[0]),
                            'channel': int(parts[1]),
                            'target': int(parts[2]),
                            'lun': int(parts[3])
                        }
        except Exception as e:
            print(f"Error reading SCSI info for {device_name}: {e}")
        
        return None
    
    def _get_serial(self, device_path: str) -> Optional[str]:
        """Get drive serial number"""
        try:
            result = subprocess.run(
                ['smartctl', '-i', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Serial Number:' in line or 'Serial number:' in line:
                        return line.split(':')[1].strip()
        except Exception:
            pass
        
        # Fallback: try sysfs
        device_name = device_path.replace('/dev/', '')
        serial_path = f'/sys/block/{device_name}/device/serial'
        try:
            if os.path.exists(serial_path):
                with open(serial_path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        
        return None
    
    def _get_model(self, device_path: str) -> Optional[str]:
        """Get drive model number"""
        try:
            result = subprocess.run(
                ['smartctl', '-i', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Device Model:' in line or 'Model Number:' in line or 'Model Family:' in line:
                        return line.split(':')[1].strip()
        except Exception:
            pass
        
        # Fallback: try sysfs
        device_name = device_path.replace('/dev/', '')
        model_path = f'/sys/block/{device_name}/device/model'
        try:
            if os.path.exists(model_path):
                with open(model_path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        
        return None
    
    def _get_capacity(self, device_path: str) -> Optional[str]:
        """Get drive capacity"""
        try:
            result = subprocess.run(
                ['lsblk', '-b', '-d', '-n', '-o', 'SIZE', device_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                size_bytes = result.stdout.strip()
                if size_bytes.isdigit():
                    size_gb = int(size_bytes) / (1024**3)
                    return f"{size_gb:.2f} GB"
        except Exception:
            pass
        
        return None
    
    def _get_connection_info(self, device_path: str) -> tuple[Optional[str], Optional[str]]:
        """Get connection type (SATA/SAS) and SATA version"""
        connection_type = None
        sata_version = None
        
        try:
            result = subprocess.run(
                ['smartctl', '-i', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'sas' in output:
                    connection_type = 'SAS'
                elif 'sata' in output or 'ata' in output:
                    connection_type = 'SATA'
                    
                    # Try to detect SATA version
                    if 'sata 3' in output or 'sata/600' in output:
                        sata_version = 'SATA3'
                    elif 'sata 2' in output or 'sata/300' in output:
                        sata_version = 'SATA2'
                    elif 'sata 1' in output or 'sata/150' in output:
                        sata_version = 'SATA1'
        except Exception:
            pass
        
        return connection_type, sata_version
    
    def get_bay_map(self) -> Dict[int, DriveInfo]:
        """Get mapping of bay numbers to drives"""
        return self.bay_mapping
    
    def get_drive_by_bay(self, bay_number: int) -> Optional[DriveInfo]:
        """Get drive information for a specific bay"""
        return self.bay_mapping.get(bay_number)
    
    def get_drive_by_path(self, device_path: str) -> Optional[DriveInfo]:
        """Get drive information by device path"""
        return self.drives.get(device_path)


if __name__ == '__main__':
    # Test drive detection
    detector = DriveDetector()
    print(f"OS Drive: {detector.os_drive_name} -> {detector.os_drive_path}\n")
    
    drives = detector.scan_drives()
    print(f"Detected {len(drives)} non-OS drives:\n")
    
    for device_path, drive_info in drives.items():
        print(f"Device: {drive_info.device_path}")
        print(f"  Stable Path: {drive_info.stable_path}")
        print(f"  Bay Number: {drive_info.bay_number}")
        print(f"  Serial: {drive_info.serial}")
        print(f"  Model: {drive_info.model}")
        print(f"  Capacity: {drive_info.capacity}")
        print(f"  Connection: {drive_info.connection_type} {drive_info.sata_version}")
        print(f"  SCSI: {drive_info.scsi_host}:{drive_info.scsi_channel}:{drive_info.scsi_target}:{drive_info.scsi_lun}")
        print()

