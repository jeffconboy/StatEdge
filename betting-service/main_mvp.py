"""
MVP Betting Service - Launch Ready
=================================

Super simple betting service for tomorrow's launch.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
import asyncpg
import os
import json

app = FastAPI(
    title="StatEdge Betting MVP",
    description="Simple betting prediction service",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = os.getenv("BETTING_DATABASE_URL", "postgresql://betting_user:betting_secure_2025@host.docker.internal:5432/betting_data")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "betting-mvp",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StatEdge Betting MVP",
        "status": "running",
        "docs": "/docs"
    }

# Simple data models using basic Python types
@app.post("/predictions")
async def create_prediction(
    game_id: str,
    team: str,
    bet_type: str,
    prediction: str,
    confidence: float,
    reasoning: str
):
    """Create a betting prediction"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        INSERT INTO bets (game_id, bet_type, team, prediction, confidence, reasoning, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        
        bet_id = await conn.fetchval(
            query, 
            game_id, 
            bet_type, 
            team, 
            prediction, 
            confidence, 
            reasoning, 
            datetime.now()
        )
        
        await conn.close()
        
        return {
            "id": bet_id,
            "game_id": game_id,
            "team": team,
            "prediction": prediction,
            "confidence": confidence,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/predictions")
async def get_predictions():
    """Get all predictions"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        SELECT id, game_id, bet_type, team, prediction, confidence, reasoning, created_at
        FROM bets
        ORDER BY created_at DESC
        LIMIT 50
        """
        
        rows = await conn.fetch(query)
        await conn.close()
        
        predictions = []
        for row in rows:
            predictions.append({
                "id": row["id"],
                "game_id": row["game_id"],
                "bet_type": row["bet_type"],
                "team": row["team"],
                "prediction": row["prediction"],
                "confidence": float(row["confidence"]),
                "reasoning": row["reasoning"],
                "created_at": row["created_at"].isoformat()
            })
        
        return {"predictions": predictions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/predictions/today")
async def get_todays_predictions():
    """Get today's predictions"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        SELECT id, game_id, bet_type, team, prediction, confidence, reasoning, created_at
        FROM bets
        WHERE DATE(created_at) = CURRENT_DATE
        ORDER BY confidence DESC
        """
        
        rows = await conn.fetch(query)
        await conn.close()
        
        predictions = []
        for row in rows:
            predictions.append({
                "id": row["id"],
                "game_id": row["game_id"],
                "bet_type": row["bet_type"],
                "team": row["team"],
                "prediction": row["prediction"],
                "confidence": float(row["confidence"]),
                "reasoning": row["reasoning"],
                "created_at": row["created_at"].isoformat()
            })
        
        return {
            "date": datetime.now().date().isoformat(),
            "predictions": predictions,
            "count": len(predictions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18002)