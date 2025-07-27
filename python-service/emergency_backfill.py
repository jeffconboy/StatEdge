#!/usr/bin/env python3
"""
EMERGENCY 2025 SEASON DATA BACKFILL
===================================

This script directly collects missing season data without requiring the full API service.
It will systematically collect ALL missing March-June 2025 data.
"""

import pybaseball as pyb
import pandas as pd
import psycopg2
import json
import os
from datetime import date, timedelta, datetime
import logging
from typing import Dict, List
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmergencyBackfillCollector:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 15432,
            'user': 'statedge_user',
            'password': 'statedge_pass',
            'database': 'statedge'
        }
        
        # Missing date ranges based on our investigation
        self.missing_ranges = [
            (date(2025, 3, 15), date(2025, 3, 31)),  # Late March
            (date(2025, 4, 1), date(2025, 4, 30)),   # Full April
            (date(2025, 5, 1), date(2025, 5, 31)),   # Full May  
            (date(2025, 6, 1), date(2025, 6, 24)),   # Early June
        ]
        
        self.progress_file = '/tmp/emergency_backfill_progress.json'
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            # Try alternative connection with different database name
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=15432,
                    user='statedge_user', 
                    password='statedge_pass',
                    database='statedge_data'  # Try alternative database name
                )  
                return conn
            except:
                logger.error("All database connection attempts failed")
                return None
    
    def _convert_to_date(self, date_value):
        """Convert various date formats to Python date object"""
        if date_value is None:
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            try:
                if 'T' in date_value:  # ISO format with time
                    return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
                else:  # Simple date format
                    parsed_dt = datetime.strptime(date_value, '%Y-%m-%d')
                    return parsed_dt.date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse date: {date_value}, error: {e}")
                return None
        
        # If pandas Timestamp, convert to date
        if hasattr(date_value, 'date'):
            return date_value.date()
        
        logger.warning(f"Unknown date format: {type(date_value)} - {date_value}")
        return None
    
    def store_statcast_batch(self, conn, df: pd.DataFrame, target_date: str) -> int:
        """Store batch of Statcast data"""
        cursor = conn.cursor()
        records_inserted = 0
        
        try:
            logger.info(f"Storing {len(df)} records for {target_date}...")
            
            for _, row in df.iterrows():
                # Convert entire row to JSON - preserve ALL fields
                statcast_json = row.to_dict()
                
                # Handle NaN values and convert timestamps
                for key, value in statcast_json.items():
                    if pd.isna(value):
                        statcast_json[key] = None
                    elif hasattr(value, 'isoformat'):  # Handle timestamps
                        statcast_json[key] = value.isoformat()
                    elif hasattr(value, 'item'):  # Handle numpy types
                        statcast_json[key] = value.item()
                
                # Extract key fields for indexing
                game_pk = statcast_json.get('game_pk')
                play_id = statcast_json.get('play_id') or 0
                pitch_number = statcast_json.get('pitch_number') or 0
                at_bat_number = statcast_json.get('at_bat_number') or 0
                inning = statcast_json.get('inning') or 0
                pitch_id = f"{game_pk}_{play_id}_{pitch_number}_{at_bat_number}_{inning}"
                
                # Handle game_date conversion properly
                raw_game_date = statcast_json.get('game_date')
                if raw_game_date is not None:
                    game_date = self._convert_to_date(raw_game_date)
                else:
                    game_date = None
                    
                batter_id = statcast_json.get('batter')
                pitcher_id = statcast_json.get('pitcher')
                
                try:
                    # Insert query with proper conflict handling
                    cursor.execute("""
                        INSERT INTO statcast_pitches (
                            game_pk, pitch_id, game_date, batter_id, pitcher_id,
                            statcast_data, pitch_type, release_speed, events,
                            launch_speed, launch_angle, hit_distance_sc
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (pitch_id) DO UPDATE SET
                            statcast_data = EXCLUDED.statcast_data,
                            created_at = NOW()
                    """, (
                        game_pk, pitch_id, game_date, batter_id, pitcher_id,
                        json.dumps(statcast_json),
                        statcast_json.get('pitch_type'),
                        statcast_json.get('release_speed'),
                        statcast_json.get('events'),
                        statcast_json.get('launch_speed'),
                        statcast_json.get('launch_angle'),
                        statcast_json.get('hit_distance_sc')
                    ))
                    
                    records_inserted += 1
                    
                except Exception as record_error:
                    logger.warning(f"Failed to insert record: {str(record_error)[:200]}")
                    continue
            
            conn.commit()
            logger.info(f"✅ Successfully stored {records_inserted} records for {target_date}")
            return records_inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Batch storage failed for {target_date}: {str(e)}")
            return 0
        finally:
            cursor.close()
    
    def collect_single_date(self, target_date: date, conn) -> bool:
        """Collect data for a single date"""
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            logger.info(f"🎯 Collecting data for {date_str}")
            
            # Get data from Baseball Savant
            data = pyb.statcast(start_dt=date_str, end_dt=date_str)
            
            if data.empty:
                logger.info(f"📅 No games on {date_str}")
                return True
            
            # Store in database
            records_stored = self.store_statcast_batch(conn, data, date_str)
            
            if records_stored > 0:
                logger.info(f"✅ {date_str}: Stored {records_stored} records")
                return True
            else:
                logger.error(f"❌ {date_str}: Failed to store records")
                return False
                
        except Exception as e:
            logger.error(f"❌ {date_str}: Collection error - {str(e)}")
            return False
    
    def get_current_db_stats(self, conn) -> Dict:
        """Get current database statistics"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_pitches,
                    COUNT(DISTINCT game_pk) as unique_games,
                    COUNT(DISTINCT batter_id) as unique_batters,
                    MIN(game_date) as earliest_date,
                    MAX(game_date) as latest_date
                FROM statcast_pitches
            """)
            
            row = cursor.fetchone()
            return {
                'total_pitches': row[0] or 0,
                'unique_games': row[1] or 0,
                'unique_batters': row[2] or 0,
                'earliest_date': row[3].isoformat() if row[3] else None,
                'latest_date': row[4].isoformat() if row[4] else None
            }
        finally:
            cursor.close()
    
    def load_progress(self) -> Dict:
        """Load existing progress"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_dates': [],
            'failed_dates': [],
            'total_records_added': 0,
            'last_update': None
        }
    
    def save_progress(self, progress: Dict):
        """Save progress to file"""
        progress['last_update'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def run_emergency_backfill(self):
        """Run the emergency backfill process"""
        logger.info("🚨 STARTING EMERGENCY 2025 SEASON BACKFILL")
        logger.info("=" * 60)
        
        # Get database connection
        conn = self.get_db_connection()
        if not conn:
            logger.error("❌ Cannot connect to database - aborting")
            return False
        
        try:
            # Get current database state
            initial_stats = self.get_current_db_stats(conn)
            logger.info(f"📊 Initial DB: {initial_stats['total_pitches']:,} pitches, {initial_stats['unique_games']} games")
            logger.info(f"📅 Current range: {initial_stats['earliest_date']} to {initial_stats['latest_date']}")
            
            # Load progress
            progress = self.load_progress()
            
            # Generate list of all missing dates
            all_missing_dates = []
            for start_date, end_date in self.missing_ranges:
                current = start_date
                while current <= end_date:
                    date_str = current.strftime('%Y-%m-%d')
                    if date_str not in progress['completed_dates']:
                        all_missing_dates.append(current)
                    current += timedelta(days=1)
            
            logger.info(f"🎯 Processing {len(all_missing_dates)} missing dates")
            
            successful = 0
            failed = 0
            
            for i, target_date in enumerate(all_missing_dates, 1):
                date_str = target_date.strftime('%Y-%m-%d')
                
                logger.info(f"\\n[{i}/{len(all_missing_dates)}] Processing {date_str}")
                
                success = self.collect_single_date(target_date, conn)
                
                if success:
                    successful += 1
                    progress['completed_dates'].append(date_str)
                    if date_str in progress['failed_dates']:
                        progress['failed_dates'].remove(date_str)
                else:
                    failed += 1
                    if date_str not in progress['failed_dates']:
                        progress['failed_dates'].append(date_str)
                
                # Save progress and show stats every 10 dates
                if i % 10 == 0:
                    self.save_progress(progress)
                    current_stats = self.get_current_db_stats(conn)
                    added_records = current_stats['total_pitches'] - initial_stats['total_pitches']
                    
                    logger.info(f"📈 Progress: {successful} successful, {failed} failed")
                    logger.info(f"📊 Added {added_records:,} records so far")
                    logger.info(f"💾 Progress saved to {self.progress_file}")
                
                # Brief pause to avoid overwhelming the source
                time.sleep(1)
            
            # Final summary
            final_stats = self.get_current_db_stats(conn)
            total_added = final_stats['total_pitches'] - initial_stats['total_pitches']
            
            self.save_progress(progress)
            
            logger.info("\\n" + "=" * 60)
            logger.info("🎉 EMERGENCY BACKFILL COMPLETE")
            logger.info("=" * 60)
            logger.info(f"✅ Successful dates: {successful}")
            logger.info(f"❌ Failed dates: {failed}")
            logger.info(f"📊 Total records added: {total_added:,}")
            logger.info(f"📊 Final DB: {final_stats['total_pitches']:,} pitches, {final_stats['unique_games']} games")
            logger.info(f"📅 New range: {final_stats['earliest_date']} to {final_stats['latest_date']}")
            
            if failed > 0:
                logger.warning(f"⚠️ {failed} dates failed - check logs")
                logger.warning(f"Failed dates: {progress['failed_dates']}")
            
            return failed == 0
            
        finally:
            conn.close()

def main():
    """Main execution"""
    collector = EmergencyBackfillCollector()
    success = collector.run_emergency_backfill()
    
    if success:
        print("\\n🎉 ALL DATA COLLECTED SUCCESSFULLY!")
        print("The database now has complete 2025 season coverage.")
        print("League averages will be accurate and Aaron Judge will have all his data.")
    else:
        print("\\n⚠️ Some data collection failed - check logs and retry")
    
    return success

if __name__ == "__main__":
    main()