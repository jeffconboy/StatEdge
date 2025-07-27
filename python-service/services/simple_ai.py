import httpx
import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SimpleAIService:
    """Simple AI service using direct HTTP calls to OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(self, messages: list, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Make a chat completion request to OpenAI API"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 800
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {e}")
            raise
    
    async def analyze_betting_context(self, query: str, context: Dict[str, Any]) -> str:
        """Analyze betting context using OpenAI"""
        
        system_prompt = """You are an elite sports betting analyst specializing in baseball props. Provide sharp, actionable betting analysis in clean, readable format.

Structure your response as:

RECOMMENDATION: Clear OVER/UNDER/PASS recommendation

CONFIDENCE: High/Moderate/Low confidence level

KEY METRICS: 
• Most important stat 1
• Most important stat 2  
• Most important stat 3

RECENT FORM: Contact quality and power trends from last 5 games based on Statcast data

RISK FACTORS:
• Key concern 1
• Key concern 2

VALUE ASSESSMENT: Why this bet has edge or should be avoided

IMPORTANT: Use only plain text with bullet points (•). Do NOT use markdown formatting like **bold** or *italic*. Write in clear, readable sentences without special formatting symbols."""

        user_prompt = f"""
Question: {query}

REAL PLAYER DATA FROM DATABASE:
{json.dumps(context, indent=2, default=str)}

This is LIVE data from our Statcast database with 493k+ pitch records. Analyze recent trends, power metrics, and current form to provide sharp betting insights.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Error in betting analysis: {e}")
            return f"Analysis temporarily unavailable. Based on the provided stats, this player shows interesting patterns worth monitoring. Sample size: {context.get('statcast_metrics', {}).get('sample_size', 'N/A')} tracked pitches."