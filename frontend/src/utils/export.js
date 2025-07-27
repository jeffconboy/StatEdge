// StatEdge Data Export Utilities
// Comprehensive data export functionality with multiple formats

export const exportFormats = {
  JSON: 'json',
  CSV: 'csv',
  PDF: 'pdf',
  EXCEL: 'xlsx'
};

export const exportPlayerData = async (playerData, format = exportFormats.JSON, options = {}) => {
  try {
    const timestamp = new Date().toISOString();
    const playerName = playerData.player?.name || 'Unknown Player';
    const sanitizedName = playerName.replace(/[^a-zA-Z0-9]/g, '_');
    
    // Prepare comprehensive export data
    const exportData = {
      metadata: {
        player_name: playerName,
        export_timestamp: timestamp,
        export_format: format,
        source: 'StatEdge Analytics Platform',
        data_version: '2025.1',
        ...options.metadata
      },
      player_info: {
        id: playerData.player?.id,
        name: playerName,
        team: playerData.player?.current_team || playerData.player?.team,
        position: playerData.player?.primary_position || playerData.player?.position,
        mlb_id: playerData.player?.mlb_id,
        active: playerData.player?.active || true
      },
      statistics: {
        fangraphs_batting: playerData.stats?.fangraphs_batting || [],
        fangraphs_pitching: playerData.stats?.fangraphs_pitching || [],
        statcast_summary: playerData.stats?.statcast_summary || [],
        statcast_detailed: playerData.stats?.statcast_data || []
      },
      analytics: {
        season_2025_data: extractSeasonData(playerData.stats, 2025),
        league_context: generateLeagueContext(playerData.stats),
        performance_metrics: calculatePerformanceMetrics(playerData.stats),
        export_summary: generateExportSummary(playerData.stats)
      }
    };

    switch (format) {
      case exportFormats.JSON:
        return downloadJSON(exportData, `${sanitizedName}_stats.json`);
      case exportFormats.CSV:
        return downloadCSV(exportData, `${sanitizedName}_stats.csv`);
      case exportFormats.PDF:
        return downloadPDF(exportData, `${sanitizedName}_report.pdf`);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  } catch (error) {
    console.error('Export error:', error);
    throw new Error(`Failed to export data: ${error.message}`);
  }
};

const extractSeasonData = (stats, season) => {
  if (!stats) return null;
  
  const season2025 = {
    fangraphs_batting: stats.fangraphs_batting?.filter(s => s.Season === season) || [],
    fangraphs_pitching: stats.fangraphs_pitching?.filter(s => s.Season === season) || [],
    statcast_events: stats.statcast_summary?.filter(s => s.game_year === season) || []
  };
  
  return {
    ...season2025,
    has_data: season2025.fangraphs_batting.length > 0 || 
              season2025.fangraphs_pitching.length > 0 || 
              season2025.statcast_events.length > 0,
    data_completeness: {
      fangraphs_batting: season2025.fangraphs_batting.length,
      fangraphs_pitching: season2025.fangraphs_pitching.length,
      statcast_events: season2025.statcast_events.length
    }
  };
};

const generateLeagueContext = (stats) => {
  if (!stats?.fangraphs_batting?.length) return null;
  
  const battingStats = stats.fangraphs_batting[0];
  
  return {
    wrc_plus_ranking: getWRCPlusRanking(battingStats.wRC_plus),
    war_classification: getWARClassification(battingStats.WAR),
    ops_percentile: getOPSPercentile(battingStats.OPS),
    avg_classification: getAVGClassification(battingStats.AVG)
  };
};

const calculatePerformanceMetrics = (stats) => {
  if (!stats) return null;
  
  const metrics = {};
  
  // Statcast metrics
  if (stats.statcast_data?.length) {
    const validHits = stats.statcast_data.filter(p => 
      p.data.launch_speed && p.data.launch_speed > 0
    );
    
    if (validHits.length > 0) {
      metrics.statcast = {
        avg_exit_velocity: validHits.reduce((sum, hit) => 
          sum + hit.data.launch_speed, 0) / validHits.length,
        hard_hit_rate: validHits.filter(hit => 
          hit.data.launch_speed >= 95).length / validHits.length * 100,
        barrel_rate: validHits.filter(hit => 
          hit.data.launch_speed >= 98 && 
          hit.data.launch_angle >= 26 && 
          hit.data.launch_angle <= 30).length / validHits.length * 100,
        sweet_spot_rate: validHits.filter(hit => 
          hit.data.launch_angle >= 8 && 
          hit.data.launch_angle <= 32).length / validHits.length * 100
      };
    }
  }
  
  // FanGraphs advanced metrics
  if (stats.fangraphs_batting?.length) {
    const batting = stats.fangraphs_batting[0];
    metrics.advanced_batting = {
      iso: batting.SLG - batting.AVG,
      bb_k_ratio: batting.BB / batting.SO,
      contact_rate: (batting.AB - batting.SO) / batting.AB * 100,
      power_speed_number: (2 * batting.HR * batting.SB) / (batting.HR + batting.SB)
    };
  }
  
  return metrics;
};

const generateExportSummary = (stats) => {
  const summary = {
    data_sources: [],
    total_records: 0,
    date_range: null,
    quality_score: 0
  };
  
  if (stats?.fangraphs_batting?.length) {
    summary.data_sources.push('FanGraphs Batting');
    summary.total_records += stats.fangraphs_batting.length;
  }
  
  if (stats?.fangraphs_pitching?.length) {
    summary.data_sources.push('FanGraphs Pitching');
    summary.total_records += stats.fangraphs_pitching.length;
  }
  
  if (stats?.statcast_summary?.length) {
    summary.data_sources.push('MLB Statcast');
    summary.total_records += stats.statcast_summary.length;
  }
  
  // Calculate quality score (0-100)
  summary.quality_score = Math.min(100, 
    (summary.data_sources.length * 20) + 
    (Math.min(summary.total_records, 100) * 0.4)
  );
  
  return summary;
};

// Ranking helper functions
const getWRCPlusRanking = (wrcPlus) => {
  if (!wrcPlus) return 'N/A';
  if (wrcPlus >= 140) return 'Elite (Top 10%)';
  if (wrcPlus >= 115) return 'Above Average';
  if (wrcPlus >= 85) return 'Average';
  return 'Below Average';
};

const getWARClassification = (war) => {
  if (!war) return 'N/A';
  if (war >= 6) return 'MVP Candidate';
  if (war >= 4) return 'All-Star Level';
  if (war >= 2) return 'Solid Starter';
  if (war >= 1) return 'Role Player';
  return 'Below Replacement';
};

const getOPSPercentile = (ops) => {
  if (!ops) return 'N/A';
  if (ops >= 0.900) return '90th+ percentile';
  if (ops >= 0.800) return '75th+ percentile';
  if (ops >= 0.750) return '50th+ percentile';
  return 'Below 50th percentile';
};

const getAVGClassification = (avg) => {
  if (!avg) return 'N/A';
  if (avg >= 0.300) return 'Excellent';
  if (avg >= 0.275) return 'Above Average';
  if (avg >= 0.250) return 'Average';
  return 'Below Average';
};

// Export format functions
const downloadJSON = (data, filename) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { 
    type: 'application/json' 
  });
  downloadBlob(blob, filename);
  return true;
};

