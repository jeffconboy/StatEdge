import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PlayerSearch from '../components/PlayerSearch';
import { playerAPI, analyticsAPI, aiAPI, handleAPIError } from '../utils/api';
import { useAuth } from '../hooks/useAuth';

const Dashboard = () => {
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [trendingPlayers, setTrendingPlayers] = useState([]);
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [dbStats, setDbStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async (isRetry = false) => {
    try {
      if (!isRetry) {
        setLoading(true);
        setError(null);
      }

      // Load database stats and trending players with timeout handling
      const [dbStatsResponse, trendingResponse] = await Promise.allSettled([
        analyticsAPI.getDatabaseStats(),
        playerAPI.getTrending(5)
      ]);

      let hasErrors = false;

      if (dbStatsResponse.status === 'fulfilled') {
        setDbStats(dbStatsResponse.value.data);
      } else {
        console.error('Database stats failed:', dbStatsResponse.reason);
        hasErrors = true;
      }

      if (trendingResponse.status === 'fulfilled') {
        setTrendingPlayers(trendingResponse.value.data || []);
      } else {
        console.error('Trending players failed:', trendingResponse.reason);
        hasErrors = true;
      }

      // Set AI suggestions with error handling
      setAiSuggestions([
        "Show me Aaron Judge's home run stats",
        "Compare Mookie Betts and Ronald Acuña Jr",
        "Who has the highest exit velocity this season?",
        "Find pitchers with the best strikeout rates"
      ]);

      setLastUpdated(new Date().toLocaleTimeString());
      setRetryAttempts(0);

      // Show partial error if some requests failed but others succeeded
      if (hasErrors && (dbStats || trendingPlayers.length > 0)) {
        setError('Some data could not be loaded. Dashboard may be incomplete.');
      }

    } catch (error) {
      console.error('Dashboard loading error:', error);
      setError(handleAPIError(error));
      
      // Implement exponential backoff for retries
      if (retryAttempts < 3) {
        setTimeout(() => {
          setRetryAttempts(prev => prev + 1);
          loadDashboardData(true);
        }, Math.pow(2, retryAttempts) * 1000);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = async (player) => {
    setSelectedPlayer(player);
    setPlayerStats(null);
    setLoading(true);
    setError(null);

    try {
      const response = await playerAPI.getSummary(player.id);
      const playerData = response.data;
      
      // Validate data quality
      if (!playerData.player_info) {
        throw new Error('Player information not available');
      }

      // Check for 2025 data availability
      const has2025Data = playerData.fangraphs_batting?.some(stat => stat.Season === 2025) ||
                         playerData.statcast_summary?.some(pitch => pitch.game_year === 2025);
      
      if (!has2025Data) {
        setError(`Limited 2025 data available for ${player.name}. Showing historical data.`);
      }

      setPlayerStats(playerData);
    } catch (error) {
      const errorMessage = handleAPIError(error);
      setError(`Failed to load data for ${player.name}: ${errorMessage}`);
      console.error('Player selection error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAiQuery = async (query = aiQuery) => {
    if (!query.trim()) return;

    setAiLoading(true);
    setError(null);

    try {
      const response = await aiAPI.chat(query, { source: 'dashboard' });
      setAiResponse(response.data);
      setAiQuery('');
    } catch (error) {
      setError(handleAPIError(error));
    } finally {
      setAiLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setAiQuery(suggestion);
    handleAiQuery(suggestion);
  };

  const formatStatValue = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      return value.toFixed(3);
    }
    return value;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-gradient">
            Welcome back, {user?.email?.split('@')[0]}
          </h1>
          <p className="text-secondary-600 mt-1 flex items-center">
            <span className="mr-2">⚾</span>
            Analyze baseball statistics with AI assistance
            <span className="success-indicator ml-3">2025 Season Live</span>
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <div className="flex items-center space-x-4 text-sm">
            <span className="text-secondary-600">
              Tier: <span className="font-medium text-primary-600">{user?.tier?.toUpperCase()}</span>
            </span>
            <span className="text-secondary-600">
              Queries Today: <span className="font-medium">{user?.query_count_today || 0}</span>
            </span>
            {lastUpdated && (
              <span className="text-secondary-500">
                Updated: {lastUpdated}
              </span>
            )}
            <button
              onClick={() => loadDashboardData()}
              disabled={loading}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
              title="Refresh dashboard data"
            >
              {loading ? '↻' : '⟳'} Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Player Search */}
      <div className="card">
        <h2 className="text-xl font-semibold text-secondary-900 mb-4">Player Search</h2>
        <PlayerSearch 
          onPlayerSelect={handlePlayerSelect}
          placeholder="Search for any MLB player..."
        />
      </div>

      {/* AI Chat Interface */}
      <div className="card">
        <h2 className="text-xl font-semibold text-secondary-900 mb-4">AI Assistant</h2>
        <div className="space-y-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={aiQuery}
              onChange={(e) => setAiQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAiQuery()}
              placeholder="Ask anything about baseball statistics..."
              className="input-primary flex-1"
            />
            <button
              onClick={() => handleAiQuery()}
              disabled={aiLoading || !aiQuery.trim()}
              className="btn-primary"
            >
              {aiLoading ? 'Thinking...' : 'Ask AI'}
            </button>
          </div>

          {/* AI Suggestions */}
          {aiSuggestions.length > 0 && (
            <div>
              <p className="text-sm text-secondary-600 mb-2">Try these queries:</p>
              <div className="flex flex-wrap gap-2">
                {aiSuggestions.slice(0, 4).map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="text-xs bg-secondary-100 hover:bg-secondary-200 text-secondary-700 px-3 py-1 rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* AI Response */}
          {aiResponse && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">AI Analysis:</h3>
              <p className="text-blue-800 text-sm mb-3">{aiResponse.explanation}</p>
              
              {aiResponse.suggestions && (
                <div>
                  <p className="text-xs text-blue-600 mb-1">Follow-up questions:</p>
                  <div className="space-y-1">
                    {aiResponse.suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="block text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Selected Player Stats */}
        {selectedPlayer && (
          <div className="card">
            <h2 className="text-xl font-semibold text-secondary-900 mb-4">
              {selectedPlayer.name} - {selectedPlayer.team}
            </h2>
            
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : playerStats ? (
              <div className="space-y-4">
                {/* Basic Info */}
                <div className="bg-secondary-50 rounded-lg p-4">
                  <h3 className="font-medium text-secondary-900 mb-2">Player Info</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-secondary-600">Position:</span>
                      <span className="ml-2 font-medium">{selectedPlayer.position}</span>
                    </div>
                    <div>
                      <span className="text-secondary-600">Team:</span>
                      <span className="ml-2 font-medium">{selectedPlayer.team}</span>
                    </div>
                  </div>
                </div>

                {/* Quick Stats */}
                {playerStats.fangraphs_batting && playerStats.fangraphs_batting.length > 0 && (() => {
                  // Find 2025 season data, fallback to most recent
                  const season2025 = playerStats.fangraphs_batting.find(stat => stat.Season === 2025);
                  const currentSeasonStats = season2025 || playerStats.fangraphs_batting[0];
                  const displaySeason = currentSeasonStats?.Season || 'Current';
                  
                  return (
                    <div>
                      <h3 className="font-medium text-secondary-900 mb-2">{displaySeason} Performance</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { key: 'AVG', label: 'AVG' },
                          { key: 'OPS', label: 'OPS' }, 
                          { key: 'wOBA', label: 'wOBA' },
                          { key: 'wRC_plus', label: 'wRC+' }
                        ].map((stat) => (
                          <div key={stat.key} className="stat-card">
                            <div className="text-xs text-secondary-600 uppercase">{stat.label}</div>
                            <div className="text-lg font-semibold text-secondary-900">
                              {formatStatValue(currentSeasonStats?.[stat.key])}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}

                {/* League Context & Rankings */}
                {playerStats.fangraphs_batting && playerStats.fangraphs_batting.length > 0 && (() => {
                  // Find 2025 season data, fallback to most recent
                  const season2025 = playerStats.fangraphs_batting.find(stat => stat.Season === 2025);
                  const currentSeasonStats = season2025 || playerStats.fangraphs_batting[0];
                  
                  return (
                    <div>
                      <h3 className="font-medium text-secondary-900 mb-2">League Context</h3>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-green-700">wRC+ Rank:</span>
                            <span className="ml-2 font-medium text-green-900">
                              {currentSeasonStats.wRC_plus >= 140 ? 'Elite (Top 10%)' :
                               currentSeasonStats.wRC_plus >= 115 ? 'Above Average' :
                               currentSeasonStats.wRC_plus >= 85 ? 'Average' : 'Below Average'}
                            </span>
                          </div>
                          <div>
                            <span className="text-green-700">WAR Pace:</span>
                            <span className="ml-2 font-medium text-green-900">
                              {(currentSeasonStats.WAR || 0) > 4 ? 'All-Star Level' :
                               (currentSeasonStats.WAR || 0) > 2 ? 'Solid Starter' :
                               (currentSeasonStats.WAR || 0) > 0 ? 'Role Player' : 'Below Average'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Statcast Recent Activity */}
                {playerStats.statcast_summary && playerStats.statcast_summary.length > 0 && (
                  <div>
                    <h3 className="font-medium text-secondary-900 mb-2">Recent Activity</h3>
                    <div className="bg-secondary-50 rounded-lg p-3">
                      <div className="text-sm text-secondary-700">
                        Last game: <span className="font-medium">{playerStats.statcast_summary[0].game_date?.split('T')[0]}</span>
                      </div>
                      <div className="text-sm text-secondary-700 mt-1">
                        vs {playerStats.statcast_summary[0].home_team === selectedPlayer.team ? 
                          playerStats.statcast_summary[0].away_team : 
                          playerStats.statcast_summary[0].home_team}
                      </div>
                      <div className="text-xs text-secondary-600 mt-2">
                        Total Statcast events: {playerStats.statcast_summary.length}
                      </div>
                    </div>
                  </div>
                )}

                <button
                  onClick={() => navigate(`/player/${selectedPlayer.id}`)}
                  className="btn-primary w-full"
                >
                  View Detailed Analysis
                </button>
              </div>
            ) : error ? (
              <div className="text-red-600 text-sm">{error}</div>
            ) : (
              <div className="text-secondary-600 text-sm">Select a player to view statistics</div>
            )}
          </div>
        )}

        {/* Database Stats & Trending Players */}
        <div className="space-y-6">
          {/* Database Statistics */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-secondary-900">Platform Statistics</h2>
              {loading && (
                <div className="flex items-center text-sm text-secondary-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                  Loading...
                </div>
              )}
            </div>
            
            {dbStats ? (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="stat-card">
                    <div className="text-xs text-secondary-600 uppercase">Total Players</div>
                    <div className="text-2xl font-semibold text-secondary-900">
                      {dbStats.total_players?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                  <div className="stat-card">
                    <div className="text-xs text-secondary-600 uppercase">Statcast Pitches</div>
                    <div className="text-2xl font-semibold text-secondary-900">
                      {dbStats.total_statcast_pitches?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                  <div className="stat-card">
                    <div className="text-xs text-secondary-600 uppercase">2025 Records</div>
                    <div className="text-2xl font-semibold text-green-600">
                      {dbStats.statcast_2025_records?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                  <div className="stat-card">
                    <div className="text-xs text-secondary-600 uppercase">FanGraphs Players</div>
                    <div className="text-2xl font-semibold text-secondary-900">
                      {dbStats.fangraphs_2025_batting_players?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                </div>
                
                {/* Data Quality Indicators */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-700 font-medium">Data Status:</span>
                    <span className="text-green-900">✓ 2025 Season Active</span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-1">
                    <span className="text-green-700">Date Range:</span>
                    <span className="text-green-900">
                      {dbStats.statcast_date_range?.earliest?.split('T')[0]} to {dbStats.statcast_date_range?.latest?.split('T')[0]}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <div className="text-secondary-600">
                  {loading ? 'Loading platform statistics...' : 'Platform statistics unavailable'}
                </div>
              </div>
            )}
          </div>

          {/* Trending Players */}
          {trendingPlayers.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-secondary-900 mb-4">Trending Players</h2>
              <div className="space-y-3">
                {trendingPlayers.map((player, index) => (
                  <button
                    key={player.id}
                    onClick={() => handlePlayerSelect(player)}
                    className="w-full text-left p-3 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-secondary-900">{player.name}</div>
                        <div className="text-sm text-secondary-600">
                          {player.team} • {player.position}
                        </div>
                      </div>
                      <div className="text-sm text-secondary-500">
                        #{index + 1}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                Data Loading Issue
              </h3>
              <div className="mt-1 text-sm text-red-600">
                {error}
              </div>
              {retryAttempts > 0 && (
                <div className="mt-2 text-xs text-red-500">
                  Retry attempt {retryAttempts}/3...
                </div>
              )}
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => {
                  setError(null);
                  loadDashboardData();
                }}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;