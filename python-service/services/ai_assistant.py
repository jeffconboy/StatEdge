from openai import AsyncOpenAI
import json
import os
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def process_natural_language_query(
        self, 
        user_query: str, 
        session: AsyncSession
    ) -> Dict:
        """Convert natural language to database query and execute"""
        
        try:
            # Step 1: Parse the user's intent
            query_intent = await self._parse_query_intent(user_query)
            
            # Step 2: Generate and execute database query
            query_results = await self._execute_statistical_query(
                query_intent, session
            )
            
            # Step 3: Generate AI explanation
            explanation = await self._generate_explanation(
                user_query, query_results
            )
            
            return {
                "query": user_query,
                "intent": query_intent,
                "data": query_results,
                "explanation": explanation,
                "suggestions": await self._generate_follow_up_questions(query_results)
            }
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {str(e)}")
            raise
    
    async def _parse_query_intent(self, user_query: str) -> Dict:
        """Use OpenAI to parse user intent into structured query"""
        
        system_prompt = """
        You are a baseball analytics expert. Convert natural language queries into structured database parameters.
        
        Available data sources:
        - Statcast pitch-level data (100+ fields): exit_velocity, launch_angle, barrel_rate, etc.
        - FanGraphs batting stats (300+ fields): wOBA, wRC+, OPS, situational splits
        - FanGraphs pitching stats (300+ fields): FIP, xFIP, K%, BB%, etc.
        
        Return JSON format:
        {
            "player_names": ["Player Name"],
            "statistics": ["stat1", "stat2"],
            "filters": {
                "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
                "opponent_type": "LHP|RHP",
                "situation": "home|away|day|night"
            },
            "data_sources": ["statcast", "fangraphs_batting", "fangraphs_pitching"],
            "aggregation": "avg|sum|count|recent"
        }
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            parsed_intent = json.loads(response.choices[0].message.content)
            return parsed_intent
            
        except Exception as e:
            logger.error(f"Error parsing query intent: {str(e)}")
            # Fallback to simple parsing
            return {
                "player_names": [user_query],  # Assume it's a player name
                "statistics": ["*"],
                "filters": {},
                "data_sources": ["statcast", "fangraphs_batting"],
                "aggregation": "recent"
            }
    
    async def _execute_statistical_query(
        self, 
        query_intent: Dict, 
        session: AsyncSession
    ) -> Dict:
        """Execute database queries based on parsed intent"""
        
        results = {}
        player_names = query_intent.get("player_names", [])
        
        for player_name in player_names:
            player_data = {}
            
            # Get player info
            player_info = await self._get_player_info(session, player_name)
            if not player_info:
                continue
                
            player_data["player_info"] = player_info
            
            # Get requested data sources
            data_sources = query_intent.get("data_sources", [])
            
            if "statcast" in data_sources:
                player_data["statcast"] = await self._get_statcast_data(
                    session, player_info["mlb_id"], query_intent
                )
            
            if "fangraphs_batting" in data_sources:
                player_data["fangraphs_batting"] = await self._get_fangraphs_batting(
                    session, player_info["id"], query_intent
                )
            
            if "fangraphs_pitching" in data_sources:
                player_data["fangraphs_pitching"] = await self._get_fangraphs_pitching(
                    session, player_info["id"], query_intent
                )
            
            results[player_name] = player_data
        
        return results
    
    async def _get_player_info(self, session: AsyncSession, player_name: str) -> Optional[Dict]:
        """Get basic player information"""
        
        query = text("""
            SELECT id, mlb_id, name, current_team, primary_position, bio_data
            FROM players 
            WHERE name ILIKE :name 
            LIMIT 1
        """)
        
        result = await session.execute(query, {"name": f"%{player_name}%"})
        row = result.fetchone()
        
        if row:
            return {
                "id": row[0],
                "mlb_id": row[1],
                "name": row[2],
                "team": row[3],
                "position": row[4],
                "bio": json.loads(row[5]) if row[5] else {}
            }
        
        return None
    
    async def _get_statcast_data(
        self, 
        session: AsyncSession, 
        mlb_id: int, 
        query_intent: Dict
    ) -> List[Dict]:
        """Get Statcast data with ALL fields preserved"""
        
        # Build dynamic query based on filters
        base_query = """
            SELECT statcast_data, game_date
            FROM statcast_pitches 
            WHERE batter_id = :mlb_id
        """
        
        params = {"mlb_id": mlb_id}
        
        # Add date filters
        filters = query_intent.get("filters", {})
        if "date_range" in filters:
            base_query += " AND game_date BETWEEN :start_date AND :end_date"
            params["start_date"] = filters["date_range"]["start"]
            params["end_date"] = filters["date_range"]["end"]
        else:
            # Default to last 30 days
            base_query += " AND game_date >= CURRENT_DATE - INTERVAL '30 days'"
        
        base_query += " ORDER BY game_date DESC LIMIT 1000"
        
        result = await session.execute(text(base_query), params)
        rows = result.fetchall()
        
        return [
            {
                "data": json.loads(row[0]),
                "game_date": row[1].isoformat()
            }
            for row in rows
        ]
    
    async def _get_fangraphs_batting(
        self, 
        session: AsyncSession, 
        player_id: int, 
        query_intent: Dict
    ) -> List[Dict]:
        """Get FanGraphs batting data with ALL fields preserved"""
        
        query = text("""
            SELECT batting_stats, season, split_type, date_range_start, date_range_end
            FROM fangraphs_batting 
            WHERE player_id = :player_id
            ORDER BY season DESC, date_range_start DESC
        """)
        
        result = await session.execute(query, {"player_id": player_id})
        rows = result.fetchall()
        
        return [
            {
                "stats": json.loads(row[0]),
                "season": row[1],
                "split_type": row[2],
                "date_range": {
                    "start": row[3].isoformat() if row[3] else None,
                    "end": row[4].isoformat() if row[4] else None
                }
            }
            for row in rows
        ]
    
    async def _get_fangraphs_pitching(
        self, 
        session: AsyncSession, 
        player_id: int, 
        query_intent: Dict
    ) -> List[Dict]:
        """Get FanGraphs pitching data with ALL fields preserved"""
        
        query = text("""
            SELECT pitching_stats, season, split_type, date_range_start, date_range_end
            FROM fangraphs_pitching 
            WHERE player_id = :player_id
            ORDER BY season DESC, date_range_start DESC
        """)
        
        result = await session.execute(query, {"player_id": player_id})
        rows = result.fetchall()
        
        return [
            {
                "stats": json.loads(row[0]),
                "season": row[1],
                "split_type": row[2],
                "date_range": {
                    "start": row[3].isoformat() if row[3] else None,
                    "end": row[4].isoformat() if row[4] else None
                }
            }
            for row in rows
        ]
    
    async def _generate_explanation(
        self, 
        user_query: str, 
        query_results: Dict
    ) -> str:
        """Generate AI explanation of the statistical results"""
        
        explanation_prompt = f"""
        The user asked: "{user_query}"
        
        Here are the statistical results:
        {json.dumps(query_results, indent=2, default=str)[:2000]}...
        
        Provide a clear, concise explanation of:
        1. What the numbers show
        2. Key insights for sports betting
        3. Notable trends or patterns
        4. Context for the statistics
        
        Keep it under 200 words and focus on actionable insights.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional baseball analyst specializing in betting insights."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return "Statistical data retrieved successfully. Analysis available on request."
    
    async def _generate_follow_up_questions(self, query_results: Dict) -> List[str]:
        """Generate relevant follow-up questions"""
        
        questions = [
            "How does this compare to league average?",
            "What about situational splits (home/away, day/night)?",
            "Show me recent game-by-game performance",
            "How does this translate to betting value?"
        ]
        
        return questions[:3]  # Return top 3 suggestions
    
    async def analyze_prop_bet(
        self, 
        session: AsyncSession,
        player_name: str, 
        prop_type: str, 
        betting_line: float
    ) -> Dict:
        """AI analysis of prop betting opportunities"""
        
        try:
            # Get comprehensive player data
            player_query = {
                "player_names": [player_name],
                "statistics": ["*"],
                "data_sources": ["statcast", "fangraphs_batting", "fangraphs_pitching"],
                "filters": {"date_range": {"start": "2024-01-01", "end": "2024-12-31"}}
            }
            
            player_data = await self._execute_statistical_query(player_query, session)
            
            # Generate AI analysis
            analysis_prompt = f"""
            Analyze this prop bet:
            Player: {player_name}
            Prop Type: {prop_type}
            Line: {betting_line}
            
            Player Statistics:
            {json.dumps(player_data, indent=2, default=str)[:3000]}...
            
            Provide:
            1. Probability assessment (0-100%)
            2. Key supporting factors
            3. Risk factors
            4. Confidence level (1-10)
            5. Recommendation (OVER/UNDER/PASS)
            
            Format as JSON:
            {
                "probability_over": 65,
                "probability_under": 35,
                "confidence": 7,
                "recommendation": "OVER",
                "key_factors": ["factor1", "factor2"],
                "risk_factors": ["risk1", "risk2"],
                "reasoning": "Detailed explanation..."
            }
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sports betting analyst."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error analyzing prop bet: {str(e)}")
            return {
                "error": "Analysis unavailable",
                "recommendation": "PASS"
            }