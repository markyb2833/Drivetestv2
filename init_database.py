#!/usr/bin/env python3
"""
Database Initialization Script

Creates all database tables if they don't exist.
Run this once before starting the application.
"""

import sys
from database import init_database, get_db

def main():
    """Initialize database"""
    print("Initializing MySQL database...")
    print("Connection: mysql://newinv:***@192.168.0.197/compudrive")
    
    try:
        # Initialize database (creates tables)
        init_database()
        
        # Test connection
        db = get_db()
        session = db.get_session()
        try:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            print("\n✓ Database connection successful!")
            print("✓ Tables created/verified successfully!")
            return 0
        except Exception as e:
            print(f"\n✗ Database connection test failed: {e}")
            print("\nPlease check:")
            print("  1. MySQL server is running at 192.168.0.197")
            print("  2. Database 'compudrive' exists")
            print("  3. User 'newinv' has proper permissions")
            print("  4. Network connectivity to database server")
            return 1
        finally:
            session.close()
            
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

