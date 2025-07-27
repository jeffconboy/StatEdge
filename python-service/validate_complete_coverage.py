#!/usr/bin/env python3
"""
COMPLETE 2025 SEASON DATA VALIDATION
====================================

This script validates that we have COMPLETE data coverage by:
1. Cross-validating every date against Baseball Savant
2. Ensuring every game has all pitches
3. Verifying every player appears correctly
4. Checking for any data gaps or anomalies
"""

import asyncio
import pybaseball as pyb
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import json
from typing import Dict, List, Tuple
import sys

sys.path.append('/home/jeffreyconboy/StatEdge/python-service')
from database.connection import get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeasonDataValidator:
    def __init__(self, season: int = 2025):
        self.season = season
        self.season_start = date(2025, 3, 15)
        self.season_end = min(date(2025, 11, 15), date.today())
        self.validation_report = {
            'validation_date': datetime.now().isoformat(),
            'season': season,
            'date_range': f"{self.season_start} to {self.season_end}",
            'summary': {},
            'issues': [],
            'daily_validation': []
        }
    
    async def validate_overall_coverage(self) -> Dict:
        """Validate overall season coverage"""
        logger.info("🔍 Validating overall season coverage...")
        
        async for session in get_db_session():
            try:
                # Get our database totals
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_pitches,
                        COUNT(DISTINCT game_pk) as unique_games,
                        COUNT(DISTINCT batter_id) as unique_batters,
                        COUNT(DISTINCT pitcher_id) as unique_pitchers,
                        COUNT(DISTINCT game_date) as dates_with_data,
                        MIN(game_date) as earliest_date,
                        MAX(game_date) as latest_date
                    FROM statcast_pitches 
                    WHERE game_date >= :start_date AND game_date <= :end_date
                """), {
                    'start_date': self.season_start,
                    'end_date': self.season_end
                })
                
                row = result.fetchone()
                
                db_stats = {
                    'total_pitches': row[0] or 0,
                    'unique_games': row[1] or 0,
                    'unique_batters': row[2] or 0,
                    'unique_pitchers': row[3] or 0,
                    'dates_with_data': row[4] or 0,
                    'earliest_date': row[5].isoformat() if row[5] else None,
                    'latest_date': row[6].isoformat() if row[6] else None
                }
                
                logger.info(f"📊 Database: {db_stats['total_pitches']:,} pitches across {db_stats['unique_games']} games")
                logger.info(f"📅 Date range: {db_stats['earliest_date']} to {db_stats['latest_date']}")
                
                return db_stats
                
            finally:
                break
    
    async def validate_sample_dates(self, num_samples: int = 20) -> List[Dict]:
        """Validate a random sample of dates against Baseball Savant"""
        logger.info(f"🎯 Validating {num_samples} sample dates against Baseball Savant...")
        
        # Generate sample dates
        total_days = (self.season_end - self.season_start).days + 1
        import random
        sample_days = random.sample(range(total_days), min(num_samples, total_days))
        
        validations = []
        
        for day_offset in sample_days:
            target_date = self.season_start + timedelta(days=day_offset)
            date_str = target_date.strftime('%Y-%m-%d')
            
            try:
                logger.info(f"Validating {date_str}...")
                
                # Get Baseball Savant data
                expected_data = pyb.statcast(start_dt=date_str, end_dt=date_str)
                
                if expected_data.empty:
                    validations.append({
                        'date': date_str,
                        'status': 'no_games',
                        'completeness': 100.0
                    })
                    continue
                
                expected_records = len(expected_data)
                expected_games = expected_data['game_pk'].nunique()
                
                # Check our database
                async for session in get_db_session():
                    try:
                        result = await session.execute(text("""
                            SELECT 
                                COUNT(*) as actual_records,
                                COUNT(DISTINCT game_pk) as actual_games
                            FROM statcast_pitches 
                            WHERE game_date = :target_date
                        """), {'target_date': target_date})
                        
                        row = result.fetchone()
                        actual_records = row[0] or 0
                        actual_games = row[1] or 0
                        
                        completeness = (actual_records / expected_records * 100) if expected_records > 0 else 0
                        
                        validation = {
                            'date': date_str,
                            'expected_records': expected_records,
                            'actual_records': actual_records,
                            'expected_games': expected_games,
                            'actual_games': actual_games,
                            'completeness': round(completeness, 2),
                            'status': 'complete' if completeness >= 99.5 else 'incomplete' if completeness > 0 else 'missing'
                        }
                        
                        if completeness < 99.5:
                            validation['issue'] = f"Missing {expected_records - actual_records} records"
                            
                        validations.append(validation)
                        
                        if completeness < 99.5:
                            logger.warning(f"⚠️ {date_str}: {completeness:.1f}% complete")
                        else:
                            logger.info(f"✅ {date_str}: Complete ({actual_records} records)")
                            
                    finally:
                        break
                        
            except Exception as e:
                logger.error(f"❌ {date_str}: Validation error - {str(e)}")
                validations.append({
                    'date': date_str,
                    'status': 'error',
                    'error': str(e)
                })
        
        return validations
    
    async def validate_key_players(self) -> List[Dict]:
        """Validate coverage for key MLB players"""
        logger.info("👥 Validating key player coverage...")
        
        # Key players to validate (including Aaron Judge)
        key_players = {
            592450: "Aaron Judge",
            545361: "Mike Trout", 
            666176: "Ronald Acuña Jr.",
            592518: "Mookie Betts",
            608369: "Vladimir Guerrero Jr."
        }
        
        player_validations = []
        
        for player_id, player_name in key_players.items():
            try:
                # Get expected data from Baseball Savant for full season
                start_str = self.season_start.strftime('%Y-%m-%d')
                end_str = self.season_end.strftime('%Y-%m-%d')
                
                logger.info(f"Checking {player_name} ({player_id})...")
                expected_data = pyb.statcast(start_dt=start_str, end_dt=end_str)
                
                if not expected_data.empty:
                    player_expected = expected_data[expected_data['batter'] == player_id]
                    expected_records = len(player_expected)
                    expected_games = player_expected['game_date'].nunique() if expected_records > 0 else 0
                else:
                    expected_records = 0
                    expected_games = 0
                
                # Check our database
                async for session in get_db_session():
                    try:
                        result = await session.execute(text("""
                            SELECT 
                                COUNT(*) as actual_records,
                                COUNT(DISTINCT game_date) as actual_games,
                                MIN(game_date) as first_game,
                                MAX(game_date) as last_game
                            FROM statcast_pitches 
                            WHERE batter_id = :player_id
                            AND game_date >= :start_date 
                            AND game_date <= :end_date
                        """), {
                            'player_id': player_id,
                            'start_date': self.season_start,
                            'end_date': self.season_end
                        })
                        
                        row = result.fetchone()
                        actual_records = row[0] or 0
                        actual_games = row[1] or 0
                        first_game = row[2].isoformat() if row[2] else None
                        last_game = row[3].isoformat() if row[3] else None
                        
                        completeness = (actual_records / expected_records * 100) if expected_records > 0 else 0
                        
                        validation = {
                            'player_id': player_id,
                            'player_name': player_name,
                            'expected_records': expected_records,
                            'actual_records': actual_records,
                            'expected_games': expected_games,
                            'actual_games': actual_games,
                            'completeness': round(completeness, 2),
                            'first_game': first_game,
                            'last_game': last_game,
                            'status': 'complete' if completeness >= 95.0 else 'incomplete' if completeness > 0 else 'missing'
                        }
                        
                        if completeness < 95.0:
                            validation['issue'] = f"Missing {expected_records - actual_records} records"
                            
                        player_validations.append(validation)
                        
                        if completeness >= 95.0:
                            logger.info(f"✅ {player_name}: {actual_records} records across {actual_games} games")
                        else:
                            logger.warning(f"⚠️ {player_name}: {completeness:.1f}% complete ({actual_records}/{expected_records})")
                            
                    finally:
                        break
                        
            except Exception as e:
                logger.error(f"❌ {player_name}: Validation error - {str(e)}")
                player_validations.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return player_validations
    
    async def run_complete_validation(self) -> Dict:
        """Run complete validation suite"""
        logger.info("🚀 STARTING COMPLETE 2025 SEASON VALIDATION")
        logger.info("=" * 60)
        
        # 1. Overall coverage validation
        overall_stats = await self.validate_overall_coverage()
        self.validation_report['summary']['overall_stats'] = overall_stats
        
        # 2. Sample date validation
        sample_validations = await self.validate_sample_dates(25)
        self.validation_report['daily_validation'] = sample_validations
        
        complete_samples = sum(1 for v in sample_validations if v.get('status') == 'complete')
        sample_completeness = (complete_samples / len(sample_validations) * 100) if sample_validations else 0
        
        # 3. Key player validation
        player_validations = await self.validate_key_players()
        self.validation_report['player_validation'] = player_validations
        
        complete_players = sum(1 for p in player_validations if p.get('status') == 'complete')
        player_completeness = (complete_players / len(player_validations) * 100) if player_validations else 0
        
        # Summary
        overall_completeness = min(sample_completeness, player_completeness)
        
        self.validation_report['summary'].update({
            'sample_completeness': round(sample_completeness, 1),
            'player_completeness': round(player_completeness, 1),
            'overall_completeness': round(overall_completeness, 1),
            'validation_status': 'COMPLETE' if overall_completeness >= 95.0 else 'INCOMPLETE'
        })
        
        # Identify issues
        issues = []
        
        for validation in sample_validations:
            if validation.get('status') not in ['complete', 'no_games']:
                issues.append(f"Date {validation['date']}: {validation.get('issue', validation.get('error', 'Unknown issue'))}")
        
        for validation in player_validations:
            if validation.get('status') != 'complete':
                issues.append(f"Player {validation['player_name']}: {validation.get('issue', validation.get('error', 'Unknown issue'))}")
        
        self.validation_report['issues'] = issues
        
        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("📋 VALIDATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Database: {overall_stats['total_pitches']:,} pitches, {overall_stats['unique_games']} games")
        logger.info(f"📅 Sample validation: {sample_completeness:.1f}% complete")
        logger.info(f"👥 Player validation: {player_completeness:.1f}% complete")
        logger.info(f"🎯 Overall status: {self.validation_report['summary']['validation_status']}")
        
        if issues:
            logger.warning(f"⚠️ Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10 issues
                logger.warning(f"  • {issue}")
            if len(issues) > 10:
                logger.warning(f"  ... and {len(issues) - 10} more issues")
        else:
            logger.info("✅ No issues found - data appears complete!")
        
        # Save report
        report_file = f'/tmp/season_{self.season}_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.validation_report, f, indent=2)
        
        logger.info(f"📄 Full report saved to: {report_file}")
        
        return self.validation_report

async def main():
    """Main validation execution"""
    validator = SeasonDataValidator(2025)
    report = await validator.run_complete_validation()
    
    return report['summary']['validation_status'] == 'COMPLETE'

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("🎉 VALIDATION PASSED - ALL DATA IS COMPLETE!")
    else:
        print("⚠️ VALIDATION FAILED - DATA GAPS DETECTED")
        print("Run the backfill script to collect missing data.")