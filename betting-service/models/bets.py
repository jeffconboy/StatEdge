"""
Betting Data Models
==================

Pydantic models for betting service API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum

class BetType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PROP = "prop"

class BetSide(str, Enum):
    HOME = "home"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"
    YES = "yes"
    NO = "no"

class BetResult(str, Enum):
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    VOID = "void"

class GameStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Sport(str, Enum):
    MLB = "MLB"
    NBA = "NBA"
    NFL = "NFL"
    NHL = "NHL"

# Request Models
class CreateBetRequest(BaseModel):
    """Request model for creating a new bet"""
    game_id: str = Field(..., description="Unique game identifier")
    sport: Sport = Field(Sport.MLB, description="Sport type")
    home_team: str = Field(..., description="Home team abbreviation")
    away_team: str = Field(..., description="Away team abbreviation")
    game_date: date = Field(..., description="Game date")
    game_time: Optional[time] = Field(None, description="Game time")
    
    # Bet Details
    bet_type: BetType = Field(..., description="Type of bet")
    bet_side: BetSide = Field(..., description="Side of the bet")
    bet_amount: float = Field(..., description="Amount wagered", gt=0)
    odds: Optional[float] = Field(None, description="American odds format")
    
    # Prediction Details
    confidence_level: int = Field(..., description="Confidence level 1-10", ge=1, le=10)
    prediction_reasoning: Optional[str] = Field(None, description="Reasoning for the bet")
    predicted_score_home: Optional[int] = Field(None, description="Predicted home team score")
    predicted_score_away: Optional[int] = Field(None, description="Predicted away team score")
    
    # Optional categorization
    category_ids: Optional[List[int]] = Field([], description="Bet category IDs")
    strategy_ids: Optional[List[int]] = Field([], description="Strategy IDs")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('odds')
    def validate_odds(cls, v):
        if v is not None and (v < -1000 or v > 1000):
            raise ValueError('Odds must be between -1000 and +1000')
        return v

class UpdateBetRequest(BaseModel):
    """Request model for updating a bet"""
    confidence_level: Optional[int] = Field(None, ge=1, le=10)
    prediction_reasoning: Optional[str] = None
    predicted_score_home: Optional[int] = None
    predicted_score_away: Optional[int] = None
    notes: Optional[str] = None
    category_ids: Optional[List[int]] = None
    strategy_ids: Optional[List[int]] = None

class SettleBetRequest(BaseModel):
    """Request model for settling a bet with outcome"""
    actual_score_home: int = Field(..., description="Actual home team score")
    actual_score_away: int = Field(..., description="Actual away team score")
    bet_result: BetResult = Field(..., description="Bet outcome")
    payout: Optional[float] = Field(None, description="Payout amount", ge=0)
    notes: Optional[str] = Field(None, description="Settlement notes")

class CreatePlayerPropRequest(BaseModel):
    """Request model for creating a player prop bet"""
    bet_id: int = Field(..., description="Related bet ID")
    player_id: str = Field(..., description="Player identifier")
    player_name: str = Field(..., description="Player full name")
    prop_type: str = Field(..., description="Type of prop (hits, runs, rbis, etc.)")
    prop_line: float = Field(..., description="Prop bet line")

class UpdatePlayerPropRequest(BaseModel):
    """Request model for updating player prop outcome"""
    actual_result: float = Field(..., description="Actual statistical result")

# Response Models
class BetResponse(BaseModel):
    """Response model for bet data"""
    id: int
    game_id: str
    sport: str
    home_team: str
    away_team: str
    game_date: date
    game_time: Optional[time]
    
    # Bet Details
    bet_type: str
    bet_side: str
    bet_amount: float
    odds: Optional[float]
    implied_probability: Optional[float]
    
    # Prediction Details
    confidence_level: int
    prediction_reasoning: Optional[str]
    predicted_score_home: Optional[int]
    predicted_score_away: Optional[int]
    
    # Outcome
    game_status: str
    actual_score_home: Optional[int]
    actual_score_away: Optional[int]
    bet_result: Optional[str]
    payout: Optional[float]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    notes: Optional[str]
    
    # Calculated fields
    potential_payout: Optional[float] = None
    profit_loss: Optional[float] = None

    class Config:
        from_attributes = True

class BetSummaryResponse(BaseModel):
    """Summary statistics for bets"""
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_percentage: Optional[float]
    total_wagered: float
    total_profit: float
    roi_percentage: Optional[float]
    
    # Breakdown by type
    by_bet_type: Optional[Dict] = None
    by_sport: Optional[Dict] = None

class BankrollRequest(BaseModel):
    """Request model for bankroll entry"""
    date: date = Field(..., description="Date of bankroll entry")
    starting_balance: float = Field(..., description="Starting balance", gt=0)
    ending_balance: float = Field(..., description="Ending balance", gt=0)
    total_wagered: Optional[float] = Field(0, description="Total amount wagered")
    number_of_bets: Optional[int] = Field(0, description="Number of bets placed")
    notes: Optional[str] = Field(None, description="Daily notes")

class BankrollResponse(BaseModel):
    """Response model for bankroll data"""
    id: int
    date: date
    starting_balance: float
    ending_balance: float
    daily_pnl: float
    total_wagered: float
    number_of_bets: int
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BetCategoryRequest(BaseModel):
    """Request model for bet category"""
    category_name: str = Field(..., description="Category name", max_length=50)
    description: Optional[str] = Field(None, description="Category description")
    color_code: Optional[str] = Field("#007bff", description="Hex color code")

class BetCategoryResponse(BaseModel):
    """Response model for bet category"""
    id: int
    category_name: str
    description: Optional[str]
    color_code: str
    
    class Config:
        from_attributes = True

class BettingStrategyRequest(BaseModel):
    """Request model for betting strategy"""
    strategy_name: str = Field(..., description="Strategy name", max_length=100)
    description: Optional[str] = Field(None, description="Strategy description")
    criteria: Optional[Dict[str, Any]] = Field({}, description="Strategy criteria as JSON")

class BettingStrategyResponse(BaseModel):
    """Response model for betting strategy with performance"""
    id: int
    strategy_name: str
    description: Optional[str]
    criteria: Dict[str, Any]
    
    # Performance metrics
    total_bets: int
    wins: int
    losses: int
    pushes: int
    total_wagered: float
    total_profit: float
    win_rate: Optional[float]
    roi: Optional[float]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PlayerPropResponse(BaseModel):
    """Response model for player prop bet"""
    id: int
    bet_id: int
    player_id: str
    player_name: str
    prop_type: str
    prop_line: float
    actual_result: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True