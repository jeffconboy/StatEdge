# StatEdge Service Interactions Guide

Comprehensive guide to service communication patterns, API interactions, and data flow within the StatEdge microservice architecture.

## Service Communication Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend  │    │     API      │    │ Load Balancer│
│   Vue.js    │◄──►│   Gateway    │◄──►│    Nginx     │
│  Port 3000  │    │ (Optional)   │    │   Port 80    │
└─────┬───────┘    └──────────────┘    └─────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                Service Mesh Layer                       │
└─────┬─────────┬─────────────┬─────────────┬─────────────┘
      │         │             │             │
      ▼         ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│Sports   │ │  User   │ │  Betting    │ │Infrastructure│
│  API    │ │Managmnt │ │   Odds      │ │   Services   │
│Port 8000│ │Port 8001│ │ Port 8002   │ │   Various    │
└────┬────┘ └────┬────┘ └─────┬───────┘ └──────┬──────┘
     │           │            │                │
     ▼           ▼            ▼                ▼
┌─────────┐ ┌─────────┐ ┌─────────┐      ┌─────────┐
│Sports DB│ │Users DB │ │Shared   │      │  Redis  │
│Port 5432│ │Port 5433│ │Sports DB│      │Port 6379│
└─────────┘ └─────────┘ └─────────┘      └─────────┘
```

## Core Service Interactions

### 1. Frontend → Sports API
**Use Case**: Displaying player stats, game data, analytics

```typescript
// Frontend service calls
class SportsApiService {
  private baseUrl = 'http://localhost:8000/api/v1';

