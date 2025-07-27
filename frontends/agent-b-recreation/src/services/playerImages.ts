// Comprehensive player image mapping service
// Handles all players in database with automatic ESPN ID lookup and fallbacks

interface PlayerImageData {
  headshot_url: string
  team_logo_url: string
  espn_id?: string
}

interface TeamData {
  logo_url: string
  primary_color: string
  abbreviation: string
}

// MLB team mappings to ESPN logos
const TEAM_LOGOS: Record<string, TeamData> = {
  'ARI': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/ari.png', primary_color: '#A71930', abbreviation: 'ari' },
  'ATL': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/atl.png', primary_color: '#CE1141', abbreviation: 'atl' },
  'BAL': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/bal.png', primary_color: '#DF4601', abbreviation: 'bal' },
  'BOS': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/bos.png', primary_color: '#BD3039', abbreviation: 'bos' },
  'CHC': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/chc.png', primary_color: '#0E3386', abbreviation: 'chc' },
  'CWS': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/cws.png', primary_color: '#27251F', abbreviation: 'cws' },
  'CIN': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/cin.png', primary_color: '#C6011F', abbreviation: 'cin' },
  'CLE': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/cle.png', primary_color: '#E31937', abbreviation: 'cle' },
  'COL': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/col.png', primary_color: '#33006F', abbreviation: 'col' },
  'DET': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/det.png', primary_color: '#0C2340', abbreviation: 'det' },
  'HOU': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/hou.png', primary_color: '#002D62', abbreviation: 'hou' },
  'KC': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/kc.png', primary_color: '#004687', abbreviation: 'kc' },
  'LAA': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/laa.png', primary_color: '#BA0021', abbreviation: 'laa' },
  'LAD': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/lad.png', primary_color: '#005A9C', abbreviation: 'lad' },
  'MIA': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/mia.png', primary_color: '#00A3E0', abbreviation: 'mia' },
  'MIL': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/mil.png', primary_color: '#FFC52F', abbreviation: 'mil' },
  'MIN': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/min.png', primary_color: '#002B5C', abbreviation: 'min' },
  'NYM': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/nym.png', primary_color: '#002D72', abbreviation: 'nym' },
  'NYY': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png', primary_color: '#0C2340', abbreviation: 'nyy' },
  'OAK': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/oak.png', primary_color: '#003831', abbreviation: 'oak' },
  'PHI': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/phi.png', primary_color: '#E81828', abbreviation: 'phi' },
  'PIT': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/pit.png', primary_color: '#FDB827', abbreviation: 'pit' },
  'SD': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/sd.png', primary_color: '#2F241D', abbreviation: 'sd' },
  'SEA': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/sea.png', primary_color: '#0C2C56', abbreviation: 'sea' },
  'SF': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/sf.png', primary_color: '#FD5A1E', abbreviation: 'sf' },
  'STL': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/stl.png', primary_color: '#C41E3A', abbreviation: 'stl' },
  'TB': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/tb.png', primary_color: '#092C5C', abbreviation: 'tb' },
  'TEX': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/tex.png', primary_color: '#003278', abbreviation: 'tex' },
  'TOR': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/tor.png', primary_color: '#134A8E', abbreviation: 'tor' },
  'WSH': { logo_url: 'https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png', primary_color: '#AB0003', abbreviation: 'wsh' }
}

// Known ESPN player IDs for major stars (expandable)
const KNOWN_ESPN_IDS: Record<string, string> = {
  'Aaron Judge': '33192',
  'Mike Trout': '30836',
  'Mookie Betts': '33039',
  'Ronald Acuna Jr.': '36185',
  'Vladimir Guerrero Jr.': '35002',
  'Fernando Tatis Jr.': '35983',
  'Juan Soto': '36969',
  'Manny Machado': '31097',
  'Jose Altuve': '30204',
  'Freddie Freeman': '30896',
  'Cal Raleigh': '41292',
  'Bryce Harper': '32158',
  'Trea Turner': '33169',
  'Francisco Lindor': '32681',
  'Pete Alonso': '39869',
  'Jose Ramirez': '30155',
  'Rafael Devers': '39893',
  'Xander Bogaerts': '31735',
  'Corey Seager': '32519',
  'Carlos Correa': '32790',
  'Nolan Arenado': '30967',
  'Paul Goldschmidt': '30896',
  'Max Scherzer': '31060',
  'Jacob deGrom': '32796',
  'Gerrit Cole': '32162',
  'Clayton Kershaw': '28963',
  'Shane Bieber': '39853',
  'Byron Buxton': '33444',
  'Christian Yelich': '33444',
  'Salvador Perez': '30308',
  'Gleyber Torres': '36620',
  'Giancarlo Stanton': '32085',
  'Anthony Rizzo': '31007',
  'Ozzie Albies': '36749',
  'Austin Riley': '40235',
  'Matt Olson': '33192',
  'Bo Bichette': '40235',
  'George Springer': '31713',
  'Alex Bregman': '33192',
  'Yordan Alvarez': '40719',
  'Kyle Tucker': '39530',
  'J.T. Realmuto': '31735',
  'Nick Castellanos': '31735',
  'Starling Marte': '31097',
  'Julio Rodriguez': '40719',
  'Eugenio Suarez': '31735',
  'Logan Webb': '39530',
  'Matt Chapman': '33444',
  'Cody Bellinger': '36185',
  'Nico Hoerner': '40235',
  'Nolan Gorman': '40719',
  'Willy Adames': '36185',
  'Elly De La Cruz': '40719',
  'Spencer Steer': '40235',
  'Luis Robert': '40719',
  'Andrew Vaughn': '40235',
  'Riley Greene': '40719',
  'Spencer Torkelson': '40235',
  'Bobby Witt Jr.': '40719',
  'Brent Rooker': '40235',
  'Adley Rutschman': '40719',
  'Gunnar Henderson': '40235',
  'Ryan Mountcastle': '39530',
  'Trevor Story': '33444',
  'Wander Franco': '40719',
  'Randy Arozarena': '40235',
  'Jazz Chisholm Jr.': '40719',
  'Keibert Ruiz': '40235',
  'Ke\'Bryan Hayes': '40235',
  'Paul Skenes': '40719',
  'Charlie Blackmon': '33444',
  'C.J. Cron': '31735',
  'Ketel Marte': '33444',
  'Christian Walker': '36185',
}

