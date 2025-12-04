"""
Database Operations Helper

Convenience functions for common database operations.
"""

from datetime import datetime
from typing import Optional, Dict, List
from database import (
    get_db, Drive, TestSession, TestResult, TestConfiguration,
    BackplaneConfig, UserSession, PersistentSetting, Log
)
from sqlalchemy.orm import Session


# ============================================================================
# Drive Operations
# ============================================================================

def get_or_create_drive(serial: str, **kwargs) -> Drive:
    """Get existing drive or create new one"""
    db = get_db()
    session = db.get_session()
    try:
        drive = session.query(Drive).filter(Drive.serial == serial).first()
        if not drive:
            drive = Drive(serial=serial, **kwargs)
            session.add(drive)
            session.commit()
            session.refresh(drive)
        else:
            # Update last_seen and other fields
            drive.last_seen = datetime.now()
            for key, value in kwargs.items():
                if hasattr(drive, key):
                    setattr(drive, key, value)
            session.commit()
        return drive
    finally:
        session.close()


def get_drive_by_serial(serial: str) -> Optional[Drive]:
    """Get drive by serial number"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(Drive).filter(Drive.serial == serial).first()
    finally:
        session.close()


def get_drive_by_bay(bay_number: int) -> Optional[Drive]:
    """Get drive by bay number"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(Drive).filter(Drive.bay_location == bay_number).first()
    finally:
        session.close()


# ============================================================================
# User Session Operations
# ============================================================================

def get_or_create_active_session(po_number: Optional[str] = None, 
                                 user_name: Optional[str] = None) -> UserSession:
    """Get active user session or create new one"""
    db = get_db()
    session = db.get_session()
    try:
        # Try to find active session
        active_session = session.query(UserSession).filter(
            UserSession.is_active == True
        ).first()
        
        if active_session:
            # Update PO number if provided
            if po_number:
                active_session.po_number = po_number
            if user_name:
                active_session.user_name = user_name
            active_session.last_activity = datetime.now()
            session.commit()
            session.refresh(active_session)
            return active_session
        else:
            # Create new session
            new_session = UserSession(
                po_number=po_number,
                user_name=user_name,
                is_active=True
            )
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            return new_session
    finally:
        session.close()


def get_active_session() -> Optional[UserSession]:
    """Get current active user session"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(UserSession).filter(
            UserSession.is_active == True
        ).first()
    finally:
        session.close()


def update_po_number(po_number: str) -> UserSession:
    """Update PO number in active session"""
    session_obj = get_or_create_active_session(po_number=po_number)
    return session_obj


# ============================================================================
# Test Session Operations
# ============================================================================

def create_test_session(drive_serial: str, po_number: Optional[str] = None,
                       user_session_id: Optional[int] = None) -> TestSession:
    """Create a new test session"""
    db = get_db()
    session = db.get_session()
    try:
        # Get or create user session if PO number provided
        if po_number and not user_session_id:
            user_session = get_or_create_active_session(po_number=po_number)
            user_session_id = user_session.id
        
        test_session = TestSession(
            drive_serial=drive_serial,
            po_number=po_number,
            user_session_id=user_session_id,
            status='running'
        )
        session.add(test_session)
        session.commit()
        session.refresh(test_session)
        return test_session
    finally:
        session.close()


def update_test_session(session_id: int, status: str, 
                       end_time: Optional[datetime] = None):
    """Update test session status"""
    db = get_db()
    session = db.get_session()
    try:
        test_session = session.query(TestSession).filter(
            TestSession.id == session_id
        ).first()
        if test_session:
            test_session.status = status
            if end_time:
                test_session.end_time = end_time
            session.commit()
    finally:
        session.close()


def add_test_result(session_id: int, test_type: str, passed: bool,
                   result_data: Optional[Dict] = None,
                   error_message: Optional[str] = None) -> TestResult:
    """Add a test result"""
    db = get_db()
    session = db.get_session()
    try:
        test_result = TestResult(
            session_id=session_id,
            test_type=test_type,
            passed=passed,
            result_data=result_data,
            error_message=error_message
        )
        session.add(test_result)
        session.commit()
        session.refresh(test_result)
        return test_result
    finally:
        session.close()


# ============================================================================
# Settings Operations
# ============================================================================

def get_setting(setting_key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a persistent setting"""
    db = get_db()
    session = db.get_session()
    try:
        setting = session.query(PersistentSetting).filter(
            PersistentSetting.setting_key == setting_key
        ).first()
        return setting.setting_value if setting else default
    finally:
        session.close()


