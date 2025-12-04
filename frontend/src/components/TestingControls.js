import React, { useState } from 'react';
import './TestingControls.css';

function TestingControls({ testConfig, onTestConfigChange, onStartAllTests, onStopAllTests }) {
  const [expanded, setExpanded] = useState(false);
  const [enabledTests, setEnabledTests] = useState(
    testConfig?.enabled_tests || ['smart', 'badblocks']
  );

  const testTypes = [
    { id: 'hdsentinel', label: 'HDSentinel Health Check', description: 'Actual HDSentinel comprehensive health check' },
    { id: 'smart', label: 'SMART Full Health Check', description: 'Comprehensive SMART attributes and health' },
    { id: 'smart_short', label: 'SMART Short Self-Test', description: 'Quick SMART self-test (~2 minutes)' },
    { id: 'smart_extended', label: 'SMART Extended Self-Test', description: 'Full SMART self-test (~1-2 hours)' },
    { id: 'smart_conveyance', label: 'SMART Conveyance Test', description: 'SMART test for shipping verification' },
    { id: 'badblocks_read', label: 'Badblocks Read Test', description: 'Read-only bad block detection (non-destructive)' },
    { id: 'badblocks_write', label: 'Badblocks Write Test', description: 'Destructive write test - WARNING: Destroys data!' },
    { id: 'performance_seq', label: 'Sequential Performance', description: 'Sequential read/write speed test' },
    { id: 'performance_random', label: 'Random I/O Performance', description: 'Random read/write performance (requires fio)' },
    { id: 'format', label: 'Format/Block Size', description: 'Change block size and format drive' },
    { id: 'health_check', label: 'Comprehensive Health Check', description: 'Full health check (temperature, power-on hours, etc.)' },
  ];

  const handleTestToggle = (testId) => {
    const newEnabled = enabledTests.includes(testId)
      ? enabledTests.filter(id => id !== testId)
      : [...enabledTests, testId];
    
    setEnabledTests(newEnabled);
    
    // Update config (would save to backend)
    if (onTestConfigChange) {
      onTestConfigChange({
        ...testConfig,
        enabled_tests: newEnabled
      });
    }
  };

  return (
    <div className="testing-controls">
      <div className="controls-header" onClick={() => setExpanded(!expanded)}>
        <h2>Testing Controls</h2>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div className="controls-content">
          <div className="test-selection">
            <h3>Enable Tests</h3>
            <div className="test-checkboxes">
              {testTypes.map(test => (
                <label key={test.id} className="test-checkbox">
                  <input
                    type="checkbox"
                    checked={enabledTests.includes(test.id)}
                    onChange={() => handleTestToggle(test.id)}
                  />
                  <div className="test-info">
                    <span className="test-label">{test.label}</span>
                    <span className="test-description">{test.description}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="global-controls">
            <h3>Global Actions</h3>
            <div className="control-buttons">
              <button onClick={onStartAllTests} className="btn btn-primary">
                Start All Tests
              </button>
              <button onClick={onStopAllTests} className="btn btn-danger">
                Stop All Tests
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TestingControls;

