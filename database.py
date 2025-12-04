"""
Database Module

MySQL database connection and schema management.
All settings and PO numbers persist across reboots.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from typing import Optional
from config import DATABASE_URL

Base = declarative_base()


class Drive(Base):
    """Drive information table"""
    __tablename__ = 'drives'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial = Column(String(100), unique=True, nullable=False, index=True)
    model = Column(String(200))
    capacity = Column(String(50))
    connection_type = Column(String(20))  # 'SATA' or 'SAS'
    sata_version = Column(String(20))  # 'SATA1', 'SATA2', 'SATA3'
    bay_location = Column(Integer, index=True)
    device_path = Column(String(100))  # e.g., '/dev/sdb'
    stable_path = Column(String(200))  # e.g., 'pci-0000:01:00.0-scsi-0:0:5:0'
    scsi_host = Column(Integer)
    scsi_channel = Column(Integer)
    scsi_target = Column(Integer)
    scsi_lun = Column(Integer)
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    test_sessions = relationship("TestSession", back_populates="drive")


class TestSession(Base):
    """Test session tracking"""
    __tablename__ = 'test_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drive_serial = Column(String(100), ForeignKey('drives.serial'), nullable=False, index=True)
    po_number = Column(String(100), index=True)
    user_session_id = Column(Integer, ForeignKey('user_sessions.id'), nullable=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default='running')  # 'running', 'completed', 'failed', 'cancelled'
    
    # Relationships
    drive = relationship("Drive", back_populates="test_sessions")
    user_session = relationship("UserSession", back_populates="test_sessions")
    test_results = relationship("TestResult", back_populates="session")


class TestResult(Base):
    """Individual test results"""
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # 'smart', 'badblocks', 'format', etc.
    result_data = Column(JSON)  # Store detailed results as JSON
    timestamp = Column(DateTime, default=datetime.now)
    passed = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("TestSession", back_populates="test_results")


class TestConfiguration(Base):
    """Test configuration presets"""
    __tablename__ = 'test_configurations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    enabled_tests = Column(JSON)  # List of enabled test types
    test_parameters = Column(JSON)  # Test-specific parameters
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class BackplaneConfig(Base):
    """Backplane configuration"""
    __tablename__ = 'backplane_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_bays = Column(Integer, nullable=False)
    layout_type = Column(String(50), default='grid')  # 'grid', 'list', 'custom'
    layout_config = Column(JSON)  # Layout-specific configuration
    auto_detect = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserSession(Base):
    """User session tracking (PO numbers, etc.)"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(100), index=True)
    user_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_activity = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    test_sessions = relationship("TestSession", back_populates="user_session")


class PersistentSetting(Base):
    """Persistent settings storage"""
    __tablename__ = 'persistent_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text)  # Can store JSON as text or simple values
    category = Column(String(50))  # 'ui', 'test', 'system', etc.
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Log(Base):
    """System logs"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('test_sessions.id'), nullable=True)
    level = Column(String(20), nullable=False)  # 'INFO', 'WARNING', 'ERROR', 'DEBUG'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)


class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        print("Database tables created successfully")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()


# Global database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_database():
    """Initialize database (create tables)"""
    db = get_db()
    db.create_tables()


if __name__ == '__main__':
    # Initialize database
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    
    # Test connection
    db = get_db()
    session = db.get_session()
    try:
        # Test query
        result = session.execute("SELECT 1")
        print("Database connection test: SUCCESS")
    except Exception as e:
        print(f"Database connection test: FAILED - {e}")
    finally:
        session.close()

