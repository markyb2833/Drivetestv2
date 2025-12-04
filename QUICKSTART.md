# Quick Start Guide

## First Time Setup

### 1. Create Virtual Environment

```bash
./setup_venv.sh
```

This will:
- Create a `venv/` directory (gitignored)
- Install all Python dependencies
- Isolate the project from your system Python

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### 3. Initialize Database

```bash
python init_database.py
```

This creates all database tables in MySQL.

### 4. Verify Setup

```bash
# Test OS drive detection (requires sudo)
sudo python verify_safety.py

# Test drive detection (requires sudo)
sudo python drive_detector.py
```

## Daily Usage

### Activate Environment

```bash
source venv/bin/activate
# or
./activate.sh
```

### Run Application

```bash
# (When Flask app is ready)
python app.py
```

### Deactivate Environment

```bash
deactivate
```

## Troubleshooting

### Virtual Environment Not Found

If `venv/` doesn't exist, run:
```bash
./setup_venv.sh
```

### Database Connection Error

Check:
1. MySQL server is running at `192.168.0.197`
2. Database `compudrive` exists
3. User `newinv` has proper permissions
4. Network connectivity

### Permission Errors

Some operations require root/sudo:
- Drive detection
- Running tests
- Reading `/dev/` devices

Use `sudo` when running scripts that access hardware.

