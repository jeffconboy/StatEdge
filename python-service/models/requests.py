from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class PlayerSearchRequest(BaseModel):
    query: str
    limit: int = 10

class PlayerStatsRequest(BaseModel):
    player_id: int
    season: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    stat_types: List[str] = ["batting", "pitching", "statcast"]

class NaturalLanguageQueryRequest(BaseModel):
    query: str
    user_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None

class PropBetAnalysisRequest(BaseModel):
    player_name: str
    prop_type: str
    betting_line: float
    game_context: Optional[Dict[str, Any]] = None

class DataCollectionRequest(BaseModel):
    date: Optional[str] = None
    data_sources: List[str] = ["statcast", "fangraphs", "mlb_api"]
    force_refresh: bool = False

class PlayerStatsResponse(BaseModel):
    player_info: Dict[str, Any]
    statcast_data: Optional[List[Dict[str, Any]]] = None
    fangraphs_batting: Optional[List[Dict[str, Any]]] = None
    fangraphs_pitching: Optional[List[Dict[str, Any]]] = None
    
class AIQueryResponse(BaseModel):
    query: str
    intent: Dict[str, Any]
    data: Dict[str, Any]
    explanation: str
    suggestions: List[str]

class PropBetAnalysisResponse(BaseModel):
    probability_over: float
    probability_under: float
    confidence: int
    recommendation: str
    key_factors: List[str]
    risk_factors: List[str]
    reasoning: str