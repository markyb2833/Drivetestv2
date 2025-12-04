import React, { useState } from 'react';
import './Header.css';

function Header({ session, onPONumberChange, connected }) {
  const [poNumber, setPONumber] = useState(session?.po_number || '');
  const [isEditing, setIsEditing] = useState(false);

  React.useEffect(() => {
    if (session?.po_number) {
      setPONumber(session.po_number);
    }
  }, [session]);

  const handleSave = () => {
    if (poNumber.trim()) {
      onPONumberChange(poNumber.trim());
    }
    setIsEditing(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      setPONumber(session?.po_number || '');
      setIsEditing(false);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1>HDD Tester Platform</h1>
          <div className="connection-status">
            <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
        
        <div className="header-right">
          <div className="po-number-section">
            <label>PO Number:</label>
            {isEditing ? (
              <div className="po-input-group">
                <input
                  type="text"
                  value={poNumber}
                  onChange={(e) => setPONumber(e.target.value)}
                  onBlur={handleSave}
                  onKeyDown={handleKeyPress}
                  className="po-input"
                  autoFocus
                  placeholder="Enter PO number"
                />
                <button onClick={handleSave} className="btn-save">Save</button>
              </div>
            ) : (
              <div className="po-display-group">
                <span className="po-value">{poNumber || 'Not set'}</span>
                <button onClick={() => setIsEditing(true)} className="btn-edit">Edit</button>
              </div>
            )}
          </div>
          
          {session?.user_name && (
            <div className="user-name">
              User: {session.user_name}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;

