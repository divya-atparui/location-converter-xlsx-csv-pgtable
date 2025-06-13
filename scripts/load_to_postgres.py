#!/usr/bin/env python3
"""
Script to load farmer data from CSV into PostgreSQL database.
Usage: python scripts/load_to_postgres.py [--csv-path path/to/csv] [--create-table]
"""

import sys
import argparse
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
    """Main function to load data into PostgreSQL."""
    parser = argparse.ArgumentParser(description='Load farmer data into PostgreSQL')
    parser.add_argument(
        '--csv-path', 
        default='data/processed/bellary_farmers_clean.csv',
        help='Path to the CSV file to load'
    )
    parser.add_argument(
        '--create-table', 
        action='store_true',
        help='Create the table before loading data'
    )
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=1000,
        help='Batch size for loading data'
    )
    parser.add_argument(
        '--config', 
        default='config/database.yaml',
        help='Path to database configuration file'
    )
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    logger.info("="*60)
    logger.info("BELLARY FARMERS DATA LOADER")
    logger.info("="*60)
    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Config file: {args.config}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Create table: {args.create_table}")
    
    try:
        # Initialize database loader
        logger.info("\n1. Initializing database loader...")
        loader = DatabaseLoader(config_path=args.config)
        
        # Connect to database
        logger.info("\n2. Connecting to PostgreSQL database...")
        if not loader.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Create table if requested
        if args.create_table:
            logger.info("\n3. Creating database table...")
            if not loader.create_table():
                logger.error("Failed to create table")
                return False
        else:
            logger.info("\n3. Skipping table creation (use --create-table to create)")
        
        # Load CSV data
        logger.info("\n4. Loading CSV data into database...")
        if not loader.load_csv_data(str(csv_path), batch_size=args.batch_size):
            logger.error("Failed to load CSV data")
            return False
        
        # Get and display statistics
        logger.info("\n5. Getting database statistics...")
        stats = loader.get_table_stats()
        if stats:
            logger.info("\n" + "="*40)
            logger.info("DATABASE STATISTICS")
            logger.info("="*40)
            logger.info(f"Total records: {stats['total_records']:,}")
            
            logger.info("\nRecords by source sheet:")
            for sheet, count in stats['records_by_sheet'].items():
                logger.info(f"  {sheet}: {count:,}")
            
            logger.info("\nRecords by status:")
            for status, count in stats['records_by_status'].items():
                logger.info(f"  {status}: {count:,}")
        
        # Close connection
        loader.close()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 DATA LOADING COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 