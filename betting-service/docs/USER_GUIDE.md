# User Guide

## StatEdge Betting Service User Guide

A comprehensive guide to using the StatEdge Betting Service for personal baseball betting prediction tracking.

---

## Getting Started

### What is the Betting Service?

The StatEdge Betting Service is a **personal betting tracker** designed to help you:
- Log your betting predictions before games
- Track outcomes and calculate your ROI
- Analyze which betting strategies work best
- Manage your betting bankroll over time
- Learn from your betting patterns

### What it's NOT
- ❌ Not a real-time betting platform
- ❌ Not connected to sportsbooks
- ❌ No automated betting features
- ❌ No real money transactions

It's a **personal analytics tool** to make you a better bettor through data-driven insights.

---

## Core Concepts

### Bet Types

#### Moneyline
Bet on which team will win the game.
- **Example**: Yankees -150, Red Sox +130
- **Meaning**: Bet $150 to win $100 on Yankees, or bet $100 to win $130 on Red Sox

#### Spread (Run Line)
Bet on the margin of victory.
- **Example**: Yankees -1.5 (-110), Red Sox +1.5 (-110)
- **Meaning**: Yankees must win by 2+ runs, Red Sox must lose by 1 or win

#### Total (Over/Under)
Bet on total runs scored by both teams.
- **Example**: Over 8.5 (-110), Under 8.5 (-110)
- **Meaning**: Combined score must be 9+ (over) or 8 or less (under)

#### Props (Propositions)
Bet on individual player or game statistics.
- **Examples**: 
  - Aaron Judge Over 1.5 hits
  - Gerrit Cole Over 7.5 strikeouts
  - First inning runs: Yes/No

### Confidence Levels (1-10 Scale)

Use this scale to rate your confidence in each bet:

- **1-2**: Experimental/fun bets with little analysis
- **3-4**: Slight lean based on basic analysis
- **5-6**: Moderate confidence with decent research
- **7-8**: High confidence with strong analysis
- **9-10**: Maximum confidence "lock" bets

### Betting Strategies

Organize your bets by strategy to see what approaches work:

- **Home Favorites**: Betting on favored home teams
- **Value Bets**: Finding good odds vs true probability
- **Starting Pitcher**: Basing bets on pitching matchups
- **Weather/Conditions**: Factoring in game conditions
- **Revenge Spots**: Teams motivated after recent losses

---

## Using the Service

### 1. Logging Your First Bet

