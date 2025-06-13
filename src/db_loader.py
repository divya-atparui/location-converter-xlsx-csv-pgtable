"""
Database loader module for PostgreSQL operations.
Handles connection, table creation, and data loading.
"""

import os
import pandas as pd
import psycopg2
import sqlalchemy
from sqlalchemy import create_engine, text
from pathlib import Path
import yaml
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Handles PostgreSQL database operations for farmer data."""
    
    def __init__(self, config_path: str = "config/database.yaml"):
        """Initialize database loader with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.engine = None
        self.connection = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
    
    def _get_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables or config."""
        # Try environment variables first
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        
        # Fall back to individual environment variables
        host = os.getenv('POSTGRES_HOST', self.config['database']['host'])
        port = os.getenv('POSTGRES_PORT', self.config['database']['port'])
        database = os.getenv('POSTGRES_DB', self.config['database']['database'])
        username = os.getenv('POSTGRES_USER', self.config['database']['username'])
        password = os.getenv('POSTGRES_PASSWORD', self.config['database']['password'])
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def connect(self) -> bool:
        """Establish connection to PostgreSQL database."""
        try:
            connection_string = self._get_connection_string()
            self.engine = create_engine(connection_string)
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def create_table(self) -> bool:
        """Create the bellary_farmers table if it doesn't exist."""
        try:
            table_schema = self.config['table_schema']
            table_name = table_schema['table_name']
            
            # Build CREATE TABLE SQL
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            
            columns = []
            for col_name, col_config in table_schema['columns'].items():
                col_def = f"    {col_name} {col_config['type']}"
                
                if col_config.get('primary_key'):
                    col_def += " PRIMARY KEY"
                elif col_config.get('unique'):
                    col_def += " UNIQUE"
                
                if not col_config.get('nullable', True):
                    col_def += " NOT NULL"
                
                if col_config.get('default'):
                    col_def += f" DEFAULT {col_config['default']}"
                
                columns.append(col_def)
            
            create_sql += ",\n".join(columns) + "\n);"
            
            # Execute table creation
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
                logger.info(f"Table '{table_name}' created successfully")
            
            # Create indexes
            self._create_indexes()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            return False
    
    def _create_indexes(self) -> None:
        """Create indexes for performance optimization."""
        try:
            table_name = self.config['table_schema']['table_name']
            indexes = self.config.get('indexes', [])
            
            with self.engine.connect() as conn:
                for index in indexes:
                    index_name = index['name']
                    columns = index['columns']
                    unique = "UNIQUE " if index.get('unique', False) else ""
                    
                    # Check if index already exists
                    check_sql = text("""
                        SELECT 1 FROM pg_indexes 
                        WHERE tablename = :table_name AND indexname = :index_name
                    """)
                    
                    result = conn.execute(check_sql, {
                        'table_name': table_name,
                        'index_name': index_name
                    })
                    
                    if not result.fetchone():
                        index_sql = f"""
                            CREATE {unique}INDEX {index_name} 
                            ON {table_name} ({', '.join(columns)})
                        """
                        conn.execute(text(index_sql))
                        logger.info(f"Index '{index_name}' created")
                    else:
                        logger.info(f"Index '{index_name}' already exists")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def load_csv_data(self, csv_path: str, batch_size: int = 1000) -> bool:
        """Load data from CSV file into the database table."""
        try:
            csv_file = Path(csv_path)
            if not csv_file.exists():
                logger.error(f"CSV file not found: {csv_path}")
                return False
            
            # Read CSV file
            logger.info(f"Reading CSV file: {csv_path}")
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} records from CSV")
            
            # Prepare data for database
            df_prepared = self._prepare_data_for_db(df)
            
            # Get table name
            table_name = self.config['table_schema']['table_name']
            
            # Load data in batches
            total_records = len(df_prepared)
            logger.info(f"Loading {total_records} records into '{table_name}' table...")
            
            # Use pandas to_sql for efficient loading
            df_prepared.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='append',  # Append to existing table
                index=False,
                chunksize=batch_size,
                method='multi'  # Use multi-row INSERT for better performance
            )
            
            logger.info(f"Successfully loaded {total_records} records")
            
            # Verify the load
            self._verify_data_load(table_name, total_records)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            return False
    
    def _prepare_data_for_db(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for database insertion."""
        df_prep = df.copy()
        
        # Map CSV columns to database columns
        column_mapping = {
            'S.no': 'serial_number',
            'Status': 'status',
            'Farmer Code': 'farmer_code',
            'Farmer Name': 'farmer_name',
            'Govt id num': 'govt_id_number',
            'Primary Contact': 'primary_contact',
            'Farmer Created Date': 'farmer_created_date',
            'Plot Created Date': 'plot_created_date',
            'Sync Date': 'sync_date',
            'Updation Date': 'updation_date',
            'Area': 'area',
            'GPS Area': 'gps_area',
            'Village': 'village',
            'source_sheet': 'source_sheet'
        }
        
        # Rename columns
        df_prep = df_prep.rename(columns=column_mapping)
        
        # Convert data types
        # Handle dates
        date_columns = ['farmer_created_date', 'plot_created_date', 'sync_date', 'updation_date']
        for col in date_columns:
            if col in df_prep.columns:
                df_prep[col] = pd.to_datetime(df_prep[col], errors='coerce')
        
        # Handle numeric columns
        numeric_columns = ['serial_number', 'area', 'gps_area']
        for col in numeric_columns:
            if col in df_prep.columns:
                df_prep[col] = pd.to_numeric(df_prep[col], errors='coerce')
        
        # Handle string columns - clean and truncate if necessary
        string_columns = ['status', 'farmer_code', 'farmer_name', 'govt_id_number', 
                         'primary_contact', 'village', 'source_sheet']
        for col in string_columns:
            if col in df_prep.columns:
                df_prep[col] = df_prep[col].astype(str).str.strip()
                # Replace 'nan' string with None
                df_prep[col] = df_prep[col].replace('nan', None)
        
        # Add metadata columns
        df_prep['imported_at'] = pd.Timestamp.now()
        df_prep['created_at'] = pd.Timestamp.now()
        df_prep['updated_at'] = pd.Timestamp.now()
        
        return df_prep
    
    def _verify_data_load(self, table_name: str, expected_count: int) -> None:
        """Verify that data was loaded correctly."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                actual_count = result.fetchone()[0]
                
                logger.info(f"Verification: {actual_count} records in database")
                
                if actual_count >= expected_count:
                    logger.info("✅ Data verification successful")
                else:
                    logger.warning(f"⚠️ Expected {expected_count}, found {actual_count}")
                    
        except Exception as e:
            logger.error(f"Failed to verify data load: {e}")
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded data."""
        try:
            table_name = self.config['table_schema']['table_name']
            
            with self.engine.connect() as conn:
                # Total count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_count = count_result.fetchone()[0]
                
                # Count by source sheet
                sheet_result = conn.execute(text(f"""
                    SELECT source_sheet, COUNT(*) as count 
                    FROM {table_name} 
                    GROUP BY source_sheet 
                    ORDER BY count DESC
                """))
                sheet_counts = dict(sheet_result.fetchall())
                
                # Count by status
                status_result = conn.execute(text(f"""
                    SELECT status, COUNT(*) as count 
                    FROM {table_name} 
                    GROUP BY status 
                    ORDER BY count DESC
                """))
                status_counts = dict(status_result.fetchall())
                
                return {
                    'total_records': total_count,
                    'records_by_sheet': sheet_counts,
                    'records_by_status': status_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}
    
    def close(self) -> None:
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


def main():
    """Main function for testing the database loader."""
    # Initialize loader
    loader = DatabaseLoader()
    
    # Connect to database
    if not loader.connect():
        logger.error("Failed to connect to database")
        return False
    
    # Create table
    if not loader.create_table():
        logger.error("Failed to create table")
        return False
    
    # Load CSV data
    csv_path = "data/processed/bellary_farmers_clean.csv"
    if not loader.load_csv_data(csv_path):
        logger.error("Failed to load CSV data")
        return False
    
    # Get statistics
    stats = loader.get_table_stats()
    if stats:
        logger.info("Database Statistics:")
        logger.info(f"  Total records: {stats['total_records']}")
        logger.info(f"  Records by sheet: {stats['records_by_sheet']}")
        logger.info(f"  Records by status: {stats['records_by_status']}")
    
    # Close connection
    loader.close()
    
    return True


if __name__ == "__main__":
    main() 