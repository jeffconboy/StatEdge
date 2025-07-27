export interface NavigationItem {
  name: string
  path: string
  icon: string
  active?: boolean
  badge?: string
}

export interface Player {
  id: string
  name: string
  team: string
  position: string
  photo?: string
  stats?: Record<string, any>
}

export interface Team {
  id: string
  name: string
  abbreviation: string
  logo?: string
  record?: {
    wins: number
    losses: number
    percentage: number
  }
}

export interface Game {
  id: string
  homeTeam: Team
  awayTeam: Team
  homeScore: number
  awayScore: number
  status: 'scheduled' | 'live' | 'final'
  time?: string
  inning?: string
}

export interface StandingsData {
  team: Team
  wins: number
  losses: number
  percentage: number
  gamesBehind: number
  streak?: string
}

export interface TrendingPlayer {
  player: Player
  stats: Record<string, number | string>
  trend: 'up' | 'down' | 'stable'
}