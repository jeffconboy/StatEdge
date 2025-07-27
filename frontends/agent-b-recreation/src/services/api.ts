import axios from 'axios'
import type { Player, Team, Game, StandingsData, TrendingPlayer } from '@/types'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',  // Clean backend container port
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const authApi = axios.create({
  baseURL: 'http://localhost:3001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('statEdgeToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('statEdgeToken')
      // Redirect to login or show auth error
    }
    return Promise.reject(error)
  }
)

export interface SearchPlayersRequest {
  query: string
  limit?: number
  position?: string
  team?: string
}

export interface SearchPlayersResponse {
  players: Player[]
  total: number
}

export interface PlayerStatsResponse {
  player: Player
  stats: {
    batting?: Record<string, number>
    pitching?: Record<string, number>
    fielding?: Record<string, number>
  }
  recentGames?: Array<{
    date: string
    opponent: string
    stats: Record<string, any>
  }>
}

export interface DatabaseStatsResponse {
  total_players: number
  total_statcast_pitches: number
  statcast_2025_records: number
  fangraphs_2025_batting_players: number
  timestamp: string
}

export interface TrendingPlayersResponse {
  players: TrendingPlayer[]
  updatedAt: string
}

export interface AuthRequest {
  email: string
  password: string
}

export interface AuthResponse {
  token: string
  user: {
    id: string
    email: string
    name: string
  }
}

// Player APIs
export const playerApi = {
  // Search players
  search: async (params: SearchPlayersRequest): Promise<any> => {
    const queryParams = new URLSearchParams({
      query: params.query,
      limit: (params.limit || 10).toString()
    })
    if (params.position) queryParams.append('position', params.position)
    if (params.team) queryParams.append('team', params.team)
    
    const response = await api.get(`/players/search?${queryParams.toString()}`)
    return response.data
  },

  // Get player summary/stats
  getSummary: async (playerId: string): Promise<PlayerStatsResponse> => {
    const response = await api.get(`/players/${playerId}/summary`)
    return response.data
  },

  // Get trending players
  getTrending: async (): Promise<any> => {
    const response = await api.get('/players/trending?limit=4')
    return response.data
  }
}

// Image APIs
export const imageApi = {
  // Get player headshot
  getPlayerHeadshot: async (playerId: string): Promise<any> => {
    const response = await api.get(`/images/player/${playerId}/headshot`)
    return response.data
  },

  // Get team logo
  getTeamLogo: async (teamCode: string): Promise<any> => {
    const response = await api.get(`/images/team/${teamCode}/logo`)
    return response.data
  },

  // Get trending players with images
  getTrendingWithImages: async (limit: number = 4): Promise<any> => {
    const response = await api.get(`/images/trending-with-images?limit=${limit}`)
    return response.data
  },

  // Get batch player images
  getBatchPlayerImages: async (playerIds: string[]): Promise<any> => {
    const response = await api.get(`/images/batch/players?player_ids=${playerIds.join(',')}`)
    return response.data
  }
}

// Database/System APIs
export const systemApi = {
  // Get database statistics
  getDatabaseStats: async (): Promise<DatabaseStatsResponse> => {
    const response = await api.get('/test/database-stats')
    return response.data
  }
}

// Auth APIs
export const authApi_service = {
  // Login
  login: async (credentials: AuthRequest): Promise<AuthResponse> => {
    const response = await authApi.post('/auth/login', credentials)
    if (response.data.token) {
      localStorage.setItem('statEdgeToken', response.data.token)
    }
    return response.data
  },

  // Logout
  logout: () => {
    localStorage.removeItem('statEdgeToken')
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('statEdgeToken')
  }
}

