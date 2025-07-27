const { Pool } = require('pg');
const redis = require('redis');

// PostgreSQL connection
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

// Redis connection
let redisClient;

const getRedisClient = async () => {
    if (!redisClient) {
        redisClient = redis.createClient({
            url: process.env.REDIS_URL || 'redis://redis:6379'
        });
        
        redisClient.on('error', (err) => {
            console.error('Redis Client Error:', err);
        });
        
        redisClient.on('connect', () => {
            console.log('Connected to Redis');
        });
        
        await redisClient.connect();
    }
    
    return redisClient;
};

// Database query wrapper
const query = async (text, params) => {
    const start = Date.now();
    try {
        const res = await pool.query(text, params);
        const duration = Date.now() - start;
        console.log('Executed query', { text: text.substring(0, 100), duration, rows: res.rowCount });
        return res;
    } catch (error) {
        console.error('Database query error:', error);
        throw error;
    }
};

// Test database connection
const testConnection = async () => {
    try {
        const result = await query('SELECT NOW() as current_time');
        console.log('Database connected successfully:', result.rows[0].current_time);
        return true;
    } catch (error) {
        console.error('Database connection failed:', error.message);
        return false;
    }
};

// Graceful shutdown
const shutdown = async () => {
    try {
        await pool.end();
        if (redisClient) {
            await redisClient.quit();
        }
        console.log('Database connections closed');
    } catch (error) {
        console.error('Error closing database connections:', error);
    }
};

module.exports = {
    query,
    pool,
    getRedisClient,
    testConnection,
    shutdown
};