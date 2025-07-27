#!/usr/bin/env python3
"""
Comprehensive trace of data collection execution path to identify data loss points.
This script will monitor each step and log detailed information about data flow.
"""

import asyncio
import logging
import sys
import json
import pybaseball as pyb
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from services.data_collector import DataCollector

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCollectionTracer:
    def __init__(self):
        self.collector = DataCollector()
        
    async def trace_complete_pipeline(self, test_date: str = None):
        """Trace the complete data collection pipeline with detailed monitoring"""
        if test_date is None:
            # Use a recent date that should have data
            test_date = "2024-07-24"  # Use a date from last season that we know has data
            
        logger.info(f"🔍 STARTING COMPLETE PIPELINE TRACE FOR DATE: {test_date}")
        logger.info("=" * 80)
        
        # Step 1: Test PyBaseball API directly
        await self.step1_test_pybaseball_api(test_date)
        
        # Step 2: Test data collection method
        await self.step2_test_collect_statcast_data(test_date)
        
        # Step 3: Test database storage
        await self.step3_test_database_storage(test_date)
        
        # Step 4: Test data retrieval
        await self.step4_test_data_retrieval(test_date)
        
        # Step 5: Database analysis
        await self.step5_database_analysis()
        
        logger.info("=" * 80)
        logger.info("🏁 PIPELINE TRACE COMPLETED")
        
    async def step1_test_pybaseball_api(self, test_date: str):
        """Step 1: Test PyBaseball API directly to see raw data volume"""
        logger.info("📡 STEP 1: Testing PyBaseball API directly")
        logger.info("-" * 50)
        
        try:
            logger.info(f"Calling pyb.statcast(start_dt='{test_date}', end_dt='{test_date}')")
            raw_data = pyb.statcast(start_dt=test_date, end_dt=test_date)
            
            logger.info(f"✅ Raw PyBaseball data retrieved:")
            logger.info(f"   - Shape: {raw_data.shape}")
            logger.info(f"   - Columns: {len(raw_data.columns)}")
            logger.info(f"   - Memory usage: {raw_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            if not raw_data.empty:
                logger.info(f"   - Date range in data: {raw_data['game_date'].min()} to {raw_data['game_date'].max()}")
                logger.info(f"   - Unique games: {raw_data['game_pk'].nunique()}")
                logger.info(f"   - Sample columns: {list(raw_data.columns[:10])}")
                
                # Sample data inspection
                logger.info("   - Sample records:")
                for i, (idx, row) in enumerate(raw_data.head(3).iterrows()):
                    logger.info(f"     Record {i+1}: game_pk={row.get('game_pk')}, "
                              f"pitch_number={row.get('pitch_number')}, "
                              f"batter={row.get('batter')}, "
                              f"pitcher={row.get('pitcher')}")
            else:
                logger.warning("❌ No data returned from PyBaseball API")
                
            return raw_data
            
        except Exception as e:
            logger.error(f"❌ PyBaseball API call failed: {str(e)}")
            raise
            
    async def step2_test_collect_statcast_data(self, test_date: str):
        """Step 2: Test the collect_statcast_data method with monitoring"""
        logger.info("\n🔄 STEP 2: Testing collect_statcast_data method")
        logger.info("-" * 50)
        
        try:
            await self.collector.init_redis()
            
            # Monitor the collection process
            logger.info(f"Starting collection for date: {test_date}")
            
            # Hook into the data collection to monitor progress
            original_store_method = self.collector.store_statcast_data
            
            stored_count = 0
            
            async def monitored_store(session: AsyncSession, df: pd.DataFrame):
                nonlocal stored_count
                logger.info(f"📥 store_statcast_data called with DataFrame shape: {df.shape}")
                
                # Log first few records being stored
                for i, (idx, row) in enumerate(df.head(3).iterrows()):
                    logger.info(f"   Storing record {i+1}: game_pk={row.get('game_pk')}, "
                              f"pitch_id={row.get('game_pk')}_{row.get('play_id', 0)}_{row.get('pitch_number', 0)}")
                
                # Call original method
                result = await original_store_method(session, df)
                stored_count = len(df)
                logger.info(f"✅ Stored {stored_count} records to database")
                return result
                
            # Replace the method temporarily
            self.collector.store_statcast_data = monitored_store
            
            # Run the collection
            await self.collector.collect_statcast_data(test_date)
            
            # Restore original method
            self.collector.store_statcast_data = original_store_method
            
            logger.info(f"✅ Collection completed. Records stored: {stored_count}")
            
        except Exception as e:
            logger.error(f"❌ collect_statcast_data failed: {str(e)}")
            raise
            
    async def step3_test_database_storage(self, test_date: str):
        """Step 3: Test database storage and transaction handling"""
        logger.info("\n💾 STEP 3: Testing database storage")
        logger.info("-" * 50)
        
        async for session in get_db_session():
            try:
                # Check what was actually stored
                query = text("""
                    SELECT COUNT(*) as total_count,
                           COUNT(DISTINCT game_pk) as unique_games,
                           MIN(game_date) as min_date,
                           MAX(game_date) as max_date
                    FROM statcast_pitches 
                    WHERE game_date = :test_date
                """)
                
                result = await session.execute(query, {'test_date': test_date})
                row = result.fetchone()
                
                logger.info(f"📊 Database storage results for {test_date}:")
                logger.info(f"   - Total records: {row.total_count}")
                logger.info(f"   - Unique games: {row.unique_games}")
                logger.info(f"   - Date range: {row.min_date} to {row.max_date}")
                
                # Sample some stored records
                sample_query = text("""
                    SELECT game_pk, pitch_id, batter_id, pitcher_id, 
                           statcast_data->>'pitch_type' as pitch_type,
                           statcast_data->>'release_speed' as release_speed
                    FROM statcast_pitches 
                    WHERE game_date = :test_date
                    LIMIT 5
                """)
                
                sample_result = await session.execute(sample_query, {'test_date': test_date})
                sample_rows = sample_result.fetchall()
                
                logger.info("   - Sample stored records:")
                for i, row in enumerate(sample_rows):
                    logger.info(f"     Record {i+1}: game_pk={row.game_pk}, "
                              f"pitch_id={row.pitch_id}, "
                              f"batter={row.batter_id}, "
                              f"pitcher={row.pitcher_id}, "
                              f"pitch_type={row.pitch_type}, "
                              f"speed={row.release_speed}")
                
                # Check for any constraint violations or duplicates
                duplicate_query = text("""
                    SELECT pitch_id, COUNT(*) as count
                    FROM statcast_pitches 
                    WHERE game_date = :test_date
                    GROUP BY pitch_id
                    HAVING COUNT(*) > 1
                    LIMIT 5
                """)
                
                dup_result = await session.execute(duplicate_query, {'test_date': test_date})
                duplicates = dup_result.fetchall()
                
                if duplicates:
                    logger.warning(f"⚠️  Found {len(duplicates)} duplicate pitch_ids:")
                    for dup in duplicates:
                        logger.warning(f"     pitch_id={dup.pitch_id} appears {dup.count} times")
                else:
                    logger.info("✅ No duplicate pitch_ids found")
                    
            except Exception as e:
                logger.error(f"❌ Database storage check failed: {str(e)}")
                raise
            finally:
                break
                
    async def step4_test_data_retrieval(self, test_date: str):
        """Step 4: Test data retrieval through API endpoints"""
        logger.info("\n📤 STEP 4: Testing data retrieval")
        logger.info("-" * 50)
        
        async for session in get_db_session():
            try:
                # Test the same queries that the analytics API uses
                stats_query = text("SELECT COUNT(*) FROM statcast_pitches")
                result = await session.execute(stats_query)
                total_pitches = result.scalar()
                logger.info(f"📈 Total Statcast pitches in database: {total_pitches}")
                
                # Recent data query (like the analytics endpoint)
                recent_query = text("""
                    SELECT COUNT(*) FROM statcast_pitches 
                    WHERE game_date >= CURRENT_DATE - INTERVAL '7 days'
                """)
                result = await session.execute(recent_query)
                recent_pitches = result.scalar()
                logger.info(f"📈 Recent Statcast pitches (last 7 days): {recent_pitches}")
                
                # Date range query
                range_query = text("""
                    SELECT MIN(game_date), MAX(game_date) 
                    FROM statcast_pitches
                """)
                result = await session.execute(range_query)
                date_range = result.fetchone()
                logger.info(f"📅 Data date range: {date_range[0]} to {date_range[1]}")
                
                # Check specific date
                date_query = text("""
                    SELECT COUNT(*) 
                    FROM statcast_pitches 
                    WHERE game_date = :test_date
                """)
                result = await session.execute(date_query, {'test_date': test_date})
                date_count = result.scalar()
                logger.info(f"📅 Records for {test_date}: {date_count}")
                
                # Daily record counts for recent dates
                daily_query = text("""
                    SELECT game_date, COUNT(*) as daily_count
                    FROM statcast_pitches 
                    WHERE game_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY game_date
                    ORDER BY game_date DESC
                    LIMIT 10
                """)
                result = await session.execute(daily_query)
                daily_counts = result.fetchall()
                
                logger.info("📊 Daily record counts (last 30 days):")
                for row in daily_counts:
                    logger.info(f"   {row.game_date}: {row.daily_count} records")
                    
            except Exception as e:
                logger.error(f"❌ Data retrieval test failed: {str(e)}")
                raise
            finally:
                break
                
    async def step5_database_analysis(self):
        """Step 5: Analyze database for potential issues"""
        logger.info("\n🔍 STEP 5: Database analysis for issues")
        logger.info("-" * 50)
        
        async for session in get_db_session():
            try:
                # Check for NULL values in key fields
                null_query = text("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN game_pk IS NULL THEN 1 END) as null_game_pk,
                        COUNT(CASE WHEN pitch_id IS NULL THEN 1 END) as null_pitch_id,
                        COUNT(CASE WHEN game_date IS NULL THEN 1 END) as null_game_date,
                        COUNT(CASE WHEN statcast_data IS NULL THEN 1 END) as null_statcast_data
                    FROM statcast_pitches
                """)
                result = await session.execute(null_query)
                null_stats = result.fetchone()
                
                logger.info("🔍 NULL value analysis:")
                logger.info(f"   Total records: {null_stats.total_records}")
                logger.info(f"   NULL game_pk: {null_stats.null_game_pk}")
                logger.info(f"   NULL pitch_id: {null_stats.null_pitch_id}")
                logger.info(f"   NULL game_date: {null_stats.null_game_date}")
                logger.info(f"   NULL statcast_data: {null_stats.null_statcast_data}")
                
                # Check JSON data quality
                json_query = text("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN statcast_data::text = '{}' THEN 1 END) as empty_json,
                        COUNT(CASE WHEN LENGTH(statcast_data::text) < 100 THEN 1 END) as suspiciously_small_json
                    FROM statcast_pitches
                """)
                result = await session.execute(json_query)
                json_stats = result.fetchone()
                
                logger.info("🔍 JSON data quality analysis:")
                logger.info(f"   Total records: {json_stats.total_records}")
                logger.info(f"   Empty JSON objects: {json_stats.empty_json}")
                logger.info(f"   Suspiciously small JSON: {json_stats.suspiciously_small_json}")
                
                # Check for table constraints and indexes
                constraint_query = text("""
                    SELECT conname, contype 
                    FROM pg_constraint 
                    WHERE conrelid = 'statcast_pitches'::regclass
                """)
                result = await session.execute(constraint_query)
                constraints = result.fetchall()
                
                logger.info("🔍 Table constraints:")
                for constraint in constraints:
                    logger.info(f"   {constraint.conname} ({constraint.contype})")
                
                # Check table size and performance
                size_query = text("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('statcast_pitches')) as total_size,
                        pg_size_pretty(pg_relation_size('statcast_pitches')) as table_size,
                        pg_size_pretty(pg_total_relation_size('statcast_pitches') - pg_relation_size('statcast_pitches')) as index_size
                """)
                result = await session.execute(size_query)
                size_stats = result.fetchone()
                
                logger.info("🔍 Table size analysis:")
                logger.info(f"   Total size: {size_stats.total_size}")
                logger.info(f"   Table size: {size_stats.table_size}")
                logger.info(f"   Index size: {size_stats.index_size}")
                
            except Exception as e:
                logger.error(f"❌ Database analysis failed: {str(e)}")
                raise
            finally:
                break

async def test_specific_date_with_known_data():
    """Test with a specific date that should have lots of data"""
    tracer = DataCollectionTracer()
    
    # Use July 24, 2024 - middle of season, should have full slate of games
    test_date = "2024-07-24"
    
    logger.info(f"🎯 TESTING SPECIFIC DATE WITH KNOWN DATA: {test_date}")
    await tracer.trace_complete_pipeline(test_date)

async def test_recent_date():
    """Test with a more recent date"""
    tracer = DataCollectionTracer()
    
    # Use a recent date from 2024 season
    recent_date = "2024-09-15"  # Late season date
    
    logger.info(f"🕐 TESTING RECENT DATE: {recent_date}")
    await tracer.trace_complete_pipeline(recent_date)

async def compare_api_vs_database():
    """Compare what API returns vs what gets stored"""
    logger.info("\n🔄 COMPARING API RESPONSE VS DATABASE STORAGE")
    logger.info("=" * 80)
    
    test_date = "2024-07-24"
    
    # Get direct API data
    logger.info("📡 Getting direct API data...")
    api_data = pyb.statcast(start_dt=test_date, end_dt=test_date)
    api_count = len(api_data)
    logger.info(f"API returned: {api_count} records")
    
    # Check database
    async for session in get_db_session():
        query = text("SELECT COUNT(*) FROM statcast_pitches WHERE game_date = :test_date")
        result = await session.execute(query, {'test_date': test_date})
        db_count = result.scalar()
        logger.info(f"Database contains: {db_count} records for {test_date}")
        
        if api_count != db_count:
            logger.warning(f"⚠️  DATA MISMATCH: API={api_count}, DB={db_count}")
            logger.warning(f"   Missing records: {api_count - db_count}")
        else:
            logger.info("✅ API and database counts match")
        break

async def main():
    """Main execution function"""
    logger.info("🚀 STARTING COMPREHENSIVE DATA COLLECTION TRACE")
    logger.info("This will identify exactly where data loss occurs in the pipeline")
    logger.info("=" * 80)
    
    try:
        # Test 1: Specific date with known data
        await test_specific_date_with_known_data()
        
        # Test 2: Recent date
        await test_recent_date()
        
        # Test 3: Compare API vs Database
        await compare_api_vs_database()
        
        logger.info("\n🎉 TRACE COMPLETED SUCCESSFULLY!")
        logger.info("Check the logs above for any data loss points or issues.")
        
    except Exception as e:
        logger.error(f"💥 TRACE FAILED: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())