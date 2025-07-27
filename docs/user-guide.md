# 📖 StatEdge User Guide

Welcome to StatEdge, the most comprehensive baseball analytics platform for sports betting and statistical analysis. This guide will help you get started and make the most of our advanced features.

## 🎯 What is StatEdge?

StatEdge combines real-time Statcast data with advanced FanGraphs statistics to provide actionable insights for sports betting and baseball analysis. Our platform processes 493k+ pitch records with 118 fields each, plus comprehensive statistics for 2,088+ MLB players.

### Key Features

- **Complete Player Database**: Every active MLB player with comprehensive stats
- **Real-time Statcast Data**: Pitch-by-pitch analysis with 118 statistical fields
- **Advanced Analytics**: 320+ batting and 393+ pitching metrics from FanGraphs
- **AI-Powered Insights**: Natural language queries and betting analysis
- **Export Capabilities**: Download data for your own analysis

## 🚀 Getting Started

### 1. Account Setup

Currently, StatEdge is in MVP phase with demo access:

- **Demo Login**: admin@statedge.com / admin123
- **Access Level**: Full premium features for testing

### 2. Platform Access

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:18000/docs
- **Database Access**: Direct PostgreSQL connection available

### 3. First Steps

1. **Explore Player Search**: Start by searching for your favorite players
2. **Review Statistics**: Examine comprehensive statistical profiles
3. **Try AI Chat**: Ask natural language questions about players and stats
4. **Export Data**: Download statistics for offline analysis

## 🔍 Core Features Guide

### Player Search

The player search is your gateway to StatEdge's comprehensive database.

#### How to Search
1. Type any part of a player's name in the search box
2. Use autocomplete suggestions for quick selection
3. Results show active players with current team and position

#### Search Tips
- **Partial names work**: "Judge" finds "Aaron Judge"
- **Team codes**: Search "NYY" to find Yankees players
- **Position codes**: Search "SS" for shortstops
- **Fuzzy matching**: Handles spelling variations

#### Search Results
Each result shows:
- Player name and current team
- Primary position
- Current season availability
- Bio information (height, weight, batting stance)

### Player Statistics

Once you've found a player, dive deep into their statistical profile.

#### Available Statistics

**Traditional Stats**
- Batting: AVG, OBP, SLG, HR, RBI, SB
- Pitching: ERA, WHIP, K/9, BB/9, BABIP
- Basic counting stats and rate statistics

**Advanced Metrics**
- **wRC+**: Weighted Runs Created Plus (league-adjusted offensive value)
- **WAR**: Wins Above Replacement (overall player value)
- **FIP**: Fielding Independent Pitching (pitcher skill isolator)
- **xwOBA**: Expected Weighted On-Base Average (quality of contact)

**Statcast Metrics**
- **Exit Velocity**: Speed of ball off the bat
- **Launch Angle**: Vertical angle of batted ball
- **Barrel Rate**: Percentage of optimal contact
- **Spin Rate**: Pitch rotation speed
- **Release Point**: Pitcher delivery consistency

#### Reading the Statistics

**Batting Context**
- **Excellent**: wRC+ > 140, OPS > .900
- **Above Average**: wRC+ 110-140, OPS .800-.900
- **Average**: wRC+ 90-110, OPS .700-.800
- **Below Average**: wRC+ < 90, OPS < .700

**Pitching Context**
- **Excellent**: ERA < 3.00, FIP < 3.50, WAR > 4.0
- **Above Average**: ERA 3.00-3.75, FIP 3.50-4.00, WAR 2-4
- **Average**: ERA 3.75-4.50, FIP 4.00-4.50, WAR 1-2
- **Below Average**: ERA > 4.50, FIP > 4.50, WAR < 1

### AI-Powered Analytics

StatEdge's AI assistant can answer complex baseball questions in natural language.

#### How to Use AI Chat

1. **Ask Questions**: Type your question in natural language
2. **Get Insights**: Receive detailed analysis with supporting data
3. **Follow Up**: Ask clarifying questions or dive deeper
4. **Context Aware**: AI remembers your conversation context

#### Example Queries

**Player Comparisons**
- "Compare Aaron Judge and Mookie Betts batting stats"
- "Who has a better WAR between deGrom and Scherzer?"
- "Show me the top 5 shortstops by wRC+ this season"

**Situational Analysis**
- "How does Aaron Judge perform against left-handed pitching?"
- "What is Jacob deGrom's ERA in day games?"
- "Show me Vladimir Guerrero Jr's stats at Fenway Park"

**Trend Analysis**
- "Who are the hottest hitters over the last 30 days?"
- "Which pitchers have the highest strikeout rates in July?"
- "Show me players with the biggest improvement from last season"

**Betting Insights** (Premium Feature)
- "Should I bet the over on Juan Soto home runs today?"
- "What's the value on Gerrit Cole strikeout props?"
- "Give me confidence levels on tonight's run totals"

#### AI Response Format

AI responses typically include:
- **Direct Answer**: Clear response to your question
- **Supporting Data**: Relevant statistics and metrics
- **Context**: Situational factors and comparisons
- **Confidence Level**: How certain the analysis is
- **Follow-up Suggestions**: Related questions you might ask

### Data Export

Export comprehensive datasets for your own analysis.

#### Export Formats
- **JSON**: Full statistical profiles with all fields
- **CSV**: Simplified format for spreadsheet analysis
- **API Access**: Direct database queries via REST API

#### Export Process
1. Navigate to any player's detailed statistics page
2. Click "Export Data" button
3. Choose format (JSON recommended for completeness)
4. Download begins automatically

