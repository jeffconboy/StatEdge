"""
Bankroll Router
===============

Bankroll management and tracking endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging

from database.connection import get_db_session
from models.bets import BankrollRequest, BankrollResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/",
             summary="Add Bankroll Entry",
             description="Record daily bankroll information",
             response_model=BankrollResponse)
async def add_bankroll_entry(entry: BankrollRequest):
    """
    ## Add Bankroll Entry
    
    Record your daily bankroll balance and betting activity.
    
    ### Example
    ```json
    {
        "date": "2025-07-26",
        "starting_balance": 1000.00,
        "ending_balance": 1050.00,
        "total_wagered": 200.00,
        "number_of_bets": 3,
        "notes": "Good day with 2 wins"
    }
    ```
    """
    try:
        async for conn in get_db_session():
            # Calculate daily P&L
            daily_pnl = entry.ending_balance - entry.starting_balance
            
            # Check if entry for this date already exists
            existing = await conn.fetchrow("""
                SELECT id FROM bankroll_history WHERE date = $1
            """, entry.date)
            
            if existing:
                # Update existing entry
                await conn.execute("""
                    UPDATE bankroll_history 
                    SET starting_balance = $1, ending_balance = $2, daily_pnl = $3,
                        total_wagered = $4, number_of_bets = $5, notes = $6
                    WHERE date = $7
                """, entry.starting_balance, entry.ending_balance, daily_pnl,
                    entry.total_wagered, entry.number_of_bets, entry.notes, entry.date)
                
                entry_id = existing['id']
            else:
                # Insert new entry
                entry_id = await conn.fetchval("""
                    INSERT INTO bankroll_history (
                        date, starting_balance, ending_balance, daily_pnl,
                        total_wagered, number_of_bets, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, entry.date, entry.starting_balance, entry.ending_balance, daily_pnl,
                    entry.total_wagered, entry.number_of_bets, entry.notes)
            
            # Fetch the entry
            bankroll_data = await conn.fetchrow("""
                SELECT * FROM bankroll_history WHERE id = $1
            """, entry_id)
            
            return BankrollResponse(**dict(bankroll_data))
            
    except Exception as e:
        logger.error(f"Error adding bankroll entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/",
            summary="Get Bankroll History",
            description="Get bankroll history with optional date range",
            response_model=List[BankrollResponse])
async def get_bankroll_history(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(30, description="Number of entries to return")
):
    """
    ## Get Bankroll History
    
    Retrieve your bankroll tracking history.
    """
    try:
        async for conn in get_db_session():
            # Build query with optional date filters
            where_clauses = []
            params = []
            
            if start_date:
                params.append(start_date)
                where_clauses.append(f"date >= ${len(params)}")
            
            if end_date:
                params.append(end_date)
                where_clauses.append(f"date <= ${len(params)}")
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            params.append(limit)
            
            query = f"""
                SELECT * FROM bankroll_history 
                {where_sql}
                ORDER BY date DESC
                LIMIT ${len(params)}
            """
            
            entries = await conn.fetch(query, *params)
            
            return [BankrollResponse(**dict(row)) for row in entries]
            
    except Exception as e:
        logger.error(f"Error getting bankroll history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary",
            summary="Bankroll Summary",
            description="Get bankroll performance summary")
async def get_bankroll_summary(
    days: int = Query(30, description="Number of days to analyze")
):
    """
    ## Bankroll Summary
    
    Get summary statistics for bankroll performance over specified period.
    """
    try:
        async for conn in get_db_session():
            start_date = date.today() - timedelta(days=days)
            
            # Get overall summary
            summary = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_days,
                    SUM(daily_pnl) as total_pnl,
                    SUM(total_wagered) as total_wagered,
                    SUM(number_of_bets) as total_bets,
                    AVG(daily_pnl) as avg_daily_pnl,
                    MAX(daily_pnl) as best_day,
                    MIN(daily_pnl) as worst_day,
                    COUNT(CASE WHEN daily_pnl > 0 THEN 1 END) as positive_days,
                    COUNT(CASE WHEN daily_pnl < 0 THEN 1 END) as negative_days
                FROM bankroll_history 
                WHERE date >= $1
            """, start_date)
            
            # Get current balance (most recent entry)
            current_balance = await conn.fetchrow("""
                SELECT ending_balance, date
                FROM bankroll_history 
                ORDER BY date DESC 
                LIMIT 1
            """)
            
            # Get starting balance for the period
            period_start = await conn.fetchrow("""
                SELECT starting_balance
                FROM bankroll_history 
                WHERE date >= $1
                ORDER BY date ASC
                LIMIT 1
            """, start_date)
            
            # Calculate period return
            period_return = 0
            if period_start and current_balance:
                period_return = ((current_balance['ending_balance'] - period_start['starting_balance']) / 
                               period_start['starting_balance'] * 100)
            
            return {
                "period": f"{days} days",
                "current_balance": float(current_balance['ending_balance']) if current_balance else 0,
                "last_updated": current_balance['date'].isoformat() if current_balance else None,
                "period_return": round(period_return, 2),
                "total_pnl": float(summary['total_pnl']) if summary['total_pnl'] else 0,
                "total_wagered": float(summary['total_wagered']) if summary['total_wagered'] else 0,
                "total_bets": summary['total_bets'] or 0,
                "avg_daily_pnl": round(float(summary['avg_daily_pnl']), 2) if summary['avg_daily_pnl'] else 0,
                "best_day": float(summary['best_day']) if summary['best_day'] else 0,
                "worst_day": float(summary['worst_day']) if summary['worst_day'] else 0,
                "positive_days": summary['positive_days'] or 0,
                "negative_days": summary['negative_days'] or 0,
                "total_days": summary['total_days'] or 0
            }
            
    except Exception as e:
        logger.error(f"Error getting bankroll summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart-data",
            summary="Bankroll Chart Data",
            description="Get bankroll data formatted for charts")
async def get_bankroll_chart_data(
    days: int = Query(30, description="Number of days to include")
):
    """
    ## Bankroll Chart Data
    
    Get bankroll progression data formatted for frontend charts.
    """
    try:
        async for conn in get_db_session():
            start_date = date.today() - timedelta(days=days)
            
            chart_data = await conn.fetch("""
                SELECT 
                    date,
                    starting_balance,
                    ending_balance,
                    daily_pnl,
                    total_wagered,
                    number_of_bets
                FROM bankroll_history 
                WHERE date >= $1
                ORDER BY date ASC
            """, start_date)
            
            # Calculate cumulative P&L
            cumulative_pnl = 0
            formatted_data = []
            
            for row in chart_data:
                cumulative_pnl += float(row['daily_pnl'])
                
                formatted_data.append({
                    "date": row['date'].isoformat(),
                    "balance": float(row['ending_balance']),
                    "daily_pnl": float(row['daily_pnl']),
                    "cumulative_pnl": cumulative_pnl,
                    "wagered": float(row['total_wagered']),
                    "bets": row['number_of_bets']
                })
            
            return {
                "data": formatted_data,
                "period": f"{days} days",
                "total_points": len(formatted_data)
            }
            
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{entry_date}",
               summary="Delete Bankroll Entry",
               description="Delete a bankroll entry for specific date")
async def delete_bankroll_entry(entry_date: date):
    """Delete a bankroll entry for a specific date"""
    try:
        async for conn in get_db_session():
            result = await conn.execute("""
                DELETE FROM bankroll_history WHERE date = $1
            """, entry_date)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Bankroll entry not found")
            
            return {"message": f"Bankroll entry for {entry_date} deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bankroll entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))