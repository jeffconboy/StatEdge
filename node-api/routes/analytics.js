const express = require('express');
const axios = require('axios');
const { query, getRedisClient } = require('../config/database');
const { authenticateToken, checkQueryLimit } = require('../middleware/auth');

const router = express.Router();
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://python-service:8000';

// Trigger data collection
router.post('/collect-data', authenticateToken, async (req, res) => {
    try {
        // Only allow premium users to trigger manual data collection
        if (req.user.tier !== 'premium') {
            return res.status(403).json({
                error: 'Premium tier required for manual data collection'
            });
        }

        const { date, data_sources = ['statcast', 'fangraphs', 'mlb_api'], force_refresh = false } = req.body;

        // Call Python service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/analytics/collect-data`, {
            date,
            data_sources,
            force_refresh
        });

        res.json(response.data);

    } catch (error) {
        console.error('Data collection error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Data collection failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during data collection'
        });
    }
});

// Get database statistics
router.get('/database-stats', authenticateToken, async (req, res) => {
    try {
        // Check cache first
        const redis = await getRedisClient();
        const cacheKey = 'database_stats';
        const cachedStats = await redis.get(cacheKey);

        if (cachedStats) {
            return res.json({
                ...JSON.parse(cachedStats),
                cached: true
            });
        }

        // Get from Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/analytics/database-stats`);

        // Cache for 10 minutes
        await redis.setEx(cacheKey, 600, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Database stats error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Stats retrieval failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during stats retrieval'
        });
    }
});

// Get leaderboards
router.get('/leaderboards/:statName', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { statName } = req.params;
        const { limit = 10, min_pa = 100 } = req.query;

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `leaderboard:${statName}:${limit}:${min_pa}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                ...JSON.parse(cachedResult),
                cached: true
            });
        }

        // Get from Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/analytics/leaderboards/${statName}`, {
            params: { limit, min_pa }
        });

        // Cache for 30 minutes
        await redis.setEx(cacheKey, 1800, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Leaderboard error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Leaderboard retrieval failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during leaderboard retrieval'
        });
    }
});

// Compare players
router.get('/compare-players', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { player_names, stats = 'avg,ops,woba,wrc_plus' } = req.query;

        if (!player_names) {
            return res.status(400).json({
                error: 'player_names parameter is required (comma-separated)'
            });
        }

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `compare:${player_names}:${stats}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                ...JSON.parse(cachedResult),
                cached: true
            });
        }

        // Get from Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/analytics/compare-players`, {
            params: { player_names, stats }
        });

        // Cache for 15 minutes
        await redis.setEx(cacheKey, 900, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Player comparison error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Comparison failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during comparison'
        });
    }
});

// Get team statistics
router.get('/team-stats/:team', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { team } = req.params;

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `team_stats:${team.toUpperCase()}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                ...JSON.parse(cachedResult),
                cached: true
            });
        }

        // Get from Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/analytics/team-stats/${team}`);

        // Cache for 1 hour
        await redis.setEx(cacheKey, 3600, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Team stats error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Team stats retrieval failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during team stats retrieval'
        });
    }
});

// Get available statistics list
router.get('/available-stats', authenticateToken, async (req, res) => {
    try {
        // Cache this for a long time since it rarely changes
        const redis = await getRedisClient();
        const cacheKey = 'available_stats';
        const cachedStats = await redis.get(cacheKey);

        if (cachedStats) {
            return res.json({
                stats: JSON.parse(cachedStats),
                cached: true
            });
        }

        // Define available statistics (could be pulled from DB schema)
        const availableStats = {
            batting: {
                basic: ['avg', 'obp', 'slg', 'ops', 'hr', 'rbi', 'runs', 'hits'],
                advanced: ['woba', 'wrc_plus', 'war', 'babip', 'iso', 'bb_rate', 'k_rate'],
                statcast: ['exit_velocity', 'launch_angle', 'barrel_rate', 'hard_hit_rate', 'xba', 'xslg']
            },
            pitching: {
                basic: ['era', 'whip', 'wins', 'losses', 'saves', 'strikeouts', 'walks'],
                advanced: ['fip', 'xfip', 'siera', 'war', 'k_rate', 'bb_rate', 'hr_per_9'],
                statcast: ['spin_rate', 'release_speed', 'extension', 'whiff_rate']
            },
            situational: ['vs_lhp', 'vs_rhp', 'home', 'away', 'day', 'night', 'clutch']
        };

        // Cache for 24 hours
        await redis.setEx(cacheKey, 86400, JSON.stringify(availableStats));

        res.json({
            stats: availableStats,
            cached: false
        });

    } catch (error) {
        console.error('Available stats error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// Search across all statistics
router.post('/search-stats', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { 
            stat_name, 
            operator = '>', 
            value, 
            min_pa = 100, 
            limit = 20,
            data_source = 'fangraphs_batting'
        } = req.body;

        if (!stat_name || value === undefined) {
            return res.status(400).json({
                error: 'stat_name and value are required'
            });
        }

        // This would be a complex query in the Python service
        // For MVP, we'll implement basic search functionality

        let searchQuery;
        let params;

        if (data_source === 'fangraphs_batting') {
            searchQuery = `
                SELECT p.name, p.current_team, 
                       (fb.batting_stats->>'${stat_name.toUpperCase()}')::numeric as stat_value,
                       (fb.batting_stats->>'PA')::integer as plate_appearances
                FROM players p
                JOIN fangraphs_batting fb ON p.id = fb.player_id
                WHERE (fb.batting_stats->>'PA')::integer >= $1
                AND (fb.batting_stats->>'${stat_name.toUpperCase()}')::numeric ${operator} $2
                AND fb.batting_stats->>'${stat_name.toUpperCase()}' IS NOT NULL
                ORDER BY stat_value DESC
                LIMIT $3
            `;
            params = [min_pa, value, limit];
        } else {
            return res.status(400).json({
                error: 'Data source not supported in MVP'
            });
        }

        const result = await query(searchQuery, params);

        const searchResults = result.rows.map((row, index) => ({
            rank: index + 1,
            name: row.name,
            team: row.current_team,
            value: parseFloat(row.stat_value),
            plate_appearances: row.plate_appearances
        }));

        res.json({
            search_criteria: {
                stat_name,
                operator,
                value,
                min_pa,
                data_source
            },
            results: searchResults,
            count: searchResults.length
        });

    } catch (error) {
        console.error('Search stats error:', error);
        res.status(500).json({
            error: 'Internal server error during search'
        });
    }
});

// Get analytics insights (daily summary)
router.get('/insights', authenticateToken, async (req, res) => {
    try {
        // Get cached insights
        const redis = await getRedisClient();
        const cacheKey = 'daily_insights';
        const cachedInsights = await redis.get(cacheKey);

        if (cachedInsights) {
            return res.json({
                insights: JSON.parse(cachedInsights),
                cached: true
            });
        }

        // Get recent insights from database
        const result = await query(
            `SELECT content, insight_type, relevance_score, generated_at
             FROM ai_insights 
             WHERE insight_date >= CURRENT_DATE - INTERVAL '7 days'
             ORDER BY relevance_score DESC, generated_at DESC
             LIMIT 10`
        );

        const insights = result.rows.map(row => ({
            content: row.content,
            type: row.insight_type,
            relevance: row.relevance_score,
            generated_at: row.generated_at
        }));

        // Cache for 1 hour
        await redis.setEx(cacheKey, 3600, JSON.stringify(insights));

        res.json({
            insights,
            cached: false
        });

    } catch (error) {
        console.error('Insights error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

module.exports = router;