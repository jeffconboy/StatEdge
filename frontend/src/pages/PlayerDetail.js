import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { playerAPI, aiAPI, handleAPIError } from '../utils/api';
import { exportPlayerData, exportFormats } from '../utils/export';

const PlayerDetail = () => {
  const { playerId } = useParams();
  const navigate = useNavigate();
  
  const [player, setPlayer] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('batting');
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  useEffect(() => {
    loadPlayerData();
  }, [playerId]);

  const loadPlayerData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get both summary and detailed stats
      const [summaryResponse, statsResponse] = await Promise.allSettled([
        playerAPI.getSummary(playerId),
        playerAPI.getStats(playerId)
      ]);

      if (summaryResponse.status === 'fulfilled') {
        const summaryData = summaryResponse.value.data;
        setPlayer(summaryData.player_info);
        
        // Merge summary data
        const mergedStats = {
          player_info: summaryData.player_info,
          fangraphs_batting: summaryData.fangraphs_batting,
          statcast_summary: summaryData.statcast_summary
        };

        // Add detailed stats if available
        if (statsResponse.status === 'fulfilled') {
          mergedStats.statcast_data = statsResponse.value.data.statcast_data;
        }

        setPlayerStats(mergedStats);
      } else {
        throw new Error('Failed to load player data');
      }

    } catch (error) {
      setError(handleAPIError(error));
    } finally {
      setLoading(false);
    }
  };

  const generateAiAnalysis = async () => {
    if (!player) return;

    setAiLoading(true);
    try {
      const response = await aiAPI.chat(
        `Analyze ${player.name}'s recent performance and provide betting insights`,
        { player_id: playerId, source: 'player_detail' }
      );
      setAiAnalysis(response.data);
    } catch (error) {
      console.error('AI analysis error:', error);
    } finally {
      setAiLoading(false);
    }
  };

  const handleExport = async (format) => {
    if (!player || !playerStats) return;
    
    try {
      setExportLoading(true);
      setShowExportMenu(false);
      
      const exportData = {
        player: player,
        stats: playerStats
      };
      
      await exportPlayerData(exportData, format, {
        metadata: {
          export_source: 'Player Detail Page',
          user_tier: 'premium', // Could be dynamic based on auth
          features_included: ['fangraphs', 'statcast', 'analytics']
        }
      });
      
      // Show success message (could be a toast notification)
      console.log(`Successfully exported ${player.name} data as ${format.toUpperCase()}`);
      
    } catch (error) {
      console.error('Export error:', error);
      setError(`Failed to export data: ${error.message}`);
    } finally {
      setExportLoading(false);
    }
  };

  const formatStatValue = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      return value.toFixed(3);
    }
    return value;
  };

  const renderBattingStats = () => {
    if (!playerStats?.fangraphs_batting?.length) {
      return <div className="text-secondary-600">No batting statistics available</div>;
    }

    // Find 2025 season data, fallback to most recent
    const season2025 = playerStats.fangraphs_batting.find(stat => stat.Season === 2025);
    const stats = season2025 || playerStats.fangraphs_batting[0];
    if (!stats) return <div className="text-secondary-600">No batting data found</div>;

    const basicStats = [
      { label: 'Games', key: 'G' },
      { label: 'Plate Appearances', key: 'PA' },
      { label: 'At Bats', key: 'AB' },
      { label: 'Hits', key: 'H' },
      { label: 'Home Runs', key: 'HR' },
      { label: 'RBI', key: 'RBI' },
      { label: 'Runs', key: 'R' },
      { label: 'Stolen Bases', key: 'SB' },
    ];

    const advancedStats = [
      { label: 'Batting Average', key: 'AVG' },
      { label: 'On Base %', key: 'OBP' },
      { label: 'Slugging %', key: 'SLG' },
      { label: 'OPS', key: 'OPS' },
      { label: 'wOBA', key: 'wOBA' },
      { label: 'wRC+', key: 'wRC_plus' },
      { label: 'WAR', key: 'WAR' },
      { label: 'BABIP', key: 'BABIP' },
    ];

    return (
      <div className="space-y-6">
        {/* Season Header */}
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-primary-900">{stats.Season} Season Statistics</h3>
              <p className="text-sm text-primary-700">
                Season: {stats.Season} • Team: {player.current_team || player.team}
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary-900">{stats.G || 0}</div>
              <div className="text-xs text-primary-600 uppercase">Games Played</div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Offensive Production</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {basicStats.map(({ label, key }) => (
              <div key={key} className="stat-card">
                <div className="text-xs text-secondary-600 uppercase">{label}</div>
                <div className="text-xl font-semibold text-secondary-900">
                  {key === 'AVG' || key === 'OBP' || key === 'SLG' ? 
                    (stats[key] ? stats[key].toFixed(3) : 'N/A') : 
                    (stats[key] || 'N/A')}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Advanced Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {advancedStats.map(({ label, key }) => (
              <div key={key} className="stat-card">
                <div className="text-xs text-secondary-600 uppercase">{label}</div>
                <div className="text-xl font-semibold text-secondary-900">
                  {key === 'wRC_plus' ? 
                    (stats[key] ? Math.round(stats[key]) : 'N/A') :
                    formatStatValue(stats[key])}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderStatcastStats = () => {
    if (!playerStats?.statcast_data?.length) {
      return <div className="text-secondary-600">No Statcast data available</div>;
    }

    // Aggregate Statcast data
    const statcastPitches = playerStats.statcast_data;
    const validPitches = statcastPitches.filter(pitch => pitch.data.launch_speed && pitch.data.launch_speed > 0);
    
    if (validPitches.length === 0) {
      return <div className="text-secondary-600">No recent batted ball data available</div>;
    }

    const avgExitVelo = validPitches.reduce((sum, pitch) => sum + (pitch.data.launch_speed || 0), 0) / validPitches.length;
    const avgLaunchAngle = validPitches.reduce((sum, pitch) => sum + (pitch.data.launch_angle || 0), 0) / validPitches.length;
    const hardHitBalls = validPitches.filter(pitch => pitch.data.launch_speed >= 95).length;
    const hardHitRate = (hardHitBalls / validPitches.length) * 100;

    // Additional Statcast metrics
    const homeRuns = validPitches.filter(pitch => pitch.data.events === 'home_run').length;
    const barrels = validPitches.filter(pitch => 
      pitch.data.launch_speed >= 98 && 
      pitch.data.launch_angle >= 26 && 
      pitch.data.launch_angle <= 30
    ).length;
    const sweetSpotRate = validPitches.filter(pitch => 
      pitch.data.launch_angle >= 8 && 
      pitch.data.launch_angle <= 32
    ).length / validPitches.length * 100;

    // Calculate percentiles and rankings
    const exitVeloRank = avgExitVelo >= 95 ? 'Elite (95th %ile)' : avgExitVelo >= 90 ? 'Above Avg (75th %ile)' : avgExitVelo >= 87 ? 'Average' : 'Below Avg';
    const hardHitRank = hardHitRate >= 50 ? 'Elite' : hardHitRate >= 40 ? 'Above Avg' : hardHitRate >= 30 ? 'Average' : 'Below Avg';
    
    const statcastStats = [
      { label: 'Avg Exit Velocity', value: avgExitVelo.toFixed(1) + ' mph', color: avgExitVelo >= 90 ? 'text-green-600' : 'text-secondary-900', rank: exitVeloRank },
      { label: 'Avg Launch Angle', value: avgLaunchAngle.toFixed(1) + '°', color: 'text-secondary-900', rank: avgLaunchAngle >= 10 && avgLaunchAngle <= 25 ? 'Optimal Range' : 'Outside Optimal' },
      { label: 'Hard Hit Rate', value: hardHitRate.toFixed(1) + '%', color: hardHitRate >= 40 ? 'text-green-600' : 'text-secondary-900', rank: hardHitRank },
      { label: 'Sweet Spot %', value: sweetSpotRate.toFixed(1) + '%', color: sweetSpotRate >= 35 ? 'text-green-600' : 'text-secondary-900', rank: sweetSpotRate >= 40 ? 'Elite' : 'Average' },
      { label: 'Home Runs', value: homeRuns, color: homeRuns > 0 ? 'text-primary-600' : 'text-secondary-900', rank: `${homeRuns} HR in 2025` },
      { label: 'Barrels', value: barrels, color: barrels > 0 ? 'text-primary-600' : 'text-secondary-900', rank: `${((barrels/validPitches.length)*100).toFixed(1)}% Barrel Rate` },
      { label: 'Total Batted Balls', value: validPitches.length, color: 'text-secondary-600', rank: 'From 2025 Season' },
      { label: 'Data Freshness', value: 'Live 2025', color: 'text-green-600', rank: '493k+ Total Records' },
    ];

    return (
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Statcast Advanced Metrics</h3>
          <p className="text-sm text-blue-700 mb-4">
            Real-time tracking data from MLB Statcast system • Updated through 2025 season
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {statcastStats.map(({ label, value, color, rank }) => (
              <div key={label} className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="text-xs text-blue-600 uppercase font-medium">{label}</div>
                <div className={`text-lg font-bold mt-1 ${color}`}>{value}</div>
                <div className="text-xs text-blue-500 mt-1">{rank}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Performance Heat Map</h3>
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{hardHitBalls}</div>
                <div className="text-xs text-green-700">Hard Hit Balls (95+ mph)</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{barrels}</div>
                <div className="text-xs text-blue-700">Barrel Events</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{homeRuns}</div>
                <div className="text-xs text-purple-700">Home Runs</div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Recent Batted Balls</h3>
          <div className="bg-secondary-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <div className="space-y-2">
              {validPitches.slice(0, 10).map((pitch, index) => {
                const isHardHit = pitch.data.launch_speed >= 95;
                const isBarrel = pitch.data.launch_speed >= 98 && pitch.data.launch_angle >= 26 && pitch.data.launch_angle <= 30;
                return (
                  <div key={index} className={`flex justify-between items-center text-sm p-2 rounded ${isHardHit ? 'bg-green-100' : isBarrel ? 'bg-blue-100' : 'bg-white'}`}>
                    <span className="text-secondary-600">{pitch.game_date?.split('T')[0]}</span>
                    <span className="font-medium">
                      {pitch.data.launch_speed?.toFixed(1)} mph, {pitch.data.launch_angle?.toFixed(1)}°
                      {isBarrel && <span className="ml-2 text-blue-600 font-bold">🎯</span>}
                      {isHardHit && !isBarrel && <span className="ml-2 text-green-600 font-bold">💪</span>}
                    </span>
                    <span className="text-secondary-600">{pitch.data.events || 'In play'}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button onClick={() => navigate('/')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!player) {
    return (
      <div className="text-center py-12">
        <div className="text-secondary-600 mb-4">Player not found</div>
        <button onClick={() => navigate('/')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-primary-600 hover:text-primary-700 text-sm mb-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-secondary-900">
            {player.name}
          </h1>
          <p className="text-secondary-600">
            {player.team} • {player.position}
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-3">
          <button
            onClick={generateAiAnalysis}
            disabled={aiLoading}
            className="btn-primary animate-fade-in"
          >
            {aiLoading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing...
              </div>
            ) : (
              '🤖 AI Analysis'
            )}
          </button>
          
          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={exportLoading}
              className="btn-secondary flex items-center animate-fade-in"
            >
              {exportLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-secondary-600 mr-2"></div>
                  Exporting...
                </div>
              ) : (
                <>
                  📊 Export Data
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </>
              )}
            </button>
            
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-secondary-200 z-10 animate-slide-up">
                <div className="py-1">
                  <div className="px-4 py-2 text-xs text-secondary-600 font-medium uppercase border-b border-secondary-100">
                    Export Formats
                  </div>
                  <button
                    onClick={() => handleExport(exportFormats.JSON)}
                    className="w-full text-left px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50 flex items-center"
                  >
                    <span className="mr-2">📄</span> JSON (Complete Data)
                  </button>
                  <button
                    onClick={() => handleExport(exportFormats.CSV)}
                    className="w-full text-left px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50 flex items-center"
                  >
                    <span className="mr-2">📊</span> CSV (Statistics)
                  </button>
                  <button
                    onClick={() => handleExport(exportFormats.PDF)}
                    className="w-full text-left px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-50 flex items-center"
                  >
                    <span className="mr-2">📋</span> PDF (Report)
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Analysis */}
      {aiAnalysis && (
        <div className="card bg-blue-50 border-blue-200">
          <h2 className="text-xl font-semibold text-blue-900 mb-3">AI Analysis</h2>
          <p className="text-blue-800 mb-4">{aiAnalysis.explanation}</p>
          {aiAnalysis.suggestions && (
            <div>
              <p className="text-sm font-medium text-blue-800 mb-2">Recommended Actions:</p>
              <ul className="text-sm text-blue-700 space-y-1">
                {aiAnalysis.suggestions.map((suggestion, index) => (
                  <li key={index}>• {suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Stats Tabs */}
      <div className="card">
        <div className="border-b border-secondary-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'batting', label: 'Batting Stats' },
              { id: 'statcast', label: 'Statcast Data' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'batting' && renderBattingStats()}
          {activeTab === 'statcast' && renderStatcastStats()}
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;