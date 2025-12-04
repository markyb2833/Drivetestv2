# Quick Deployment Guide

## One-Command Deployment

```bash
# 1. Transfer files to server (from your Mac)
scp -r Compudrive/ user@server:/opt/hdd_tester/

# 2. SSH to server
ssh user@server
cd /opt/hdd_tester

# 3. Run installation
chmod +x install.sh && ./install.sh

# 4. Initialize database
source venv/bin/activate
python init_database.py

# 5. Start backend
python app.py
```

## What install.sh Does

✅ Installs system packages (smartmontools, hdparm, etc.)  
✅ Creates Python virtual environment  
✅ Installs Python dependencies  
✅ Installs Node.js dependencies  
✅ Checks for HDSentinel (optional)  
✅ Verifies installation  

## After Installation

1. **Initialize Database**:
   ```bash
   source venv/bin/activate
   python init_database.py
   ```

2. **Start Backend**:
   ```bash
   python app.py
   ```
   Access at: `http://server-ip:5005`

3. **Start Frontend** (Development):
   ```bash
   cd frontend && npm start
   ```
   Access at: `http://server-ip:3000`

4. **Build Frontend** (Production):
   ```bash
   cd frontend && npm run build
   ```
   Then Flask serves it automatically at port 5005

## Prerequisites

- ✅ Ubuntu LTS or Debian Linux
- ✅ sudo/root access
- ✅ MySQL server accessible at `192.168.0.197:3306`
- ✅ Internet connection (for package downloads)

## Troubleshooting

**If install.sh fails:**
- Check internet connection
- Verify sudo access: `sudo -v`
- Check disk space: `df -h`
- Review error messages

**If database init fails:**
- Verify MySQL connection: `mysql -h 192.168.0.197 -u newinv -p`
- Check database exists: `SHOW DATABASES;`
- Verify firewall allows MySQL port 3306

**If backend won't start:**
- Check port 5005 is free: `netstat -tuln | grep 5005`
- Check Python version: `python3 --version` (need 3.8+)
- Check virtual environment: `source venv/bin/activate && which python`

## Next Steps

See `DEPLOYMENT.md` for detailed production deployment instructions.

