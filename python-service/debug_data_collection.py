#!/usr/bin/env python3
"""Debug script to identify where we're losing 97% of Statcast data"""

import asyncio
import pybaseball as pyb
import pandas as pd
from datetime import datetime
import json

async def debug_data_collection():
    """Debug the complete data collection and storage process"""
    
    print("=== DEBUG: 2025 STATCAST DATA COLLECTION ===")
    
    # Step 1: Test PyBaseball data retrieval
    print("\n1. Testing PyBaseball data retrieval...")
    test_date = '2025-07-01'
    statcast_data = pyb.statcast(start_dt=test_date, end_dt=test_date)
    print(f"   PyBaseball returned: {len(statcast_data)} records")
    
    if len(statcast_data) == 0:
        print("   ERROR: No data returned from PyBaseball!")
        return
    
    # Step 2: Test data processing
    print("\n2. Testing data processing...")
    processed_count = 0
    for _, row in statcast_data.iterrows():
        # Simulate the processing logic
        statcast_json = row.to_dict()
        
        # Handle NaN values and convert timestamps
        for key, value in statcast_json.items():
            if pd.isna(value):
                statcast_json[key] = None
            elif hasattr(value, 'isoformat'):  # Handle timestamps
                statcast_json[key] = value.isoformat()
            elif hasattr(value, 'item'):  # Handle numpy types
                statcast_json[key] = value.item()
        
        processed_count += 1
        
        # Test first few records
        if processed_count <= 3:
            print(f"   Record {processed_count}: game_pk={statcast_json.get('game_pk')}, pitcher={statcast_json.get('pitcher')}")
    
    print(f"   Successfully processed: {processed_count} records")
    
    # Step 3: Test database connection (simulate)
    print("\n3. Database insertion simulation...")
    insertion_count = 0
    for _, row in statcast_data.iterrows():
        # Simulate database insertion logic
        statcast_json = row.to_dict()
        
        # Extract key fields
        game_pk = statcast_json.get('game_pk')
        pitch_id = f"{game_pk}_{statcast_json.get('play_id', 0)}_{statcast_json.get('pitch_number', 0)}"
        
        if game_pk and pitch_id:
            insertion_count += 1
        
        # Stop after first 10 for debugging
        if insertion_count >= 10:
            break
    
    print(f"   Records ready for insertion: {insertion_count}")
    
    # Step 4: Summary
    print(f"\n=== SUMMARY ===")
    print(f"PyBaseball records: {len(statcast_data)}")
    print(f"Processed records: {processed_count}")
    print(f"Ready for DB: {insertion_count}")
    print(f"Expected storage: {min(len(statcast_data), insertion_count)}")
    
    # Check for obvious issues
    if len(statcast_data) > 1000 and insertion_count < 100:
        print("⚠️  WARNING: Major data loss detected in processing!")
    elif len(statcast_data) > 0 and processed_count == len(statcast_data):
        print("✅ Data processing looks correct")
    else:
        print("❌ Data processing issue detected")

if __name__ == "__main__":
    asyncio.run(debug_data_collection())