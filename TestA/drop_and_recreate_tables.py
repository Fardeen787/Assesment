# drop_and_recreate_tables.py
from database import engine, Base
from models import User, Patient, MedicalRecord, AccessPermission, AuditLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_tables():
    """Drop all tables and recreate them"""
    try:
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating all tables with fixed relationships...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All tables recreated successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error recreating tables: {e}")
        return False

if __name__ == "__main__":
    if recreate_tables():
        print("\n✅ Database has been reset and is ready!")
        print("You can now run the API and register users.")
    else:
        print("\n❌ Failed to recreate database tables.")
