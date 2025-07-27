const express = require('express');
const axios = require('axios');
const { query, getRedisClient } = require('../config/database');
const { authenticateToken, checkQueryLimit } = require('../middleware/auth');

const router = express.Router();
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://python-service:8000';

// Search players
router.get('/search', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { q: searchQuery, limit = 10 } = req.query;

        if (!searchQuery || searchQuery.length < 2) {
            return res.status(400).json({
                error: 'Search query must be at least 2 characters'
            });
        }

        // Check cache first
        const redis = await getRedisClient();
        const cacheKey = `player_search:${searchQuery}:${limit}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                results: JSON.parse(cachedResult),
                cached: true
            });
        }

        // Query Python service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/players/search`, {
            query: searchQuery,
            limit: parseInt(limit)
        });

        // Cache for 5 minutes
        await redis.setEx(cacheKey, 300, JSON.stringify(response.data));

        res.json({
            results: response.data,
            cached: false
        });

    } catch (error) {
        console.error('Player search error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Search failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during search'
        });
    }
});

// Get player statistics
router.get('/:playerId/stats', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { playerId } = req.params;
        const { 
            stat_types = 'batting,pitching,statcast',
            season,
            days_back = 30
        } = req.query;

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `player_stats:${playerId}:${stat_types}:${season || 'current'}:${days_back}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                ...JSON.parse(cachedResult),
                cached: true
            });
        }

        // Query Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/players/${playerId}/stats`, {
            params: {
                stat_types,
                season,
                days_back
            }
        });

        // Cache for 10 minutes
        await redis.setEx(cacheKey, 600, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Player stats error:', error.message);
        
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

// Get player summary
router.get('/:playerId/summary', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { playerId } = req.params;

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `player_summary:${playerId}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                ...JSON.parse(cachedResult),
                cached: true
            });
        }

        // Query Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/players/${playerId}/summary`);

        // Cache for 15 minutes
        await redis.setEx(cacheKey, 900, JSON.stringify(response.data));

        res.json({
            ...response.data,
            cached: false
        });

    } catch (error) {
        console.error('Player summary error:', error.message);
        
        if (error.response?.status === 404) {
            return res.status(404).json({
                error: 'Player not found'
            });
        }

        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Summary retrieval failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during summary retrieval'
        });
    }
});

// Get trending players
router.get('/trending', authenticateToken, async (req, res) => {
    try {
        const { limit = 10 } = req.query;

        // Check cache
        const redis = await getRedisClient();
        const cacheKey = `trending_players:${limit}`;
        const cachedResult = await redis.get(cacheKey);

        if (cachedResult) {
            return res.json({
                trending: JSON.parse(cachedResult),
                cached: true
            });
        }

        // Query Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/players/trending`, {
            params: { limit }
        });

        // Cache for 30 minutes
        await redis.setEx(cacheKey, 1800, JSON.stringify(response.data));

        res.json({
            trending: response.data,
            cached: false
        });

    } catch (error) {
        console.error('Trending players error:', error.message);
        
        res.status(500).json({
            error: 'Internal server error during trending retrieval'
        });
    }
});

// Compare players
router.post('/compare', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { player_ids, stat_types = ['batting', 'statcast'] } = req.body;

        if (!player_ids || !Array.isArray(player_ids) || player_ids.length < 2) {
            return res.status(400).json({
                error: 'Must provide at least 2 player IDs for comparison'
            });
        }

        if (player_ids.length > 5) {
            return res.status(400).json({
                error: 'Maximum 5 players can be compared at once'
            });
        }

        // Query Python service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/players/bulk-stats`, {
            player_ids,
            stat_types
        });

        res.json({
            comparison: response.data,
            player_count: player_ids.length
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

// Export player data
router.get('/:playerId/export', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { playerId } = req.params;
        const { format = 'json' } = req.query;

        // Query Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/analytics/export/${playerId}`, {
            params: { format }
        });

        if (format.toLowerCase() === 'csv') {
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', `attachment; filename="player_${playerId}_data.csv"`);
        } else {
            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Content-Disposition', `attachment; filename="player_${playerId}_data.json"`);
        }

        res.json(response.data);

    } catch (error) {
        console.error('Player export error:', error.message);
        
        if (error.response?.status === 404) {
            return res.status(404).json({
                error: 'Player not found'
            });
        }

        res.status(500).json({
            error: 'Internal server error during export'
        });
    }
});

module.exports = router;