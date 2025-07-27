from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.connection import get_db_session
from services.ai_assistant import AIAssistant
from services.simple_ai import SimpleAIService
from models.requests import (
    NaturalLanguageQueryRequest, 
    PropBetAnalysisRequest,
    AIQueryResponse,
    PropBetAnalysisResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/simple-chat")
async def simple_ai_chat(request: dict):
    """Simple AI chat endpoint using direct OpenAI API calls"""
    
    try:
        query = request.get("query", "")
        context = request.get("context", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        simple_ai = SimpleAIService()
        explanation = await simple_ai.analyze_betting_context(query, context)
        
        return {
            "explanation": explanation,
            "query": query,
            "data": context,
            "suggestions": [
                "How does this compare to league average?",
                "What about recent trends?",
                "Show me situational splits"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in simple AI chat: {str(e)}")
        return {
            "explanation": f"Analysis temporarily unavailable due to: {str(e)}. However, based on the provided stats, interesting patterns can be observed in the player's performance metrics.",
            "query": query,
            "error": str(e)
        }

@router.post("/chat", response_model=AIQueryResponse)
async def ai_chat(
    request: NaturalLanguageQueryRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Process natural language queries about baseball statistics"""
    
    try:
        ai_assistant = AIAssistant()
        result = await ai_assistant.process_natural_language_query(
            request.query, 
            session
        )
        
        return AIQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/analyze-prop", response_model=PropBetAnalysisResponse)
async def analyze_prop_bet(
    request: PropBetAnalysisRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """AI analysis of prop betting opportunities"""
    
    try:
        ai_assistant = AIAssistant()
        analysis = await ai_assistant.analyze_prop_bet(
            session,
            request.player_name,
            request.prop_type,
            request.betting_line
        )
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return PropBetAnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing prop bet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/explain-stats")
async def explain_statistics(
    player_name: str,
    statistics: list,
    session: AsyncSession = Depends(get_db_session)
):
    """Get AI explanation of specific statistics"""
    
    try:
        ai_assistant = AIAssistant()
        
        # Create a query to get the requested stats
        query_text = f"Explain {', '.join(statistics)} for {player_name}"
        
        result = await ai_assistant.process_natural_language_query(
            query_text, 
            session
        )
        
        return {
            "player": player_name,
            "statistics": statistics,
            "explanation": result["explanation"],
            "data": result["data"]
        }
        
    except Exception as e:
        logger.error(f"Error explaining statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

@router.get("/suggestions")
async def get_query_suggestions():
    """Get suggested queries for users"""
    
    suggestions = [
        "Show me Aaron Judge's exit velocity this season",
        "Compare Kyle Schwarber vs left-handed pitchers",
        "What is Shohei Ohtani's performance in day games?",
        "Show me the top 5 players by barrel rate",
        "How does Vladimir Guerrero Jr perform at home vs away?",
        "What are Jacob deGrom's advanced pitching metrics?",
        "Show me Juan Soto's plate discipline statistics",
        "Compare Mike Trout's 2024 vs 2023 performance"
    ]
    
    return {"suggestions": suggestions}

@router.post("/batch-analyze")
async def batch_analyze_players(
    queries: list,
    session: AsyncSession = Depends(get_db_session)
):
    """Process multiple AI queries in batch"""
    
    try:
        ai_assistant = AIAssistant()
        results = []
        
        for query in queries[:5]:  # Limit to 5 queries per batch
            try:
                result = await ai_assistant.process_natural_language_query(
                    query, 
                    session
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Check if AI services are working"""
    
    try:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {
                "status": "unhealthy",
                "error": "OPENAI_API_KEY not configured"
            }
            
        return {
            "status": "healthy",
            "ai_service": "configured",
            "api_key_present": bool(api_key),
            "features": [
                "natural_language_queries",
                "prop_bet_analysis", 
                "statistical_explanations",
                "batch_processing"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }