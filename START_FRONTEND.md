# Starting the Frontend

You have two options to run the frontend:

## Option 1: Development Mode (Recommended)

Run React dev server separately for hot-reloading:

```bash
# Terminal 1: Start Flask backend
source venv/bin/activate
python app.py

# Terminal 2: Start React frontend
cd frontend
npm install  # First time only
npm start
```

Then access the app at: **http://localhost:3000**

The React dev server will proxy API calls to Flask on port 5005.

## Option 2: Production Build

Build React and serve from Flask:

```bash
# Build React frontend
cd frontend
npm install  # First time only
npm run build

# Start Flask (will serve the built frontend)
cd ..
source venv/bin/activate
python app.py
```

Then access the app at: **http://localhost:5005**

## Troubleshooting

### 404 Error

If you get a 404:
- **Option 1**: Make sure React dev server is running (`npm start` in `frontend/` directory)
- **Option 2**: Make sure you've built the frontend (`npm run build` in `frontend/` directory)

### API Connection Issues

- Make sure Flask backend is running on port 5005
- Check browser console for CORS errors
- Verify WebSocket connection in browser dev tools

### Port Already in Use

If port 3000 or 5005 is in use:
- Change React port: `PORT=3001 npm start`
- Change Flask port: Set `PORT=5006` in environment or edit `config.py`

