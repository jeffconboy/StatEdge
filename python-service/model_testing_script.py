#!/usr/bin/env python3
"""
Model Testing Script for Vast.ai
Test multiple Stable Diffusion models on sample players
"""

import requests
import base64
import json
from pathlib import Path
import time

API_URL = "http://localhost:7860"

# Sample players for testing (diverse representation)
TEST_PLAYERS = [
    "jose-alvarado-621237.jpg",           # Afro-Latino, beard, Phillies
    "aaron-judge-592450.jpg",             # Tall, Yankees pinstripes  
    "shohei-ohtani-660271.jpg",          # Asian, Angels
    "mookie-betts-605141.jpg",           # African-American, Dodgers
    "vladimir-guerrero-jr-665489.jpg"    # Latin, Blue Jays
]

# Models to test
MODELS_TO_TEST = [
    {
        "name": "RealCartoon3D",
        "filename": "realcartoon3d_v18.safetensors",
        "prompt_style": "cartoon, professional sports player, detailed"
    },
    {
        "name": "ReV_Animated", 
        "filename": "revAnimated_v2Rebirth.safetensors",
        "prompt_style": "anime, high quality character art, detailed"
    },
    {
        "name": "Anything_V5",
        "filename": "anythingV5_PrtRE.safetensors", 
        "prompt_style": "anime style, cartoon character, high quality"
    }
]

# Test parameters
TEST_SETTINGS = [
    {"cfg_scale": 8, "denoising": 0.75, "steps": 25},
    {"cfg_scale": 10, "denoising": 0.8, "steps": 30},
    {"cfg_scale": 6, "denoising": 0.7, "steps": 20}
]

