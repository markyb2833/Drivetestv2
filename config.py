"""
Configuration Module

Centralized configuration management.
"""

import os
from typing import Optional

# Database Configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://newinv:password123!@192.168.0.197/compudrive'
)

# Application Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5005))

# WebSocket Configuration
WEBSOCKET_CORS_ALLOWED_ORIGINS = os.getenv(
    'WEBSOCKET_CORS_ALLOWED_ORIGINS',
    '*'
).split(',')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', '/var/log/hdd_tester')

# Test Configuration
MAX_CONCURRENT_TESTS = int(os.getenv('MAX_CONCURRENT_TESTS', '20'))
TEST_TIMEOUT_DEFAULT = int(os.getenv('TEST_TIMEOUT_DEFAULT', '3600'))  # 1 hour

# Paths - Use local directories for development, system directories for production
# Check if we're in development (local directory) or production
_script_dir = os.path.dirname(os.path.abspath(__file__))
_is_development = os.path.exists(os.path.join(_script_dir, '.git')) or os.path.exists(os.path.join(_script_dir, 'venv'))

if _is_development:
    # Development: Use local directories
    DATA_DIR = os.getenv('DATA_DIR', os.path.join(_script_dir, 'data'))
    CONFIG_DIR = os.getenv('CONFIG_DIR', os.path.join(_script_dir, 'config'))
    LOG_DIR = os.getenv('LOG_DIR', os.path.join(_script_dir, 'logs'))
else:
    # Production: Use system directories
    DATA_DIR = os.getenv('DATA_DIR', '/var/lib/hdd_tester')
    CONFIG_DIR = os.getenv('CONFIG_DIR', '/etc/hdd_tester')
    LOG_DIR = os.getenv('LOG_DIR', '/var/log/hdd_tester')

# Ensure directories exist (handle permission errors gracefully)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except PermissionError:
    print(f"Warning: Could not create {DATA_DIR}, using current directory")
    DATA_DIR = _script_dir

try:
    os.makedirs(CONFIG_DIR, exist_ok=True)
except PermissionError:
    print(f"Warning: Could not create {CONFIG_DIR}, using current directory")
    CONFIG_DIR = _script_dir

try:
    os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError:
    print(f"Warning: Could not create {LOG_DIR}, using current directory")
    LOG_DIR = _script_dir