  async getPlayerProfile(playerName: string) {
    const response = await fetch(`${this.baseUrl}/player/profile?name=${playerName}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  async getStatcastData(playerId: number, limit: number = 100) {
    return fetch(`${this.baseUrl}/statcast/player/${playerId}?limit=${limit}`)
      .then(res => res.json());
  }

  async getFanGraphsData(season: number = 2025) {
    return fetch(`${this.baseUrl}/fangraphs/batting?season=${season}`)
      .then(res => res.json());
  }
}
```

### 2. Frontend → User Management
**Use Case**: Authentication, subscription management, user preferences

```typescript
// User authentication service
class UserService {
  private baseUrl = 'http://localhost:8001/api/v1';

  async login(credentials: LoginCredentials) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (response.ok) {
      const { access_token, refresh_token, user } = await response.json();
      this.storeTokens(access_token, refresh_token);
      return user;
    }
    throw new Error('Login failed');
  }

  async getCurrentUser() {
    return fetch(`${this.baseUrl}/user/profile`, {
      headers: { 'Authorization': `Bearer ${this.getAccessToken()}` }
    }).then(res => res.json());
  }

  async upgradeSubscription(tierId: number, paymentMethod: string) {
    return fetch(`${this.baseUrl}/subscription/upgrade`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getAccessToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tier_id: tierId, payment_method: paymentMethod })
    }).then(res => res.json());
  }
}
```

### 3. Frontend → Betting Odds
**Use Case**: Displaying current odds, market analysis, arbitrage opportunities

```typescript
// Betting odds service
class BettingOddsService {
  private baseUrl = 'http://localhost:8002/api/v1';

  async getCurrentOdds() {
    return fetch(`${this.baseUrl}/odds/current`, {
      headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
    }).then(res => res.json());
  }

  async getGameOdds(gamePk: number) {
    return fetch(`${this.baseUrl}/odds/game/${gamePk}`)
      .then(res => res.json());
  }

  async getArbitrageOpportunities() {
    return fetch(`${this.baseUrl}/odds/arbitrage`, {
      headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
    }).then(res => res.json());
  }

  async getMarketMovements(gamePk: number, hours: number = 24) {
    return fetch(`${this.baseUrl}/odds/movements?game_pk=${gamePk}&hours=${hours}`)
      .then(res => res.json());
  }
}
```

## Inter-Service Communication

### 1. User Management → Sports API
**Use Case**: Rate limiting validation, user tier verification

```python
# In Sports API - middleware for authentication
from user_management_client import UserManagementClient

class AuthenticationMiddleware:
    def __init__(self):
        self.user_client = UserManagementClient(base_url="http://user-management:8001")
    
    async def verify_user_access(self, token: str, endpoint: str):
        """Verify user has access to specific endpoint based on subscription"""
        
        # Validate JWT token with User Management service
        user_info = await self.user_client.validate_token(token)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check rate limiting
        rate_limit_status = await self.user_client.check_rate_limit(
            user_id=user_info['user_id'],
            endpoint=endpoint
        )
        
        if rate_limit_status['exceeded']:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Limit: {rate_limit_status['limit']}"
            )
        
        # Check subscription tier access
        if not await self.user_client.check_endpoint_access(
            user_id=user_info['user_id'],
            endpoint=endpoint
        ):
            raise HTTPException(
                status_code=403, 
                detail="Subscription tier required"
            )
        
        return user_info

# Usage in Sports API endpoints
@app.get("/api/v1/statcast/player/{player_id}")
async def get_player_statcast(
    player_id: int,
    limit: int = 100,
    user_info = Depends(auth_middleware.verify_user_access)
):
    # Record API usage
    await user_client.record_api_usage(
        user_id=user_info['user_id'],
        endpoint=f"/api/v1/statcast/player/{player_id}",
        method="GET"
    )
    
    # Fetch and return data
    return await get_statcast_data(player_id, limit)
```

### 2. Betting Odds → Sports API
**Use Case**: Cross-referencing game data, player information

```python
# In Betting Odds Service - integrating with Sports API
from sports_api_client import SportsApiClient

class BettingOddsProcessor:
    def __init__(self):
        self.sports_client = SportsApiClient(base_url="http://sports-api:8000")
    
    async def enrich_odds_with_game_data(self, odds_data: dict):
        """Enrich betting odds with game and player context"""
        
        game_pk = odds_data['game_pk']
        
        # Get game information from Sports API
        game_info = await self.sports_client.get_game_details(game_pk)
        
        # Get team rosters for player props
        home_roster = await self.sports_client.get_team_roster(game_info['home_team'])
        away_roster = await self.sports_client.get_team_roster(game_info['away_team'])
        
        # Get recent player performance for context
        player_stats = {}
        for player in home_roster + away_roster:
            stats = await self.sports_client.get_recent_player_stats(
                player['id'], 
                days=10
            )
            player_stats[player['id']] = stats
        
        # Enrich odds data
        enriched_odds = {
            **odds_data,
            'game_info': game_info,
            'player_context': player_stats,
            'weather': game_info.get('weather'),
            'venue': game_info.get('venue'),
            'pitching_matchup': {
                'home_pitcher': game_info.get('probable_home_pitcher'),
                'away_pitcher': game_info.get('probable_away_pitcher')
            }
        }
        
        return enriched_odds

    async def calculate_enhanced_probabilities(self, game_pk: int):
        """Calculate probabilities using both odds and statistical data"""
        
        # Get current odds
        current_odds = await self.get_current_game_odds(game_pk)
        
        # Get statistical projections from Sports API
        projections = await self.sports_client.get_game_projections(game_pk)
        
        # Combine market odds with statistical models
        enhanced_probability = self.combine_odds_and_stats(current_odds, projections)
        
        return enhanced_probability
```

### 3. Sports API → User Management
**Use Case**: Usage tracking, analytics reporting

```python
# In Sports API - reporting usage back to User Management
class UsageTracker:
    def __init__(self):
        self.user_client = UserManagementClient(base_url="http://user-management:8001")
    
    async def track_api_usage(self, user_id: int, endpoint: str, response_time: float):
        """Track API usage for analytics and billing"""
        
        usage_data = {
            'user_id': user_id,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow(),
            'response_time_ms': int(response_time * 1000),
            'data_points_returned': self.calculate_data_points(endpoint),
            'computational_cost': self.calculate_computational_cost(endpoint)
        }
        
        # Send to User Management service
        await self.user_client.record_detailed_usage(usage_data)
    
    async def send_usage_analytics(self):
        """Send periodic usage analytics to User Management"""
        
        # Aggregate usage data
        usage_summary = await self.aggregate_usage_data()
        
        # Send to User Management for dashboard display
        await self.user_client.update_usage_analytics(usage_summary)
```

## Authentication Flow

### JWT Token Validation Pattern
```python
# Shared authentication utility across services
class ServiceAuthenticator:
    def __init__(self, user_management_url: str):
        self.user_management_url = user_management_url
        self.token_cache = {}  # Redis cache in production
    
    async def validate_request(self, request: Request) -> dict:
        """Validate incoming request authentication"""
        
        # Extract JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        token = auth_header.split(' ')[1]
        
        # Check cache first
        if token in self.token_cache:
            cached_info = self.token_cache[token]
            if cached_info['expires_at'] > datetime.utcnow():
                return cached_info['user_info']
        
        # Validate with User Management service
        user_info = await self.validate_token_remote(token)
        
        # Cache valid token
        self.token_cache[token] = {
            'user_info': user_info,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        return user_info
    
    async def validate_token_remote(self, token: str) -> dict:
        """Validate token with User Management service"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.user_management_url}/api/v1/auth/validate",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=401, detail="Invalid token")

# Usage in each service
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Authentication middleware for service endpoints"""
    
    # Skip authentication for health checks and docs
    if request.url.path in ['/health', '/docs', '/openapi.json']:
        return await call_next(request)
    
    try:
        user_info = await authenticator.validate_request(request)
        request.state.user_info = user_info
    except HTTPException:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"}
        )
    
    return await call_next(request)
```

## Data Synchronization

### Real-time Data Updates
```python
# Redis pub/sub for real-time updates
class DataSynchronizer:
    def __init__(self):
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    async def publish_data_update(self, channel: str, data: dict):
        """Publish data updates to subscribers"""
        
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'data': data
        }
        
        await self.redis.publish(channel, json.dumps(message))
    
    async def subscribe_to_updates(self, channels: list, callback):
        """Subscribe to data updates from other services"""
        
        pubsub = self.redis.pubsub()
        for channel in channels:
            await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await callback(message['channel'], data)

# Example usage in Betting Odds service
class BettingOddsService:
    def __init__(self):
        self.sync = DataSynchronizer()
        
    async def start_game_updates_subscriber(self):
        """Subscribe to game updates from Sports API"""
        
        await self.sync.subscribe_to_updates(
            channels=['game_updates', 'player_updates'],
            callback=self.handle_sports_data_update
        )
    
    async def handle_sports_data_update(self, channel: str, data: dict):
        """Handle updates from Sports API"""
        
        if channel == 'game_updates':
            await self.update_game_odds_context(data)
        elif channel == 'player_updates':
            await self.update_player_props_context(data)
    
    async def publish_odds_update(self, odds_data: dict):
        """Publish odds updates to other services"""
        
        await self.sync.publish_data_update('odds_updates', odds_data)
```

## Error Handling and Circuit Breakers

### Service Resilience Pattern
```python
# Circuit breaker implementation for service calls
from circuit_breaker import CircuitBreaker

class ResilientServiceClient:
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.RequestError
        )
    
    @circuit_breaker
    async def make_request(self, endpoint: str, method: str = 'GET', **kwargs):
        """Make resilient HTTP request to another service"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                **kwargs
            )
            
            if response.status_code >= 500:
                raise httpx.RequestError(f"Server error: {response.status_code}")
            
            return response.json() if response.content else None
    
    async def get_with_fallback(self, endpoint: str, fallback_data=None):
        """Get data with fallback on failure"""
        
        try:
            return await self.make_request(endpoint)
        except Exception as e:
            logger.error(f"Service call failed: {self.service_name}{endpoint} - {e}")
            
            # Return cached data or default
            if fallback_data is not None:
                return fallback_data
            
            # Try to get from cache
            cached_data = await self.get_cached_data(endpoint)
            if cached_data:
                logger.info(f"Returning cached data for {endpoint}")
                return cached_data
            
            raise ServiceUnavailableError(f"{self.service_name} is unavailable")

# Usage across services
sports_api_client = ResilientServiceClient("sports-api", "http://sports-api:8000")
user_mgmt_client = ResilientServiceClient("user-management", "http://user-management:8001")
betting_odds_client = ResilientServiceClient("betting-odds", "http://betting-odds:8002")
```

## API Gateway Pattern (Optional)

### Centralized API Gateway
```python
# Optional API Gateway for request routing and middleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="StatEdge API Gateway")

# Service routing configuration
SERVICES = {
    'sports': 'http://sports-api:8000',
    'users': 'http://user-management:8001',
    'odds': 'http://betting-odds:8002'
}

@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Central gateway middleware for logging, auth, rate limiting"""
    
    # Log all requests
    logger.info(f"Gateway request: {request.method} {request.url}")
    
    # Add correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Add common headers
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Gateway-Version"] = "1.0.0"
    
    return response

@app.api_route("/api/v1/sports/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_sports_api(request: Request, path: str):
    """Proxy requests to Sports API"""
    return await proxy_request(request, 'sports', f"/api/v1/{path}")

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_user_mgmt(request: Request, path: str):
    """Proxy requests to User Management"""
    return await proxy_request(request, 'users', f"/api/v1/auth/{path}")

@app.api_route("/api/v1/odds/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_betting_odds(request: Request, path: str):
    """Proxy requests to Betting Odds"""
    return await proxy_request(request, 'odds', f"/api/v1/odds/{path}")

async def proxy_request(request: Request, service: str, path: str):
    """Generic request proxy with load balancing"""
    
    service_url = SERVICES[service]
    
    # Preserve headers
    headers = dict(request.headers)
    headers['X-Forwarded-For'] = request.client.host
    headers['X-Correlation-ID'] = request.state.correlation_id
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                request.method,
                f"{service_url}{path}",
                headers=headers,
                params=request.query_params,
                content=await request.body() if request.method in ['POST', 'PUT'] else None,
                timeout=30.0
            )
            
            return JSONResponse(
                content=response.json() if response.content else None,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.RequestError as e:
            logger.error(f"Proxy error for {service}: {e}")
            return JSONResponse(
                content={"error": f"Service {service} unavailable"},
                status_code=503
            )
```

## Development and Testing

### Service Integration Testing
```python
# Integration test example
import pytest
import httpx
from testcontainers import DockerCompose

@pytest.fixture(scope="session")
def services():
    """Start all services for integration testing"""
    
    with DockerCompose(".", compose_file_name="docker-compose.test.yml") as compose:
        # Wait for services to be ready
        compose.wait_for("sports-api:8000/health")
        compose.wait_for("user-management:8001/health")
        compose.wait_for("betting-odds:8002/health")
        
        yield {
            'sports_api': compose.get_service_host("sports-api", 8000),
            'user_management': compose.get_service_host("user-management", 8001),
            'betting_odds': compose.get_service_host("betting-odds", 8002)
        }

@pytest.mark.asyncio
async def test_user_authentication_flow(services):
    """Test complete user authentication and API access flow"""
    
    # 1. Register user
    async with httpx.AsyncClient() as client:
        register_response = await client.post(
            f"http://{services['user_management']}/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123"
            }
        )
        assert register_response.status_code == 201
        
        # 2. Login and get token
        login_response = await client.post(
            f"http://{services['user_management']}/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data['access_token']
        
        # 3. Use token to access Sports API
        sports_response = await client.get(
            f"http://{services['sports_api']}/api/v1/player/search?q=Judge",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert sports_response.status_code == 200
        
        # 4. Check rate limiting is enforced
        for _ in range(60):  # Exceed free tier limit
            await client.get(
                f"http://{services['sports_api']}/api/v1/statcast?limit=1",
                headers={'Authorization': f'Bearer {access_token}'}
            )
        
        # Should be rate limited now
        rate_limit_response = await client.get(
            f"http://{services['sports_api']}/api/v1/statcast?limit=1",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert rate_limit_response.status_code == 429
```

---

This service interactions guide provides comprehensive examples of how the StatEdge microservices communicate, authenticate, and share data in a secure and resilient manner.