#### What's Included
- **Complete statistical profile**: All available metrics
- **Historical data**: Multiple seasons where available
- **Metadata**: Player bio, team, position information
- **Timestamps**: When data was last updated

## 🎲 Sports Betting Features

### Betting Analysis (Premium)

StatEdge provides AI-powered betting insights and recommendations.

#### Supported Bet Types

**Player Props**
- Home runs, hits, RBIs, runs scored
- Strikeouts, walks, earned runs (pitchers)
- Total bases, stolen bases

**Game Props**
- Total runs (over/under)
- Team run totals
- Inning props

**Matchup Analysis**
- Head-to-head comparisons
- Historical performance vs opponent
- Ballpark factors

#### How to Get Betting Insights

1. **Ask the AI**: "Should I bet over 1.5 home runs for Aaron Judge?"
2. **Player Analysis**: Review recent form and matchup data
3. **Historical Context**: Check performance vs specific pitchers/teams
4. **Environmental Factors**: Consider ballpark, weather, situation

#### Understanding Recommendations

**Confidence Levels**
- **High (80%+)**: Strong statistical edge identified
- **Medium (60-80%)**: Moderate advantage with some risk
- **Low (<60%)**: Coin flip or insufficient data

**Risk Factors**
AI will highlight potential concerns:
- Recent injury or performance decline
- Unfavorable matchup history
- Weather or ballpark disadvantages
- Sample size limitations

### Responsible Betting

StatEdge promotes responsible gambling:
- **Educational Focus**: Emphasizes analysis over guarantees
- **Risk Awareness**: Highlights uncertainty and variance
- **Data-Driven**: Encourages informed decision-making
- **No Guarantees**: Makes clear that betting involves risk

## 📊 Advanced Features

### Custom Queries

Use the API to create custom analysis and reports.

#### API Access
- **Interactive Docs**: http://localhost:18000/docs
- **Authentication**: JWT token required
- **Rate Limits**: Vary by subscription tier

#### Common Use Cases
- **Portfolio Analysis**: Track multiple players
- **Team Building**: Compare players by position
- **Market Research**: Identify undervalued players
- **Performance Tracking**: Monitor player development

### Statistical Education

Understanding the metrics is key to effective analysis.

#### Key Concepts

**WAR (Wins Above Replacement)**
- Measures total player value vs replacement-level player
- Combines offense, defense, baserunning, positional value
- 0 = replacement level, 2 = starter, 5+ = MVP candidate

**wRC+ (Weighted Runs Created Plus)**
- Offensive value adjusted for league and ballpark
- 100 = league average, 110 = 10% above average
- Accounts for different run environments

**FIP (Fielding Independent Pitching)**
- Pitcher performance isolating defense
- Based on strikeouts, walks, hit by pitch, home runs
- Often more predictive than ERA

**Expected Stats (xBA, xSLG, xwOBA)**
- What stats "should be" based on quality of contact
- Useful for identifying luck vs skill
- Predictive of future performance

### Data Quality

Understanding StatEdge's data sources and limitations.

#### Data Sources
- **Statcast**: MLB's official tracking system
- **FanGraphs**: Advanced baseball statistics site
- **MLB API**: Official league data

#### Update Frequency
- **Daily**: Automatic collection at 6 AM EST
- **Real-time**: Game data available within hours
- **Historical**: Complete 2025 season coverage

#### Data Accuracy
- **99.5%+**: Statistical precision rate
- **Complete Coverage**: All MLB games and players
- **Quality Checks**: Automated validation and error detection

## 🛠️ Troubleshooting

### Common Issues

#### Player Not Found
- Verify spelling and try partial names
- Check if player is currently active in MLB
- Some minor league or retired players not included

#### Missing Statistics
- Recent call-ups may have limited data
- Injured players may have outdated stats
- Some historical data may be incomplete

#### Slow Performance
- Complex queries may take 2-5 seconds
- Large data exports require processing time
- Peak usage times may experience delays

### Getting Help

#### Self-Service Resources
- **Interactive Docs**: http://localhost:18000/docs
- **API Reference**: Complete endpoint documentation
- **Database Schema**: Understanding data structure

#### Support Channels
- **Email**: support@statedge.com
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and examples

## 📈 Best Practices

### Effective Analysis

#### Research Process
1. **Start Broad**: Review overall player performance
2. **Drill Down**: Examine specific situations and matchups
3. **Context Matters**: Consider recent form, injuries, team changes
4. **Multiple Sources**: Cross-reference different metrics

#### Avoiding Pitfalls
- **Small Samples**: Be cautious with limited data
- **Recency Bias**: Don't overweight recent performance
- **Context Missing**: Consider situation and opposition
- **Stat Shopping**: Don't cherry-pick favorable metrics

### Data Interpretation

#### Understanding Variance
- Baseball has high inherent randomness
- Large sample sizes more reliable
- Extreme performances often regress to mean
- Injuries and age affect trajectories

#### Trend Analysis
- Look for consistent patterns across metrics
- Consider underlying skills vs results
- Monitor changes in approach or role
- Factor in team and environmental changes

## 🔮 Platform Roadmap

### Coming Soon
- **Real-time Game Data**: Live pitch tracking during games
- **Mobile App**: iOS and Android applications
- **Team Analytics**: Front office tools and insights
- **Social Features**: Share analysis and discussions

### Future Enhancements
- **Multi-sport Expansion**: Basketball, football, hockey
- **Predictive Modeling**: Machine learning predictions
- **Video Analysis**: Pitch-by-pitch video breakdown
- **API Marketplace**: Third-party integrations

---

**Ready to dive deeper into baseball analytics? Start exploring players, asking AI questions, and discovering insights that give you the edge in understanding America's pastime.**