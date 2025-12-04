# Deployment Guide

## Pre-Deployment Checklist

### ✅ System Requirements

- **OS**: Ubuntu LTS (18.04, 20.04, 22.04, or 24.04) or Debian
- **Python**: 3.8+ (Python 3.10+ recommended)
- **Node.js**: 14+ (Node.js 18+ recommended)
- **MySQL**: Server accessible at `192.168.0.197:3306`
- **Network**: Access to MySQL database
- **Permissions**: sudo/root access for system package installation

### ✅ Files Ready

- ✅ `install.sh` - Auto-installation script
- ✅ `requirements.txt` - Python dependencies
- ✅ `frontend/package.json` - Node.js dependencies
- ✅ `init_database.py` - Database initialization
- ✅ All Python modules (app.py, test_executor.py, etc.)
- ✅ Frontend React application

### ⚠️ Manual Steps Required

1. **HDSentinel Linux** (Optional but recommended)
   - Download from: https://www.hdsentinel.com/hard_disk_sentinel_linux.php
   - Install to: `/usr/local/bin/hdsentinel`
   - Or place in: `./tools/hdsentinel` or `./hdsentinel`

2. **MySQL Database**
   - Ensure database `compudrive` exists
   - Verify connection: `mysql://newinv:password123!@192.168.0.197/compudrive`
   - Test connection from Linux server

## Deployment Steps

### Step 1: Transfer Files to Linux Server

```bash
# Option 1: Using SCP
scp -r Compudrive/ user@server:/opt/hdd_tester/

# Option 2: Using Git (if repository)
git clone <repository-url> /opt/hdd_tester
cd /opt/hdd_tester

# Option 3: Using rsync
rsync -avz Compudrive/ user@server:/opt/hdd_tester/
```

### Step 2: SSH into Linux Server

```bash
ssh user@server
cd /opt/hdd_tester  # or wherever you placed the files
```

### Step 3: Run Installation Script

```bash
# Make install script executable
chmod +x install.sh

# Run installation (will prompt for sudo password)
./install.sh
```

The script will:
- ✅ Install system packages (smartmontools, hdparm, etc.)
- ✅ Set up Python virtual environment
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Check for HDSentinel (optional)
- ✅ Verify installation

### Step 4: Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database tables
python init_database.py
```

Expected output:
```
✓ Database connection successful!
✓ Tables created/verified successfully!
```

### Step 5: Verify MySQL Connection

```bash
# Test database connection
python -c "from database import get_db; db = get_db(); session = db.get_session(); print('Connected!'); session.close()"
```

### Step 6: (Optional) Install HDSentinel

If you have HDSentinel Linux binary:

```bash
# Copy to system location
sudo cp /path/to/hdsentinel /usr/local/bin/
sudo chmod +x /usr/local/bin/hdsentinel

# Verify
hdsentinel --version
```

### Step 7: Test Drive Detection (Requires sudo)

```bash
# Activate venv
source venv/bin/activate

# Test drive detection (requires root for drive access)
sudo python drive_detector.py
```

### Step 8: Start Backend Server

```bash
# Activate venv
source venv/bin/activate

# Start Flask backend
python app.py
```

Or use the run script:
```bash
./run.sh
```

Backend will start on: `http://0.0.0.0:5005`

### Step 9: Start Frontend (Development)

In a **separate terminal**:

```bash
cd /opt/hdd_tester/frontend
npm start
```

Frontend will start on: `http://localhost:3000`

### Step 10: Build Frontend for Production

```bash
cd /opt/hdd_tester/frontend
npm run build
```

The built frontend will be served by Flask at `http://server:5005`

## Production Deployment

### Option 1: Systemd Service (Recommended)

Create `/etc/systemd/system/hdd-tester.service`:

```ini
[Unit]
Description=HDD Tester Platform
After=network.target mysql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/hdd_tester
Environment="PATH=/opt/hdd_tester/venv/bin"
ExecStart=/opt/hdd_tester/venv/bin/python /opt/hdd_tester/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hdd-tester
sudo systemctl start hdd-tester
sudo systemctl status hdd-tester
```

### Option 2: Screen/Tmux

```bash
# Using screen
screen -S hdd-tester
source venv/bin/activate
python app.py
# Press Ctrl+A then D to detach

# Using tmux
tmux new -s hdd-tester
source venv/bin/activate
python app.py
# Press Ctrl+B then D to detach
```

### Option 3: Nohup

```bash
source venv/bin/activate
nohup python app.py > logs/app.log 2>&1 &
```

## Firewall Configuration

If firewall is enabled, open ports:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5005/tcp
sudo ufw allow 3000/tcp  # Only if running frontend separately

# CentOS/RHEL (firewalld)
sudo firewall-cmd --add-port=5005/tcp --permanent
sudo firewall-cmd --reload
```

## Verification

### Check Backend

```bash
curl http://localhost:5005/api/system/status
```

Expected: JSON response with system status

### Check Frontend

Open browser: `http://server-ip:5005`

Should see the HDD Tester Platform interface

### Check WebSocket

```bash
# Test WebSocket connection
wscat -c ws://localhost:5005/socket.io/?EIO=4&transport=websocket
```

## Troubleshooting

### Database Connection Failed

1. Verify MySQL server is running: `systemctl status mysql`
2. Check MySQL is accessible: `mysql -h 192.168.0.197 -u newinv -p`
3. Verify database exists: `SHOW DATABASES;`
4. Check firewall: `telnet 192.168.0.197 3306`

### Permission Errors

- Drive access requires root/sudo
- Run drive detection with: `sudo python drive_detector.py`
- Backend may need sudo for drive operations

### Port Already in Use

Change port in `config.py` or set environment variable:
```bash
export PORT=5006
python app.py
```

### Frontend Build Fails

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Post-Deployment

1. ✅ Verify drive detection works
2. ✅ Test starting a test on a drive
3. ✅ Check WebSocket real-time updates
4. ✅ Verify PO number persistence
5. ✅ Test bay mapping display
6. ✅ Check logs in `logs/` directory

## Security Notes

- ⚠️ Backend runs on `0.0.0.0:5005` (all interfaces) - consider firewall rules
- ⚠️ MySQL credentials are in `config.py` - secure this file
- ⚠️ Drive operations require root - ensure proper access controls
- ⚠️ Consider using reverse proxy (nginx) for production

## Support Files

- `README.md` - General documentation
- `QUICKSTART.md` - Quick start guide
- `HDSENTINEL_SETUP.md` - HDSentinel installation
- `TESTS.md` - Test documentation
- `SAFETY.md` - Safety features documentation

