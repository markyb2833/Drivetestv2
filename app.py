"""
Flask Application

Main Flask application with REST API and WebSocket support.
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

from config import HOST, PORT, DEBUG, WEBSOCKET_CORS_ALLOWED_ORIGINS
from drive_detector import DriveDetector
from test_executor import TestExecutor, TestStatus
from db_operations import (
    get_or_create_drive, get_drive_by_serial, get_drive_by_bay,
    get_or_create_active_session, get_active_session, update_po_number,
    create_test_session, update_test_session, add_test_result,
    get_setting, set_setting, get_all_settings,
    get_default_test_config, save_test_config,
    get_backplane_config, save_backplane_config,
    add_log
)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins=WEBSOCKET_CORS_ALLOWED_ORIGINS)

# Frontend paths
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'build')
FRONTEND_DEV_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'public')

# Global instances
drive_detector = DriveDetector()
test_executor = TestExecutor()

# Background thread for drive scanning
scanning_thread = None
scanning_active = False


# ============================================================================
# Drive Detection Background Service
# ============================================================================

def start_drive_scanning():
    """Background thread to periodically scan for drives"""
    global scanning_active
    scanning_active = True
    
    while scanning_active:
        try:
            # Scan drives
            drives = drive_detector.scan_drives()
            
            # Update database
            for device_path, drive_info in drives.items():
                if drive_info.serial:
                    get_or_create_drive(
                        serial=drive_info.serial,
                        model=drive_info.model,
                        capacity=drive_info.capacity,
                        connection_type=drive_info.connection_type,
                        sata_version=drive_info.sata_version,
                        bay_location=drive_info.bay_number,
                        device_path=drive_info.device_path,
                        stable_path=drive_info.stable_path,
                        scsi_host=drive_info.scsi_host,
                        scsi_channel=drive_info.scsi_channel,
                        scsi_target=drive_info.scsi_target,
                        scsi_lun=drive_info.scsi_lun
                    )
            
            # Emit WebSocket update
            socketio.emit('drives_updated', {
                'count': len(drives),
                'timestamp': datetime.now().isoformat()
            })
            
            # Sleep before next scan
            time.sleep(5)  # Scan every 5 seconds
            
        except Exception as e:
            print(f"Error in drive scanning: {e}")
            time.sleep(10)


# ============================================================================
# REST API Endpoints - Drives
# ============================================================================

@app.route('/api/drives', methods=['GET'])
def list_drives():
    """List all detected drives"""
    try:
        drives = drive_detector.scan_drives()
        drives_list = []
        
        for device_path, drive_info in drives.items():
            drives_list.append({
                'device_path': drive_info.device_path,
                'device_name': drive_info.device_name,
                'serial': drive_info.serial,
                'model': drive_info.model,
                'capacity': drive_info.capacity,
                'connection_type': drive_info.connection_type,
                'sata_version': drive_info.sata_version,
                'bay_number': drive_info.bay_number,
                'stable_path': drive_info.stable_path,
                'scsi_path': f"{drive_info.scsi_host}:{drive_info.scsi_channel}:{drive_info.scsi_target}:{drive_info.scsi_lun}" if drive_info.scsi_target is not None else None
            })
        
        return jsonify({
            'success': True,
            'drives': drives_list,
            'count': len(drives_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/drives/<serial>', methods=['GET'])
def get_drive(serial: str):
    """Get drive details by serial number"""
    try:
        drive_info = drive_detector.get_drive_by_path(None)  # Would need to find by serial
        # For now, scan and find
        drives = drive_detector.scan_drives()
        for device_path, info in drives.items():
            if info.serial == serial:
                return jsonify({
                    'success': True,
                    'drive': {
                        'device_path': info.device_path,
                        'device_name': info.device_name,
                        'serial': info.serial,
                        'model': info.model,
                        'capacity': info.capacity,
                        'connection_type': info.connection_type,
                        'sata_version': info.sata_version,
                        'bay_number': info.bay_number,
                        'stable_path': info.stable_path
                    }
                })
        
        return jsonify({'success': False, 'error': 'Drive not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/drives/<serial>/test', methods=['POST'])
def start_test(serial: str):
    """Start a test session on a drive"""
    try:
        data = request.get_json() or {}
        test_type = data.get('test_type', 'smart')
        
        # Find drive
        drives = drive_detector.scan_drives()
        drive_info = None
        for device_path, info in drives.items():
            if info.serial == serial:
                drive_info = info
                break
        
        if not drive_info:
            return jsonify({'success': False, 'error': 'Drive not found'}), 404
        
        # Get active session
        active_session = get_active_session()
        po_number = active_session.po_number if active_session else None
        
        # Create test session in database
        db_session = create_test_session(
            drive_serial=serial,
            po_number=po_number,
            user_session_id=active_session.id if active_session else None
        )
        
        # Start test
        def progress_callback(progress_data):
            socketio.emit('test_progress', {
                'serial': serial,
                'bay_number': drive_info.bay_number,
                **progress_data
            })
        
        success = test_executor.start_test(
            device_path=drive_info.device_path,
            test_type=test_type,
            progress_callback=progress_callback
        )
        
        if success:
            add_log('INFO', f"Test started on drive {serial}: {test_type}")
            return jsonify({
                'success': True,
                'session_id': db_session.id,
                'message': 'Test started'
            })
        else:
            return jsonify({'success': False, 'error': 'Test already running'}), 400
            
    except Exception as e:
        add_log('ERROR', f"Error starting test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/drives/<serial>/test', methods=['GET'])
def get_test_status(serial: str):
    """Get current test status for a drive"""
    try:
        drives = drive_detector.scan_drives()
        drive_info = None
        for device_path, info in drives.items():
            if info.serial == serial:
                drive_info = info
                break
        
        if not drive_info:
            return jsonify({'success': False, 'error': 'Drive not found'}), 404
        
        progress = test_executor.get_progress(drive_info.device_path)
        
        if progress:
            return jsonify({
                'success': True,
                'status': progress.status.value,
                'progress': progress.progress_percent,
                'current_step': progress.current_step,
                'elapsed_seconds': progress.elapsed_seconds
            })
        else:
            return jsonify({
                'success': True,
                'status': 'none',
                'message': 'No test running'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/drives/<serial>/test', methods=['DELETE'])
def cancel_test(serial: str):
    """Cancel a running test"""
    try:
        drives = drive_detector.scan_drives()
        drive_info = None
        for device_path, info in drives.items():
            if info.serial == serial:
                drive_info = info
                break
        
        if not drive_info:
            return jsonify({'success': False, 'error': 'Drive not found'}), 404
        
        success = test_executor.stop_test(drive_info.device_path)
        
        if success:
            add_log('INFO', f"Test cancelled on drive {serial}")
            return jsonify({'success': True, 'message': 'Test cancelled'})
        else:
            return jsonify({'success': False, 'error': 'No test running'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REST API Endpoints - Bay Map
# ============================================================================

@app.route('/api/bay-map', methods=['GET'])
def get_bay_map():
    """Get visual bay mapping"""
    try:
        drives = drive_detector.scan_drives()
        bay_map = drive_detector.get_bay_map()
        
        # Get backplane config
        bp_config = get_backplane_config()
        total_bays = bp_config.total_bays if bp_config else max(bay_map.keys(), default=0) + 1
        
        # Build bay array
        bays = []
        for bay_num in range(total_bays):
            if bay_num in bay_map:
                drive_info = bay_map[bay_num]
                bays.append({
                    'bay_number': bay_num,
                    'occupied': True,
                    'device_path': drive_info.device_path,
                    'serial': drive_info.serial,
                    'model': drive_info.model,
                    'capacity': drive_info.capacity,
                    'connection_type': drive_info.connection_type,
                    'sata_version': drive_info.sata_version,
                    'test_running': test_executor.is_test_running(drive_info.device_path),
                    'test_progress': None  # Will be filled if test running
                })
            else:
                bays.append({
                    'bay_number': bay_num,
                    'occupied': False
                })
        
        return jsonify({
            'success': True,
            'bays': bays,
            'total_bays': total_bays,
            'occupied_bays': len(bay_map)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bay-map/<int:bay_number>', methods=['GET'])
def get_bay_details(bay_number: int):
    """Get details for a specific bay"""
    try:
        drive_info = drive_detector.get_drive_by_bay(bay_number)
        
        if not drive_info:
            return jsonify({
                'success': True,
                'bay_number': bay_number,
                'occupied': False
            })
        
        return jsonify({
            'success': True,
            'bay_number': bay_number,
            'occupied': True,
            'drive': {
                'device_path': drive_info.device_path,
                'serial': drive_info.serial,
                'model': drive_info.model,
                'capacity': drive_info.capacity,
                'connection_type': drive_info.connection_type,
                'sata_version': drive_info.sata_version
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REST API Endpoints - Session
# ============================================================================

@app.route('/api/session', methods=['GET'])
def get_session():
    """Get current user session"""
    try:
        session = get_active_session()
        if session:
            return jsonify({
                'success': True,
                'session': {
                    'id': session.id,
                    'po_number': session.po_number,
                    'user_name': session.user_name,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat()
                }
            })
        else:
            return jsonify({
                'success': True,
                'session': None
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/session', methods=['POST'])
def create_session():
    """Create or update user session"""
    try:
        data = request.get_json() or {}
        po_number = data.get('po_number')
        user_name = data.get('user_name')
        
        session = get_or_create_active_session(
            po_number=po_number,
            user_name=user_name
        )
        
        socketio.emit('session_updated', {
            'po_number': session.po_number,
            'user_name': session.user_name
        })
        
        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'po_number': session.po_number,
                'user_name': session.user_name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/session/po', methods=['PUT'])
def update_session_po():
    """Update PO number"""
    try:
        data = request.get_json() or {}
        po_number = data.get('po_number')
        
        if not po_number:
            return jsonify({'success': False, 'error': 'PO number required'}), 400
        
        session = update_po_number(po_number)
        
        socketio.emit('session_updated', {
            'po_number': session.po_number
        })
        
        return jsonify({
            'success': True,
            'po_number': session.po_number
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REST API Endpoints - Settings
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all persistent settings"""
    try:
        category = request.args.get('category')
        settings = get_all_settings(category=category)
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/<key>', methods=['GET'])
def get_setting_value(key: str):
    """Get a specific setting"""
    try:
        value = get_setting(key)
        return jsonify({
            'success': True,
            'key': key,
            'value': value
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/<key>', methods=['PUT'])
def update_setting(key: str):
    """Update a setting"""
    try:
        data = request.get_json() or {}
        value = data.get('value')
        category = data.get('category', 'system')
        
        if value is None:
            return jsonify({'success': False, 'error': 'Value required'}), 400
        
        set_setting(key, str(value), category)
        
        socketio.emit('settings_updated', {
            'key': key,
            'value': value
        })
        
        return jsonify({
            'success': True,
            'key': key,
            'value': value
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REST API Endpoints - Configuration
# ============================================================================

@app.route('/api/config/tests', methods=['GET'])
def get_test_config():
    """Get test configuration"""
    try:
        config = get_default_test_config()
        if config:
            return jsonify({
                'success': True,
                'config': {
                    'name': config.name,
                    'enabled_tests': config.enabled_tests,
                    'test_parameters': config.test_parameters,
                    'is_default': config.is_default
                }
            })
        else:
            return jsonify({
                'success': True,
                'config': {
                    'enabled_tests': [],
                    'test_parameters': {}
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/tests', methods=['PUT'])
def update_test_config():
    """Update test configuration"""
    try:
        data = request.get_json() or {}
        name = data.get('name', 'default')
        enabled_tests = data.get('enabled_tests', [])
        test_parameters = data.get('test_parameters', {})
        is_default = data.get('is_default', True)
        
        save_test_config(name, enabled_tests, test_parameters, is_default)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/backplane', methods=['GET'])
def get_backplane_config_endpoint():
    """Get backplane configuration"""
    try:
        config = get_backplane_config()
        if config:
            return jsonify({
                'success': True,
                'config': {
                    'total_bays': config.total_bays,
                    'layout_type': config.layout_type,
                    'layout_config': config.layout_config,
                    'auto_detect': config.auto_detect
                }
            })
        else:
            return jsonify({
                'success': True,
                'config': {
                    'total_bays': 0,
                    'layout_type': 'grid',
                    'layout_config': {},
                    'auto_detect': True
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/backplane', methods=['PUT'])
def update_backplane_config_endpoint():
    """Update backplane configuration"""
    try:
        data = request.get_json() or {}
        total_bays = data.get('total_bays', 0)
        layout_type = data.get('layout_type', 'grid')
        layout_config = data.get('layout_config', {})
        auto_detect = data.get('auto_detect', True)
        
        save_backplane_config(total_bays, layout_type, layout_config, auto_detect)
        
        socketio.emit('backplane_config_updated')
        
        return jsonify({
            'success': True,
            'message': 'Backplane configuration saved'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REST API Endpoints - System
# ============================================================================

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get system status"""
    try:
        drives = drive_detector.scan_drives()
        active_tests = test_executor.get_all_progress()
        
        return jsonify({
            'success': True,
            'status': {
                'drives_detected': len(drives),
                'active_tests': len(active_tests),
                'os_drive': drive_detector.os_drive_name,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Frontend Serving
# ============================================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend - catch-all route"""
    # Don't serve API routes through this
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # Try to serve from React build directory (production)
    if os.path.exists(FRONTEND_BUILD_DIR):
        if path == '' or path == '/':
            return send_file(os.path.join(FRONTEND_BUILD_DIR, 'index.html'))
        
        # Check if it's a static file
        file_path = os.path.join(FRONTEND_BUILD_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        
        # For React Router - serve index.html for all routes
        return send_file(os.path.join(FRONTEND_BUILD_DIR, 'index.html'))
    
    # Development fallback - serve a simple message
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>HDD Tester Platform</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #667eea; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }
            code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>HDD Tester Platform</h1>
            <div class="info">
                <h3>Frontend not built yet</h3>
                <p>To run the frontend in development mode:</p>
                <ol>
                    <li>Open a new terminal</li>
                    <li>Run: <code>cd frontend && npm install && npm start</code></li>
                    <li>Access the app at <code>http://localhost:3000</code></li>
                </ol>
                <p>Or build for production:</p>
                <ol>
                    <li>Run: <code>cd frontend && npm install && npm run build</code></li>
                    <li>Refresh this page</li>
                </ol>
            </div>
            <p><strong>API Status:</strong> Backend is running on port 5005</p>
            <p><strong>API Endpoint:</strong> <a href="/api/system/status">/api/system/status</a></p>
        </div>
    </body>
    </html>
    ''', 200


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to HDD Tester'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')


# ============================================================================
# Application Startup
# ============================================================================

def initialize_app():
    """Initialize application on startup"""
    global scanning_thread
    
    # Start background drive scanning if not already started
    if scanning_thread is None or not scanning_thread.is_alive():
        scanning_thread = threading.Thread(target=start_drive_scanning, daemon=True)
        scanning_thread.start()
        print("Drive scanning thread started")


if __name__ == '__main__':
    print(f"Starting HDD Tester API on {HOST}:{PORT}")
    print(f"Debug mode: {DEBUG}")
    
    # Initialize drive scanning
    initialize_app()
    
    # Run Flask-SocketIO app
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
else:
    # When running with WSGI server (gunicorn, etc.)
    initialize_app()

