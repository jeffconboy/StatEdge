const express = require('express');
const axios = require('axios');
const { query, getRedisClient } = require('../config/database');
const { authenticateToken, checkQueryLimit, requireTier } = require('../middleware/auth');

const router = express.Router();
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://python-service:8000';

// Natural language chat interface (allow demo access)
router.post('/chat', async (req, res) => {
    try {
        const { query: userQuery, context } = req.body;

        if (!userQuery || userQuery.trim().length < 3) {
            return res.status(400).json({
                error: 'Query must be at least 3 characters long'
            });
        }

        // Log user query (if user is authenticated)
        if (req.user && req.user.id) {
            await query(
                'INSERT INTO user_queries (user_id, query_text, query_params) VALUES ($1, $2, $3)',
                [req.user.id, userQuery, JSON.stringify({ context: context || {} })]
            );
        }

        // Call Python AI service (simple chat endpoint)
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/ai/simple-chat`, {
            query: userQuery,
            context: {
                user_tier: req.user ? req.user.tier : 'demo',
                user_id: req.user ? req.user.id : 'demo',
                ...context
            }
        });

        res.json({
            ...response.data,
            user_tier: req.user ? req.user.tier : 'demo'
        });

    } catch (error) {
        console.error('AI chat error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'AI processing failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during AI processing'
        });
    }
});

// Prop bet analysis
router.post('/analyze-prop', authenticateToken, requireTier('premium'), checkQueryLimit, async (req, res) => {
    try {
        const { player_name, prop_type, betting_line, game_context } = req.body;

        if (!player_name || !prop_type || betting_line === undefined) {
            return res.status(400).json({
                error: 'Missing required fields: player_name, prop_type, betting_line'
            });
        }

        // Log analysis request
        await query(
            'INSERT INTO user_queries (user_id, query_text, query_params) VALUES ($1, $2, $3)',
            [req.user.id, `Prop analysis: ${player_name} ${prop_type} ${betting_line}`, JSON.stringify({
                player_name,
                prop_type,
                betting_line,
                game_context
            })]
        );

        // Call Python AI service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/ai/analyze-prop`, {
            player_name,
            prop_type,
            betting_line,
            game_context: game_context || {}
        });

        res.json(response.data);

    } catch (error) {
        console.error('Prop analysis error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Analysis failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during analysis'
        });
    }
});

// Explain specific statistics
router.post('/explain-stats', authenticateToken, checkQueryLimit, async (req, res) => {
    try {
        const { player_name, statistics } = req.body;

        if (!player_name || !statistics || !Array.isArray(statistics)) {
            return res.status(400).json({
                error: 'Missing required fields: player_name, statistics (array)'
            });
        }

        // Call Python AI service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/ai/explain-stats`, null, {
            params: {
                player_name,
                statistics: statistics
            }
        });

        res.json(response.data);

    } catch (error) {
        console.error('Stats explanation error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Explanation failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during explanation'
        });
    }
});

