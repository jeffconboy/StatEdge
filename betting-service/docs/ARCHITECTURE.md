# Architecture Documentation

## StatEdge Betting Service Architecture

### Overview

The StatEdge Betting Service is designed as a lightweight, standalone microservice for personal baseball betting prediction tracking. It follows a simplified architecture pattern focused on ease of use and maintainability rather than enterprise-scale complexity.

---

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │  Sports Data    │
│   (React)       │    │   (Node.js)     │    │   Service       │
│   Port: 3002    │    │   Port: 3001    │    │   Port: 18001   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────────────────┘
                     │
          ┌─────────────────┐
          │ Betting Service │
          │   (FastAPI)     │
          │   Port: 18002   │
          └─────────┬───────┘
                    │
          ┌─────────────────┐    ┌─────────────────┐
          │ PostgreSQL DB   │    │   Tank01 API    │
          │ (betting_data)  │    │  (External)     │
          │   Port: 5432    │    │     HTTPS       │
          └─────────────────┘    └─────────────────┘
```

### Microservice Design Principles

1. **Single Responsibility**: Betting service only handles bet tracking and analytics
2. **Data Isolation**: Separate database from sports data service
3. **API-First**: All functionality exposed via REST APIs
4. **Stateless**: No session management, each request is independent
5. **Containerized**: Docker-first deployment strategy

---

## Service Components

### 1. FastAPI Application Layer

**File**: `main.py`

```python
# Application Structure
FastAPI App
├── CORS Middleware
├── Router Mounting
│   ├── /api/bets/* → bets.router
│   ├── /api/analytics/* → analytics.router
│   ├── /api/strategies/* → strategies.router
│   └── /api/bankroll/* → bankroll.router
├── Lifespan Management
└── Error Handling
```

**Responsibilities**:
- HTTP request routing
- Middleware configuration
- Service lifecycle management
- Global error handling
- API documentation generation

### 2. Router Layer

**Files**: `routers/*.py`

#### Bets Router (`routers/bets.py`)
- **Endpoints**: CRUD operations for betting predictions
- **Operations**: Create, read, update, delete, settle bets
- **Validation**: Pydantic models for request/response
- **Business Logic**: Bet settlement calculations

#### Analytics Router (`routers/analytics.py`)
- **Endpoints**: Performance analysis and reporting
- **Operations**: Summary stats, trends, confidence analysis
- **Data Processing**: Aggregation queries and calculations
- **Formatting**: Chart-ready data structures

#### Strategies Router (`routers/strategies.py`)
- **Endpoints**: Betting strategy management
- **Operations**: Strategy CRUD, performance tracking
- **Analysis**: Strategy effectiveness metrics
- **Mapping**: Bet-to-strategy relationships

#### Bankroll Router (`routers/bankroll.py`)
- **Endpoints**: Bankroll tracking and management
- **Operations**: Daily balance recording, P&L tracking
- **Calculations**: ROI, profit/loss, trend analysis
- **Visualization**: Chart data preparation

### 3. Data Layer

#### Database Models (`models/bets.py`)

```python
# Pydantic Model Hierarchy
BaseModel
├── Request Models
│   ├── CreateBetRequest
│   ├── UpdateBetRequest
│   ├── SettleBetRequest
│   └── BankrollRequest
└── Response Models
    ├── BetResponse
    ├── BetSummaryResponse
    ├── BankrollResponse
    └── StrategyResponse
```

**Validation Features**:
- Type validation
- Range validation (confidence 1-10)
- Business rule validation
- Automatic serialization

#### Database Connection (`database/connection.py`)

```python
# Connection Management
Connection Pool
├── PostgreSQL Engine (SQLAlchemy)
├── Async Connection Pool (asyncpg)
├── Connection Health Checks
└── Schema Initialization
```

**Features**:
- Connection pooling for performance
- Async operations for scalability
- Automatic schema creation
- Health monitoring

### 4. Integration Layer

#### Tank01 Service (`services/tank01_service.py`)

```python
# External API Integration
Tank01Service
├── HTTP Client Configuration
├── Rate Limiting
├── Error Handling
├── Response Caching
└── Data Transformation
```

**Capabilities**:
- MLB game schedules
- Live betting odds
- Team information
- Error recovery

---

## Data Flow Architecture

### 1. Bet Creation Flow

```
User Request → FastAPI → Validation → Database → Response
     ↓
  1. POST /api/bets/
  2. CreateBetRequest validation
  3. Calculate implied probability
  4. Insert into bets table
  5. Link to categories/strategies
  6. Return BetResponse
```

### 2. Analytics Generation Flow

```
Analytics Request → Database Query → Aggregation → Response
         ↓
  1. GET /api/analytics/summary
  2. Query bets with filters
  3. Calculate win rates, ROI
  4. Group by periods/types
  5. Format for consumption
```

### 3. Bet Settlement Flow

```
Settlement → Validation → Database Update → Strategy Update
     ↓
  1. POST /api/bets/{id}/settle
  2. Validate game outcome
  3. Calculate payout
  4. Update bet record
  5. Update strategy metrics
  6. Trigger analytics refresh
```

---

## Database Architecture

### Schema Design

```sql
-- Core Tables
bets (main betting records)
├── Foreign Keys: None (independent)
├── Indexes: game_date, bet_type, result
└── Constraints: confidence (1-10), amount > 0

bet_categories (bet organization)
├── Relationship: Many-to-many with bets
└── Pre-loaded: 8 default categories

betting_strategies (strategy tracking)
├── Relationship: Many-to-many with bets
├── Performance Metrics: Auto-calculated
└── JSON Criteria: Flexible rule storage

bankroll_history (money management)
├── Relationship: Independent
├── Daily Records: One per date
└── Calculations: Automatic P&L
```

### Performance Optimizations

1. **Strategic Indexing**:
   ```sql
   -- Common query patterns
   CREATE INDEX idx_bets_game_date ON bets(game_date);
   CREATE INDEX idx_bets_result ON bets(bet_result);
   CREATE INDEX idx_bets_confidence_date ON bets(confidence_level, game_date);
   ```

2. **Materialized Views**:
   ```sql
   -- Pre-calculated summaries
   CREATE VIEW bet_summary AS
   SELECT sport, bet_type, COUNT(*), win_rate, roi
   FROM bets WHERE game_status = 'completed'
   GROUP BY sport, bet_type;
   ```

3. **Query Optimization**:
   - Date range filters on indexed columns
   - Limit clauses for pagination
   - Aggregate functions for summaries

---

## API Design Architecture

### RESTful Design Principles

1. **Resource-Based URLs**:
   ```
   /api/bets/          → Bet collection
   /api/bets/{id}      → Individual bet
   /api/bets/{id}/settle → Bet action
   ```

2. **HTTP Methods**:
   - `GET`: Retrieve data
   - `POST`: Create new resources
   - `PATCH`: Partial updates
   - `DELETE`: Remove resources

3. **Response Consistency**:
   ```json
   {
     "success": true,
     "data": {...},
     "timestamp": "2025-07-26T19:30:00Z"
   }
   ```

### Error Handling Strategy

```python
# Hierarchical Error Handling
Application Level
├── HTTP Exceptions (404, 400, 422)
├── Database Exceptions
├── External API Exceptions
└── Validation Exceptions

# Error Response Format
{
  "detail": "Descriptive error message",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

---

## Security Architecture

### Data Protection

1. **Local Data Storage**:
   - All betting data stored locally
   - No external data sharing
   - Personal use only

2. **Database Security**:
   ```sql
   -- User permissions
   GRANT SELECT, INSERT, UPDATE, DELETE ON bets TO betting_user;
   REVOKE ALL ON SCHEMA public FROM public;
   ```

3. **API Security**:
   - No authentication required (personal use)
   - CORS restrictions to known origins
   - Input validation on all endpoints

### Configuration Security

```python
# Environment Variables
DATABASE_URL=postgresql://user:pass@host/db  # Secure credentials
TANK01_API_KEY=secret_key                    # External API access
DEBUG=False                                  # No debug info in production
```

---

## Deployment Architecture

### Container Strategy

```dockerfile
# Multi-stage Build
FROM python:3.11-slim
├── System Dependencies
├── Python Dependencies
├── Application Code
├── Non-root User
└── Health Checks
```

### Docker Compose Orchestration

```yaml
# Service Dependencies
betting-service:
  depends_on:
    - sports-data-service  # For game data
  environment:
    - BETTING_DATABASE_URL
    - TANK01_API_KEY
  volumes:
    - ./betting-service:/app  # Development mounting
```

### Health Monitoring

```python
# Health Check Endpoints
/health          → Service status
/api/games/today → External API status
Database queries → Database connectivity
```

---

## Performance Architecture

### Async Processing

```python
# Async Patterns
async def get_betting_history():
    async for conn in get_db_session():
        rows = await conn.fetch(query)
        return [BetResponse(**dict(row)) for row in rows]
```

### Caching Strategy

1. **Database-Level**: PostgreSQL query cache
2. **Application-Level**: Computed analytics caching
3. **External API**: Tank01 response caching

### Pagination

```python
# Efficient Pagination
GET /api/bets/?limit=50&offset=100
```

---

## Monitoring and Observability

### Logging Architecture

```python
# Structured Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log Categories
- INFO: Normal operations
- WARNING: Recoverable errors
- ERROR: Failed operations
- DEBUG: Development details
```

### Metrics Collection

1. **Business Metrics**:
   - Total bets created
   - Settlement rate
   - Win/loss ratios

2. **Technical Metrics**:
   - Response times
   - Error rates
   - Database connection counts

3. **External Dependencies**:
   - Tank01 API availability
   - Database connectivity

---

## Integration Architecture

### Microservice Communication

```python
# Service-to-Service Communication
sports_data_service = "http://sports-data-service:18001"
betting_service = "http://betting-service:18002"

# API Gateway Routing
/api/sports/*  → Sports Data Service
/api/betting/* → Betting Service
```

### Frontend Integration

```javascript
// React Frontend Integration
const bettingAPI = {
  baseURL: 'http://localhost:18002/api',
  createBet: (data) => fetch(`${baseURL}/bets/`, {...}),
  getHistory: () => fetch(`${baseURL}/bets/`),
  getAnalytics: () => fetch(`${baseURL}/analytics/summary`)
};
```

---

## Scalability Considerations

### Current Architecture Limits

1. **Single Instance**: Designed for personal use
2. **Local Database**: PostgreSQL on single machine
3. **Synchronous Processing**: Adequate for low volume

### Future Scaling Options

1. **Horizontal Scaling**:
   - Load balancer for multiple instances
   - Database read replicas
   - Containerized deployment

2. **Performance Optimizations**:
   - Redis caching layer
   - Background job processing
   - Database partitioning

3. **Cloud Migration**:
   - Container orchestration (Kubernetes)
   - Managed database services
   - CDN for static assets

---

## Development Architecture

### Local Development

```bash
# Development Setup
betting-service/
├── main.py           # FastAPI app
├── requirements.txt  # Dependencies
├── .env.example     # Configuration template
├── Dockerfile       # Container definition
└── test_service.py  # Integration tests
```

### Testing Strategy

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: API endpoint testing
3. **Health Checks**: Service connectivity testing
4. **Manual Testing**: Interactive API docs

### Development Workflow

```bash
# Local Development
docker-compose up --build  # Start all services
python test_service.py     # Run tests
curl /health              # Verify status
```

---

This architecture provides a solid foundation for personal betting tracking while maintaining simplicity and room for future enhancements. The design prioritizes ease of use and maintenance over enterprise-scale complexity.