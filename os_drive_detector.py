"""
OS Drive Detection Module

CRITICAL SAFETY MODULE: Prevents tests from running on the OS drive.
This module provides multiple methods to identify the OS drive and must
be used before any destructive operations.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Set


def get_os_drive() -> tuple[Optional[str], Optional[str]]:
    """
    Detect the OS drive using multiple methods for reliability.
    
    Returns:
        tuple: (device_name, device_path) e.g., ('sda', '/dev/sda')
               Returns (None, None) if detection fails
    """
    # Method 1: Check /proc/mounts for root filesystem
    root_device = _get_root_device_from_mounts()
    if root_device:
        device_name, device_path = _normalize_device(root_device)
        if device_name:
            return device_name, device_path
    
    # Method 2: Check /etc/fstab for root partition
    root_device = _get_root_device_from_fstab()
    if root_device:
        device_name, device_path = _normalize_device(root_device)
        if device_name:
            return device_name, device_path
    
    # Method 3: Check which device contains /boot
    boot_device = _get_boot_device()
    if boot_device:
        device_name, device_path = _normalize_device(boot_device)
        if device_name:
            return device_name, device_path
    
    # Method 4: Use lsblk to find root filesystem
    root_device = _get_root_device_from_lsblk()
    if root_device:
        device_name, device_path = _normalize_device(root_device)
        if device_name:
            return device_name, device_path
    
    return None, None


def _get_root_device_from_mounts() -> Optional[str]:
    """Get root device from /proc/mounts"""
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == '/':
                    device = parts[0]
                    # Remove partition number if present (e.g., /dev/sda1 -> /dev/sda)
                    if device.startswith('/dev/'):
                        device = re.sub(r'(\d+)$', '', device)
                    return device
    except Exception as e:
        print(f"Error reading /proc/mounts: {e}")
    return None


def _get_root_device_from_fstab() -> Optional[str]:
    """Get root device from /etc/fstab"""
    try:
        with open('/etc/fstab', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == '/':
                        device = parts[0]
                        if device.startswith('/dev/'):
                            device = re.sub(r'(\d+)$', '', device)
                        return device
    except Exception as e:
        print(f"Error reading /etc/fstab: {e}")
    return None


def _get_boot_device() -> Optional[str]:
    """Get device containing /boot directory"""
    try:
        result = subprocess.run(
            ['df', '/boot'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if parts:
                    device = parts[0]
                    if device.startswith('/dev/'):
                        device = re.sub(r'(\d+)$', '', device)
                    return device
    except Exception as e:
        print(f"Error getting boot device: {e}")
    return None


def _get_root_device_from_lsblk() -> Optional[str]:
    """Get root device using lsblk"""
    try:
        result = subprocess.run(
            ['lsblk', '-n', '-o', 'NAME,MOUNTPOINT'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == '/':
                    device_name = parts[0]
                    # Remove partition number
                    device_name = re.sub(r'(\d+)$', '', device_name)
                    return f'/dev/{device_name}'
    except Exception as e:
        print(f"Error using lsblk: {e}")
    return None


def _normalize_device(device: str) -> tuple[Optional[str], Optional[str]]:
    """
    Normalize device path to standard format.
    
    Args:
        device: Device path (e.g., '/dev/sda', 'sda', '/dev/disk/by-uuid/...')
    
    Returns:
        tuple: (device_name, device_path) e.g., ('sda', '/dev/sda')
    """
    if not device:
        return None, None
    
    # Handle UUID/LABEL paths - resolve to actual device
    if '/dev/disk/by-' in device:
        try:
            real_path = os.path.realpath(device)
            device = real_path
        except Exception:
            pass
    
    # Extract device name
    if device.startswith('/dev/'):
        device_name = device.replace('/dev/', '')
    else:
        device_name = device
    
    # Remove partition numbers (sda1 -> sda)
    device_name = re.sub(r'(\d+)$', '', device_name)
    
    # Ensure it's a block device (starts with sd, nvme, etc.)
    if not (device_name.startswith('sd') or device_name.startswith('nvme') or 
            device_name.startswith('hd')):
        return None, None
    
    device_path = f'/dev/{device_name}'
    
    # Verify device exists
    if os.path.exists(device_path):
        return device_name, device_path
    
    return None, None


def is_os_drive(device_path: str) -> bool:
    """
    Check if a device path is the OS drive.
    
    Args:
        device_path: Device path to check (e.g., '/dev/sda')
    
    Returns:
        bool: True if device is the OS drive
    """
    os_drive_name, os_drive_path = get_os_drive()
    
    if not os_drive_name or not os_drive_path:
        # If we can't detect OS drive, be conservative and reject
        print("WARNING: Could not detect OS drive. Rejecting device for safety.")
        return True
    
    # Normalize input device
    device_name, normalized_path = _normalize_device(device_path)
    
    if not device_name:
        return False
    
    # Compare device names (e.g., 'sda' == 'sda')
    return device_name == os_drive_name


def get_all_non_os_drives() -> Set[str]:
    """
    Get set of all non-OS drive device paths.
    
    Returns:
        set: Set of device paths (e.g., {'/dev/sdb', '/dev/sdc'})
    """
    os_drive_name, _ = get_os_drive()
    drives = set()
    
    try:
        result = subprocess.run(
            ['lsblk', '-d', '-n', '-o', 'NAME'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                device_name = line.strip()
                
                # Skip if OS drive
                if os_drive_name and device_name == os_drive_name:
                    continue
                
                # Only include block devices (sd*, nvme*, hd*)
                if device_name.startswith(('sd', 'nvme', 'hd')):
                    device_path = f'/dev/{device_name}'
                    if os.path.exists(device_path):
                        drives.add(device_path)
    
    except Exception as e:
        print(f"Error getting drive list: {e}")
    
    return drives


if __name__ == '__main__':
    # Test OS drive detection
    os_name, os_path = get_os_drive()
    print(f"OS Drive: {os_name} -> {os_path}")
    
    # Test all drives
    all_drives = get_all_non_os_drives()
    print(f"\nNon-OS Drives ({len(all_drives)}):")
    for drive in sorted(all_drives):
        print(f"  {drive}")

