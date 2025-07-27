#!/usr/bin/env python3
"""
Remove jersey_number column from mlb_probable_pitchers table
"""
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_jersey_column():
    """Remove jersey_number column from mlb_probable_pitchers table"""
    
    # Database connection
    db_url = "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data"
    
    try:
        # Connect to database
        logger.info("Connecting to sports_data database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Remove jersey_number column
        logger.info("Removing jersey_number column from mlb_probable_pitchers...")
        cursor.execute("ALTER TABLE mlb_probable_pitchers DROP COLUMN IF EXISTS jersey_number;")
        
        # Verify column was removed
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'mlb_probable_pitchers' 
            ORDER BY ordinal_position;
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ Remaining columns in mlb_probable_pitchers: {columns}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to remove column: {e}")
        return False

if __name__ == "__main__":
    success = remove_jersey_column()
    if success:
        print("✅ Jersey number column removed successfully!")
    else:
        print("❌ Failed to remove jersey number column")