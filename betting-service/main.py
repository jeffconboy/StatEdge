"""
Betting Service - Personal Bet Tracking
=======================================

Simplified microservice for tracking personal baseball betting predictions and outcomes.
No real-time odds or compliance features - just clean bet logging and analysis.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database.connection import get_db_session
from models.bets import *
from routers import bets, analytics, strategies, bankroll
from services.tank01_service import Tank01Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Betting Service...")
    
    # Initialize Tank01 service for odds data
    tank01 = Tank01Service()
    app.state.tank01 = tank01
    
    yield
    
    # Shutdown
    logger.info("Shutting down Betting Service...")

app = FastAPI(
    title="StatEdge Betting Service",
    description="""
    ## Personal Baseball Betting Tracker
    
    Simple microservice for tracking your personal baseball betting predictions and outcomes.
    
    ### Features
    - **Bet Logging**: Record your predictions with confidence levels and reasoning
    - **Outcome Tracking**: Track wins, losses, and calculate ROI
    - **Strategy Analysis**: Analyze which betting strategies work best
    - **Bankroll Management**: Monitor your betting bankroll over time
    - **Performance Analytics**: View detailed statistics and trends
    
    ### Bet Types Supported
    - **Moneyline**: Win/loss bets on teams
    - **Spread**: Point spread betting
    - **Totals**: Over/under run totals
    - **Player Props**: Individual player performance bets
    
    ### Data Sources
    - Tank01 API for live MLB odds and game data
    - Personal bet tracking database
    - StatEdge sports data integration
    
    ### No Real-Time Features
    This is a simplified personal tracker - no real-time odds monitoring,
    no compliance features, just clean bet logging for your own analysis.
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "StatEdge Betting Support",
        "email": "betting@statedge.com",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3007",
        "http://localhost:3008", 
        "http://localhost:3009"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bets.router, prefix="/api/bets", tags=["bets"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(bankroll.router, prefix="/api/bankroll", tags=["bankroll"])

@app.get("/", 
         summary="Betting Service Root",
         description="Welcome endpoint for the betting service",
         tags=["System"])
async def root():
    """
    ## Welcome to StatEdge Betting Service
    
    Personal betting tracker for baseball predictions and outcomes.
    
    ### Quick Start
    1. Log a new bet using `/api/bets/`
    2. View your betting history at `/api/bets/history`
    3. Check performance analytics at `/api/analytics/summary`
    4. Manage your bankroll via `/api/bankroll/`
    
    ### Documentation
    - Interactive API docs: `/docs`
    - OpenAPI schema: `/openapi.json`
    """
    return {
        "message": "StatEdge Betting Service",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "bets": "/api/bets/",
            "analytics": "/api/analytics/",
            "strategies": "/api/strategies/",
            "bankroll": "/api/bankroll/"
        }
    }

@app.get("/health",
         summary="Health Check",
         description="System health check for monitoring",
         tags=["System"])
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "service": "betting-service"
    }

@app.get("/api/games/today",
         summary="Today's MLB Games",
         description="Get today's MLB games with current odds for betting reference",
         tags=["Games"])
async def get_todays_games():
    """
    ## Today's MLB Games
    
    Get today's MLB games with current odds from Tank01 API.
    Useful for finding games to bet on.
    
    ### Response Format
    ```json
    {
        "success": true,
        "games": [
            {
                "game_id": "20250726_BOS@NYY",
                "home_team": "NYY",
                "away_team": "BOS",
                "game_time": "7:05p",
                "odds": {
                    "home_ml": -150,
                    "away_ml": 130,
                    "total_over": 8.5
                }
            }
        ]
    }
    ```
    """
    try:
        tank01 = app.state.tank01
        
        # Get today's games
        today = datetime.now().strftime("%Y%m%d")
        games_data = await tank01.get_games_for_date(today)
        
        if not games_data:
            return {
                "success": False,
                "message": "No games found for today",
                "games": []
            }
        
        # Get current odds
        odds_data = await tank01.get_betting_odds()
        
        # Combine game and odds data
        games_with_odds = []
        for game in games_data:
            game_id = game.get('gameID', '')
            
            # Find odds for this game
            game_odds = {}
            if odds_data:
                for odds_game in odds_data:
                    if odds_game.get('gameID') == game_id:
                        game_odds = {
                            'home_ml': odds_game.get('homeML'),
                            'away_ml': odds_game.get('awayML'),
                            'home_spread': odds_game.get('homeSpread'),
                            'total_over': odds_game.get('totalOver'),
                            'total_under': odds_game.get('totalUnder')
                        }
                        break
            
            games_with_odds.append({
                'game_id': game_id,
                'home_team': game.get('home', ''),
                'away_team': game.get('away', ''),
                'game_time': game.get('gameTime', ''),
                'game_date': game.get('gameDate', ''),
                'game_status': game.get('gameStatus', ''),
                'odds': game_odds
            })
        
        return {
            "success": True,
            "games": games_with_odds,
            "count": len(games_with_odds),
            "date": today,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting today's games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get games: {str(e)}")

@app.get("/api/games/{game_id}/odds",
         summary="Game Odds",
         description="Get current odds for a specific game",
         tags=["Games"])
async def get_game_odds(game_id: str):
    """
    ## Game Specific Odds
    
    Get current betting odds for a specific MLB game.
    
    ### Parameters
    - **game_id**: Game identifier (e.g., "20250726_BOS@NYY")
    
    ### Response Format
    ```json
    {
        "success": true,
        "game_id": "20250726_BOS@NYY",
        "odds": {
            "moneyline": {"home": -150, "away": 130},
            "spread": {"home": {"line": -1.5, "odds": 110}},
            "total": {"over": {"line": 8.5, "odds": -110}}
        }
    }
    ```
    """
    try:
        tank01 = app.state.tank01
        odds_data = await tank01.get_betting_odds()
        
        if not odds_data:
            raise HTTPException(status_code=500, detail="Failed to fetch odds data")
        
        # Find specific game odds
        for game in odds_data:
            if game.get('gameID') == game_id:
                return {
                    "success": True,
                    "game_id": game_id,
                    "home_team": game.get('home', ''),
                    "away_team": game.get('away', ''),
                    "odds": {
                        "moneyline": {
                            "home": game.get('homeML'),
                            "away": game.get('awayML')
                        },
                        "spread": {
                            "home": {
                                "line": game.get('homeSpread'),
                                "odds": game.get('homeSpreadOdds')
                            },
                            "away": {
                                "line": game.get('awaySpread'), 
                                "odds": game.get('awaySpreadOdds')
                            }
                        },
                        "total": {
                            "over": {
                                "line": game.get('totalOver'),
                                "odds": game.get('totalOverOdds')
                            },
                            "under": {
                                "line": game.get('totalUnder'),
                                "odds": game.get('totalUnderOdds')
                            }
                        }
                    },
                    "last_updated": datetime.now()
                }
        
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting odds for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get odds: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18002)