const downloadCSV = (data, filename) => {
  // Convert key statistics to CSV format
  let csv = 'Category,Metric,Value\\n';
  
  // Player info
  if (data.player_info) {
    Object.entries(data.player_info).forEach(([key, value]) => {
      csv += `Player Info,${key},${value || 'N/A'}\\n`;
    });
  }
  
  // 2025 batting stats
  if (data.analytics?.season_2025_data?.fangraphs_batting?.length) {
    const stats = data.analytics.season_2025_data.fangraphs_batting[0];
    Object.entries(stats).forEach(([key, value]) => {
      if (typeof value === 'number') {
        csv += `2025 Batting,${key},${value}\\n`;
      }
    });
  }
  
  // Performance metrics
  if (data.analytics?.performance_metrics?.statcast) {
    Object.entries(data.analytics.performance_metrics.statcast).forEach(([key, value]) => {
      csv += `Statcast Metrics,${key},${value}\\n`;
    });
  }
  
  const blob = new Blob([csv], { type: 'text/csv' });
  downloadBlob(blob, filename);
  return true;
};

const downloadPDF = (data, filename) => {
  // For now, create a simple text-based PDF content
  // In a real implementation, you'd use a library like jsPDF
  const content = `
StatEdge Player Report
===================

Player: ${data.player_info?.name || 'Unknown'}
Team: ${data.player_info?.team || 'Unknown'}
Position: ${data.player_info?.position || 'Unknown'}
Export Date: ${data.metadata?.export_timestamp || 'Unknown'}

2025 Season Summary:
${data.analytics?.season_2025_data?.has_data ? 'Data Available' : 'Limited Data'}

League Context:
wRC+ Ranking: ${data.analytics?.league_context?.wrc_plus_ranking || 'N/A'}
WAR Classification: ${data.analytics?.league_context?.war_classification || 'N/A'}

Data Quality Score: ${data.analytics?.export_summary?.quality_score || 0}/100

Generated by StatEdge Analytics Platform
  `;
  
  const blob = new Blob([content], { type: 'text/plain' });
  downloadBlob(blob, filename.replace('.pdf', '.txt'));
  return true;
};

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export default {
  exportFormats,
  exportPlayerData,
  downloadJSON,
  downloadCSV,
  downloadPDF
};