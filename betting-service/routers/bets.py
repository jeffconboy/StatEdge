"""
Bets Router
===========

API endpoints for managing personal betting predictions and outcomes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging
import asyncpg

from database.connection import get_db_session
from models.bets import *

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", 
             summary="Create New Bet",
             description="Log a new betting prediction",
             response_model=BetResponse)
async def create_bet(bet: CreateBetRequest):
    """
    ## Create New Bet
    
    Log a new betting prediction with your confidence level and reasoning.
    
    ### Parameters
    - **game_id**: Unique game identifier (e.g., "20250726_BOS@NYY")
    - **bet_type**: Type of bet (moneyline, spread, total, prop)
    - **bet_side**: Side of the bet (home, away, over, under)
    - **bet_amount**: Amount wagered
    - **confidence_level**: Your confidence level (1-10)
    
    ### Example
    ```json
    {
        "game_id": "20250726_BOS@NYY",
        "home_team": "NYY",
        "away_team": "BOS",
        "game_date": "2025-07-26",
        "bet_type": "moneyline",
        "bet_side": "home",
        "bet_amount": 50.00,
        "odds": -150,
        "confidence_level": 7,
        "prediction_reasoning": "Yankees have better starting pitcher and home field advantage"
    }
    ```
    """
    try:
        async for conn in get_db_session():
            # Calculate implied probability from odds if provided
            implied_prob = None
            if bet.odds:
                if bet.odds > 0:
                    implied_prob = 100 / (bet.odds + 100) * 100
                else:
                    implied_prob = abs(bet.odds) / (abs(bet.odds) + 100) * 100
            
            # Insert bet
            bet_id = await conn.fetchval("""
                INSERT INTO bets (
                    game_id, sport, home_team, away_team, game_date, game_time,
                    bet_type, bet_side, bet_amount, odds, implied_probability,
                    confidence_level, prediction_reasoning, predicted_score_home, 
                    predicted_score_away, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING id
            """, 
                bet.game_id, bet.sport.value, bet.home_team, bet.away_team, 
                bet.game_date, bet.game_time, bet.bet_type.value, bet.bet_side.value,
                bet.bet_amount, bet.odds, implied_prob, bet.confidence_level,
                bet.prediction_reasoning, bet.predicted_score_home, 
                bet.predicted_score_away, bet.notes
            )
            
            # Add category mappings if provided
            if bet.category_ids:
                for category_id in bet.category_ids:
                    await conn.execute("""
                        INSERT INTO bet_category_mapping (bet_id, category_id) 
                        VALUES ($1, $2)
                    """, bet_id, category_id)
            
            # Add strategy mappings if provided
            if bet.strategy_ids:
                for strategy_id in bet.strategy_ids:
                    await conn.execute("""
                        INSERT INTO bet_strategy_mapping (bet_id, strategy_id) 
                        VALUES ($1, $2)
                    """, bet_id, strategy_id)
            
            # Fetch the created bet
            bet_data = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            return BetResponse(**dict(bet_data))
            
    except Exception as e:
        logger.error(f"Error creating bet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bet: {str(e)}")

@router.get("/", 
            summary="Get Betting History",
            description="Get your betting history with optional filters",
            response_model=List[BetResponse])
async def get_betting_history(
    limit: int = Query(50, description="Number of bets to return"),
    offset: int = Query(0, description="Number of bets to skip"),
    sport: Optional[str] = Query(None, description="Filter by sport"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type"),
    game_status: Optional[str] = Query(None, description="Filter by game status"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter")
):
    """
    ## Get Betting History
    
    Retrieve your betting history with optional filters.
    
    ### Query Parameters
    - **limit**: Number of bets to return (default: 50)
    - **offset**: Number of bets to skip for pagination
    - **sport**: Filter by sport (e.g., "MLB")
    - **bet_type**: Filter by bet type (e.g., "moneyline")
    - **game_status**: Filter by status (e.g., "pending", "completed")
    - **start_date**: Start date for filtering (YYYY-MM-DD)
    - **end_date**: End date for filtering (YYYY-MM-DD)
    """
    try:
        async for conn in get_db_session():
            # Build query with filters
            where_clauses = []
            params = []
            param_count = 0
            
            if sport:
                param_count += 1
                where_clauses.append(f"sport = ${param_count}")
                params.append(sport)
            
            if bet_type:
                param_count += 1
                where_clauses.append(f"bet_type = ${param_count}")
                params.append(bet_type)
            
            if game_status:
                param_count += 1
                where_clauses.append(f"game_status = ${param_count}")
                params.append(game_status)
            
            if start_date:
                param_count += 1
                where_clauses.append(f"game_date >= ${param_count}")
                params.append(start_date)
            
            if end_date:
                param_count += 1
                where_clauses.append(f"game_date <= ${param_count}")
                params.append(end_date)
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Add limit and offset
            param_count += 1
            limit_param = f"${param_count}"
            params.append(limit)
            
            param_count += 1
            offset_param = f"${param_count}"
            params.append(offset)
            
            query = f"""
                SELECT * FROM bets 
                {where_sql}
                ORDER BY created_at DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """
            
            rows = await conn.fetch(query, *params)
            
            return [BetResponse(**dict(row)) for row in rows]
            
    except Exception as e:
        logger.error(f"Error getting betting history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get betting history: {str(e)}")

@router.get("/{bet_id}", 
            summary="Get Specific Bet",
            description="Get details for a specific bet",
            response_model=BetResponse)
async def get_bet(bet_id: int):
    """Get details for a specific bet by ID"""
    try:
        async for conn in get_db_session():
            bet_data = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            if not bet_data:
                raise HTTPException(status_code=404, detail="Bet not found")
            
            return BetResponse(**dict(bet_data))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bet {bet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bet: {str(e)}")

@router.patch("/{bet_id}", 
              summary="Update Bet",
              description="Update bet details before game starts",
              response_model=BetResponse)
async def update_bet(bet_id: int, update: UpdateBetRequest):
    """
    ## Update Bet
    
    Update bet details like confidence level, reasoning, or predictions.
    Can only be updated before the game is completed.
    """
    try:
        async for conn in get_db_session():
            # Check if bet exists and is not completed
            existing_bet = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            if not existing_bet:
                raise HTTPException(status_code=404, detail="Bet not found")
            
            if existing_bet['game_status'] == 'completed':
                raise HTTPException(status_code=400, detail="Cannot update completed bet")
            
            # Build update query
            update_fields = []
            params = []
            param_count = 0
            
            if update.confidence_level is not None:
                param_count += 1
                update_fields.append(f"confidence_level = ${param_count}")
                params.append(update.confidence_level)
            
            if update.prediction_reasoning is not None:
                param_count += 1
                update_fields.append(f"prediction_reasoning = ${param_count}")
                params.append(update.prediction_reasoning)
            
            if update.predicted_score_home is not None:
                param_count += 1
                update_fields.append(f"predicted_score_home = ${param_count}")
                params.append(update.predicted_score_home)
            
            if update.predicted_score_away is not None:
                param_count += 1
                update_fields.append(f"predicted_score_away = ${param_count}")
                params.append(update.predicted_score_away)
            
            if update.notes is not None:
                param_count += 1
                update_fields.append(f"notes = ${param_count}")
                params.append(update.notes)
            
            if update_fields:
                param_count += 1
                update_fields.append(f"updated_at = ${param_count}")
                params.append(datetime.now())
                
                param_count += 1
                params.append(bet_id)
                
                query = f"""
                    UPDATE bets 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                """
                
                await conn.execute(query, *params)
            
            # Handle category updates
            if update.category_ids is not None:
                # Remove existing mappings
                await conn.execute("""
                    DELETE FROM bet_category_mapping WHERE bet_id = $1
                """, bet_id)
                
                # Add new mappings
                for category_id in update.category_ids:
                    await conn.execute("""
                        INSERT INTO bet_category_mapping (bet_id, category_id) 
                        VALUES ($1, $2)
                    """, bet_id, category_id)
            
            # Handle strategy updates
            if update.strategy_ids is not None:
                # Remove existing mappings
                await conn.execute("""
                    DELETE FROM bet_strategy_mapping WHERE bet_id = $1
                """, bet_id)
                
                # Add new mappings
                for strategy_id in update.strategy_ids:
                    await conn.execute("""
                        INSERT INTO bet_strategy_mapping (bet_id, strategy_id) 
                        VALUES ($1, $2)
                    """, bet_id, strategy_id)
            
            # Fetch updated bet
            updated_bet = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            return BetResponse(**dict(updated_bet))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bet {bet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bet: {str(e)}")

@router.post("/{bet_id}/settle", 
             summary="Settle Bet",
             description="Record the outcome of a completed game",
             response_model=BetResponse)
async def settle_bet(bet_id: int, settlement: SettleBetRequest):
    """
    ## Settle Bet
    
    Record the outcome of a game and determine bet result.
    
    ### Parameters
    - **actual_score_home**: Final home team score
    - **actual_score_away**: Final away team score  
    - **bet_result**: Outcome (win, loss, push, void)
    - **payout**: Amount won (optional, will calculate if not provided)
    """
    try:
        async for conn in get_db_session():
            # Get bet details
            bet_data = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            if not bet_data:
                raise HTTPException(status_code=404, detail="Bet not found")
            
            # Calculate payout if not provided
            payout = settlement.payout
            if payout is None and settlement.bet_result == BetResult.WIN:
                bet_amount = bet_data['bet_amount']
                odds = bet_data['odds']
                
                if odds and odds > 0:
                    payout = bet_amount + (bet_amount * odds / 100)
                elif odds and odds < 0:
                    payout = bet_amount + (bet_amount * 100 / abs(odds))
                else:
                    payout = bet_amount * 2  # Default even money
            elif settlement.bet_result == BetResult.PUSH:
                payout = bet_data['bet_amount']  # Return original bet
            elif settlement.bet_result in [BetResult.LOSS, BetResult.VOID]:
                payout = 0
            
            # Update bet with settlement
            await conn.execute("""
                UPDATE bets 
                SET actual_score_home = $1, actual_score_away = $2, 
                    bet_result = $3, payout = $4, game_status = 'completed',
                    updated_at = $5, notes = COALESCE(notes, '') || COALESCE($6, '')
                WHERE id = $7
            """, 
                settlement.actual_score_home, settlement.actual_score_away,
                settlement.bet_result.value, payout, datetime.now(),
                f"\nSettlement: {settlement.notes}" if settlement.notes else "",
                bet_id
            )
            
            # Update strategy performance
            await conn.execute("""
                UPDATE betting_strategies 
                SET total_bets = total_bets + 1,
                    wins = wins + CASE WHEN $1 = 'win' THEN 1 ELSE 0 END,
                    losses = losses + CASE WHEN $1 = 'loss' THEN 1 ELSE 0 END,
                    pushes = pushes + CASE WHEN $1 = 'push' THEN 1 ELSE 0 END,
                    total_wagered = total_wagered + $2,
                    total_profit = total_profit + ($3 - $2),
                    updated_at = $4
                WHERE id IN (
                    SELECT strategy_id FROM bet_strategy_mapping WHERE bet_id = $5
                )
            """, 
                settlement.bet_result.value, bet_data['bet_amount'], 
                payout, datetime.now(), bet_id
            )
            
            # Update win rates and ROI for strategies
            await conn.execute("""
                UPDATE betting_strategies 
                SET win_rate = CASE 
                    WHEN (total_bets - pushes) > 0 
                    THEN ROUND((wins::decimal / (total_bets - pushes)) * 100, 2)
                    ELSE 0 
                END,
                roi = CASE 
                    WHEN total_wagered > 0 
                    THEN ROUND((total_profit / total_wagered) * 100, 2)
                    ELSE 0 
                END
                WHERE id IN (
                    SELECT strategy_id FROM bet_strategy_mapping WHERE bet_id = $1
                )
            """, bet_id)
            
            # Fetch updated bet
            updated_bet = await conn.fetchrow("""
                SELECT * FROM bets WHERE id = $1
            """, bet_id)
            
            return BetResponse(**dict(updated_bet))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error settling bet {bet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to settle bet: {str(e)}")

@router.delete("/{bet_id}", 
               summary="Delete Bet",
               description="Delete a bet (only if not completed)")
async def delete_bet(bet_id: int):
    """
    ## Delete Bet
    
    Delete a bet that hasn't been completed yet.
    Completed bets cannot be deleted for record-keeping integrity.
    """
    try:
        async for conn in get_db_session():
            # Check if bet exists and is not completed
            bet_data = await conn.fetchrow("""
                SELECT game_status FROM bets WHERE id = $1
            """, bet_id)
            
            if not bet_data:
                raise HTTPException(status_code=404, detail="Bet not found")
            
            if bet_data['game_status'] == 'completed':
                raise HTTPException(status_code=400, detail="Cannot delete completed bet")
            
            # Delete bet (cascading deletes will handle mappings)
            result = await conn.execute("""
                DELETE FROM bets WHERE id = $1
            """, bet_id)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Bet not found")
            
            return {"message": "Bet deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bet {bet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete bet: {str(e)}")

@router.get("/summary/stats", 
            summary="Get Betting Summary",
            description="Get overall betting performance statistics",
            response_model=BetSummaryResponse)
async def get_betting_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary")
):
    """
    ## Betting Performance Summary
    
    Get comprehensive statistics about your betting performance.
    
    ### Query Parameters
    - **start_date**: Start date for analysis (optional)
    - **end_date**: End date for analysis (optional)
    
    ### Returns
    - Overall win/loss record
    - Win percentage and ROI
    - Performance breakdown by bet type and sport
    - Total amounts wagered and profit/loss
    """
    try:
        async for conn in get_db_session():
            # Build date filter
            date_filter = ""
            params = []
            
            if start_date or end_date:
                conditions = []
                if start_date:
                    params.append(start_date)
                    conditions.append(f"game_date >= ${len(params)}")
                if end_date:
                    params.append(end_date)
                    conditions.append(f"game_date <= ${len(params)}")
                date_filter = "AND " + " AND ".join(conditions)
            
            # Get overall summary
            overall = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN bet_result = 'push' THEN 1 ELSE 0 END) as pushes,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit
                FROM bets 
                WHERE game_status = 'completed' {date_filter}
            """, *params)
            
            # Calculate win percentage
            total_decided = overall['total_bets'] - overall['pushes']
            win_percentage = (overall['wins'] / total_decided * 100) if total_decided > 0 else 0
            
            # Calculate ROI
            roi_percentage = (overall['total_profit'] / overall['total_wagered'] * 100) if overall['total_wagered'] > 0 else 0
            
            # Get breakdown by bet type
            by_type = await conn.fetch(f"""
                SELECT 
                    bet_type,
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit
                FROM bets 
                WHERE game_status = 'completed' {date_filter}
                GROUP BY bet_type
            """, *params)
            
            # Get breakdown by sport
            by_sport = await conn.fetch(f"""
                SELECT 
                    sport,
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit
                FROM bets 
                WHERE game_status = 'completed' {date_filter}
                GROUP BY sport
            """, *params)
            
            # Format breakdown data
            by_bet_type = {}
            for row in by_type:
                decided = row['total_bets'] - (row['total_bets'] - row['wins'] - row['losses'])
                by_bet_type[row['bet_type']] = {
                    'total_bets': row['total_bets'],
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'win_percentage': (row['wins'] / decided * 100) if decided > 0 else 0,
                    'total_wagered': row['total_wagered'],
                    'total_profit': row['total_profit'],
                    'roi': (row['total_profit'] / row['total_wagered'] * 100) if row['total_wagered'] > 0 else 0
                }
            
            by_sport_dict = {}
            for row in by_sport:
                decided = row['total_bets'] - (row['total_bets'] - row['wins'] - row['losses'])
                by_sport_dict[row['sport']] = {
                    'total_bets': row['total_bets'],
                    'wins': row['wins'], 
                    'losses': row['losses'],
                    'win_percentage': (row['wins'] / decided * 100) if decided > 0 else 0,
                    'total_wagered': row['total_wagered'],
                    'total_profit': row['total_profit'],
                    'roi': (row['total_profit'] / row['total_wagered'] * 100) if row['total_wagered'] > 0 else 0
                }
            
            return BetSummaryResponse(
                total_bets=overall['total_bets'],
                wins=overall['wins'],
                losses=overall['losses'],
                pushes=overall['pushes'],
                win_percentage=round(win_percentage, 2),
                total_wagered=overall['total_wagered'],
                total_profit=overall['total_profit'],
                roi_percentage=round(roi_percentage, 2),
                by_bet_type=by_bet_type,
                by_sport=by_sport_dict
            )
            
    except Exception as e:
        logger.error(f"Error getting betting summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")