def set_setting(setting_key: str, setting_value: str, category: str = 'system'):
    """Set a persistent setting"""
    db = get_db()
    session = db.get_session()
    try:
        setting = session.query(PersistentSetting).filter(
            PersistentSetting.setting_key == setting_key
        ).first()
        
        if setting:
            setting.setting_value = setting_value
            setting.category = category
            setting.updated_at = datetime.now()
        else:
            setting = PersistentSetting(
                setting_key=setting_key,
                setting_value=setting_value,
                category=category
            )
            session.add(setting)
        
        session.commit()
    finally:
        session.close()


def get_all_settings(category: Optional[str] = None) -> Dict[str, str]:
    """Get all settings, optionally filtered by category"""
    db = get_db()
    session = db.get_session()
    try:
        query = session.query(PersistentSetting)
        if category:
            query = query.filter(PersistentSetting.category == category)
        
        settings = {}
        for setting in query.all():
            settings[setting.setting_key] = setting.setting_value
        
        return settings
    finally:
        session.close()


# ============================================================================
# Test Configuration Operations
# ============================================================================

def get_default_test_config() -> Optional[TestConfiguration]:
    """Get default test configuration"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(TestConfiguration).filter(
            TestConfiguration.is_default == True
        ).first()
    finally:
        session.close()


def get_test_config(name: str) -> Optional[TestConfiguration]:
    """Get test configuration by name"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(TestConfiguration).filter(
            TestConfiguration.name == name
        ).first()
    finally:
        session.close()


def save_test_config(name: str, enabled_tests: List[str],
                    test_parameters: Dict, is_default: bool = False):
    """Save test configuration"""
    db = get_db()
    session = db.get_session()
    try:
        # If setting as default, unset other defaults
        if is_default:
            session.query(TestConfiguration).update({TestConfiguration.is_default: False})
        
        config = session.query(TestConfiguration).filter(
            TestConfiguration.name == name
        ).first()
        
        if config:
            config.enabled_tests = enabled_tests
            config.test_parameters = test_parameters
            config.is_default = is_default
            config.updated_at = datetime.now()
        else:
            config = TestConfiguration(
                name=name,
                enabled_tests=enabled_tests,
                test_parameters=test_parameters,
                is_default=is_default
            )
            session.add(config)
        
        session.commit()
    finally:
        session.close()


# ============================================================================
# Backplane Configuration Operations
# ============================================================================

def get_backplane_config() -> Optional[BackplaneConfig]:
    """Get backplane configuration"""
    db = get_db()
    session = db.get_session()
    try:
        return session.query(BackplaneConfig).first()
    finally:
        session.close()


def save_backplane_config(total_bays: int, layout_type: str = 'grid',
                         layout_config: Optional[Dict] = None,
                         auto_detect: bool = True):
    """Save backplane configuration"""
    db = get_db()
    session = db.get_session()
    try:
        config = session.query(BackplaneConfig).first()
        
        if config:
            config.total_bays = total_bays
            config.layout_type = layout_type
            config.layout_config = layout_config or {}
            config.auto_detect = auto_detect
            config.updated_at = datetime.now()
        else:
            config = BackplaneConfig(
                total_bays=total_bays,
                layout_type=layout_type,
                layout_config=layout_config or {},
                auto_detect=auto_detect
            )
            session.add(config)
        
        session.commit()
    finally:
        session.close()


# ============================================================================
# Logging Operations
# ============================================================================

def add_log(level: str, message: str, session_id: Optional[int] = None):
    """Add a log entry"""
    db = get_db()
    session = db.get_session()
    try:
        log_entry = Log(
            session_id=session_id,
            level=level,
            message=message
        )
        session.add(log_entry)
        session.commit()
    finally:
        session.close()