Before any game, record your prediction:

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
  "prediction_reasoning": "Yankees have Gerrit Cole pitching vs weak Boston lineup. Home field advantage in crucial series."
}
```

**Key Tips:**
- ✅ **Be honest** - Record actual predictions, not post-game rationalization
- ✅ **Include reasoning** - Write why you're making the bet
- ✅ **Set confidence** - Rate your actual confidence level
- ✅ **Use categories** - Tag bets for better organization

### 2. Getting Today's Games and Odds

Check what games are available today:

**API Call**: `GET /api/games/today`

This returns:
- Today's MLB schedule
- Current odds from Tank01 API
- Game times and status
- Team matchups

Use this to find games you want to bet on and get current odds for reference.

### 3. Settling Bets After Games

After games finish, record the outcomes:

```json
{
  "actual_score_home": 6,
  "actual_score_away": 4,
  "bet_result": "win",
  "notes": "Cole pitched 7 strong innings as predicted"
}
```

The service automatically:
- Calculates your payout based on odds
- Updates your win/loss record
- Adjusts strategy performance metrics
- Tracks profit/loss

### 4. Tracking Your Bankroll

Record your daily betting bankroll:

```json
{
  "date": "2025-07-26",
  "starting_balance": 1000.00,
  "ending_balance": 1050.00,
  "total_wagered": 200.00,
  "number_of_bets": 3,
  "notes": "Good day with 2/3 wins"
}
```

This helps you:
- Monitor bankroll growth/decline
- Track daily profit/loss
- See betting volume patterns
- Practice money management

---

## Analytics and Insights

### Performance Summary

Get your overall betting performance:

**API Call**: `GET /api/analytics/summary?days=30`

**Key Metrics:**
- **Win Rate**: Percentage of bets won (excluding pushes)
- **ROI**: Return on investment percentage
- **Total Profit**: Net profit/loss in dollars
- **Average Confidence**: Your average confidence level

### Confidence Analysis

See how your confidence correlates with success:

**API Call**: `GET /api/analytics/confidence-analysis`

**Questions Answered:**
- Do your high-confidence bets actually win more?
- What confidence level gives you the best ROI?
- Are you overconfident or underconfident?

**Example Insights:**
- Confidence 8+ bets: 75% win rate, 25% ROI
- Confidence 5-6 bets: 45% win rate, -5% ROI
- **Conclusion**: Trust your high-confidence reads!

### Bet Type Performance

Compare performance across different bet types:

**API Call**: `GET /api/analytics/bet-type-performance`

**Example Results:**
- **Moneyline**: 65% win rate, 18% ROI (your strength)
- **Totals**: 52% win rate, 3% ROI (break even)
- **Props**: 58% win rate, 12% ROI (decent)
- **Spreads**: 48% win rate, -8% ROI (avoid these)

### Strategy Performance

Track which approaches work best:

**API Call**: `GET /api/strategies/{id}/performance`

**Example Strategy Analysis:**
- **"Home Favorites"**: 15 bets, 70% win rate, 22% ROI
- **"Value Underdogs"**: 8 bets, 50% win rate, 15% ROI
- **"Starting Pitcher"**: 20 bets, 65% win rate, 18% ROI

---

## Best Practices

### Bet Logging Best Practices

#### 1. Log Before Games Start
Record predictions **before** first pitch, not during or after games. This ensures honest self-assessment.

#### 2. Include Detailed Reasoning
Write down **why** you're making each bet:
- **Good**: "Cole (2.89 ERA) vs weak Boston offense (22nd in runs). Yankees 8-2 at home vs AL East."
- **Bad**: "Yankees look good"

#### 3. Use Consistent Unit Sizing
Base bet amounts on your bankroll:
- **Conservative**: 1-2% of bankroll per bet
- **Moderate**: 2-5% of bankroll per bet
- **Aggressive**: 5-10% of bankroll per bet

#### 4. Rate Confidence Honestly
Don't inflate confidence levels. Use the full 1-10 scale:
- Most bets should be 5-7 range
- Reserve 8+ for truly strong spots
- Use 1-3 for experimental bets

### Bankroll Management

#### Daily Tracking
Record your bankroll every day you bet:
- Starting balance
- Ending balance
- Amount wagered
- Number of bets placed

#### Set Loss Limits
Establish rules like:
- Maximum 5% of bankroll per day
- Stop betting after 3 consecutive losses
- Take breaks after big losing days

#### Profit Goals
Set realistic targets:
- 10-20% annual ROI is excellent
- Focus on process over results
- Bankroll preservation over huge wins

### Strategy Development

#### 1. Define Clear Criteria
Create specific rules for each strategy:

**Example - "Home Favorites" Strategy:**
```json
{
  "criteria": {
    "team_location": "home",
    "max_odds": -200,
    "min_odds": -120,
    "min_confidence": 6,
    "division_games_only": true
  }
}
```

#### 2. Track Everything
Link every bet to relevant strategies for proper analysis.

#### 3. Be Patient
Give strategies time to prove themselves:
- Minimum 20-30 bets before evaluation
- Look for consistent patterns
- Don't abandon after short losing streaks

#### 4. Adapt Based on Data
Modify strategies based on performance:
- Tighten criteria for losing strategies
- Increase bet sizing for profitable strategies
- Eliminate consistently losing approaches

---

## Common Workflows

### Weekly Routine

#### Sunday: Planning
1. Review previous week's performance
2. Analyze upcoming week's games
3. Set betting budget for the week
4. Update bankroll tracking

#### Daily: Game Day
1. Check today's games and odds
2. Analyze matchups using your criteria
3. Log predictions before games start
4. Monitor games (but don't change bets)

#### Evening: Settlement
1. Update game results
2. Settle completed bets
3. Record daily bankroll changes
4. Make notes on what worked/didn't work

#### Monthly: Analysis
1. Run comprehensive performance reports
2. Analyze strategy effectiveness
3. Adjust betting approaches based on data
4. Set goals for next month

### Finding Betting Opportunities

#### 1. Get Today's Games
```bash
GET /api/games/today
```

#### 2. Analyze Matchups
Look for:
- Pitching advantages
- Offensive/defensive mismatches
- Weather conditions
- Team motivation factors
- Recent form

#### 3. Check Your Strategies
Apply your proven strategies:
- Do any games fit your "Home Favorite" criteria?
- Any good "Starting Pitcher" spots?
- Value opportunities in underdog prices?

#### 4. Set Confidence Levels
Rate each potential bet:
- How strong is your analysis?
- How much edge do you think you have?
- Are you forcing bets or finding genuine value?

#### 5. Log Your Predictions
Record all bets before games start with reasoning.

---

## Advanced Features

### Custom Categories

Organize bets beyond the default categories:

```json
{
  "category_name": "Playoff Race Spots",
  "description": "Teams fighting for playoff positioning",
  "color_code": "#ff6b35"
}
```

### Player Props Tracking

For player proposition bets:

```json
{
  "player_name": "Aaron Judge",
  "prop_type": "home_runs",
  "prop_line": 0.5,
  "actual_result": 1
}
```

### Strategy Criteria JSON

Define complex strategy rules:

```json
{
  "min_temperature": 70,
  "max_wind_speed": 10,
  "home_team_last_10": ">=7",
  "starting_pitcher_era": "<=3.50",
  "opposing_team_vs_rhp": "<=.250"
}
```

---

## Tips for Success

### Analytical Approach

#### 1. Focus on Process
- Good process with small edge beats lucky guessing
- Track decision-making quality, not just results
- Short-term variance is normal

#### 2. Use Multiple Data Sources
- StatEdge sports data for advanced metrics
- Tank01 odds for line shopping
- Weather and injury reports
- Team news and motivation factors

#### 3. Specialize
- Become expert in specific areas
- Maybe focus on AL East teams you know well
- Or specialize in starting pitcher matchups
- Depth beats breadth in betting

### Psychological Factors

#### 1. Avoid Tilt
- Don't chase losses with bigger bets
- Take breaks after bad days
- Stick to your bankroll management rules

#### 2. Handle Winning Streaks
- Don't get overconfident
- Maintain discipline during hot streaks
- Variance works both ways

#### 3. Learn from Mistakes
- Review losing bets honestly
- Look for patterns in failures
- Adjust strategies based on data, not emotions

---

## Troubleshooting

### Common Issues

#### "My win rate is good but ROI is negative"
- You're probably betting too many favorites with bad odds
- Focus on finding better value bets
- Consider if you're getting the best available odds

#### "High confidence bets keep losing"
- Might be overconfident in analysis
- Re-evaluate what factors you're weighing
- Consider if you're missing key information

#### "Bankroll keeps declining despite feeling like you're picking well"
- Check your actual win rate vs perceived performance
- Verify bet sizing is appropriate
- Look for hidden biases in bet selection

#### "Can't find enough betting opportunities"
- You might be too selective (good problem to have)
- Consider expanding to different bet types
- Look at props and alternate lines

---

## API Quick Reference

### Essential Endpoints

**Create Bet**: `POST /api/bets/`
**Get History**: `GET /api/bets/?limit=20`
**Settle Bet**: `POST /api/bets/{id}/settle`
**Performance Summary**: `GET /api/analytics/summary`
**Today's Games**: `GET /api/games/today`
**Strategy Performance**: `GET /api/strategies/{id}/performance`

### Interactive Documentation

Visit http://localhost:18002/docs for:
- Complete API documentation
- Try-it-out functionality
- Request/response examples
- Schema definitions

---

This user guide should help you get the most value from the StatEdge Betting Service. Remember, the goal is to become a more analytical, disciplined bettor through data-driven insights. Focus on the process, be honest with your tracking, and let the data guide your improvements.