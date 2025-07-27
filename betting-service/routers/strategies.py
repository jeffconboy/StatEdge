"""
Strategies Router
=================

Betting strategy management and performance tracking.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from database.connection import get_db_session
from models.bets import BettingStrategyRequest, BettingStrategyResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/",
            summary="Get All Strategies",
            description="Get all betting strategies with performance metrics",
            response_model=List[BettingStrategyResponse])
async def get_strategies():
    """
    ## Get All Betting Strategies
    
    Retrieve all your betting strategies with current performance metrics.
    """
    try:
        async for conn in get_db_session():
            strategies = await conn.fetch("""
                SELECT 
                    id, strategy_name, description, criteria,
                    total_bets, wins, losses, pushes,
                    total_wagered, total_profit, win_rate, roi,
                    created_at, updated_at
                FROM betting_strategies
                ORDER BY total_bets DESC, strategy_name
            """)
            
            return [BettingStrategyResponse(**dict(row)) for row in strategies]
            
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/",
             summary="Create Strategy",
             description="Create a new betting strategy",
             response_model=BettingStrategyResponse)
async def create_strategy(strategy: BettingStrategyRequest):
    """
    ## Create New Betting Strategy
    
    Define a new betting strategy with criteria and description.
    
    ### Example
    ```json
    {
        "strategy_name": "Road Underdogs",
        "description": "Bet on away teams getting +150 or better odds",
        "criteria": {
            "min_odds": 150,
            "team_location": "away",
            "max_spread": 2.5
        }
    }
    ```
    """
    try:
        async for conn in get_db_session():
            strategy_id = await conn.fetchval("""
                INSERT INTO betting_strategies (strategy_name, description, criteria)
                VALUES ($1, $2, $3)
                RETURNING id
            """, strategy.strategy_name, strategy.description, strategy.criteria)
            
            # Fetch the created strategy
            strategy_data = await conn.fetchrow("""
                SELECT * FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            return BettingStrategyResponse(**dict(strategy_data))
            
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}",
            summary="Get Strategy",
            description="Get specific strategy with performance",
            response_model=BettingStrategyResponse)
