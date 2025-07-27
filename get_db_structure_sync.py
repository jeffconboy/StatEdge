#!/usr/bin/env python3
"""
Get database table structure for debugging backend API issues (synchronous version)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def get_table_structure():
    """Connect to database and get table structure"""
    
    # Try different connection configurations that appear in the codebase
    connection_configs = [
        # From python-service backend (default)
        {
            'host': 'sports-db', 'port': 5432, 'user': 'sports_user', 
            'password': 'sports_secure_2025', 'database': 'sports_data'
        },
        # Localhost version
        {
            'host': 'localhost', 'port': 5432, 'user': 'sports_user', 
            'password': 'sports_secure_2025', 'database': 'sports_data'
        },
        # MLb data service config
        {
            'host': 'localhost', 'port': 15432, 'user': 'statedge_user', 
            'password': 'statedge_pass', 'database': 'statedge'
        },
        # Production config variations
        {
            'host': 'localhost', 'port': 5432, 'user': 'statedge', 
            'password': 'statedge123', 'database': 'statedge'
        }
    ]
    
    conn = None
    
    for i, config in enumerate(connection_configs):
        try:
            print(f"\n🔍 Trying connection {i+1}: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
            
            conn = psycopg2.connect(**config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            print(f"✅ Successfully connected!")
            break
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue
    
    if not conn:
        print("\n❌ Could not connect to any database configuration")
        return
    
    try:
        # List of tables to examine
        tables = ['mlb_players', 'fangraphs_batting', 'fangraphs_pitching', 'statcast']
        
        for table_name in tables:
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name}")
            print(f"{'='*60}")
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            result = cursor.fetchone()
            table_exists = result['exists'] if result else False
            
            if not table_exists:
                print(f"❌ Table '{table_name}' does not exist")
                continue
                
            print(f"✅ Table '{table_name}' exists")
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            if columns:
                print(f"\nColumns ({len(columns)} total):")
                print(f"{'Column Name':<35} {'Data Type':<20} {'Nullable':<10} {'Default'}")
                print("-" * 80)
                
                for col in columns:
                    col_name = col['column_name']
                    data_type = col['data_type']
                    nullable = col['is_nullable']
                    default = str(col['column_default']) if col['column_default'] else ''
                    print(f"{col_name:<35} {data_type:<20} {nullable:<10} {default}")
                
                # Get a count of records
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count_result = cursor.fetchone()
                    count = count_result['count'] if count_result else 0
                    print(f"\nRecord Count: {count:,}")
                except Exception as e:
                    print(f"\nError getting count: {e}")
                
                # Get a sample record to see actual data structure
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"\nSample record keys: {list(sample.keys())}")
                        # Show first few columns with data
                        for i, (key, value) in enumerate(sample.items()):
                            if i >= 10:  # Limit to first 10 columns for readability
                                print("... (more columns)")
                                break
                            print(f"  {key}: {value}")
                    else:
                        print("\nNo sample records found")
                except Exception as e:
                    print(f"\nError getting sample: {e}")
            else:
                print("No columns found")
        
        print(f"\n{'='*60}")
        print("Database structure extraction complete!")
        
    except Exception as e:
        print(f"Error during database operations: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_table_structure()