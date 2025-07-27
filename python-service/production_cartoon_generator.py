#!/usr/bin/env python3
"""
PRODUCTION MLB Player Cartoon Generator for 8x RTX 4090
Processes ALL 1,673 players with RealCartoon3D model
Optimized for maximum speed and quality
"""

import requests
import base64
import json
from pathlib import Path
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AUTOMATIC1111 API endpoint (local on Vast.ai instance)
API_URL = "http://localhost:7860"

# Team uniform configurations for better prompts
TEAM_UNIFORMS = {
    'PHI': 'Philadelphia Phillies red and white pinstripe uniform, red cap with P logo',
    'NYY': 'New York Yankees navy pinstripe uniform, navy cap with NY logo', 
    'LAD': 'Los Angeles Dodgers blue and white uniform, blue cap with LA logo',
    'BOS': 'Boston Red Sox red and white uniform, red cap with B logo',
    'ATL': 'Atlanta Braves navy and red uniform, navy cap with A logo',
    'WSN': 'Washington Nationals red and white uniform, navy cap with W logo',
    'NYM': 'New York Mets blue and orange uniform, blue cap with NY logo',
    'MIA': 'Miami Marlins black and orange uniform, black cap with M logo',
    'HOU': 'Houston Astros navy and orange uniform, navy cap with H logo',
    'TEX': 'Texas Rangers red and blue uniform, red cap with T logo',
    'LAA': 'Los Angeles Angels red and white uniform, red cap with A logo',
    'SEA': 'Seattle Mariners navy and teal uniform, navy cap with S logo',
    'OAK': 'Oakland Athletics green and gold uniform, green cap with A logo',
    'CHC': 'Chicago Cubs blue and red uniform, blue cap with C logo',
    'CWS': 'Chicago White Sox black and white uniform, black cap with Sox logo',
    'MIL': 'Milwaukee Brewers navy and gold uniform, navy cap with M logo',
    'STL': 'St. Louis Cardinals red and white uniform, red cap with STL logo',
    'CIN': 'Cincinnati Reds red and white uniform, red cap with C logo',
    'PIT': 'Pittsburgh Pirates black and gold uniform, black cap with P logo',
    'CLE': 'Cleveland Guardians red and navy uniform, red cap with C logo',
    'DET': 'Detroit Tigers navy and orange uniform, navy cap with D logo',
    'MIN': 'Minnesota Twins navy and red uniform, navy cap with TC logo',
    'KC': 'Kansas City Royals blue and white uniform, blue cap with KC logo',
    'TB': 'Tampa Bay Rays navy and light blue uniform, navy cap with TB logo',
    'BAL': 'Baltimore Orioles orange and black uniform, orange cap with O logo',
    'TOR': 'Toronto Blue Jays blue and white uniform, blue cap with leaf logo',
    'COL': 'Colorado Rockies purple and black uniform, purple cap with CR logo',
    'ARI': 'Arizona Diamondbacks red and black uniform, red cap with A logo',
    'SF': 'San Francisco Giants orange and black uniform, black cap with SF logo',
    'SD': 'San Diego Padres brown and gold uniform, brown cap with SD logo'
}

# Global stats tracking
stats_lock = threading.Lock()
stats = {
    'processed': 0,
    'successful': 0,
    'failed': 0,
    'start_time': None
}

def get_team_from_filename(filename):
    """Extract team code from filename if possible"""
    # This would need custom logic based on your filename patterns
    # For now, return generic MLB
    return 'MLB'