// Get query suggestions
router.get('/suggestions', authenticateToken, async (req, res) => {
    try {
        // Check cache first
        const redis = await getRedisClient();
        const cacheKey = 'ai_suggestions';
        const cachedSuggestions = await redis.get(cacheKey);

        if (cachedSuggestions) {
            return res.json({
                suggestions: JSON.parse(cachedSuggestions),
                cached: true
            });
        }

        // Get from Python service
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/ai/suggestions`);

        // Cache for 1 hour
        await redis.setEx(cacheKey, 3600, JSON.stringify(response.data.suggestions));

        res.json({
            suggestions: response.data.suggestions,
            cached: false
        });

    } catch (error) {
        console.error('Suggestions error:', error.message);
        
        // Fallback suggestions
        const fallbackSuggestions = [
            "Show me Aaron Judge's batting average this season",
            "What is Mike Trout's exit velocity?",
            "Compare Mookie Betts vs Ronald Acuña Jr",
            "How does Jacob deGrom perform against lefties?",
            "Show me the top 10 players by OPS"
        ];

        res.json({
            suggestions: fallbackSuggestions,
            fallback: true
        });
    }
});

// Batch AI analysis
router.post('/batch-analyze', authenticateToken, requireTier('premium'), async (req, res) => {
    try {
        const { queries } = req.body;

        if (!queries || !Array.isArray(queries) || queries.length === 0) {
            return res.status(400).json({
                error: 'Must provide an array of queries'
            });
        }

        if (queries.length > 5) {
            return res.status(400).json({
                error: 'Maximum 5 queries per batch'
            });
        }

        // Check if user has enough query allowance
        const totalQueries = queries.length;
        const today = new Date().toISOString().split('T')[0];
        
        if (req.user.last_query_reset !== today) {
            // Reset already handled by checkQueryLimit middleware
        }

        // For batch, we need to check if user has enough queries left
        const limits = { free: 50, basic: 200, premium: 1000 };
        const userLimit = limits[req.user.tier] || limits.free;
        
        if (req.user.query_count_today + totalQueries > userLimit) {
            return res.status(429).json({
                error: 'Insufficient query allowance for batch',
                required: totalQueries,
                available: userLimit - req.user.query_count_today
            });
        }

        // Update query count for batch
        await query(
            'UPDATE users SET query_count_today = query_count_today + $1 WHERE id = $2',
            [totalQueries - 1, req.user.id] // -1 because checkQueryLimit already incremented by 1
        );

        // Call Python AI service
        const response = await axios.post(`${PYTHON_SERVICE_URL}/api/ai/batch-analyze`, {
            queries
        });

        res.json({
            ...response.data,
            queries_processed: totalQueries
        });

    } catch (error) {
        console.error('Batch analysis error:', error.message);
        
        if (error.response) {
            return res.status(error.response.status).json({
                error: error.response.data?.detail || 'Batch analysis failed'
            });
        }

        res.status(500).json({
            error: 'Internal server error during batch analysis'
        });
    }
});

// Get user's AI conversation history
router.get('/conversations', authenticateToken, async (req, res) => {
    try {
        const { limit = 20, offset = 0 } = req.query;

        const result = await query(
            `SELECT id, conversation_history, session_metadata, created_at, updated_at
             FROM ai_conversations 
             WHERE user_id = $1 
             ORDER BY updated_at DESC 
             LIMIT $2 OFFSET $3`,
            [req.user.id, limit, offset]
        );

        const conversations = result.rows.map(row => ({
            id: row.id,
            messages: row.conversation_history,
            metadata: row.session_metadata,
            created_at: row.created_at,
            updated_at: row.updated_at
        }));

        res.json({
            conversations,
            count: conversations.length
        });

    } catch (error) {
        console.error('Get conversations error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// AI health check
router.get('/health', async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_SERVICE_URL}/api/ai/health`);
        res.json({
            ...response.data,
            gateway_status: 'healthy'
        });
    } catch (error) {
        console.error('AI health check error:', error.message);
        res.status(503).json({
            status: 'unhealthy',
            gateway_status: 'healthy',
            ai_service_status: 'unavailable',
            error: error.message
        });
    }
});

// AI usage statistics for user
router.get('/usage-stats', authenticateToken, async (req, res) => {
    try {
        // Get user's AI query statistics
        const result = await query(
            `SELECT 
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as queries_last_7_days,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as queries_last_30_days,
                AVG(response_time_ms) as avg_response_time
             FROM user_queries 
             WHERE user_id = $1 
             AND query_text ILIKE '%ai%' OR query_text ILIKE '%chat%'`,
            [req.user.id]
        );

        const stats = result.rows[0];

        res.json({
            user_id: req.user.id,
            tier: req.user.tier,
            query_stats: {
                total_ai_queries: parseInt(stats.total_queries) || 0,
                last_7_days: parseInt(stats.queries_last_7_days) || 0,
                last_30_days: parseInt(stats.queries_last_30_days) || 0,
                avg_response_time_ms: parseFloat(stats.avg_response_time) || 0
            },
            current_limits: {
                daily_limit: req.user.tier === 'premium' ? 1000 : req.user.tier === 'basic' ? 200 : 50,
                used_today: req.user.query_count_today
            }
        });

    } catch (error) {
        console.error('Usage stats error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

module.exports = router;