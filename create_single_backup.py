#!/usr/bin/env python3
"""
Create a single consolidated backup file from individual table backups.

This script combines all the individual JSON backup files into one comprehensive backup file.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_single_backup():
    """Create a single consolidated backup file."""
    # Find the most recent backup directory
    backup_dir = Path('database_backup')
    if not backup_dir.exists():
        logger.error("No backup directory found")
        return False
    
    # Get the most recent backup folder
    backup_folders = [d for d in backup_dir.iterdir() if d.is_dir()]
    if not backup_folders:
        logger.error("No backup folders found")
        return False
    
    latest_backup = max(backup_folders, key=lambda x: x.name)
    logger.info(f"Using backup from: {latest_backup}")
    
    # Load the table list
    tables_file = latest_backup / "tables.json"
    if not tables_file.exists():
        logger.error("Tables list not found")
        return False
    
    with open(tables_file, 'r', encoding='utf-8') as f:
        tables = json.load(f)
    
    # Create consolidated backup
    consolidated_backup = {
        "backup_info": {
            "created_at": datetime.now().isoformat(),
            "source_backup": latest_backup.name,
            "total_tables": len(tables),
            "backup_type": "full_database_backup"
        },
        "tables": {}
    }
    
    # Process each table
    for table_name in tables:
        logger.info(f"Processing table: {table_name}")
        
        # Load data file
        data_file = latest_backup / f"{table_name}_data.json"
        schema_file = latest_backup / f"{table_name}_schema.json"
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                table_data = json.load(f)
        else:
            table_data = []
        
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                table_schema = json.load(f)
        else:
            table_schema = {}
        
        consolidated_backup["tables"][table_name] = {
            "schema": table_schema,
            "data": table_data,
            "row_count": len(table_data) if isinstance(table_data, list) else 0
        }
        
        logger.info(f"  - {table_name}: {len(table_data) if isinstance(table_data, list) else 0} rows")
    
    # Save consolidated backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = backup_dir / f"complete_backup_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated_backup, f, indent=2, ensure_ascii=False)
    
    # Calculate file size
    file_size = output_file.stat().st_size / (1024 * 1024)  # MB
    
    logger.info(f"Consolidated backup created: {output_file}")
    logger.info(f"File size: {file_size:.2f} MB")
    logger.info(f"Total tables: {len(tables)}")
    
    # Show summary
    total_rows = sum(
        len(data["data"]) if isinstance(data["data"], list) else 0 
        for data in consolidated_backup["tables"].values()
    )
    logger.info(f"Total rows across all tables: {total_rows}")
    
    return True

def main():
    """Main function."""
    logger.info("=== Creating single consolidated backup ===")
    
    success = create_single_backup()
    
    if success:
        logger.info("=== Single backup created successfully ===")
        return 0
    else:
        logger.error("=== Failed to create single backup ===")
        return 1

if __name__ == "__main__":
    exit(main())