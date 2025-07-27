const jwt = require('jsonwebtoken');
const { query } = require('../config/database');

const authenticateToken = async (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // Get user from database
        const result = await query(
            'SELECT id, email, tier, query_count_today, last_query_reset FROM users WHERE id = $1',
            [decoded.userId]
        );

        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'Invalid token' });
        }

        req.user = result.rows[0];
        next();
    } catch (error) {
        console.error('Auth error:', error);
        return res.status(403).json({ error: 'Invalid or expired token' });
    }
};

const checkQueryLimit = async (req, res, next) => {
    try {
        const user = req.user;
        const today = new Date().toISOString().split('T')[0];

        // Reset count if it's a new day
        if (user.last_query_reset !== today) {
            await query(
                'UPDATE users SET query_count_today = 0, last_query_reset = $1 WHERE id = $2',
                [today, user.id]
            );
            user.query_count_today = 0;
        }

        // Check limits based on tier
        const limits = {
            free: 50,
            basic: 200,
            premium: 1000
        };

        const userLimit = limits[user.tier] || limits.free;

        if (user.query_count_today >= userLimit) {
            return res.status(429).json({
                error: 'Query limit exceeded',
                limit: userLimit,
                used: user.query_count_today,
                tier: user.tier
            });
        }

        // Increment query count
        await query(
            'UPDATE users SET query_count_today = query_count_today + 1 WHERE id = $1',
            [user.id]
        );

        next();
    } catch (error) {
        console.error('Query limit check error:', error);
        next(error);
    }
};

const requireTier = (requiredTier) => {
    const tierLevels = { free: 1, basic: 2, premium: 3 };
    
    return (req, res, next) => {
        const userTierLevel = tierLevels[req.user.tier] || 1;
        const requiredTierLevel = tierLevels[requiredTier] || 1;

        if (userTierLevel < requiredTierLevel) {
            return res.status(403).json({
                error: 'Insufficient tier',
                required: requiredTier,
                current: req.user.tier
            });
        }

        next();
    };
};

module.exports = {
    authenticateToken,
    checkQueryLimit,
    requireTier
};