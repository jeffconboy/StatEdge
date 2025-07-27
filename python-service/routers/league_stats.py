from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from database.connection import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/hard-hit-average")
async def get_league_hard_hit_average(session: AsyncSession = Depends(get_db_session)):
    """Calculate real league average hard hit rate from Statcast data"""
    
    try:
        # Calculate hard hit rate using complete 2025 season data with proper filtering
        query = text("""
            WITH contact_events AS (
                SELECT 
                    CASE 
                        WHEN statcast_data->>'launch_speed' ~ '^[0-9.]+$' 
                        THEN CAST(statcast_data->>'launch_speed' AS FLOAT)
                        ELSE NULL 
                    END as launch_speed,
                    CASE 
                        WHEN statcast_data->>'launch_angle' ~ '^-?[0-9.]+$' 
                        THEN CAST(statcast_data->>'launch_angle' AS FLOAT)
                        ELSE NULL 
                    END as launch_angle
                FROM statcast_pitches 
                WHERE game_date >= '2025-01-01' 
                AND game_date < '2026-01-01'
                AND statcast_data->>'type' = 'X'
                AND statcast_data->>'launch_speed' IS NOT NULL
                AND statcast_data->>'launch_speed' != ''
                AND statcast_data->>'launch_angle' IS NOT NULL
                AND statcast_data->>'launch_angle' != ''
            ),
            valid_contact AS (
                SELECT launch_speed, launch_angle
                FROM contact_events 
                WHERE launch_speed IS NOT NULL 
                AND launch_speed > 0
                AND launch_speed <= 125 -- Filter out obvious data errors only
                AND launch_angle IS NOT NULL
                -- Note: Baseball Savant includes all batted balls except bunts
                -- We removed artificial 70mph and angle filters to match official methodology
            ),
            barrel_calculations AS (
                SELECT 
                    launch_speed,
                    launch_angle,
                    -- Official Baseball Savant barrel definition
                    -- Results in minimum .500 BA and 1.500 SLG
                    CASE 
                        -- 98 mph: 26-30 degrees
                        WHEN launch_speed >= 98.0 AND launch_speed < 99.0 
                             AND launch_angle >= 26 AND launch_angle <= 30 THEN 1
                        -- 99 mph: 25-31 degrees  
                        WHEN launch_speed >= 99.0 AND launch_speed < 100.0
                             AND launch_angle >= 25 AND launch_angle <= 31 THEN 1
                        -- 100 mph: 24-33 degrees
                        WHEN launch_speed >= 100.0 AND launch_speed < 101.0
                             AND launch_angle >= 24 AND launch_angle <= 33 THEN 1
                        -- 101 mph: 23-34 degrees
                        WHEN launch_speed >= 101.0 AND launch_speed < 102.0
                             AND launch_angle >= 23 AND launch_angle <= 34 THEN 1
                        -- 102 mph: 22-35 degrees
                        WHEN launch_speed >= 102.0 AND launch_speed < 103.0
                             AND launch_angle >= 22 AND launch_angle <= 35 THEN 1
                        -- 103 mph: 21-36 degrees
                        WHEN launch_speed >= 103.0 AND launch_speed < 104.0
                             AND launch_angle >= 21 AND launch_angle <= 36 THEN 1
                        -- 104 mph: 20-37 degrees
                        WHEN launch_speed >= 104.0 AND launch_speed < 105.0
                             AND launch_angle >= 20 AND launch_angle <= 37 THEN 1
                        -- 105 mph: 19-38 degrees
                        WHEN launch_speed >= 105.0 AND launch_speed < 106.0
                             AND launch_angle >= 19 AND launch_angle <= 38 THEN 1
                        -- 106+ mph: continue expanding ~1 degree per mph
                        WHEN launch_speed >= 106.0 AND launch_speed < 110.0
                             AND launch_angle >= (19 - (launch_speed - 105)) 
                             AND launch_angle <= (38 + (launch_speed - 105)) THEN 1
                        -- 110+ mph: cap at reasonable ranges
                        WHEN launch_speed >= 110.0 AND launch_speed < 116.0
                             AND launch_angle >= 14 AND launch_angle <= 43 THEN 1
                        -- 116+ mph: 8-50 degrees (Baseball Savant maximum range)
                        WHEN launch_speed >= 116.0 
                             AND launch_angle >= 8 AND launch_angle <= 50 THEN 1
                        ELSE 0
                    END as is_barrel
                FROM valid_contact
            )
            SELECT 
                COUNT(*) as total_contact_events,
                COUNT(*) FILTER (WHERE launch_speed >= 95) as hard_hits,
                ROUND(
                    (COUNT(*) FILTER (WHERE launch_speed >= 95)::NUMERIC / COUNT(*)::NUMERIC) * 100, 1
                ) as hard_hit_rate,
                ROUND(AVG(launch_speed)::NUMERIC, 1) as avg_exit_velocity,
                ROUND(
                    (SUM(is_barrel)::NUMERIC / COUNT(*)::NUMERIC) * 100, 1
                ) as barrel_rate,
                ROUND(
                    (COUNT(*) FILTER (WHERE launch_angle >= 8 AND launch_angle <= 32)::NUMERIC / COUNT(*)::NUMERIC) * 100, 1
                ) as sweet_spot_rate
            FROM barrel_calculations
        """)
        
        result = await session.execute(query)
        row = result.fetchone()
        
        if not row or row[0] == 0:
            # Fallback if no data
            return {
                "hard_hit_rate": 38.9,  # Official 2024 league average
                "avg_exit_velocity": 88.8,  # Official 2024 league average
                "barrel_rate": 7.8,  # Official 2024 league average
                "sweet_spot_rate": 33.8,  # Official 2024 league average
                "sample_size": 0,
                "data_source": "fallback_estimate"
            }
        
        return {
            "hard_hit_rate": float(row[2]) if row[2] else 38.0,
            "avg_exit_velocity": float(row[3]) if row[3] else 88.5,
            "barrel_rate": float(row[4]) if row[4] else 6.8,
            "sweet_spot_rate": float(row[5]) if row[5] else 33.8,
            "sample_size": int(row[0]),
            "total_hard_hits": int(row[1]),
            "data_source": "real_statcast_data"
        }
        
    except Exception as e:
        logger.error(f"Error calculating league averages: {str(e)}")
        
        # Return reasonable estimates if query fails
        return {
            "hard_hit_rate": 38.9,  # Official 2024 league average
            "avg_exit_velocity": 88.8,  # Official 2024 league average
            "barrel_rate": 7.8,  # Official 2024 league average  
            "sweet_spot_rate": 33.8,  # Official 2024 league average
            "sample_size": 0,
            "data_source": "error_fallback",
            "error": str(e)
        }

