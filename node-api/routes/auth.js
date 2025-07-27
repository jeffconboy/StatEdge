const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const { query } = require('../config/database');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

// Register user
router.post('/register', [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }),
], async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { email, password } = req.body;

        // Check if user exists
        const existingUser = await query(
            'SELECT id FROM users WHERE email = $1',
            [email]
        );

        if (existingUser.rows.length > 0) {
            return res.status(409).json({
                error: 'User already exists'
            });
        }

        // Hash password
        const saltRounds = 12;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create user
        const result = await query(
            'INSERT INTO users (email, password_hash, tier) VALUES ($1, $2, $3) RETURNING id, email, tier',
            [email, hashedPassword, 'free']
        );

        const user = result.rows[0];

        // Generate JWT
        const token = jwt.sign(
            { userId: user.id, email: user.email, tier: user.tier },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.status(201).json({
            message: 'User created successfully',
            user: {
                id: user.id,
                email: user.email,
                tier: user.tier
            },
            token
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({
            error: 'Internal server error during registration'
        });
    }
});

// Login user
router.post('/login', [
    body('email').isEmail().normalizeEmail(),
    body('password').exists()
], async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { email, password } = req.body;

        // Get user
        const result = await query(
            'SELECT id, email, password_hash, tier, query_count_today FROM users WHERE email = $1',
            [email]
        );

        if (result.rows.length === 0) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }

        const user = result.rows[0];

        // Check password
        const validPassword = await bcrypt.compare(password, user.password_hash);
        if (!validPassword) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }

        // Generate JWT
        const token = jwt.sign(
            { userId: user.id, email: user.email, tier: user.tier },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.json({
            message: 'Login successful',
            user: {
                id: user.id,
                email: user.email,
                tier: user.tier,
                query_count_today: user.query_count_today
            },
            token
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            error: 'Internal server error during login'
        });
    }
});

// Get current user
router.get('/me', authenticateToken, async (req, res) => {
    try {
        const result = await query(
            'SELECT id, email, tier, query_count_today, last_query_reset, created_at FROM users WHERE id = $1',
            [req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'User not found'
            });
        }

        const user = result.rows[0];
        
        res.json({
            user: {
                id: user.id,
                email: user.email,
                tier: user.tier,
                query_count_today: user.query_count_today,
                last_query_reset: user.last_query_reset,
                member_since: user.created_at
            }
        });

    } catch (error) {
        console.error('Get user error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// Update user tier (admin only for MVP)
router.put('/tier', authenticateToken, [
    body('tier').isIn(['free', 'basic', 'premium'])
], async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { tier } = req.body;

        // For MVP, allow users to upgrade themselves (in production this would be payment-gated)
        const result = await query(
            'UPDATE users SET tier = $1, updated_at = NOW() WHERE id = $2 RETURNING id, email, tier',
            [tier, req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'User not found'
            });
        }

        const user = result.rows[0];

        res.json({
            message: 'Tier updated successfully',
            user: {
                id: user.id,
                email: user.email,
                tier: user.tier
            }
        });

    } catch (error) {
        console.error('Update tier error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// Get user query history
router.get('/queries', authenticateToken, async (req, res) => {
    try {
        const { limit = 50, offset = 0 } = req.query;

        const result = await query(
            `SELECT query_text, query_params, results_count, response_time_ms, created_at 
             FROM user_queries 
             WHERE user_id = $1 
             ORDER BY created_at DESC 
             LIMIT $2 OFFSET $3`,
            [req.user.id, limit, offset]
        );

        res.json({
            queries: result.rows,
            count: result.rows.length
        });

    } catch (error) {
        console.error('Get queries error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// Change password
router.put('/password', authenticateToken, [
    body('currentPassword').exists(),
    body('newPassword').isLength({ min: 6 })
], async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { currentPassword, newPassword } = req.body;

        // Get current password hash
        const result = await query(
            'SELECT password_hash FROM users WHERE id = $1',
            [req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'User not found'
            });
        }

        const user = result.rows[0];

        // Verify current password
        const validPassword = await bcrypt.compare(currentPassword, user.password_hash);
        if (!validPassword) {
            return res.status(401).json({
                error: 'Current password is incorrect'
            });
        }

        // Hash new password
        const saltRounds = 12;
        const hashedNewPassword = await bcrypt.hash(newPassword, saltRounds);

        // Update password
        await query(
            'UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2',
            [hashedNewPassword, req.user.id]
        );

        res.json({
            message: 'Password updated successfully'
        });

    } catch (error) {
        console.error('Change password error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

module.exports = router;