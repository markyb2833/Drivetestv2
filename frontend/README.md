# HDD Tester Frontend

React single-page application for the HDD Tester Platform.

## Features

- **Single-Page Application**: No page refreshes, all updates via WebSocket
- **Real-time Updates**: Drive status, test progress, and bay map update in real-time
- **Visual Bay Map**: Physical representation of drive bays with status indicators
- **Testing Controls**: Enable/disable tests, start/stop all tests
- **Persistent PO Number**: PO number persists across page refreshes

## Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file in the `frontend` directory:

```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SOCKET_URL=http://localhost:5000
```

### Development

```bash
npm start
```

The app will open at `http://localhost:3000`

### Production Build

```bash
npm run build
```

The build output will be in the `build` directory.

## Architecture

- **Components**:
  - `Header`: User details and PO number
  - `TestingControls`: Test configuration and global controls
  - `BayMap`: Visual bay mapping display

- **Services**:
  - `api.js`: REST API client
  - `useWebSocket.js`: WebSocket hook for real-time updates

- **Features**:
  - Auto-restores PO number and settings on page load
  - Real-time WebSocket updates for all drive changes
  - Responsive design for mobile and desktop

