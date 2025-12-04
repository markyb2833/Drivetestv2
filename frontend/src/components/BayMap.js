import React from 'react';
import './BayMap.css';

function BayMap({ bays, onStartTest, onStopTest }) {
  if (!bays || bays.length === 0) {
    return (
      <div className="bay-map-container">
        <div className="no-bays">No bays detected. Waiting for drives...</div>
      </div>
    );
  }

  // Determine grid layout (try to make it roughly square)
  const totalBays = bays.length;
  const cols = Math.ceil(Math.sqrt(totalBays));
  const rows = Math.ceil(totalBays / cols);

  const getBayStatusColor = (bay) => {
    if (!bay.occupied) return 'empty';
    if (bay.test_running) return 'testing';
    // Would check test results here for pass/fail
    return 'present';
  };

  const getBayStatusText = (bay) => {
    if (!bay.occupied) return 'Empty';
    if (bay.test_running) {
      const progress = bay.test_progress?.progress_percent || 0;
      return `Testing ${Math.round(progress)}%`;
    }
    return 'Ready';
  };

  return (
    <div className="bay-map-container">
      <h2 className="bay-map-title">Drive Bay Map</h2>
      <div 
        className="bay-grid"
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`
        }}
      >
        {bays.map((bay) => (
          <div
            key={bay.bay_number}
            className={`bay-box bay-${getBayStatusColor(bay)}`}
          >
            <div className="bay-number">Bay {bay.bay_number}</div>
            
            {bay.occupied ? (
              <>
                <div className="bay-status">{getBayStatusText(bay)}</div>
                
                {bay.test_progress && (
                  <div className="bay-progress">
                    <div 
                      className="progress-bar"
                      style={{ width: `${bay.test_progress.progress_percent}%` }}
                    ></div>
                  </div>
                )}
                
                <div className="bay-info">
                  <div className="bay-info-item">
                    <span className="label">Model:</span>
                    <span className="value">{bay.model || 'Unknown'}</span>
                  </div>
                  <div className="bay-info-item">
                    <span className="label">Serial:</span>
                    <span className="value serial">{bay.serial || 'Unknown'}</span>
                  </div>
                  <div className="bay-info-item">
                    <span className="label">Capacity:</span>
                    <span className="value">{bay.capacity || 'Unknown'}</span>
                  </div>
                  <div className="bay-info-item">
                    <span className="label">Connection:</span>
                    <span className="value">
                      {bay.connection_type || 'Unknown'}
                      {bay.sata_version && ` ${bay.sata_version}`}
                    </span>
                  </div>
                </div>
                
                <div className="bay-actions">
                  {bay.test_running ? (
                    <button
                      onClick={() => onStopTest(bay.serial)}
                      className="btn-bay btn-stop"
                    >
                      Stop Test
                    </button>
                  ) : (
                    <button
                      onClick={() => onStartTest(bay.serial, 'smart')}
                      className="btn-bay btn-start"
                    >
                      Start Test
                    </button>
                  )}
                </div>
              </>
            ) : (
              <div className="bay-empty">Empty</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default BayMap;

