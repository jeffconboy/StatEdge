"""
Analytics Router
================

Performance analytics and reporting endpoints for betting data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from database.connection import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/summary",
            summary="Performance Summary",
            description="Get overall betting performance summary")
async def get_performance_summary(
    days: int = Query(30, description="Number of days to analyze")
):
    """
    ## Performance Summary
    
    Get comprehensive performance analytics for the specified period.
    """
    try:
        async for conn in get_db_session():
            start_date = date.today() - timedelta(days=days)
            
            summary = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN bet_result = 'push' THEN 1 ELSE 0 END) as pushes,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit,
                    AVG(confidence_level) as avg_confidence
                FROM bets 
                WHERE game_status = 'completed' 
                AND game_date >= $1
            """, start_date)
            
            # Calculate percentages
            total_decided = summary['total_bets'] - summary['pushes']
            win_rate = (summary['wins'] / total_decided * 100) if total_decided > 0 else 0
            roi = (summary['total_profit'] / summary['total_wagered'] * 100) if summary['total_wagered'] > 0 else 0
            
            return {
                "period": f"{days} days",
                "total_bets": summary['total_bets'],
                "wins": summary['wins'],
                "losses": summary['losses'],
                "pushes": summary['pushes'],
                "win_rate": round(win_rate, 2),
                "total_wagered": float(summary['total_wagered']),
                "total_profit": float(summary['total_profit']),
                "roi": round(roi, 2),
                "average_confidence": round(float(summary['avg_confidence']), 1) if summary['avg_confidence'] else 0
            }
            
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends",
            summary="Performance Trends",
            description="Get performance trends over time")
async def get_performance_trends(
    period: str = Query("week", description="Grouping period: day, week, month")
):
    """
    ## Performance Trends
    
    Get performance trends grouped by day, week, or month.
    """
    try:
        async for conn in get_db_session():
            # Determine date truncation
            if period == "day":
                date_trunc = "DATE_TRUNC('day', game_date)"
                interval = "30 days"
            elif period == "week":
                date_trunc = "DATE_TRUNC('week', game_date)"
                interval = "12 weeks"
            else:  # month
                date_trunc = "DATE_TRUNC('month', game_date)"
                interval = "12 months"
            
            trends = await conn.fetch(f"""
                SELECT 
                    {date_trunc} as period_start,
                    COUNT(*) as bets_count,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(bet_amount) as wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as profit
                FROM bets 
                WHERE game_status = 'completed' 
                AND game_date >= CURRENT_DATE - INTERVAL '{interval}'
                GROUP BY {date_trunc}
                ORDER BY period_start DESC
                LIMIT 20
            """)
            
            return [
                {
                    "period": row['period_start'].isoformat(),
                    "bets_count": row['bets_count'],
                    "wins": row['wins'],
                    "win_rate": round((row['wins'] / row['bets_count'] * 100), 2) if row['bets_count'] > 0 else 0,
                    "wagered": float(row['wagered']),
                    "profit": float(row['profit']),
                    "roi": round((row['profit'] / row['wagered'] * 100), 2) if row['wagered'] > 0 else 0
                }
                for row in trends
            ]
            
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/confidence-analysis",
            summary="Confidence Level Analysis",
            description="Analyze performance by confidence level")
async def get_confidence_analysis():
    """
    ## Confidence Level Analysis
    
    Analyze betting performance across different confidence levels to see
    which confidence ranges perform best.
    """
    try:
        async for conn in get_db_session():
            analysis = await conn.fetch("""
                SELECT 
                    confidence_level,
                    COUNT(*) as bet_count,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit,
                    AVG(bet_amount) as avg_bet_size
                FROM bets 
                WHERE game_status = 'completed'
                GROUP BY confidence_level
                ORDER BY confidence_level
            """)
            
            return [
                {
                    "confidence_level": row['confidence_level'],
                    "bet_count": row['bet_count'],
                    "wins": row['wins'],
                    "win_rate": round((row['wins'] / row['bet_count'] * 100), 2),
                    "total_wagered": float(row['total_wagered']),
                    "total_profit": float(row['total_profit']),
                    "roi": round((row['total_profit'] / row['total_wagered'] * 100), 2) if row['total_wagered'] > 0 else 0,
                    "avg_bet_size": round(float(row['avg_bet_size']), 2)
                }
                for row in analysis
            ]
            
    except Exception as e:
        logger.error(f"Error getting confidence analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bet-type-performance",
            summary="Bet Type Performance",
            description="Performance breakdown by bet type")
async def get_bet_type_performance():
    """
    ## Bet Type Performance
    
    Compare performance across different bet types (moneyline, spread, total, prop).
    """
    try:
        async for conn in get_db_session():
            performance = await conn.fetch("""
                SELECT 
                    bet_type,
                    COUNT(*) as bet_count,
                    SUM(CASE WHEN bet_result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN bet_result = 'loss' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN bet_result = 'push' THEN 1 ELSE 0 END) as pushes,
                    SUM(bet_amount) as total_wagered,
                    SUM(COALESCE(payout, 0) - bet_amount) as total_profit,
                    AVG(bet_amount) as avg_bet_size,
                    AVG(confidence_level) as avg_confidence
                FROM bets 
                WHERE game_status = 'completed'
                GROUP BY bet_type
                ORDER BY bet_count DESC
            """)
            
            return [
                {
                    "bet_type": row['bet_type'],
                    "bet_count": row['bet_count'],
                    "wins": row['wins'],
                    "losses": row['losses'],
                    "pushes": row['pushes'],
                    "win_rate": round((row['wins'] / (row['bet_count'] - row['pushes']) * 100), 2) if (row['bet_count'] - row['pushes']) > 0 else 0,
                    "total_wagered": float(row['total_wagered']),
                    "total_profit": float(row['total_profit']),
                    "roi": round((row['total_profit'] / row['total_wagered'] * 100), 2) if row['total_wagered'] > 0 else 0,
                    "avg_bet_size": round(float(row['avg_bet_size']), 2),
                    "avg_confidence": round(float(row['avg_confidence']), 1)
                }
                for row in performance
            ]
            
    except Exception as e:
        logger.error(f"Error getting bet type performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-activity",
            summary="Recent Betting Activity",
            description="Get recent betting activity and results")
async def get_recent_activity(
    limit: int = Query(10, description="Number of recent bets to return")
):
    """
    ## Recent Activity
    
    Get your most recent betting activity with outcomes.
    """
    try:
        async for conn in get_db_session():
            recent_bets = await conn.fetch("""
                SELECT 
                    game_id, home_team, away_team, game_date,
                    bet_type, bet_side, bet_amount, odds,
                    confidence_level, bet_result, payout,
                    actual_score_home, actual_score_away,
                    created_at
                FROM bets 
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            return [
                {
                    "game_id": row['game_id'],
                    "matchup": f"{row['away_team']} @ {row['home_team']}",
                    "game_date": row['game_date'].isoformat(),
                    "bet_type": row['bet_type'],
                    "bet_side": row['bet_side'],
                    "bet_amount": float(row['bet_amount']),
                    "odds": float(row['odds']) if row['odds'] else None,
                    "confidence": row['confidence_level'],
                    "result": row['bet_result'],
                    "payout": float(row['payout']) if row['payout'] else None,
                    "profit": float(row['payout'] - row['bet_amount']) if row['payout'] else None,
                    "final_score": f"{row['actual_score_away']}-{row['actual_score_home']}" if row['actual_score_home'] is not None else None,
                    "created_at": row['created_at'].isoformat()
                }
                for row in recent_bets
            ]
            
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))