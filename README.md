# HDD Tester Platform

A scalable hard drive testing and utility platform for Linux Ubuntu LTS.

## Features

- Visual bay mapping with real-time updates
- Parallel, isolated drive testing
- Persistent settings and PO number tracking
- Comprehensive SMART health testing
- Block size detection and modification
- Connection type detection (SATA/SAS)

## Safety Features

- **OS Drive Protection**: Never runs tests on the operating system drive
- **Isolated Execution**: Each drive runs tests in separate processes
- **Parallel Processing**: Multiple drives can be tested simultaneously without interference

## Quick Start

### 1. Setup Virtual Environment (Recommended)

```bash
# Create and setup virtual environment
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# Or use the quick activation script
./activate.sh
```

### 2. Initialize Database

```bash
# Make sure MySQL server is accessible
# Database: mysql://newinv:password123!@192.168.0.197/compudrive

# Initialize database tables
python init_database.py
```

### 3. Verify Safety Features

```bash
# Run safety verification (requires root/sudo for drive access)
sudo python verify_safety.py
```

### 4. Test Drive Detection

```bash
# Test drive detection (requires root/sudo)
sudo python drive_detector.py
```

## Virtual Environment

The project uses a Python virtual environment to isolate dependencies:

- **Setup**: Run `./setup_venv.sh` (one time)
- **Activate**: `source venv/bin/activate` or `./activate.sh`
- **Deactivate**: `deactivate`
- **Install new packages**: `pip install <package>` (while venv is active)

The virtual environment is located in `venv/` and is gitignored.

## Installation (Without Virtual Environment)

If you prefer not to use a virtual environment:

```bash
pip install -r requirements.txt
```

**Note**: This will install packages system-wide and may affect other Python projects.

## Configuration

- Database connection: Set `DATABASE_URL` environment variable or edit `config.py`
- Application settings: Edit `config.py` or use environment variables

## Development

All code is isolated in the virtual environment. Your system Python packages remain untouched.

## License

MIT

