# Frontend Setup Guide

## Quick Start

### 1. Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment (Optional)

Create `frontend/.env` if you need to change API URLs:

```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SOCKET_URL=http://localhost:5000
```

### 3. Start Development Server

```bash
npm start
```

The frontend will start on `http://localhost:3000`

### 4. Make Sure Backend is Running

In another terminal:

```bash
# Activate venv
source venv/bin/activate

# Start Flask API
python app.py
```

## Features

✅ **Single-Page Application** - No page refreshes
✅ **Real-time Updates** - WebSocket-driven updates
✅ **PO Number Persistence** - Auto-saves and restores
✅ **Visual Bay Map** - Physical drive bay representation
✅ **Testing Controls** - Enable/disable tests, start/stop all
✅ **Responsive Design** - Works on mobile and desktop

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.js          # PO number and user details
│   │   ├── TestingControls.js # Test configuration
│   │   └── BayMap.js          # Visual bay mapping
│   ├── hooks/
│   │   └── useWebSocket.js    # WebSocket connection hook
│   ├── services/
│   │   └── api.js             # REST API client
│   ├── App.js                 # Main app component
│   └── index.js               # Entry point
├── package.json
└── README.md
```

## Development

- Hot reloading enabled
- WebSocket auto-reconnects
- API errors are logged to console
- All state persists to backend database

## Production Build

```bash
npm run build
```

Serve the `build/` directory with a web server or integrate with Flask to serve static files.

