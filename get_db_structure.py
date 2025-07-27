#!/usr/bin/env python3
"""
Get database table structure for debugging backend API issues
"""

import os
import asyncpg
import asyncio
import sys

async def get_table_structure():
    """Connect to database and get table structure"""
    
    # Use the same DATABASE_URL as the backend
    database_url = os.getenv("DATABASE_URL", "postgresql://sports_user:sports_secure_2025@sports-db:5432/sports_data")
    
    # Handle URL conversion if needed  
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    print(f"Connecting to: {database_url}")
    
    try:
        # Connect to the database
        conn = await asyncpg.connect(database_url)
        
        # List of tables to examine
        tables = ['mlb_players', 'fangraphs_batting', 'fangraphs_pitching', 'statcast']
        
        for table_name in tables:
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name}")
            print(f"{'='*60}")
            
            # Check if table exists
            exists_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """
            
            table_exists = await conn.fetchval(exists_query, table_name)
            
            if not table_exists:
                print(f"❌ Table '{table_name}' does not exist")
                continue
                
            print(f"✅ Table '{table_name}' exists")
            
            # Get column information
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = $1 
                ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(columns_query, table_name)
            
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
                count_query = f"SELECT COUNT(*) FROM {table_name};"
                try:
                    count = await conn.fetchval(count_query)
                    print(f"\nRecord Count: {count:,}")
                except Exception as e:
                    print(f"\nError getting count: {e}")
                
                # Get a sample record to see actual data
                sample_query = f"SELECT * FROM {table_name} LIMIT 1;"
                try:
                    sample = await conn.fetchrow(sample_query)
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
        
        await conn.close()
        print(f"\n{'='*60}")
        print("Database structure extraction complete!")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Connection string: {database_url}")
        
        # Try alternative connection parameters
        print("\nTrying alternative connection approaches...")
        
        # Try localhost
        alt_url = database_url.replace("sports-db:5432", "localhost:5432")
        try:
            print(f"Trying localhost: {alt_url}")
            conn = await asyncpg.connect(alt_url)
            print("✅ Connected to localhost!")
            await conn.close()
        except Exception as e2:
            print(f"❌ Localhost failed: {e2}")

if __name__ == "__main__":
    asyncio.run(get_table_structure())