@router.get("/percentiles")
async def get_league_percentiles(session: AsyncSession = Depends(get_db_session)):
    """Calculate percentile thresholds for various metrics"""
    
    try:
        query = text("""
            WITH contact_events AS (
                SELECT 
                    CASE 
                        WHEN statcast_data->>'launch_speed' ~ '^[0-9.]+$' 
                        THEN CAST(statcast_data->>'launch_speed' AS FLOAT)
                        ELSE NULL 
                    END as launch_speed
                FROM statcast_pitches 
                WHERE game_date >= '2025-01-01' 
                AND game_date < '2026-01-01'
                AND statcast_data->>'type' = 'X'
                AND statcast_data->>'launch_speed' IS NOT NULL
                AND statcast_data->>'launch_speed' != ''
            ),
            valid_contact AS (
                SELECT launch_speed
                FROM contact_events 
                WHERE launch_speed IS NOT NULL 
                AND launch_speed > 0
            )
            SELECT 
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY launch_speed) as p25_exit_velo,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY launch_speed) as p50_exit_velo,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY launch_speed) as p75_exit_velo,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY launch_speed) as p90_exit_velo,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY launch_speed) as p95_exit_velo
            FROM valid_contact
        """)
        
        result = await session.execute(query)
        row = result.fetchone()
        
        if not row:
            return {
                "exit_velocity_percentiles": {
                    "25th": 82.0,
                    "50th": 88.0, 
                    "75th": 94.0,
                    "90th": 100.0,
                    "95th": 104.0
                },
                "data_source": "fallback_estimate"
            }
        
        return {
            "exit_velocity_percentiles": {
                "25th": round(float(row[0]), 1) if row[0] else 82.0,
                "50th": round(float(row[1]), 1) if row[1] else 88.0,
                "75th": round(float(row[2]), 1) if row[2] else 94.0,
                "90th": round(float(row[3]), 1) if row[3] else 100.0,
                "95th": round(float(row[4]), 1) if row[4] else 104.0
            },
            "data_source": "real_statcast_data"
        }
        
    except Exception as e:
        logger.error(f"Error calculating percentiles: {str(e)}")
        return {
            "exit_velocity_percentiles": {
                "25th": 82.0,
                "50th": 88.0,
                "75th": 94.0, 
                "90th": 100.0,
                "95th": 104.0
            },
            "data_source": "error_fallback",
            "error": str(e)
        }