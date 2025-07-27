#!/usr/bin/env python3
"""
Simple test to verify PyBaseball API response and identify data volume
"""

import pybaseball as pyb
import pandas as pd
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pybaseball_api():
    """Test PyBaseball API with various dates to understand data volume"""
    
    # Test dates with known MLB activity
    test_dates = [
        "2024-07-24",  # Mid-season 2024
        "2024-07-25",  # Next day
        "2024-09-15",  # Late season 2024
        "2024-04-15",  # Early season 2024
        "2025-01-01",  # Off-season (should be empty)
    ]
    
    logger.info("🔍 Testing PyBaseball API with multiple dates")
    logger.info("=" * 80)
    
    for test_date in test_dates:
        logger.info(f"\n📅 Testing date: {test_date}")
        logger.info("-" * 50)
        
        try:
            # Call PyBaseball API
            logger.info(f"Calling pyb.statcast(start_dt='{test_date}', end_dt='{test_date}')")
            raw_data = pyb.statcast(start_dt=test_date, end_dt=test_date)
            
            if raw_data.empty:
                logger.info("❌ No data returned (likely off-season or off-day)")
                continue
                
            logger.info(f"✅ Data retrieved successfully!")
            logger.info(f"   📊 Shape: {raw_data.shape[0]} rows × {raw_data.shape[1]} columns")
            logger.info(f"   💾 Memory usage: {raw_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            # Analyze the data
            if 'game_date' in raw_data.columns:
                unique_dates = raw_data['game_date'].nunique()
                logger.info(f"   📆 Unique dates in data: {unique_dates}")
                if unique_dates > 0:
                    date_range = f"{raw_data['game_date'].min()} to {raw_data['game_date'].max()}"
                    logger.info(f"   📆 Date range: {date_range}")
            
            if 'game_pk' in raw_data.columns:
                unique_games = raw_data['game_pk'].nunique()
                logger.info(f"   ⚾ Unique games: {unique_games}")
                logger.info(f"   ⚾ Average pitches per game: {raw_data.shape[0] / unique_games:.1f}")
            
            # Show column information
            logger.info(f"   📋 Column count: {len(raw_data.columns)}")
            logger.info(f"   📋 Sample columns: {list(raw_data.columns[:15])}")
            
            # Show sample data structure
            logger.info("   📝 Sample records:")
            for i, (idx, row) in enumerate(raw_data.head(3).iterrows()):
                game_pk = row.get('game_pk', 'N/A')
                pitch_num = row.get('pitch_number', 'N/A')
                batter = row.get('batter', 'N/A')
                pitcher = row.get('pitcher', 'N/A')
                pitch_type = row.get('pitch_type', 'N/A')
                logger.info(f"     Record {i+1}: game_pk={game_pk}, pitch_number={pitch_num}, "
                          f"batter={batter}, pitcher={pitcher}, pitch_type={pitch_type}")
            
            # Check for null values in key fields
            null_counts = {
                'game_pk': raw_data['game_pk'].isnull().sum() if 'game_pk' in raw_data.columns else 0,
                'pitch_number': raw_data['pitch_number'].isnull().sum() if 'pitch_number' in raw_data.columns else 0,
                'batter': raw_data['batter'].isnull().sum() if 'batter' in raw_data.columns else 0,
                'pitcher': raw_data['pitcher'].isnull().sum() if 'pitcher' in raw_data.columns else 0,
            }
            
            logger.info("   ❓ Null value counts in key fields:")
            for field, count in null_counts.items():
                if count > 0:
                    logger.info(f"     {field}: {count} nulls")
                else:
                    logger.info(f"     {field}: ✅ no nulls")
            
            # This represents what should be stored in the database
            expected_storage_count = len(raw_data)
            logger.info(f"   🎯 EXPECTED DATABASE RECORDS: {expected_storage_count}")
            
        except Exception as e:
            logger.error(f"❌ API call failed for {test_date}: {str(e)}")
            continue
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PyBaseball API test completed")

def test_data_processing_simulation():
    """Simulate the data processing that happens in store_statcast_data"""
    
    logger.info("\n🔄 SIMULATING DATA PROCESSING")
    logger.info("=" * 80)
    
    test_date = "2024-07-24"  # Known good date
    
    try:
        logger.info(f"📡 Getting raw data for {test_date}")
        raw_data = pyb.statcast(start_dt=test_date, end_dt=test_date)
        
        if raw_data.empty:
            logger.warning("No data to process")
            return
            
        initial_count = len(raw_data)
        logger.info(f"📊 Initial record count: {initial_count}")
        
        # Simulate the processing that happens in store_statcast_data
        processed_count = 0
        invalid_records = 0
        
        logger.info("🔄 Simulating row-by-row processing...")
        
        for idx, row in raw_data.iterrows():
            # Convert row to dict (like in the actual code)
            statcast_json = row.to_dict()
            
            # Handle NaN values (like in actual code)
            for key, value in statcast_json.items():
                if pd.isna(value):
                    statcast_json[key] = None
                elif hasattr(value, 'isoformat'):  # Handle timestamps
                    statcast_json[key] = value.isoformat()
                elif hasattr(value, 'item'):  # Handle numpy types
                    statcast_json[key] = value.item()
            
            # Extract key fields for indexing (like in actual code)
            game_pk = statcast_json.get('game_pk')
            pitch_id = f"{game_pk}_{statcast_json.get('play_id', 0)}_{statcast_json.get('pitch_number', 0)}"
            
            # Check for required fields
            if game_pk is None:
                invalid_records += 1
                logger.warning(f"   Invalid record: missing game_pk at index {idx}")
                continue
                
            processed_count += 1
            
            # Log every 1000th record to show progress
            if processed_count % 1000 == 0:
                logger.info(f"   Processed {processed_count} records...")
        
        logger.info(f"✅ Processing simulation completed:")
        logger.info(f"   📊 Records processed: {processed_count}")
        logger.info(f"   ❌ Invalid records: {invalid_records}")
        logger.info(f"   📈 Success rate: {(processed_count/initial_count)*100:.1f}%")
        
        if processed_count != initial_count:
            logger.warning(f"⚠️  DATA LOSS DETECTED: {initial_count - processed_count} records lost during processing")
        else:
            logger.info("✅ No data loss during processing simulation")
            
    except Exception as e:
        logger.error(f"❌ Processing simulation failed: {str(e)}")

def main():
    """Main execution"""
    logger.info("🚀 Starting PyBaseball API Analysis")
    
    # Test 1: Raw API responses
    test_pybaseball_api()
    
    # Test 2: Data processing simulation
    test_data_processing_simulation()
    
    logger.info("\n🎉 Analysis completed!")
    logger.info("This shows what data is available from PyBaseball and how much should be stored.")

if __name__ == "__main__":
    main()