#!/usr/bin/env python3
"""
Update existing transactions with reference IDs.
This script adds reference IDs to all existing credit transactions that don't have them.
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(database_url)
    return engine.connect()

def generate_reference_id():
    """Generate a unique reference ID for transactions."""
    # Use timestamp + short UUID for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d')
    short_uuid = str(uuid.uuid4()).replace('-', '').upper()[:8]
    return f"TXN-{timestamp}-{short_uuid}"

def update_transaction_reference_ids():
    """Update all transactions that don't have reference IDs."""
    try:
        conn = get_db_connection()
        
        # Get all transactions without reference IDs
        result = conn.execute(text("""
            SELECT id, created_at, transaction_type 
            FROM credit_transactions 
            WHERE reference_id IS NULL OR reference_id = ''
            ORDER BY created_at ASC
        """))
        
        transactions = result.fetchall()
        logger.info(f"Found {len(transactions)} transactions without reference IDs")
        
        if not transactions:
            logger.info("All transactions already have reference IDs")
            return
        
        # Update each transaction with a unique reference ID
        updated_count = 0
        for transaction in transactions:
            reference_id = generate_reference_id()
            
            conn.execute(text("""
                UPDATE credit_transactions 
                SET reference_id = :reference_id
                WHERE id = :transaction_id
            """), {
                "reference_id": reference_id,
                "transaction_id": transaction.id
            })
            
            updated_count += 1
            
            if updated_count % 50 == 0:
                logger.info(f"Updated {updated_count} transactions...")
        
        # Commit all changes
        conn.commit()
        logger.info(f"Successfully updated {updated_count} transactions with reference IDs")
        
    except Exception as e:
        logger.error(f"Error updating transaction reference IDs: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    try:
        update_transaction_reference_ids()
        print("Transaction reference ID update completed successfully!")
    except Exception as e:
        print(f"Failed to update transaction reference IDs: {e}")
        sys.exit(1)