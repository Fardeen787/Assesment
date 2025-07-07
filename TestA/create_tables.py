# create_tables.py
"""
Create all database tables
"""
from database import engine, Base
from models import User, Patient, MedicalRecord, AccessPermission, AuditLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_tables():
    """Create all tables in the database"""
    try:
        # Import all models to ensure they're registered with Base
        logger.info("Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    if create_all_tables():
        print("\n✅ Database is ready!")
        print("You can now run the API and register users.")
    else:
        print("\n❌ Failed to create database tables.")
        print("Check the error messages above.")