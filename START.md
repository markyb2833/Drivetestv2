# How to Start the Application

## Quick Start

### 1. Initialize Database (First Time Only)

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database tables
python init_database.py
```

### 2. Start Backend Server

**Option A: Using run script**
```bash
./run.sh
```

**Option B: Manual start**
```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask backend
python app.py
```

Backend will start on: **http://0.0.0.0:5005**

### 3. Start Frontend (Choose One)

**Option A: Development Mode (Recommended for Testing)**
```bash
# Open a NEW terminal window
cd /path/to/Drivetestv2/frontend
npm start
```

Frontend will start on: **http://localhost:3000**

**Option B: Production Mode (Built Frontend)**
```bash
# Build frontend first (one time)
cd frontend
npm run build
cd ..

# Then start backend - it will serve the built frontend
python app.py
```

Access at: **http://server-ip:5005**

## Testing Checklist

### 1. Check Backend is Running
```bash
# Test API endpoint
curl http://localhost:5005/api/system/status

# Should return JSON with system status
```

### 2. Check Frontend
- Open browser: `http://localhost:3000` (dev) or `http://server-ip:5005` (production)
- You should see the HDD Tester Platform interface

### 3. Test Drive Detection
```bash
# In another terminal, test drive detection (requires sudo)
sudo python drive_detector.py
```

### 4. Test WebSocket Connection
- Open browser developer console (F12)
- Check for WebSocket connection messages
- Should see "Connected" status in the header

## Troubleshooting

### Backend Won't Start

**Port already in use:**
```bash
# Check what's using port 5005
sudo lsof -i :5005

# Or change port
export PORT=5006
python app.py
```

**Database connection error:**
```bash
# Test MySQL connection
mysql -h 192.168.0.197 -u newinv -p

# Verify database exists
mysql -h 192.168.0.197 -u newinv -p -e "SHOW DATABASES;"
```

### Frontend Won't Start

**Port 3000 in use:**
```bash
# Change port
PORT=3001 npm start
```

**npm install needed:**
```bash
cd frontend
npm install
npm start
```

### Can't Access from Another Machine

**Check firewall:**
```bash
# Ubuntu/Debian
sudo ufw allow 5005/tcp
sudo ufw allow 3000/tcp  # if running dev frontend

# Check if backend is listening on all interfaces
netstat -tuln | grep 5005
```

**Backend should show:**
```
Starting HDD Tester API on 0.0.0.0:5005
```

## Running in Background

### Using Screen
```bash
screen -S hdd-tester
source venv/bin/activate
python app.py
# Press Ctrl+A then D to detach
```

### Using Tmux
```bash
tmux new -s hdd-tester
source venv/bin/activate
python app.py
# Press Ctrl+B then D to detach
```

### Using Nohup
```bash
source venv/bin/activate
nohup python app.py > logs/app.log 2>&1 &
```

## Stopping the Application

**Backend:**
- Press `Ctrl+C` in the terminal
- Or if running in background: `pkill -f "python app.py"`

**Frontend (dev server):**
- Press `Ctrl+C` in the terminal

## Full Test Sequence

1. **Start backend:**
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **In another terminal, start frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Open browser:**
   - Go to: `http://localhost:3000`
   - You should see the HDD Tester Platform interface

4. **Test features:**
   - Check connection status (should show "Connected")
   - Enter a PO number
   - View bay map (will show empty if no drives detected)
   - Try starting a test (if drives are detected)

## Production Deployment

For production, see `DEPLOYMENT.md` for systemd service setup.

