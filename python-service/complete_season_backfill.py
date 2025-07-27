#!/usr/bin/env python3
"""
COMPREHENSIVE 2025 MLB SEASON DATA BACKFILL
===========================================

This script ensures we have COMPLETE data for every game, every pitch, every player
for the entire 2025 MLB season. No data will be missed.

Features:
- Day-by-day systematic collection
- Game-by-game validation
- Player coverage verification  
- Cross-validation against Baseball Savant
- Automatic retry on failures
- Detailed progress reporting
"""

import asyncio
import pybaseball as pyb
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import json
import os
from typing import Dict, List, Tuple, Optional

# Import our existing data collector
import sys
sys.path.append('/home/jeffreyconboy/StatEdge/python-service')
from services.data_collector import DataCollector
from database.connection import get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveSeasonCollector:
    def __init__(self):
        self.collector = DataCollector()
        self.season = 2025
        self.progress_file = f'/tmp/season_{self.season}_progress.json'
        self.validation_results = []
        
        # MLB 2025 season boundaries (conservative estimates)
        self.season_start = date(2025, 3, 15)  # Spring training games
        self.season_end = date(2025, 11, 15)   # World Series end
        
        # Don't collect future dates
        today = date.today()
        if self.season_end > today:
            self.season_end = today
            
    async def init(self):
        """Initialize all components"""
        await self.collector.init_redis()
        logger.info(f"Initialized comprehensive collector for {self.season} season")
        logger.info(f"Collection period: {self.season_start} to {self.season_end}")
        
    def load_progress(self) -> Dict:
        """Load existing progress to resume if interrupted"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_dates': [],
            'failed_dates': [],
            'total_records_collected': 0,
            'games_processed': 0,
            'last_update': None
        }
    
    def save_progress(self, progress: Dict):
        """Save progress to file"""
        progress['last_update'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    async def get_current_db_stats(self) -> Dict:
        """Get current database statistics"""
        async for session in get_db_session():
            try:
                # Get overall stats
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_pitches,
                        COUNT(DISTINCT game_pk) as unique_games,
                        COUNT(DISTINCT batter_id) as unique_batters,
                        MIN(game_date) as earliest_date,
                        MAX(game_date) as latest_date
                    FROM statcast_pitches 
                    WHERE game_date >= :start_date AND game_date <= :end_date
                """), {
                    'start_date': self.season_start,
                    'end_date': self.season_end
                })
                row = result.fetchone()
                
                # Get monthly breakdown
                monthly_result = await session.execute(text("""
                    SELECT 
                        EXTRACT(YEAR FROM game_date) as year,
                        EXTRACT(MONTH FROM game_date) as month,
                        COUNT(*) as pitch_count,
                        COUNT(DISTINCT game_pk) as game_count,
                        COUNT(DISTINCT batter_id) as batter_count
                    FROM statcast_pitches 
                    WHERE game_date >= :start_date AND game_date <= :end_date
                    GROUP BY EXTRACT(YEAR FROM game_date), EXTRACT(MONTH FROM game_date)
                    ORDER BY year, month
                """), {
                    'start_date': self.season_start,
                    'end_date': self.season_end
                })
                
                monthly_data = []
                for monthly_row in monthly_result.fetchall():
                    monthly_data.append({
                        'year': int(monthly_row[0]),
                        'month': int(monthly_row[1]),
                        'pitch_count': monthly_row[2],
                        'game_count': monthly_row[3],
                        'batter_count': monthly_row[4]
                    })
                
                return {
                    'total_pitches': row[0] or 0,
                    'unique_games': row[1] or 0,
                    'unique_batters': row[2] or 0,
                    'earliest_date': row[3].isoformat() if row[3] else None,
                    'latest_date': row[4].isoformat() if row[4] else None,
                    'monthly_breakdown': monthly_data
                }
            finally:
                break
                
    async def validate_date_collection(self, target_date: date) -> Dict:
        """Validate data collection for a specific date"""
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            # Get expected data from Baseball Savant
            logger.info(f"Validating {date_str}...")
            expected_data = pyb.statcast(start_dt=date_str, end_dt=date_str)
            
            if expected_data.empty:
                return {
                    'date': date_str,
                    'status': 'no_games',
                    'expected_records': 0,
                    'actual_records': 0,
                    'completeness': 100.0,
                    'message': 'No games scheduled'
                }
            
            expected_records = len(expected_data)
            expected_games = expected_data['game_pk'].nunique()
            expected_batters = expected_data['batter'].nunique()
            
            # Check our database
            async for session in get_db_session():
                try:
                    result = await session.execute(text("""
                        SELECT 
                            COUNT(*) as actual_records,
                            COUNT(DISTINCT game_pk) as actual_games,
                            COUNT(DISTINCT batter_id) as actual_batters
                        FROM statcast_pitches 
                        WHERE game_date = :target_date
                    """), {'target_date': target_date})
                    
                    row = result.fetchone()
                    actual_records = row[0] or 0
                    actual_games = row[1] or 0
                    actual_batters = row[2] or 0
                    
                    completeness = (actual_records / expected_records * 100) if expected_records > 0 else 0
                    
                    validation = {
                        'date': date_str,
                        'status': 'complete' if completeness >= 99.5 else 'incomplete' if completeness > 0 else 'missing',
                        'expected_records': expected_records,
                        'actual_records': actual_records,
                        'expected_games': expected_games,
                        'actual_games': actual_games,
                        'expected_batters': expected_batters,
                        'actual_batters': actual_batters,
                        'completeness': round(completeness, 2),
                        'message': f"Data {completeness:.1f}% complete"
                    }
                    
                    if completeness < 99.5:
                        validation['needs_collection'] = True
                        
                    return validation
                    
                finally:
                    break
                    
        except Exception as e:
            logger.error(f"Validation failed for {date_str}: {str(e)}")
            return {
                'date': date_str,
                'status': 'error',
                'error': str(e),
                'needs_collection': True
            }
    
    async def collect_single_date(self, target_date: date, retry_count: int = 0) -> bool:
        """Collect data for a single date with validation"""
        date_str = target_date.strftime('%Y-%m-%d')
        max_retries = 3
        
        try:
            logger.info(f"Collecting data for {date_str} (attempt {retry_count + 1})")
            
            # Use our existing data collector
            await self.collector.collect_statcast_data(date_str)
            
            # Validate the collection
            validation = await self.validate_date_collection(target_date)
            
            if validation['status'] == 'complete':
                logger.info(f"✅ {date_str}: {validation['actual_records']} records, {validation['actual_games']} games")
                return True
            elif validation['status'] == 'no_games':
                logger.info(f"📅 {date_str}: No games scheduled")
                return True
            else:
                logger.warning(f"⚠️ {date_str}: {validation['completeness']}% complete ({validation['actual_records']}/{validation['expected_records']})")
                
                if retry_count < max_retries:
                    logger.info(f"Retrying {date_str} (attempt {retry_count + 2})")
                    await asyncio.sleep(5)  # Brief delay before retry
                    return await self.collect_single_date(target_date, retry_count + 1)
                else:
                    logger.error(f"❌ {date_str}: Failed after {max_retries + 1} attempts")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ {date_str}: Collection error - {str(e)}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying {date_str} due to error (attempt {retry_count + 2})")
                await asyncio.sleep(10)  # Longer delay for errors
                return await self.collect_single_date(target_date, retry_count + 1)
            else:
                return False
    
    async def run_comprehensive_backfill(self):
        """Run the complete backfill process"""
        logger.info("🚀 STARTING COMPREHENSIVE 2025 SEASON BACKFILL")
        logger.info("=" * 60)
        
        await self.init()
        
        # Load existing progress
        progress = self.load_progress()
        
        # Get current database state
        db_stats = await self.get_current_db_stats()
        logger.info(f"Current DB: {db_stats['total_pitches']:,} pitches, {db_stats['unique_games']} games")
        
        # Generate list of all dates to process
        current_date = self.season_start
        all_dates = []
        
        while current_date <= self.season_end:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str not in progress['completed_dates']:
                all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"📊 Processing {len(all_dates)} dates from {self.season_start} to {self.season_end}")
        
        successful_dates = 0
        failed_dates = 0
        
        for i, target_date in enumerate(all_dates, 1):
            date_str = target_date.strftime('%Y-%m-%d')
            
            logger.info(f"\n[{i}/{len(all_dates)}] Processing {date_str}")
            
            success = await self.collect_single_date(target_date)
            
            if success:
                successful_dates += 1
                progress['completed_dates'].append(date_str)
                if date_str in progress['failed_dates']:
                    progress['failed_dates'].remove(date_str)
            else:
                failed_dates += 1
                if date_str not in progress['failed_dates']:
                    progress['failed_dates'].append(date_str)
            
            # Save progress every 10 dates
            if i % 10 == 0:
                self.save_progress(progress)
                updated_stats = await self.get_current_db_stats()
                logger.info(f"📈 Progress: {successful_dates} successful, {failed_dates} failed")
                logger.info(f"📊 DB now has: {updated_stats['total_pitches']:,} pitches, {updated_stats['unique_games']} games")
        
        # Final save and summary
        self.save_progress(progress)
        final_stats = await self.get_current_db_stats()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 COMPREHENSIVE BACKFILL COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Successful dates: {successful_dates}")
        logger.info(f"❌ Failed dates: {failed_dates}")
        logger.info(f"📊 Final DB stats: {final_stats['total_pitches']:,} pitches, {final_stats['unique_games']} games")
        logger.info(f"📅 Date range: {final_stats['earliest_date']} to {final_stats['latest_date']}")
        
        if failed_dates > 0:
            logger.warning(f"⚠️ {failed_dates} dates failed - check logs and retry")
            logger.warning(f"Failed dates: {progress['failed_dates']}")
        
        return {
            'success': failed_dates == 0,
            'successful_dates': successful_dates,
            'failed_dates': failed_dates,
            'final_stats': final_stats,
            'progress_file': self.progress_file
        }

async def main():
    """Main execution function"""
    collector = ComprehensiveSeasonCollector()
    result = await collector.run_comprehensive_backfill()
    
    if result['success']:
        print("🎉 ALL DATA COLLECTED SUCCESSFULLY!")
    else:
        print(f"⚠️ Collection completed with {result['failed_dates']} failures")
        print("Check logs and retry failed dates")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())