async def get_strategy(strategy_id: int):
    """Get specific betting strategy by ID"""
    try:
        async for conn in get_db_session():
            strategy = await conn.fetchrow("""
                SELECT * FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            return BettingStrategyResponse(**dict(strategy))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{strategy_id}",
            summary="Update Strategy",
            description="Update strategy details",
            response_model=BettingStrategyResponse)
async def update_strategy(strategy_id: int, strategy: BettingStrategyRequest):
    """Update an existing betting strategy"""
    try:
        async for conn in get_db_session():
            # Check if strategy exists
            existing = await conn.fetchrow("""
                SELECT id FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            if not existing:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Update strategy
            await conn.execute("""
                UPDATE betting_strategies 
                SET strategy_name = $1, description = $2, criteria = $3, updated_at = NOW()
                WHERE id = $4
            """, strategy.strategy_name, strategy.description, strategy.criteria, strategy_id)
            
            # Fetch updated strategy
            updated_strategy = await conn.fetchrow("""
                SELECT * FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            return BettingStrategyResponse(**dict(updated_strategy))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{strategy_id}",
               summary="Delete Strategy",
               description="Delete a betting strategy")
async def delete_strategy(strategy_id: int):
    """Delete a betting strategy (removes mappings but keeps bet history)"""
    try:
        async for conn in get_db_session():
            # Check if strategy exists
            strategy = await conn.fetchrow("""
                SELECT strategy_name FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Delete strategy (cascading will handle mappings)
            await conn.execute("""
                DELETE FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            return {"message": f"Strategy '{strategy['strategy_name']}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}/bets",
            summary="Get Strategy Bets", 
            description="Get all bets using this strategy")
async def get_strategy_bets(strategy_id: int):
    """Get all bets that used this strategy"""
    try:
        async for conn in get_db_session():
            # Check if strategy exists
            strategy = await conn.fetchrow("""
                SELECT strategy_name FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Get bets for this strategy
            bets = await conn.fetch("""
                SELECT b.*
                FROM bets b
                JOIN bet_strategy_mapping bsm ON b.id = bsm.bet_id
                WHERE bsm.strategy_id = $1
                ORDER BY b.game_date DESC, b.created_at DESC
            """, strategy_id)
            
            return [
                {
                    "id": row['id'],
                    "game_id": row['game_id'],
                    "matchup": f"{row['away_team']} @ {row['home_team']}",
                    "game_date": row['game_date'].isoformat(),
                    "bet_type": row['bet_type'],
                    "bet_side": row['bet_side'],
                    "bet_amount": float(row['bet_amount']),
                    "odds": float(row['odds']) if row['odds'] else None,
                    "confidence": row['confidence_level'],
                    "result": row['bet_result'],
                    "profit": float(row['payout'] - row['bet_amount']) if row['payout'] else None
                }
                for row in bets
            ]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bets for strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}/performance",
            summary="Strategy Performance",
            description="Detailed performance analysis for strategy")
async def get_strategy_performance(strategy_id: int):
    """Get detailed performance analysis for a specific strategy"""
    try:
        async for conn in get_db_session():
            # Check if strategy exists
            strategy = await conn.fetchrow("""
                SELECT * FROM betting_strategies WHERE id = $1
            """, strategy_id)
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Get monthly performance
            monthly_performance = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('month', b.game_date) as month,
                    COUNT(*) as bets_count,
                    SUM(CASE WHEN b.bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(b.bet_amount) as wagered,
                    SUM(COALESCE(b.payout, 0) - b.bet_amount) as profit
                FROM bets b
                JOIN bet_strategy_mapping bsm ON b.id = bsm.bet_id
                WHERE bsm.strategy_id = $1 AND b.game_status = 'completed'
                GROUP BY DATE_TRUNC('month', b.game_date)
                ORDER BY month DESC
                LIMIT 12
            """, strategy_id)
            
            # Get bet type breakdown
            bet_type_breakdown = await conn.fetch("""
                SELECT 
                    b.bet_type,
                    COUNT(*) as bets_count,
                    SUM(CASE WHEN b.bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(b.bet_amount) as wagered,
                    SUM(COALESCE(b.payout, 0) - b.bet_amount) as profit
                FROM bets b
                JOIN bet_strategy_mapping bsm ON b.id = bsm.bet_id
                WHERE bsm.strategy_id = $1 AND b.game_status = 'completed'
                GROUP BY b.bet_type
                ORDER BY bets_count DESC
            """, strategy_id)
            
            return {
                "strategy": {
                    "id": strategy['id'],
                    "name": strategy['strategy_name'],
                    "description": strategy['description'],
                    "criteria": strategy['criteria']
                },
                "overall_performance": {
                    "total_bets": strategy['total_bets'],
                    "wins": strategy['wins'],
                    "losses": strategy['losses'],
                    "pushes": strategy['pushes'],
                    "win_rate": float(strategy['win_rate']) if strategy['win_rate'] else 0,
                    "total_wagered": float(strategy['total_wagered']),
                    "total_profit": float(strategy['total_profit']),
                    "roi": float(strategy['roi']) if strategy['roi'] else 0
                },
                "monthly_performance": [
                    {
                        "month": row['month'].strftime("%Y-%m"),
                        "bets_count": row['bets_count'],
                        "wins": row['wins'],
                        "win_rate": round((row['wins'] / row['bets_count'] * 100), 2),
                        "wagered": float(row['wagered']),
                        "profit": float(row['profit']),
                        "roi": round((row['profit'] / row['wagered'] * 100), 2) if row['wagered'] > 0 else 0
                    }
                    for row in monthly_performance
                ],
                "bet_type_breakdown": [
                    {
                        "bet_type": row['bet_type'],
                        "bets_count": row['bets_count'],
                        "wins": row['wins'],
                        "win_rate": round((row['wins'] / row['bets_count'] * 100), 2),
                        "wagered": float(row['wagered']),
                        "profit": float(row['profit']),
                        "roi": round((row['profit'] / row['wagered'] * 100), 2) if row['wagered'] > 0 else 0
                    }
                    for row in bet_type_breakdown
                ]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance for strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))