// Games APIs
export const gamesApi = {
  // Get today's live games
  getTodaysGames: async (): Promise<any> => {
    const response = await api.get('/games/today')
    return response.data
  },

  // Get only currently live games
  getLiveGames: async (): Promise<Game[]> => {
    try {
      const response = await api.get('/games/live')
      const data = response.data
      
      // Transform API response to match frontend Game interface
      return data.games?.map((game: any) => ({
        id: game.id,
        homeTeam: {
          id: game.homeTeam.id,
          name: game.homeTeam.name,
          abbreviation: game.homeTeam.abbreviation
        },
        awayTeam: {
          id: game.awayTeam.id,
          name: game.awayTeam.name,
          abbreviation: game.awayTeam.abbreviation
        },
        homeScore: game.homeScore,
        awayScore: game.awayScore,
        status: game.status,
        time: game.time,
        inning: game.inning
      })) || []
    } catch (error) {
      console.error('Failed to fetch live games, using fallback:', error)
      return mockApi.getLiveGames()
    }
  },

  // Get games for specific team
  getTeamGames: async (teamId: string, days: number = 7): Promise<any> => {
    const response = await api.get(`/games/team/${teamId}?days=${days}`)
    return response.data
  },

  // Refresh games cache
  refreshGames: async (): Promise<any> => {
    const response = await api.get('/games/refresh')
    return response.data
  }
}

// Mock data functions for development (can be removed when APIs are fully working)
export const mockApi = {
  // Mock live games data (fallback)
  getLiveGames: async (): Promise<Game[]> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    return [
      {
        id: '1',
        homeTeam: { id: '1', name: 'New York Yankees', abbreviation: 'NYY' },
        awayTeam: { id: '2', name: 'Boston Red Sox', abbreviation: 'BOS' },
        homeScore: 7,
        awayScore: 4,
        status: 'final',
        inning: 'Final'
      },
      {
        id: '2',
        homeTeam: { id: '3', name: 'Los Angeles Dodgers', abbreviation: 'LAD' },
        awayTeam: { id: '4', name: 'San Francisco Giants', abbreviation: 'SF' },
        homeScore: 3,
        awayScore: 5,
        status: 'live',
        inning: 'Bot 8th'
      },
      {
        id: '3',
        homeTeam: { id: '5', name: 'Houston Astros', abbreviation: 'HOU' },
        awayTeam: { id: '6', name: 'Texas Rangers', abbreviation: 'TEX' },
        homeScore: 2,
        awayScore: 1,
        status: 'live',
        inning: 'Mid 6th'
      }
    ]
  },

  // Mock feature players for spotlight cards
  getFeaturedPlayers: async () => {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    return [
      {
        player: { name: 'Aaron Judge', team: 'New York Yankees' },
        matchup: 'vs Boston Red Sox',
        stats: [
          { label: 'AB', value: '4' },
          { label: 'H', value: '3' },
          { label: 'HR', value: '2' },
          { label: 'RBI', value: '4' }
        ],
        highlight: 'He has 8 HRs in his last 7 games',
        bgColor: 'blue' as const
      },
      {
        player: { name: 'Mike Trout', team: 'Los Angeles Angels' },
        matchup: 'vs Seattle Mariners',
        stats: [
          { label: 'AB', value: '3' },
          { label: 'H', value: '2' },
          { label: 'BB', value: '2' },
          { label: 'R', value: '2' }
        ],
        highlight: 'On base in 12 consecutive games',
        bgColor: 'red' as const
      },
      {
        player: { name: 'Mookie Betts', team: 'Los Angeles Dodgers' },
        matchup: 'vs San Francisco Giants',
        stats: [
          { label: 'AB', value: '5' },
          { label: 'H', value: '4' },
          { label: '2B', value: '2' },
          { label: 'SB', value: '1' }
        ],
        highlight: 'Perfect 4-for-4 night with 2 doubles',
        bgColor: 'green' as const
      },
      {
        player: { name: 'Ronald Acuña Jr.', team: 'Atlanta Braves' },
        matchup: 'vs Philadelphia Phillies',
        stats: [
          { label: 'AB', value: '4' },
          { label: 'H', value: '2' },
          { label: 'HR', value: '1' },
          { label: 'SB', value: '2' }
        ],
        highlight: 'First 30-30 season since 2018',
        bgColor: 'purple' as const
      }
    ]
  }
}

// Composable for API error handling
export const useApiError = () => {
  const handleError = (error: any) => {
    console.error('API Error:', error)
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.message || `Error ${error.response.status}: ${error.response.statusText}`
      return { message, status: error.response.status }
    } else if (error.request) {
      // Request was made but no response received
      return { message: 'Network error - please check your connection', status: 0 }
    } else {
      // Something else happened
      return { message: error.message || 'An unexpected error occurred', status: -1 }
    }
  }

  return { handleError }
}

export default api