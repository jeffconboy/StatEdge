from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from database.connection import get_db_session
from services.data_collector import DataCollector
from models.requests import DataCollectionRequest

router = APIRouter()

@router.post("/collect-data")
async def trigger_data_collection(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """Manually trigger data collection"""
    
    try:
        collector = DataCollector()
        
        if request.force_refresh or not request.date:
            # Run in background
            background_tasks.add_task(
                collector.collect_daily_data, 
                request.date
            )
            
            return {
                "message": "Data collection started",
                "date": request.date or "yesterday",
                "sources": request.data_sources,
                "status": "running"
            }
        else:
            # Run immediately for specific date
            await collector.collect_daily_data(request.date)
            
            return {
                "message": "Data collection completed",
                "date": request.date,
                "sources": request.data_sources,
                "status": "completed"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection error: {str(e)}")

@router.get("/database-stats")
async def get_database_statistics(
    session: AsyncSession = Depends(get_db_session)
):
    """Get statistics about data in the database"""
    
    try:
        stats = {}
        
        # Player count
        result = await session.execute(text("SELECT COUNT(*) FROM players"))
        stats["total_players"] = result.scalar()
        
        # Statcast records
        result = await session.execute(text("SELECT COUNT(*) FROM statcast_pitches"))
        stats["statcast_pitches"] = result.scalar()
        
        # FanGraphs records
        result = await session.execute(text("SELECT COUNT(*) FROM fangraphs_batting"))
        stats["fangraphs_batting_records"] = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM fangraphs_pitching"))
        stats["fangraphs_pitching_records"] = result.scalar()
        
        # Recent data
        result = await session.execute(text("""
            SELECT COUNT(*) FROM statcast_pitches 
            WHERE game_date >= CURRENT_DATE - INTERVAL '7 days'
        """))
        stats["recent_statcast_pitches"] = result.scalar()
        
        # Date ranges
        result = await session.execute(text("""
            SELECT MIN(game_date), MAX(game_date) 
            FROM statcast_pitches
        """))
        date_range = result.fetchone()
        if date_range and date_range[0]:
            stats["data_date_range"] = {
                "start": date_range[0].isoformat(),
                "end": date_range[1].isoformat()
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.get("/leaderboards/{stat_name}")
async def get_leaderboard(
    stat_name: str,
    limit: int = 10,
    min_pa: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    """Get leaderboards for any statistic"""
    
    try:
        # Map common stat names to JSONB paths
        stat_mappings = {
            "avg": "batting_stats->>'AVG'",
            "ops": "batting_stats->>'OPS'",
            "woba": "batting_stats->>'wOBA'",
            "wrc_plus": "batting_stats->>'wRC+'",
            "exit_velocity": "statcast_data->>'launch_speed'",
            "barrel_rate": "statcast_data->>'barrel_rate'",
            "era": "pitching_stats->>'ERA'",
            "fip": "pitching_stats->>'FIP'",
            "whip": "pitching_stats->>'WHIP'"
        }
        
        if stat_name in stat_mappings:
            jsonb_path = stat_mappings[stat_name]
            
            if "batting_stats" in jsonb_path:
                query = text(f"""
                    SELECT p.name, p.current_team, 
                           ({jsonb_path})::numeric as stat_value,
                           (fb.batting_stats->>'PA')::integer as plate_appearances
                    FROM players p
                    JOIN fangraphs_batting fb ON p.id = fb.player_id
                    WHERE (fb.batting_stats->>'PA')::integer >= :min_pa
                    AND {jsonb_path} IS NOT NULL
                    AND {jsonb_path} != ''
                    ORDER BY stat_value DESC
                    LIMIT :limit
                """)
                
            elif "pitching_stats" in jsonb_path:
                query = text(f"""
                    SELECT p.name, p.current_team,
                           ({jsonb_path})::numeric as stat_value,
                           (fp.pitching_stats->>'IP')::numeric as innings_pitched
                    FROM players p
                    JOIN fangraphs_pitching fp ON p.id = fp.player_id
                    WHERE (fp.pitching_stats->>'IP')::numeric >= 50
                    AND {jsonb_path} IS NOT NULL
                    AND {jsonb_path} != ''
                    ORDER BY stat_value {'ASC' if stat_name in ['era', 'whip', 'fip'] else 'DESC'}
                    LIMIT :limit
                """)
                
            else:  # Statcast data
                query = text(f"""
                    SELECT p.name, p.current_team,
                           AVG(({jsonb_path})::numeric) as stat_value,
                           COUNT(*) as pitch_count
                    FROM players p
                    JOIN statcast_pitches sp ON p.mlb_id = sp.batter_id
                    WHERE {jsonb_path} IS NOT NULL
                    AND {jsonb_path} != ''
                    AND sp.game_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY p.id, p.name, p.current_team
                    HAVING COUNT(*) >= 50
                    ORDER BY stat_value DESC
                    LIMIT :limit
                """)
            
            result = await session.execute(query, {"limit": limit, "min_pa": min_pa})
            
            leaderboard = []
            for i, row in enumerate(result.fetchall(), 1):
                leaderboard.append({
                    "rank": i,
                    "name": row[0],
                    "team": row[1],
                    "value": float(row[2]) if row[2] else 0,
                    "qualifier": row[3]
                })
            
            return {
                "stat_name": stat_name,
                "leaderboard": leaderboard,
                "generated_at": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Stat '{stat_name}' not supported")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard error: {str(e)}")

@router.get("/compare-players")
async def compare_players(
    player_names: str,  # Comma-separated
    stats: str = "avg,ops,woba,wrc_plus",
    session: AsyncSession = Depends(get_db_session)
):
    """Compare multiple players across specified statistics"""
    
    try:
        names = [name.strip() for name in player_names.split(",")]
        stat_list = [stat.strip() for stat in stats.split(",")]
        
        if len(names) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 players for comparison")
        
        comparisons = []
        
        for name in names:
            # Get player data
            query = text("""
                SELECT p.id, p.name, p.current_team,
                       fb.batting_stats, fp.pitching_stats
                FROM players p
                LEFT JOIN fangraphs_batting fb ON p.id = fb.player_id
                LEFT JOIN fangraphs_pitching fp ON p.id = fp.player_id
                WHERE p.name ILIKE :name
                LIMIT 1
            """)
            
            result = await session.execute(query, {"name": f"%{name}%"})
            row = result.fetchone()
            
            if row:
                player_stats = {}
                batting_data = json.loads(row[3]) if row[3] else {}
                pitching_data = json.loads(row[4]) if row[4] else {}
                
                for stat in stat_list:
                    # Map stat to appropriate data source  
                    if stat.upper() in batting_data:
                        player_stats[stat] = batting_data[stat.upper()]
                    elif stat.upper() in pitching_data:
                        player_stats[stat] = pitching_data[stat.upper()]
                    else:
                        player_stats[stat] = None
                
                comparisons.append({
                    "name": row[1],
                    "team": row[2],
                    "stats": player_stats
                })
        
        return {
            "comparison": comparisons,
            "stats_compared": stat_list,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@router.get("/team-stats/{team}")
async def get_team_statistics(
    team: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get aggregated statistics for a team"""
    
    try:
        query = text("""
            SELECT p.name, p.primary_position,
                   fb.batting_stats, fp.pitching_stats
            FROM players p
            LEFT JOIN fangraphs_batting fb ON p.id = fb.player_id
            LEFT JOIN fangraphs_pitching fp ON p.id = fp.player_id
            WHERE p.current_team = :team
            AND p.active = true
            ORDER BY p.name
        """)
        
        result = await session.execute(query, {"team": team.upper()})
        
        team_roster = []
        for row in result.fetchall():
            player_data = {
                "name": row[0],
                "position": row[1],
                "batting_stats": json.loads(row[2]) if row[2] else None,
                "pitching_stats": json.loads(row[3]) if row[3] else None
            }
            team_roster.append(player_data)
        
        return {
            "team": team.upper(),
            "roster": team_roster,
            "player_count": len(team_roster)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Team stats error: {str(e)}")

@router.get("/export/{player_id}")
async def export_player_data(
    player_id: int,
    format: str = "json",
    session: AsyncSession = Depends(get_db_session)
):
    """Export comprehensive player data"""
    
    try:
        # Get all player data
        query = text("""
            SELECT p.*, 
                   array_agg(DISTINCT fb.batting_stats) as batting_data,
                   array_agg(DISTINCT fp.pitching_stats) as pitching_data,
                   COUNT(sp.id) as statcast_pitch_count
            FROM players p
            LEFT JOIN fangraphs_batting fb ON p.id = fb.player_id
            LEFT JOIN fangraphs_pitching fp ON p.id = fp.player_id  
            LEFT JOIN statcast_pitches sp ON p.mlb_id = sp.batter_id
            WHERE p.id = :player_id
            GROUP BY p.id
        """)
        
        result = await session.execute(query, {"player_id": player_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        
        export_data = {
            "player_info": {
                "id": row[0],
                "mlb_id": row[1], 
                "name": row[2],
                "team": row[4],
                "position": row[5]
            },
            "fangraphs_batting": [json.loads(stat) for stat in row[7] if stat],
            "fangraphs_pitching": [json.loads(stat) for stat in row[8] if stat],
            "statcast_pitch_count": row[9],
            "exported_at": datetime.now().isoformat()
        }
        
        if format.lower() == "csv":
            # Convert to CSV format (simplified)
            return {"message": "CSV export not implemented yet", "data": export_data}
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")