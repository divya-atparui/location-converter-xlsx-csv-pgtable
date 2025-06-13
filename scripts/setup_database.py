#!/usr/bin/env python3
"""
Script to set up PostgreSQL database and create the bellary_farmers table.
Usage: python scripts/setup_database.py
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db_loader import DatabaseLoader
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to set up the database."""
    logger.info("="*60)
    logger.info("BELLARY FARMERS DATABASE SETUP")
    logger.info("="*60)
    
    try:
        # Initialize database loader
        logger.info("1. Initializing database loader...")
        loader = DatabaseLoader()
        
        # Connect to database
        logger.info("2. Connecting to PostgreSQL database...")
        if not loader.connect():
            logger.error("Failed to connect to database")
            logger.error("Please check your database configuration in:")
            logger.error("  - Environment variables (.env file)")
            logger.error("  - config/database.yaml")
            return False
        
        # Create table
        logger.info("3. Creating bellary_farmers table...")
        if not loader.create_table():
            logger.error("Failed to create table")
            return False
        
        # Display table information
        logger.info("4. Verifying table creation...")
        try:
            from sqlalchemy import text
            with loader.engine.connect() as conn:
                # Get table info
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'bellary_farmers'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                if columns:
                    logger.info("\n" + "="*50)
                    logger.info("TABLE STRUCTURE: bellary_farmers")
                    logger.info("="*50)
                    logger.info(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
                    logger.info("-" * 70)
                    
                    for col in columns:
                        default = col[3] if col[3] else ""
                        logger.info(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {default}")
                
                # Get indexes
                result = conn.execute(text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'bellary_farmers'
                """))
                
                indexes = result.fetchall()
                if indexes:
                    logger.info(f"\nINDEXES:")
                    for idx in indexes:
                        logger.info(f"  {idx[0]}")
                
        except Exception as e:
            logger.warning(f"Could not retrieve table information: {e}")
        
        # Close connection
        loader.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("Next steps:")
        logger.info("1. Configure your database connection in .env file")
        logger.info("2. Run: python scripts/load_to_postgres.py --create-table")
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 