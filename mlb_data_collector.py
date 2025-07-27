#!/usr/bin/env python3
"""
MLB Data Collection Script
=========================

Collects data from MLB Stats API and populates database tables for:
- Daily games with probable pitchers
- Team rosters
- Game lineups
- Teams information

Based on our API testing, we know the data structure from the MLB Stats API.
"""
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, date
from typing import List, Dict, Any
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLBDataCollector:
    """Collects and stores MLB data from the Stats API"""
    
    def __init__(self, db_url: str = "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data"):
        self.db_url = db_url
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StatEdge-Analytics/1.0 (Baseball Analytics Platform)'
        })
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def collect_teams(self, season: int = 2025) -> bool:
        """Collect all MLB teams for the season"""
        logger.info(f"Collecting teams for season {season}...")
        
        try:
            # Get teams from API
            url = f"{self.base_url}/teams?sportId=1&season={season}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            teams = data.get('teams', [])
            
            if not teams:
                logger.warning("No teams found in API response")
                return False
            
            # Store in database
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Clear existing teams for this season
            cursor.execute("DELETE FROM mlb_teams WHERE season = %s", (season,))
            
            insert_sql = """
            INSERT INTO mlb_teams (
                team_id, name, abbreviation, team_code, team_name, location_name,
                franchise_name, club_name, league_id, league_name, division_id,
                division_name, venue_id, venue_name, first_year_of_play, active, season
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            for team in teams:
                try:
                    cursor.execute(insert_sql, (
                        team['id'],
                        team['name'],
                        team.get('abbreviation', ''),
                        team.get('teamCode', ''),
                        team.get('teamName', ''),
                        team.get('locationName', ''),
                        team.get('franchiseName', ''),
                        team.get('clubName', ''),
                        team.get('league', {}).get('id'),
                        team.get('league', {}).get('name'),
                        team.get('division', {}).get('id'),
                        team.get('division', {}).get('name'),
                        team.get('venue', {}).get('id'),
                        team.get('venue', {}).get('name'),
                        team.get('firstYearOfPlay'),
                        team.get('active', True),
                        season
                    ))
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert team {team.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Collected {inserted_count} teams")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to collect teams: {e}")
            return False
    
    def collect_rosters(self, season: int = 2025) -> bool:
        """Collect current active rosters for all teams"""
        logger.info(f"Collecting rosters for season {season}...")
        
        try:
            # First get all teams
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT team_id FROM mlb_teams WHERE season = %s", (season,))
            teams = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not teams:
                logger.warning("No teams found in database - run collect_teams first")
                return False
            
            total_players = 0
            
            for team in teams:
                team_id = team['team_id']
                
                # Get roster from API
                url = f"{self.base_url}/teams/{team_id}/roster?rosterType=active"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                roster = data.get('roster', [])
                
                if roster:
                    total_players += self._store_roster(team_id, roster, season)
            
            logger.info(f"✅ Collected {total_players} players across all teams")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to collect rosters: {e}")
            return False
    
    def _store_roster(self, team_id: int, roster: List[Dict], season: int) -> int:
        """Store a team's roster in the database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing roster for this team and season
        cursor.execute("DELETE FROM mlb_players WHERE team_id = %s AND season = %s", (team_id, season))
        
        insert_sql = """
        INSERT INTO mlb_players (
            player_id, team_id, full_name, jersey_number, position_code,
            position_name, position_type, position_abbreviation, status_code,
            status_description, roster_type, season
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        inserted_count = 0
        for player in roster:
            try:
                person = player.get('person', {})
                position = player.get('position', {})
                status = player.get('status', {})
                
                cursor.execute(insert_sql, (
                    person.get('id'),
                    team_id,
                    person.get('fullName', ''),
                    player.get('jerseyNumber'),
                    position.get('code'),
                    position.get('name'),
                    position.get('type'),
                    position.get('abbreviation'),
                    status.get('code'),
                    status.get('description'),
                    'active',
                    season
                ))
                inserted_count += 1
            except Exception as e:
                logger.warning(f"Failed to insert player {person.get('fullName', 'Unknown')}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return inserted_count
    
    def collect_daily_games(self, game_date: str = None) -> bool:
        """Collect games for a specific date with lineups and probable pitchers"""
        if not game_date:
            game_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Collecting games for {game_date}...")
        
        try:
            # Get schedule with hydrated data
            url = f"{self.base_url}/schedule?sportId=1&date={game_date}&hydrate=probablePitcher,linescore"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            total_games = data.get('totalGames', 0)
            
            if total_games == 0:
                logger.info(f"No games found for {game_date}")
                return True
            
            games_processed = 0
            for date_info in data.get('dates', []):
                for game in date_info.get('games', []):
                    if self._store_game(game):
                        games_processed += 1
                        
                        # Collect lineups for completed/in-progress games
                        if game.get('status', {}).get('statusCode') in ['F', 'I', 'W']:
                            self._collect_game_lineups(game['gamePk'])
            
            logger.info(f"✅ Processed {games_processed} games for {game_date}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to collect daily games: {e}")
            return False
    
    def _store_game(self, game: Dict) -> bool:
        """Store a single game in the database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Extract game data
            game_pk = game['gamePk']
            teams = game.get('teams', {})
            home_team = teams.get('home', {})
            away_team = teams.get('away', {})
            status = game.get('status', {})
            venue = game.get('venue', {})
            
            # Store game details
            insert_sql = """
            INSERT INTO mlb_game_details (
                game_pk, game_guid, game_type, season, game_date, official_date,
                status_code, detailed_state, abstract_game_state,
                home_team_id, home_team_name, home_score, home_wins, home_losses, home_is_winner,
                away_team_id, away_team_name, away_score, away_wins, away_losses, away_is_winner,
                venue_id, venue_name, series_number, game_number, double_header
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_pk) DO UPDATE SET
                status_code = EXCLUDED.status_code,
                detailed_state = EXCLUDED.detailed_state,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_sql, (
                game_pk,
                game.get('gameGuid'),
                game.get('gameType'),
                int(game.get('season', 2025)),
                datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00')),
                datetime.strptime(game['officialDate'], '%Y-%m-%d').date(),
                status.get('statusCode'),
                status.get('detailedState'),
                status.get('abstractGameState'),
                home_team.get('team', {}).get('id'),
                home_team.get('team', {}).get('name'),
                home_team.get('score'),
                home_team.get('leagueRecord', {}).get('wins'),
                home_team.get('leagueRecord', {}).get('losses'),
                home_team.get('isWinner'),
                away_team.get('team', {}).get('id'),
                away_team.get('team', {}).get('name'),
                away_team.get('score'),
                away_team.get('leagueRecord', {}).get('wins'),
                away_team.get('leagueRecord', {}).get('losses'),
                away_team.get('isWinner'),
                venue.get('id'),
                venue.get('name'),
                home_team.get('seriesNumber'),
                game.get('gameNumber', 1),
                game.get('doubleHeader', 'N')
            ))
            
            # Store probable pitchers
            for team_type, team_data in [('home', home_team), ('away', away_team)]:
                probable_pitcher = team_data.get('probablePitcher')
                if probable_pitcher:
                    pitcher_sql = """
                    INSERT INTO mlb_probable_pitchers (
                        game_pk, team_id, team_type, pitcher_id, pitcher_name
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (game_pk, team_id, pitcher_id) DO NOTHING
                    """
                    cursor.execute(pitcher_sql, (
                        game_pk,
                        team_data.get('team', {}).get('id'),
                        team_type,
                        probable_pitcher.get('id'),
                        probable_pitcher.get('fullName')
                    ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to store game {game.get('gamePk', 'Unknown')}: {e}")
            return False
    
    def _collect_game_lineups(self, game_pk: int) -> bool:
        """Collect lineup data for a specific game"""
        try:
            url = f"{self.base_url}/game/{game_pk}/boxscore"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            teams = data.get('teams', {})
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Clear existing lineups for this game
            cursor.execute("DELETE FROM mlb_game_lineups WHERE game_pk = %s", (game_pk,))
            
            for team_type, team_data in teams.items():
                team_id = team_data.get('team', {}).get('id')
                batting_order = team_data.get('battingOrder', [])
                players = team_data.get('players', {})
                
                for order, player_id_key in enumerate(batting_order, 1):
                    # Handle both string format ("ID12345") and integer format (12345)
                    if isinstance(player_id_key, str):
                        player_id = int(player_id_key.replace('ID', ''))
                        player_lookup_key = player_id_key
                    else:
                        player_id = int(player_id_key)
                        player_lookup_key = f"ID{player_id}"
                    
                    player_data = players.get(player_lookup_key, {})
                    person = player_data.get('person', {})
                    position = player_data.get('position', {})
                    
                    lineup_sql = """
                    INSERT INTO mlb_game_lineups (
                        game_pk, team_id, team_type, player_id, batting_order,
                        position_code, position_name, jersey_number, full_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (game_pk, team_id, player_id) DO NOTHING
                    """
                    
                    cursor.execute(lineup_sql, (
                        game_pk,
                        team_id,
                        team_type,
                        player_id,
                        order,
                        position.get('code'),
                        position.get('name'),
                        player_data.get('jerseyNumber'),
                        person.get('fullName')
                    ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to collect lineups for game {game_pk}: {e}")
            return False

def main():
    """Main function to run all data collection"""
    collector = MLBDataCollector()
    
    logger.info("🚀 Starting MLB Data Collection")
    
    # Step 1: Collect teams
    logger.info("📋 Step 1: Collecting teams...")
    teams_success = collector.collect_teams()
    
    if not teams_success:
        logger.error("❌ Failed to collect teams - stopping")
        return False
    
    # Step 2: Collect rosters
    logger.info("👥 Step 2: Collecting rosters...")
    rosters_success = collector.collect_rosters()
    
    # Step 3: Collect daily games
    logger.info("⚾ Step 3: Collecting daily games...")
    games_success = collector.collect_daily_games()
    
    # Summary
    logger.info("📊 Collection Summary:")
    logger.info(f"  Teams: {'✅' if teams_success else '❌'}")
    logger.info(f"  Rosters: {'✅' if rosters_success else '❌'}")
    logger.info(f"  Games: {'✅' if games_success else '❌'}")
    
    if teams_success and rosters_success and games_success:
        logger.info("🎉 All data collection completed successfully!")
        return True
    else:
        logger.warning("⚠️ Some data collection failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)