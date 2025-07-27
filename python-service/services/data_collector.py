import pybaseball as pyb
import pandas as pd
import json
import asyncio
import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from database.connection import get_db_session, get_redis

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.redis = None
    
    def _convert_to_date(self, date_value):
        """Convert various date formats to Python date object"""
        if date_value is None:
            return None
        
        # If already a date object, return as is
        if isinstance(date_value, date):
            return date_value
        
        # If datetime object, extract date
        if isinstance(date_value, datetime):
            return date_value.date()
        
        # If string, parse it
        if isinstance(date_value, str):
            try:
                # Handle common date formats from PyBaseball
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
    
    async def init_redis(self):
        if self.redis is None:
            self.redis = await get_redis()
    
    async def collect_daily_data(self, date: Optional[str] = None):
        """Collect comprehensive daily data"""
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Collecting data for {date}")
        
        try:
            # 1. Collect Statcast data
            await self.collect_statcast_data(date)
            
            # 2. Collect FanGraphs data (if needed)
            await self.collect_fangraphs_data()
            
            # 3. Collect MLB API lineup data
            await self.collect_mlb_lineups(date)
            
            logger.info(f"Data collection completed for {date}")
            
        except Exception as e:
            logger.error(f"Error in daily data collection: {str(e)}")
            raise
    
    async def collect_statcast_data(self, date: str):
        """Collect ALL Statcast fields for a given date"""
        try:
            logger.info(f"Collecting Statcast data for {date}")
            
            # PyBaseball expects string dates, not date objects
            # Validate the date format first
            date_obj = self._convert_to_date(date)
            if date_obj is None:
                raise ValueError(f"Invalid date format: {date}")
            
            # Convert back to string format that PyBaseball expects
            date_str = date_obj.strftime('%Y-%m-%d')
            
            # Get Statcast data using pybaseball
            statcast_data = pyb.statcast(start_dt=date_str, end_dt=date_str)
            
            if statcast_data.empty:
                logger.info(f"No Statcast data found for {date}")
                return
            
            # Store in database
            async for session in get_db_session():
                await self.store_statcast_data(session, statcast_data)
                break
                
            logger.info(f"Stored {len(statcast_data)} Statcast records for {date}")
            
        except Exception as e:
            logger.error(f"Error collecting Statcast data: {str(e)}")
            raise
    
    async def store_statcast_data(self, session: AsyncSession, df: pd.DataFrame):
        """Store ALL Statcast fields in database"""
        try:
            records_processed = 0
            records_inserted = 0
            
            logger.info(f"Starting to store {len(df)} Statcast records...")
            
            for _, row in df.iterrows():
                records_processed += 1
                
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
                # Create more unique pitch_id using multiple fields to avoid conflicts
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
                    # Insert query
                    query = text("""
                        INSERT INTO statcast_pitches (
                            game_pk, pitch_id, game_date, batter_id, pitcher_id,
                            statcast_data, pitch_type, release_speed, events,
                            launch_speed, launch_angle, hit_distance_sc
                        ) VALUES (
                            :game_pk, :pitch_id, :game_date, :batter_id, :pitcher_id,
                            :statcast_data, :pitch_type, :release_speed, :events,
                            :launch_speed, :launch_angle, :hit_distance_sc
                        ) ON CONFLICT (pitch_id) DO UPDATE SET
                            statcast_data = EXCLUDED.statcast_data,
                            updated_at = NOW()
                    """)
                    
                    await session.execute(query, {
                        'game_pk': game_pk,
                        'pitch_id': pitch_id,
                        'game_date': game_date,
                        'batter_id': batter_id,
                        'pitcher_id': pitcher_id,
                        'statcast_data': json.dumps(statcast_json),
                        'pitch_type': statcast_json.get('pitch_type'),
                        'release_speed': statcast_json.get('release_speed'),
                        'events': statcast_json.get('events'),
                        'launch_speed': statcast_json.get('launch_speed'),
                        'launch_angle': statcast_json.get('launch_angle'),
                        'hit_distance_sc': statcast_json.get('hit_distance_sc')
                    })
                    
                    records_inserted += 1
                    
                    # Log progress every 100 records
                    if records_processed % 100 == 0:
                        logger.info(f"Processed {records_processed}/{len(df)} records, inserted {records_inserted}")
                        
                except Exception as record_error:
                    logger.warning(f"Failed to insert record {records_processed}: {str(record_error)[:200]}")
                    continue  # Skip this record and continue with the next
            
            await session.commit()
            logger.info(f"Storage complete: {records_inserted} records inserted out of {records_processed} processed")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing Statcast data: {str(e)}")
            raise
    
    async def collect_fangraphs_data(self, season: int = None):
        """Collect ALL FanGraphs statistics"""
        if season is None:
            season = datetime.now().year
            
        try:
            logger.info(f"Collecting FanGraphs data for {season}")
            
            # Collect batting stats with ALL fields - CORRECTED PARAMETERS
            logger.info(f"Calling PyBaseball batting_stats for {season}...")
            batting_data = pyb.batting_stats(start_season=season, end_season=season, qual=0)
            logger.info(f"PyBaseball batting returned: {len(batting_data)} players with {len(batting_data.columns)} columns")
            
            # Collect pitching stats with ALL fields - CORRECTED PARAMETERS
            logger.info(f"Calling PyBaseball pitching_stats for {season}...")
            pitching_data = pyb.pitching_stats(start_season=season, end_season=season, qual=0)
            logger.info(f"PyBaseball pitching returned: {len(pitching_data)} players with {len(pitching_data.columns)} columns")
            
            # Store in database
            async for session in get_db_session():
                await self.store_fangraphs_data(session, batting_data, 'batting', season)
                await self.store_fangraphs_data(session, pitching_data, 'pitching', season)
                break
                
            logger.info(f"Stored FanGraphs data for {season}")
            
        except Exception as e:
            logger.error(f"Error collecting FanGraphs data: {str(e)}")
            raise
    
    async def store_fangraphs_data(self, session: AsyncSession, df: pd.DataFrame, stat_type: str, season: int):
        """Store ALL FanGraphs fields in database"""
        try:
            table_name = f'fangraphs_{stat_type}'
            
            for _, row in df.iterrows():
                # Convert entire row to JSON - preserve ALL 300+ fields
                stats_json = row.to_dict()
                
                # Handle NaN values
                for key, value in stats_json.items():
                    if pd.isna(value):
                        stats_json[key] = None
                
                # Get player name for lookup
                player_name = stats_json.get('Name', '')
                
                if not player_name:
                    continue
                
                # Find or create player
                player_query = text("SELECT id FROM players WHERE name ILIKE :name LIMIT 1")
                result = await session.execute(player_query, {'name': f'%{player_name}%'})
                player_row = result.fetchone()
                
                if not player_row:
                    # Create new player entry with unique mlb_id using a negative value
                    # This ensures no conflicts while preserving ability to update with real MLB ID later
                    next_temp_id = await session.execute(text("SELECT COALESCE(MIN(mlb_id), 0) - 1 FROM players WHERE mlb_id < 0"))
                    temp_mlb_id = next_temp_id.fetchone()[0] or -1
                    
                    insert_player = text("""
                        INSERT INTO players (name, mlb_id, active) 
                        VALUES (:name, :mlb_id, true) 
                        RETURNING id
                    """)
                    result = await session.execute(insert_player, {
                        'name': player_name,
                        'mlb_id': temp_mlb_id  # Unique temporary ID
                    })
                    player_id = result.fetchone()[0]
                else:
                    player_id = player_row[0]
                
                # Insert FanGraphs data
                if stat_type == 'batting':
                    # Check if record already exists
                    check_query = text("SELECT id FROM fangraphs_batting WHERE player_id = :player_id AND season = :season AND split_type = :split_type")
                    existing = await session.execute(check_query, {'player_id': player_id, 'season': season, 'split_type': 'season'})
                    existing_record = existing.fetchone()
                    
                    if existing_record:
                        # Update existing record
                        query = text("""
                            UPDATE fangraphs_batting SET
                                batting_stats = :batting_stats,
                                games_played = :games_played,
                                plate_appearances = :plate_appearances,
                                avg = :avg, obp = :obp, slg = :slg, ops = :ops,
                                woba = :woba, wrc_plus = :wrc_plus, war_fg = :war_fg
                            WHERE player_id = :player_id AND season = :season AND split_type = :split_type
                        """)
                    else:
                        # Insert new record
                        query = text("""
                            INSERT INTO fangraphs_batting (
                                player_id, season, split_type, batting_stats,
                                games_played, plate_appearances, avg, obp, slg, ops, woba, wrc_plus, war_fg
                            ) VALUES (
                                :player_id, :season, :split_type, :batting_stats,
                                :games_played, :plate_appearances, :avg, :obp, :slg, :ops, :woba, :wrc_plus, :war_fg
                            )
                        """)
                    
                    await session.execute(query, {
                        'player_id': player_id,
                        'season': season,
                        'split_type': 'season',
                        'batting_stats': json.dumps(stats_json),
                        'games_played': stats_json.get('G', 0),
                        'plate_appearances': stats_json.get('PA', 0),
                        'avg': stats_json.get('AVG', 0),
                        'obp': stats_json.get('OBP', 0),
                        'slg': stats_json.get('SLG', 0),
                        'ops': stats_json.get('OPS', 0),
                        'woba': stats_json.get('wOBA', 0),
                        'wrc_plus': stats_json.get('wRC+', 0),
                        'war_fg': stats_json.get('WAR', 0)
                    })
                
                elif stat_type == 'pitching':
                    # Check if record already exists
                    check_query = text("SELECT id FROM fangraphs_pitching WHERE player_id = :player_id AND season = :season AND split_type = :split_type")
                    existing = await session.execute(check_query, {'player_id': player_id, 'season': season, 'split_type': 'season'})
                    existing_record = existing.fetchone()
                    
                    if existing_record:
                        # Update existing record
                        query = text("""
                            UPDATE fangraphs_pitching SET
                                pitching_stats = :pitching_stats,
                                games = :games, games_started = :games_started,
                                innings_pitched = :innings_pitched, era = :era,
                                whip = :whip, fip = :fip, war_fg = :war_fg
                            WHERE player_id = :player_id AND season = :season AND split_type = :split_type
                        """)
                    else:
                        # Insert new record
                        query = text("""
                            INSERT INTO fangraphs_pitching (
                                player_id, season, split_type, pitching_stats,
                                games, games_started, innings_pitched, era, whip, fip, war_fg
                            ) VALUES (
                                :player_id, :season, :split_type, :pitching_stats,
                                :games, :games_started, :innings_pitched, :era, :whip, :fip, :war_fg
                            )
                        """)
                    
                    await session.execute(query, {
                        'player_id': player_id,
                        'season': season,
                        'split_type': 'season',
                        'pitching_stats': json.dumps(stats_json),
                        'games': stats_json.get('G', 0),
                        'games_started': stats_json.get('GS', 0),
                        'innings_pitched': stats_json.get('IP', 0),
                        'era': stats_json.get('ERA', 0),
                        'whip': stats_json.get('WHIP', 0),
                        'fip': stats_json.get('FIP', 0),
                        'war_fg': stats_json.get('WAR', 0)
                    })
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing FanGraphs data: {str(e)}")
            raise
    
    async def collect_mlb_lineups(self, date: str):
        """Collect daily lineups from MLB API"""
        try:
            logger.info(f"Collecting MLB lineups for {date}")
            
            # Get schedule for the date
            schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
            response = requests.get(schedule_url)
            schedule_data = response.json()
            
            async for session in get_db_session():
                for game_date in schedule_data.get('dates', []):
                    for game in game_date.get('games', []):
                        await self.store_game_data(session, game, date)
                break
                
            logger.info(f"Stored lineup data for {date}")
            
        except Exception as e:
            logger.error(f"Error collecting MLB lineups: {str(e)}")
            raise
    
    async def store_game_data(self, session: AsyncSession, game_data: dict, date: str):
        """Store game and lineup data"""
        try:
            game_pk = game_data.get('gamePk')
            
            query = text("""
                INSERT INTO games (
                    game_pk, game_date, season, home_team, away_team, game_info, completed
                ) VALUES (
                    :game_pk, :game_date, :season, :home_team, :away_team, :game_info, :completed
                ) ON CONFLICT (game_pk) DO UPDATE SET
                    game_info = EXCLUDED.game_info,
                    completed = EXCLUDED.completed,
                    updated_at = NOW()
            """)
            
            # Convert date string to date object
            date_obj = self._convert_to_date(date)
            
            await session.execute(query, {
                'game_pk': game_pk,
                'game_date': date_obj,
                'season': datetime.now().year,
                'home_team': game_data.get('teams', {}).get('home', {}).get('team', {}).get('abbreviation'),
                'away_team': game_data.get('teams', {}).get('away', {}).get('team', {}).get('abbreviation'),
                'game_info': json.dumps(game_data),
                'completed': game_data.get('status', {}).get('codedGameState') == 'F'
            })
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing game data: {str(e)}")
            raise