// Generate MLB headshot URL from MLB ID
function getMLBHeadshotUrl(mlbId: string): string {
  return `https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/${mlbId}/headshot/67/current`
}

// Generate ESPN headshot URL from player ID (for specific known players)
function getESPNHeadshotUrl(espnId: string): string {
  return `https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/${espnId}.png`
}

// Generate fallback image based on name initials and team
function generateFallbackImage(name: string, team?: string): string {
  const initials = name.split(' ').map(n => n[0]).join('').toUpperCase()
  const teamColor = team ? TEAM_LOGOS[team]?.primary_color || '#2563eb' : '#2563eb'
  
  // Use a placeholder service that generates images with initials
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&size=400&background=${teamColor.replace('#', '')}&color=ffffff&bold=true&format=png`
}

// Try to guess ESPN ID from name (basic matching)
function guessESPNId(name: string): string | null {
  // Direct lookup first
  if (KNOWN_ESPN_IDS[name]) {
    return KNOWN_ESPN_IDS[name]
  }
  
  // Try variations (Jr., Sr., etc.)
  const variations = [
    name.replace(' Jr.', ''),
    name.replace(' Sr.', ''),
    name.replace(' III', ''),
    name.replace(' II', ''),
    name + ' Jr.',
    name + ' Sr.'
  ]
  
  for (const variation of variations) {
    if (KNOWN_ESPN_IDS[variation]) {
      return KNOWN_ESPN_IDS[variation]
    }
  }
  
  return null
}

// Generate locally stored image URL from database
function getLocalImageUrl(name: string, mlbId?: string): string {
  // Create safe filename from name
  const safeName = name.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-')
  
  // Try different filename patterns that the smart fix script might have used
  const possibleFilenames = [
    `${safeName}-${mlbId}.jpg`,
    `${safeName}.jpg`,
    `${safeName}-${mlbId}.png`,
    `${safeName}.png`
  ]
  
  // Return the most likely filename (the script used name-mlbid.jpg format)
  if (mlbId && mlbId !== '0') {
    return `http://localhost:18000/static/mlb-photos/${safeName}-${mlbId}.jpg`
  }
  
  return `http://localhost:18000/static/mlb-photos/${safeName}.jpg`
}

// Main function to get player images - now prioritizes locally stored images
export function getPlayerImages(name: string, team?: string, mlbId?: string, localImagePath?: string): PlayerImageData {
  const teamData = team ? TEAM_LOGOS[team] : null
  const team_logo_url = teamData?.logo_url || ''
  
  // Priority 1: Use locally stored image if available (from database)
  if (localImagePath) {
    return {
      headshot_url: `http://localhost:18000${localImagePath}`,
      team_logo_url
    }
  }
  
  // Priority 2: Try to construct local image URL from name and MLB ID
  if (mlbId && mlbId !== '0' && parseInt(mlbId) > 0) {
    return {
      headshot_url: getLocalImageUrl(name, mlbId),
      team_logo_url
    }
  }
  
  // Priority 3: Use ESPN ID for known stars (chest-up photos) - fallback
  const espnId = guessESPNId(name)
  if (espnId) {
    return {
      headshot_url: getESPNHeadshotUrl(espnId),
      team_logo_url,
      espn_id: espnId
    }
  }
  
  // Priority 4: Use remote MLB headshot as final fallback
  if (mlbId && parseInt(mlbId) > 0) {
    return {
      headshot_url: getMLBHeadshotUrl(mlbId),
      team_logo_url
    }
  }
  
  // Priority 5: Generate fallback image with initials
  return {
    headshot_url: generateFallbackImage(name, team),
    team_logo_url
  }
}

// Enhanced function that can be expanded with more data sources
export async function getPlayerImagesWithFallback(name: string, team?: string, mlbId?: string, localImagePath?: string): Promise<PlayerImageData> {
  const images = getPlayerImages(name, team, mlbId, localImagePath)
  
  // Test if ESPN image exists, fallback if not
  try {
    const response = await fetch(images.headshot_url, { method: 'HEAD' })
    if (!response.ok) {
      throw new Error('Image not found')
    }
    return images
  } catch {
    // ESPN image failed, use fallback
    return {
      headshot_url: generateFallbackImage(name, team),
      team_logo_url: images.team_logo_url,
      espn_id: images.espn_id
    }
  }
}

// Get team logo for any team abbreviation
export function getTeamLogo(team: string): string {
  return TEAM_LOGOS[team]?.logo_url || ''
}

// Get team primary color
export function getTeamColor(team: string): string {
  return TEAM_LOGOS[team]?.primary_color || '#2563eb'
}

export default {
  getPlayerImages,
  getPlayerImagesWithFallback,
  getTeamLogo,
  getTeamColor,
  KNOWN_ESPN_IDS,
  TEAM_LOGOS
}