# Makefile for Location Converter Project
.PHONY: help setup install clean test lint format notebook explore convert load all

# Default target
help:
	@echo "Available commands:"
	@echo "  setup     - Set up the project environment"
	@echo "  install   - Install dependencies"
	@echo "  clean     - Clean up temporary files"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linting"
	@echo "  format    - Format code"
	@echo "  notebook  - Start Jupyter Lab"
	@echo "  explore   - Run data exploration"
	@echo "  convert   - Convert Excel to CSV"
	@echo "  setup-db  - Set up PostgreSQL database"
	@echo "  load      - Load data to PostgreSQL"
	@echo "  all       - Run complete pipeline"

# Environment setup
setup:
	@echo "Setting up project environment..."
	uv venv .venv
	@echo "Environment created. Activate with: source .venv/bin/activate"

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv add jupyterlab pandas numpy openpyxl psycopg2-binary sqlalchemy python-dotenv
	uv add --dev pytest black flake8 pre-commit
	@echo "Dependencies installed successfully"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -name "*.log" -delete
	rm -rf .coverage htmlcov/
	@echo "Cleanup completed"

# Run tests
test:
	@echo "Running tests..."
	uv run pytest tests/ -v

# Run linting
lint:
	@echo "Running linting..."
	uv run flake8 src/ scripts/ tests/
	@echo "Linting completed"

# Format code
format:
	@echo "Formatting code..."
	uv run black src/ scripts/ tests/
	@echo "Code formatting completed"

# Start Jupyter Lab
notebook:
	@echo "Starting Jupyter Lab..."
	uv run jupyter lab

# Run data exploration
explore:
	@echo "Running data exploration..."
	uv run jupyter nbconvert --to notebook --execute notebooks/01_data_exploration.ipynb

# Convert Excel to CSV
convert:
	@echo "Converting Excel to CSV..."
	uv run python scripts/run_pipeline.py --step convert

# Set up database
setup-db:
	@echo "Setting up PostgreSQL database..."
	uv run python scripts/setup_database.py

# Load data to PostgreSQL
load:
	@echo "Loading data to PostgreSQL..."
	uv run python scripts/load_to_postgres.py --create-table

# Run complete pipeline
all: explore convert load
	@echo "Complete pipeline executed successfully"

# Development setup
dev-setup: setup install
	@echo "Development environment ready"
	@echo "Next steps:"
	@echo "1. Activate environment: source .venv/bin/activate"
	@echo "2. Copy env.example to .env and configure"
	@echo "3. Start exploring: make notebook" 