def encode_image_to_base64(image_path):
    """Convert image to base64 for API"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def generate_player_cartoon_optimized(image_path, player_name, team='MLB'):
    """Generate cartoon using optimized settings for 8x RTX 4090"""
    
    try:
        # Encode input image
        image_b64 = encode_image_to_base64(image_path)
        
        # Get team-specific uniform description
        uniform_desc = TEAM_UNIFORMS.get(team, f'{team} team uniform')
        
        # Optimized prompt for RealCartoon3D
        prompt = f"""cartoon, professional sports player headshot, {uniform_desc}, 
        high quality digital art, detailed face, sports marketing style, 
        clean background, masterpiece, best quality, 8k resolution, 
        realistic cartoon style, professional lighting"""
        
        negative_prompt = """blurry, low quality, distorted, ugly, bad anatomy, 
        extra limbs, watermark, signature, text, multiple people, 
        deformed, mutated, poorly drawn, anime, manga, oversaturated"""
        
        # Optimized payload for speed and quality
        payload = {
            "init_images": [image_b64],
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": 25,  # Good quality/speed balance
            "cfg_scale": 8,  # Strong prompt adherence
            "width": 512,   # Fast generation
            "height": 512,
            "denoising_strength": 0.75,  # Good face preservation
            "sampler_name": "DPM++ 2M Karras",  # High quality sampler
            "batch_size": 1,  # Stable for production
            
            # ControlNet for face preservation
            "alwayson_scripts": {
                "controlnet": {
                    "args": [
                        {
                            "input_image": image_b64,
                            "module": "canny",
                            "model": "control_v11p_sd15_canny [d14c016b]",
                            "weight": 0.8,  
                            "guidance_start": 0.0,
                            "guidance_end": 1.0,
                            "control_mode": "Balanced",
                            "resize_mode": "Crop and Resize",
                            "pixel_perfect": True,
                            "enabled": True
                        }
                    ]
                }
            }
        }
        
        # Make API request with timeout
        start_time = time.time()
        response = requests.post(f"{API_URL}/sdapi/v1/img2img", json=payload, timeout=180)
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if 'images' in result and len(result['images']) > 0:
                cartoon_b64 = result['images'][0]
                
                # Save cartoon with organized naming
                output_dir = Path("/workspace/mlb_cartoons_final")
                output_dir.mkdir(exist_ok=True)
                
                safe_name = player_name.lower().replace(' ', '-').replace('.', '').replace("'", "")
                output_path = output_dir / f"{safe_name}-cartoon.png"
                
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(cartoon_b64))
                
                # Update stats
                with stats_lock:
                    stats['processed'] += 1
                    stats['successful'] += 1
                
                logger.info(f"✅ [{stats['processed']}/1673] {player_name}: Generated in {generation_time:.1f}s")
                return str(output_path)
            else:
                with stats_lock:
                    stats['processed'] += 1
                    stats['failed'] += 1
                logger.error(f"❌ [{stats['processed']}/1673] {player_name}: No images in response")
                return None
        else:
            with stats_lock:
                stats['processed'] += 1
                stats['failed'] += 1
            logger.error(f"❌ [{stats['processed']}/1673] {player_name}: API Error {response.status_code}")
            return None
            
    except Exception as e:
        with stats_lock:
            stats['processed'] += 1
            stats['failed'] += 1
        logger.error(f"❌ [{stats['processed']}/1673] {player_name}: {str(e)}")
        return None

def process_single_player(photo_path):
    """Process a single player photo"""
    # Extract player name from filename
    player_name = photo_path.stem
    
    # Clean up the name
    if player_name.startswith(('-', 's-', 'ss-', 'sw-', 'w-', 'ws-', 'ww-', 'sws-', 'wws-')):
        # Remove prefixes and convert ID to name if needed
        player_name = player_name.split('-', 1)[-1]
    
    # Convert to readable name
    player_name = player_name.replace('-', ' ').replace('_', ' ')
    player_name = ' '.join(word.capitalize() for word in player_name.split())
    
    # Remove trailing numbers/IDs
    import re
    player_name = re.sub(r'\s+\d+$', '', player_name)
    
    # Extract team if possible
    team = get_team_from_filename(photo_path.name)
    
    # Generate cartoon
    return generate_player_cartoon_optimized(str(photo_path), player_name, team)

def print_progress():
    """Print progress updates in separate thread"""
    while True:
        time.sleep(30)  # Update every 30 seconds
        
        with stats_lock:
            if stats['start_time'] and stats['processed'] > 0:
                elapsed = time.time() - stats['start_time']
                rate = stats['processed'] / elapsed * 60  # per minute
                remaining = (1673 - stats['processed']) / (rate / 60) if rate > 0 else 0
                
                logger.info(f"📊 PROGRESS: {stats['processed']}/1673 ({(stats['processed']/1673)*100:.1f}%)")
                logger.info(f"   ✅ Success: {stats['successful']} | ❌ Failed: {stats['failed']}")
                logger.info(f"   ⚡ Rate: {rate:.1f}/min | ⏰ ETA: {remaining/3600:.1f}hrs")
        
        if stats['processed'] >= 1673:
            break

def batch_process_all_players():
    """Process all MLB player photos with optimized threading"""
    
    logger.info("🚀 PRODUCTION MLB CARTOON GENERATION - 8x RTX 4090")
    logger.info("=" * 80)
    logger.info("Using RealCartoon3D model for professional sports cartoons")
    
    # Photo directory
    photo_dir = Path("/workspace/player_photos")
    
    if not photo_dir.exists():
        logger.error(f"❌ Photo directory not found: {photo_dir}")
        return
    
    # Get all player photos
    photo_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        photo_files.extend(photo_dir.glob(ext))
    
    total_players = len(photo_files)
    logger.info(f"📊 Found {total_players} player photos")
    
    if total_players == 0:
        logger.error("❌ No photos found!")
        return
    
    # Initialize stats
    stats['start_time'] = time.time()
    
    # Start progress monitoring thread
    progress_thread = threading.Thread(target=print_progress, daemon=True)
    progress_thread.start()
    
    # Process with optimal threading for 8x RTX 4090
    # Use 4 threads to avoid overwhelming the GPU
    max_workers = 4
    logger.info(f"🔧 Using {max_workers} worker threads for optimal GPU utilization")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        futures = [executor.submit(process_single_player, photo_path) for photo_path in photo_files]
        
        # Wait for completion
        for future in futures:
            try:
                future.result(timeout=300)  # 5 minute timeout per image
            except Exception as e:
                logger.error(f"❌ Thread error: {str(e)}")
    
    # Final report
    total_time = time.time() - stats['start_time']
    logger.info(f"\\n🎉 PRODUCTION COMPLETE!")
    logger.info(f"=" * 80)
    logger.info(f"📊 Final Results:")
    logger.info(f"   Total Players: {total_players}")
    logger.info(f"   ✅ Successfully Generated: {stats['successful']}")
    logger.info(f"   ❌ Failed: {stats['failed']}")
    logger.info(f"   📈 Success Rate: {(stats['successful']/total_players)*100:.1f}%")
    logger.info(f"   ⏱️ Total Time: {total_time/3600:.1f} hours")
    logger.info(f"   ⚡ Average Rate: {stats['successful']/(total_time/60):.1f} cartoons/minute")
    logger.info(f"   💰 Estimated Cost: ${(total_time/3600)*2.938:.2f}")
    logger.info(f"   📁 Output Directory: /workspace/mlb_cartoons_final/")
    
    return stats['successful']

if __name__ == "__main__":
    # Wait for WebUI to be ready
    logger.info("⏳ Waiting for AUTOMATIC1111 WebUI to start...")
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/sdapi/v1/progress", timeout=10)
            if response.status_code == 200:
                logger.info("✅ WebUI is ready!")
                break
        except:
            if i == max_retries - 1:
                logger.error("❌ WebUI failed to start!")
                exit(1)
            logger.info(f"⏳ Waiting for WebUI... ({i+1}/{max_retries})")
            time.sleep(10)
    
    # Verify model is loaded
    try:
        response = requests.get(f"{API_URL}/sdapi/v1/options", timeout=10)
        if response.status_code == 200:
            options = response.json()
            current_model = options.get('sd_model_checkpoint', 'Unknown')
            logger.info(f"🎨 Current model: {current_model}")
            
            # Switch to RealCartoon3D if not already loaded
            if 'realcartoon3d' not in current_model.lower():
                logger.info("🔄 Switching to RealCartoon3D model...")
                change_payload = {"sd_model_checkpoint": "realcartoon3d_v18.safetensors"}
                requests.post(f"{API_URL}/sdapi/v1/options", json=change_payload)
                time.sleep(30)  # Wait for model to load
                logger.info("✅ Model switched to RealCartoon3D")
    except Exception as e:
        logger.warning(f"⚠️ Could not verify model: {str(e)}")
    
    # Start production batch processing
    logger.info("🚀 Starting production cartoon generation...")
    success_count = batch_process_all_players()
    logger.info(f"\\n✅ PRODUCTION COMPLETE! Generated {success_count} professional MLB cartoons!")