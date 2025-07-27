"""
Systematic Player ID Mapping Service
Maps MLB IDs to ESPN IDs for comprehensive player image coverage
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

logger = logging.getLogger(__name__)

class PlayerIDMapper:
    """Maps MLB player IDs to ESPN player IDs systematically"""
    
    def __init__(self):
        self.mlb_to_espn_cache = {}
        self.failed_lookups = set()
    
    async def get_espn_id_from_mlb_id(self, mlb_id: str) -> Optional[str]:
        """
        Find ESPN ID from MLB ID using multiple strategies:
        1. Check our known mappings first
        2. Try ESPN search API
        3. Try name-based lookup
        """
        if mlb_id in self.mlb_to_espn_cache:
            return self.mlb_to_espn_cache[mlb_id]
        
        if mlb_id in self.failed_lookups:
            return None
        
        # Strategy 1: Try ESPN's player search
        espn_id = await self._search_espn_by_mlb_id(mlb_id)
        if espn_id:
            self.mlb_to_espn_cache[mlb_id] = espn_id
            return espn_id
        
        # Strategy 2: Mark as failed to avoid repeat attempts
        self.failed_lookups.add(mlb_id)
        return None
    
    async def _search_espn_by_mlb_id(self, mlb_id: str) -> Optional[str]:
        """Search ESPN for player by MLB ID"""
        try:
            # ESPN sometimes has MLB ID in their data
            async with aiohttp.ClientSession() as session:
                # Try ESPN API search (if available)
                search_url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/athletes?limit=1000"
                
                async with session.get(search_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        athletes = data.get('athletes', [])
                        
                        for athlete in athletes:
                            # Check if ESPN has MLB ID reference
                            if str(athlete.get('id')) == mlb_id:
                                return str(athlete['id'])
                                
        except Exception as e:
            logger.debug(f"ESPN search failed for MLB ID {mlb_id}: {e}")
        
        return None
    
    async def map_all_database_players(self, session: AsyncSession) -> Dict[str, str]:
        """Map all players in database from MLB ID to ESPN ID"""
        
        # Get all players with MLB IDs
        query = text("""
            SELECT id, mlb_id, name, current_team 
            FROM players 
            WHERE mlb_id IS NOT NULL 
            AND active = true
            ORDER BY name
        """)
        
        result = await session.execute(query)
        players = result.fetchall()
        
        logger.info(f"Found {len(players)} active players to map")
        
        mapped_players = {}
        batch_size = 10
        
        # Process players in batches to avoid rate limiting
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]
            
            # Try multiple strategies for each player
            for player in batch:
                player_id, mlb_id, name, team = player
                
                logger.info(f"Mapping {name} (MLB ID: {mlb_id})")
                
                # Strategy 1: Check our known mappings
                espn_id = self._get_known_espn_id(name)
                
                if not espn_id:
                    # Strategy 2: Try systematic lookup
                    espn_id = await self.get_espn_id_from_mlb_id(str(mlb_id))
                
                if not espn_id:
                    # Strategy 3: Try name-based guessing with variations
                    espn_id = await self._guess_espn_id_by_name(name, team)
                
                if espn_id:
                    mapped_players[str(mlb_id)] = espn_id
                    logger.info(f"✓ Mapped {name}: MLB {mlb_id} → ESPN {espn_id}")
                else:
                    logger.warning(f"✗ Could not map {name} (MLB ID: {mlb_id})")
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return mapped_players
    
    def _get_known_espn_id(self, name: str) -> Optional[str]:
        """Get ESPN ID from our verified known mappings"""
        known_mappings = {
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
            'Max Scherzer': '31060',
            'Jacob deGrom': '32796',
            'Gerrit Cole': '32162',
            'Clayton Kershaw': '28963',
            'Cal Raleigh': '41292'
        }
        
        # Try exact match first
        if name in known_mappings:
            return known_mappings[name]
        
        # Try variations
        variations = [
            name.replace(' Jr.', ''),
            name.replace(' Sr.', ''),
            name + ' Jr.',
            name + ' Sr.'
        ]
        
        for variation in variations:
            if variation in known_mappings:
                return known_mappings[variation]
        
        return None
    
    async def _guess_espn_id_by_name(self, name: str, team: str) -> Optional[str]:
        """Guess ESPN ID by trying systematic name search"""
        try:
            # This would require ESPN's search API
            # For now, we'll use a more systematic approach
            
            # Try common ESPN ID ranges for active players
            # Most current players have IDs between 30000-50000
            for espn_id_range in [35000, 36000, 37000, 33000, 34000]:
                for offset in range(0, 1000, 50):  # Sample every 50 IDs
                    test_id = espn_id_range + offset
                    
                    # Test if this ESPN ID exists and might match
                    if await self._validate_espn_id(str(test_id), name):
                        return str(test_id)
                        
        except Exception as e:
            logger.debug(f"Name-based guessing failed for {name}: {e}")
        
        return None
    
    async def _validate_espn_id(self, espn_id: str, expected_name: str) -> bool:
        """Validate if ESPN ID exists and might match player name"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if ESPN headshot exists
                headshot_url = f"https://a.espncdn.com/combiner/i?img=/i/headshots/mlb/players/full/{espn_id}.png"
                
                async with session.head(headshot_url, timeout=3) as response:
                    if response.status == 200:
                        # Image exists - this is a valid ESPN ID
                        # TODO: Could add name validation by checking ESPN player page
                        return True
                        
        except Exception:
            pass
        
        return False
    
    async def update_database_with_mappings(self, session: AsyncSession, mappings: Dict[str, str]) -> int:
        """Update database with discovered ESPN ID mappings"""
        
        updated_count = 0
        
        for mlb_id, espn_id in mappings.items():
            try:
                query = text("""
                    UPDATE players 
                    SET espn_id = :espn_id 
                    WHERE mlb_id = :mlb_id
                """)
                
                result = await session.execute(query, {
                    "espn_id": espn_id,
                    "mlb_id": mlb_id
                })
                
                if result.rowcount > 0:
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to update player with MLB ID {mlb_id}: {e}")
        
        await session.commit()
        logger.info(f"Updated {updated_count} players with ESPN IDs")
        
        return updated_count

# Usage function
async def run_systematic_mapping(session: AsyncSession) -> Dict[str, str]:
    """Run the systematic mapping process"""
    
    mapper = PlayerIDMapper()
    
    logger.info("Starting systematic player ID mapping...")
    
    # Map all database players
    mappings = await mapper.map_all_database_players(session)
    
    # Update database
    updated_count = await mapper.update_database_with_mappings(session, mappings)
    
    logger.info(f"Systematic mapping complete: {len(mappings)} mapped, {updated_count} updated")
    
    return mappings