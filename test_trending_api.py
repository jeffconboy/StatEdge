#!/usr/bin/env python3
"""
Test script to verify trending API returns correct data structure
"""

import asyncio
import asyncpg
import json
from datetime import datetime

async def test_trending_api():
    """Test the trending players query directly"""
    
    # Connect to database
    database_url = "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Test the trending query
        query = """
            WITH recent_stats AS (
                SELECT 
                    s.batter as mlb_id,
                    s.player_name as name,
                    COUNT(*) as plate_appearances,
                    COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run', 'field_out', 'grounded_into_double_play', 'force_out', 'fielders_choice', 'strikeout') THEN 1 END) as at_bats,
                    COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run') THEN 1 END) as hits,
                    COUNT(CASE WHEN s.events = 'home_run' THEN 1 END) as home_runs,
                    COUNT(CASE WHEN s.events IN ('walk', 'intent_walk', 'hit_by_pitch') THEN 1 END) as walks,
                    COUNT(CASE WHEN s.events = 'strikeout' THEN 1 END) as strikeouts,
                    AVG(CASE 
                        WHEN s.launch_speed IS NOT NULL AND s.launch_speed > 0 
                        THEN s.launch_speed
                        ELSE NULL 
                    END) as avg_exit_velocity
                FROM statcast s
                WHERE s.game_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND s.player_name IS NOT NULL
                GROUP BY s.batter, s.player_name
                HAVING COUNT(CASE WHEN s.events IN ('single', 'double', 'triple', 'home_run', 'field_out', 'grounded_into_double_play', 'force_out', 'fielders_choice', 'strikeout') THEN 1 END) >= 5
            )
            SELECT *,
                   CASE 
                       WHEN at_bats > 0 THEN ROUND(hits::NUMERIC / at_bats, 3)
                       ELSE 0.000
                   END as batting_average
            FROM recent_stats
            WHERE at_bats >= 5
            ORDER BY home_runs DESC, batting_average DESC, plate_appearances DESC
            LIMIT 5
        """
        
        result = await conn.execute(query)
        rows = await conn.fetch(query)
        
        print(f"Found {len(rows)} trending players:")
        for i, row in enumerate(rows):
            print(f"\n{i+1}. {row['name']} (ID: {row['mlb_id']})")
            print(f"   Plate Appearances: {row['plate_appearances']}")
            print(f"   At Bats: {row['at_bats']}")
            print(f"   Hits: {row['hits']}")
            print(f"   Home Runs: {row['home_runs']}")
            print(f"   Batting Average: {row['batting_average']}")
            print(f"   Avg Exit Velocity: {row['avg_exit_velocity']}")
        
        # Test API response format
        trending = []
        for row in rows:
            trending.append({
                "id": row['mlb_id'],
                "name": row['name'], 
                "team": "MLB",
                "team_full_name": "Major League Baseball",
                "position": "Batter",
                "mlb_id": row['mlb_id'],
                "local_image_path": None,  
                "recent_activity": row['plate_appearances'],
                "stats": {
                    "at_bats": row['at_bats'],
                    "hits": row['hits'],
                    "home_runs": row['home_runs'],
                    "walks": row['walks'], 
                    "strikeouts": row['strikeouts'],
                    "batting_average": float(row['batting_average']) if row['batting_average'] else 0.000,
                    "avg_exit_velocity": round(float(row['avg_exit_velocity']), 1) if row['avg_exit_velocity'] else None
                }
            })
        
        print(f"\nAPI Response format:")
        print(json.dumps(trending, indent=2, default=str))
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_trending_api())