def encode_image_to_base64(image_path):
    """Convert image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def change_model(model_filename):
    """Change the active model"""
    payload = {"sd_model_checkpoint": model_filename}
    response = requests.post(f"{API_URL}/sdapi/v1/options", json=payload)
    
    if response.status_code == 200:
        print(f"✅ Changed model to: {model_filename}")
        time.sleep(5)  # Wait for model to load
        return True
    else:
        print(f"❌ Failed to change model: {response.status_code}")
        return False

def generate_test_cartoon(image_path, model_info, settings, player_name):
    """Generate a test cartoon with specific model and settings"""
    
    try:
        image_b64 = encode_image_to_base64(image_path)
        
        prompt = f"""{model_info['prompt_style']}, MLB baseball player, 
        professional headshot, team uniform, high quality, masterpiece"""
        
        negative_prompt = """blurry, low quality, distorted, ugly, bad anatomy, 
        multiple people, watermark, signature"""
        
        payload = {
            "init_images": [image_b64],
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 512,
            "height": 512,
            "steps": settings['steps'],
            "cfg_scale": settings['cfg_scale'], 
            "denoising_strength": settings['denoising'],
            "sampler_name": "DPM++ 2M Karras",
            
            # ControlNet for face preservation
            "alwayson_scripts": {
                "controlnet": {
                    "args": [
                        {
                            "input_image": image_b64,
                            "module": "canny",
                            "model": "control_v11p_sd15_canny [d14c016b]",
                            "weight": 0.8,
                            "enabled": True
                        }
                    ]
                }
            }
        }
        
        start_time = time.time()
        response = requests.post(f"{API_URL}/sdapi/v1/img2img", json=payload, timeout=120)
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            cartoon_b64 = result['images'][0]
            
            # Create organized output structure
            output_dir = Path("/workspace/model_tests")
            model_dir = output_dir / model_info['name']
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Save with descriptive filename
            settings_str = f"cfg{settings['cfg_scale']}_den{settings['denoising']}_s{settings['steps']}"
            filename = f"{player_name}_{settings_str}.png"
            output_path = model_dir / filename
            
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(cartoon_b64))
            
            print(f"  ✅ Generated: {output_path} ({generation_time:.1f}s)")
            return {
                'success': True,
                'path': str(output_path),
                'time': generation_time,
                'model': model_info['name'],
                'settings': settings
            }
        else:
            print(f"  ❌ API Error: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def run_comprehensive_test():
    """Run comprehensive model testing"""
    
    print("🧪 STABLE DIFFUSION MODEL TESTING")
    print("=" * 60)
    print(f"Testing {len(MODELS_TO_TEST)} models on {len(TEST_PLAYERS)} players")
    print(f"With {len(TEST_SETTINGS)} parameter combinations each")
    print()
    
    # Results tracking
    results = []
    test_photos_dir = Path("/workspace/player_photos")
    
    # Check if test photos exist
    missing_photos = []
    for player_file in TEST_PLAYERS:
        if not (test_photos_dir / player_file).exists():
            missing_photos.append(player_file)
    
    if missing_photos:
        print(f"❌ Missing test photos: {missing_photos}")
        print("Please upload these photos to /workspace/player_photos/")
        return
    
    total_tests = len(MODELS_TO_TEST) * len(TEST_PLAYERS) * len(TEST_SETTINGS)
    current_test = 0
    
    # Test each model
    for model_info in MODELS_TO_TEST:
        print(f"\\n🎨 Testing Model: {model_info['name']}")
        print("-" * 40)
        
        # Change to this model
        if not change_model(model_info['filename']):
            print(f"⚠️ Skipping {model_info['name']} - model file not found")
            continue
        
        # Test each player
        for player_file in TEST_PLAYERS:
            player_name = player_file.replace('.jpg', '').replace('-', '_')
            image_path = test_photos_dir / player_file
            
            print(f"\\n👤 Testing Player: {player_name}")
            
            # Test each setting combination
            for i, settings in enumerate(TEST_SETTINGS, 1):
                current_test += 1
                print(f"  🔧 Settings {i}: CFG={settings['cfg_scale']}, Den={settings['denoising']}, Steps={settings['steps']}")
                
                result = generate_test_cartoon(image_path, model_info, settings, player_name)
                result['player'] = player_name
                result['test_number'] = current_test
                results.append(result)
                
                # Progress update
                progress = (current_test / total_tests) * 100
                print(f"  📊 Progress: {current_test}/{total_tests} ({progress:.1f}%)")
                
                time.sleep(2)  # Prevent API overload
    
    # Generate summary report
    print(f"\\n📋 TESTING COMPLETE!")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful_tests)}/{total_tests}")
    print(f"❌ Failed: {len(failed_tests)}/{total_tests}")
    
    if successful_tests:
        avg_time = sum(r['time'] for r in successful_tests) / len(successful_tests)
        print(f"⏱️ Average Generation Time: {avg_time:.1f} seconds")
        
        # Performance by model
        print(f"\\n🏆 Model Performance:")
        for model_info in MODELS_TO_TEST:
            model_results = [r for r in successful_tests if r['model'] == model_info['name']]
            if model_results:
                model_avg_time = sum(r['time'] for r in model_results) / len(model_results)
                success_rate = len(model_results) / (len(TEST_PLAYERS) * len(TEST_SETTINGS)) * 100
                print(f"   {model_info['name']}: {len(model_results)} tests, {model_avg_time:.1f}s avg, {success_rate:.1f}% success")
    
    print(f"\\n📁 Check results in: /workspace/model_tests/")
    print("   Compare images to choose the best model for full batch!")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting model testing...")
    
    # Wait for WebUI to be ready
    print("⏳ Waiting for AUTOMATIC1111 WebUI...")
    max_retries = 20
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/sdapi/v1/progress", timeout=5)
            if response.status_code == 200:
                print("✅ WebUI is ready!")
                break
        except:
            if i == max_retries - 1:
                print("❌ WebUI not responding!")
                exit(1)
            time.sleep(10)
    
    # Run tests
    results = run_comprehensive_test()
    print("\\n✅ Model testing complete!")