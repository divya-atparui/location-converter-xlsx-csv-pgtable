# Location Converter: Excel to CSV to PostgreSQL Pipeline

A comprehensive data pipeline for processing farmer location data from Excel files, cleaning and analyzing the data, converting to CSV format, and loading into PostgreSQL database.

## 🎯 Project Overview

This project processes farmer data from the Bellary region across 5 Excel sheets, cleans the data by removing status-only rows, and loads it into a PostgreSQL database for analysis.

### Key Features
- ✅ **Multi-sheet Excel processing** (5 sheets: Kampli, Kampli 2, Siruguppa, Bellary 1, Bellary 2)
- ✅ **Data cleaning and validation** (removes ~50% of meaningless rows)
- ✅ **CSV export** with standardized format
- ✅ **PostgreSQL integration** with optimized schema and indexes
- ✅ **Comprehensive data analysis** using Jupyter notebooks

### Data Statistics
- **Total Records**: 2,245 clean farmer records
- **Original Data**: 4,492 rows (including status-only rows)
- **Data Retention**: ~50% after cleaning
- **File Size**: 379.75 KB (clean CSV)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- `uv` package manager

### 1. Setup Environment
```bash
# Clone and navigate to project
cd location-converter-xlsx-csv-pgtable

# Install dependencies
make install

# Or manually:
uv add jupyterlab pandas numpy openpyxl psycopg2-binary sqlalchemy python-dotenv pyyaml
```

### 2. Configure Database
```bash
# Copy environment template
cp env.example .env

# Edit .env with your PostgreSQL credentials
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=bellary_db
# POSTGRES_USER=your_username
# POSTGRES_PASSWORD=your_password
```

### 3. Run the Pipeline
```bash
# Option A: Run complete pipeline
make all

# Option B: Step by step
make notebook          # Start Jupyter for data exploration
make setup-db          # Create database table
make load              # Load CSV data to PostgreSQL
```

## 📊 Data Schema

### Source Data (Excel)
| Column | Type | Description |
|--------|------|-------------|
| S.no | Integer | Serial number |
| Status | String | Record status (Old/New/verified/pending) |
| Farmer Code | String | Unique farmer identifier |
| Farmer Name | String | Farmer's full name |
| Govt id num | String | Government ID number |
| Primary Contact | String | Phone number |
| Farmer Created Date | DateTime | Registration date |
| Plot Created Date | DateTime | Plot registration date |
| Sync Date | DateTime | Last sync timestamp |
| Updation Date | DateTime | Last update timestamp |
| Area | Float | Plot area measurement |
| GPS Area | Float | GPS-calculated area |
| Village | String | Village name |

### PostgreSQL Table: `bellary_farmers`
```sql
CREATE TABLE bellary_farmers (
    id SERIAL PRIMARY KEY,
    serial_number INTEGER,
    status VARCHAR(50),
    farmer_code VARCHAR(100) UNIQUE NOT NULL,
    farmer_name VARCHAR(255) NOT NULL,
    govt_id_number VARCHAR(50) UNIQUE,
    primary_contact VARCHAR(20),
    farmer_created_date TIMESTAMP,
    plot_created_date TIMESTAMP,
    sync_date TIMESTAMP,
    updation_date TIMESTAMP,
    area DECIMAL(10,4),
    gps_area DECIMAL(10,4),
    village VARCHAR(100) NOT NULL,
    source_sheet VARCHAR(50),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Available Commands

```bash
make help           # Show all available commands
make setup          # Set up project environment
make install        # Install dependencies
make notebook       # Start Jupyter Lab
make explore        # Run data exploration
make convert        # Convert Excel to CSV
make setup-db       # Set up PostgreSQL database
make load           # Load data to PostgreSQL
make test           # Run tests
make lint           # Run code linting
make format         # Format code
make clean          # Clean temporary files
make all            # Run complete pipeline
```

## 📁 Project Structure

```
location-converter-xlsx-csv-pgtable/
├── config/
│   ├── database.yaml           # Database configuration
│   └── data_mapping.yaml       # Column mapping rules
├── data/
│   ├── raw/                    # Original Excel files
│   ├── processed/              # Cleaned CSV files
│   └── reports/                # Data analysis reports
├── notebooks/
│   └── 01_data_exploration.ipynb  # Data analysis notebook
├── scripts/
│   ├── setup_database.py       # Database setup script
│   └── load_to_postgres.py     # Data loading script
├── src/
│   ├── __init__.py
│   └── db_loader.py            # Database operations module
├── tests/                      # Test files
├── .env                        # Environment variables
├── Makefile                    # Build automation
├── PRD.md                      # Product Requirements Document
└── README.md                   # This file
```

## 🔍 Data Analysis Insights

### Key Findings from Data Exploration:
1. **Perfect Column Consistency**: All 5 sheets have identical 13-column structure
2. **Data Pattern**: Alternating rows with actual farmer data and status-only rows
3. **Geographic Distribution**: Data covers multiple villages in Bellary region
4. **Status Categories**: Old, New, verified, pending
5. **Data Quality**: ~50% meaningful records after cleaning

### Records by Sheet:
- **Kampli**: 571 farmers
- **Kampli 2**: 669 farmers  
- **Siruguppa**: 339 farmers
- **Bellary 1**: 417 farmers
- **Bellary 2**: 248 farmers

## 🗄️ Database Operations

### Setup Database
```bash
# Create table and indexes
python scripts/setup_database.py
```

### Load Data
```bash
# Load CSV with table creation
python scripts/load_to_postgres.py --create-table

# Load specific CSV file
python scripts/load_to_postgres.py --csv-path data/processed/custom_file.csv

# Load with custom batch size
python scripts/load_to_postgres.py --batch-size 500
```

### Query Examples
```sql
-- Total farmers by village
SELECT village, COUNT(*) as farmer_count 
FROM bellary_farmers 
GROUP BY village 
ORDER BY farmer_count DESC;

-- Farmers by status
SELECT status, COUNT(*) as count 
FROM bellary_farmers 
GROUP BY status;

-- Average plot area by village
SELECT village, AVG(area) as avg_area, AVG(gps_area) as avg_gps_area
FROM bellary_farmers 
WHERE area IS NOT NULL 
GROUP BY village;
```

## 🧪 Development

### Running Tests
```bash
make test
# or
uv run pytest tests/ -v
```

### Code Quality
```bash
make lint           # Check code style
make format         # Format code with black
```

### Adding New Features
1. Create feature branch
2. Add code in appropriate module (`src/`)
3. Add tests in `tests/`
4. Update documentation
5. Run quality checks

## 📈 Performance

- **Processing Time**: ~2-3 minutes for complete pipeline
- **Memory Usage**: <500MB for 2,245 records
- **Database Loading**: ~1,000 records/second
- **File Sizes**: 
  - Original Excel: 554KB
  - Clean CSV: 379.75KB
  - Database: ~2MB with indexes

## 🔧 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify credentials in .env file
cat .env
```

**Import Errors**
```bash
# Ensure all dependencies are installed
uv pip list | grep -E "(pandas|psycopg2|sqlalchemy)"

# Reinstall if needed
make install
```

**CSV File Not Found**
```bash
# Check if CSV was generated
ls -la data/processed/

# Re-run data exploration if needed
make explore
```

## 📝 License

This project is licensed under the MIT License.

## 👥 Contributors

- **Divyasimha HR Jois** - *Initial work* - [divineleo20@gmail.com](mailto:divineleo20@gmail.com)

## 🙏 Acknowledgments

- Bellary farmers data collection team
- PostgreSQL community for excellent documentation
- Pandas and SQLAlchemy developers
