import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Header from './components/Header';
import TestingControls from './components/TestingControls';
import BayMap from './components/BayMap';
import { useWebSocket } from './hooks/useWebSocket';
import { apiService } from './services/api';

function App() {
  const [session, setSession] = useState(null);
  const [drives, setDrives] = useState([]);
  const [bayMap, setBayMap] = useState([]);
  const [testConfig, setTestConfig] = useState(null);
  
  const { connected, socket } = useWebSocket();

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // WebSocket event handlers
  useEffect(() => {
    if (!socket) return;

    socket.on('drives_updated', () => {
      loadDrives();
      loadBayMap();
    });

    socket.on('test_progress', (data) => {
      // Update test progress in bay map
      setBayMap(prev => prev.map(bay => {
        if (bay.bay_number === data.bay_number) {
          return { ...bay, test_progress: data };
        }
        return bay;
      }));
    });

    socket.on('session_updated', (data) => {
      if (data.po_number) {
        setSession(prev => ({ ...prev, po_number: data.po_number }));
      }
    });

    socket.on('settings_updated', () => {
      loadTestConfig();
    });

    return () => {
      socket.off('drives_updated');
      socket.off('test_progress');
      socket.off('session_updated');
      socket.off('settings_updated');
    };
  }, [socket]);

  const loadSession = async () => {
    try {
      const data = await apiService.getSession();
      if (data.success && data.session) {
        setSession(data.session);
      }
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const loadDrives = async () => {
    try {
      const data = await apiService.getDrives();
      if (data.success) {
        setDrives(data.drives);
      }
    } catch (error) {
      console.error('Error loading drives:', error);
    }
  };

  const loadBayMap = async () => {
    try {
      const data = await apiService.getBayMap();
      if (data.success) {
        setBayMap(data.bays);
      }
    } catch (error) {
      console.error('Error loading bay map:', error);
    }
  };

  const loadTestConfig = async () => {
    try {
      const data = await apiService.getTestConfig();
      if (data.success) {
        setTestConfig(data.config);
      }
    } catch (error) {
      console.error('Error loading test config:', error);
    }
  };

  const handlePONumberChange = async (poNumber) => {
    try {
      const data = await apiService.updatePONumber(poNumber);
      if (data.success) {
        setSession(prev => ({ ...prev, po_number: data.po_number }));
      }
    } catch (error) {
      console.error('Error updating PO number:', error);
    }
  };

  const handleStartTest = async (serial, testType) => {
    try {
      const data = await apiService.startTest(serial, testType);
      if (data.success) {
        loadBayMap(); // Refresh bay map to show test status
      }
    } catch (error) {
      console.error('Error starting test:', error);
      alert('Failed to start test: ' + error.message);
    }
  };

  const handleStopTest = async (serial) => {
    try {
      const data = await apiService.cancelTest(serial);
      if (data.success) {
        loadBayMap(); // Refresh bay map
      }
    } catch (error) {
      console.error('Error stopping test:', error);
    }
  };

  return (
    <div className="App">
      <Header 
        session={session}
        onPONumberChange={handlePONumberChange}
        connected={connected}
      />
      
      <div className="main-content">
        <TestingControls
          testConfig={testConfig}
          onTestConfigChange={setTestConfig}
          onStartAllTests={() => {
            drives.forEach(drive => {
              handleStartTest(drive.serial, 'smart');
            });
          }}
          onStopAllTests={() => {
            drives.forEach(drive => {
              handleStopTest(drive.serial);
            });
          }}
        />
        
        <BayMap
          bays={bayMap}
          onStartTest={handleStartTest}
          onStopTest={handleStopTest}
        />
      </div>
    </div>
  );
}

export default App;

