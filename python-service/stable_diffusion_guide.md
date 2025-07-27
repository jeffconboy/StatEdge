# Stable Diffusion Player Cartoon Generation Guide
*Complete setup for generating 1,682+ player cartoons using Stable Diffusion + ControlNet*

## 🎯 **Goal**: Convert MLB player headshots to professional cartoons at scale

---

## 📋 **System Requirements**

### Hardware
- **GPU**: NVIDIA RTX 3060+ (8GB+ VRAM recommended)
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space (models are large)
- **CPU**: Modern multi-core processor

### Software Stack
- **Docker** (recommended for easy setup)
- **AUTOMATIC1111 WebUI** (most popular interface)
- **ControlNet Extension** (for face preservation)
- **Python API** (for batch automation)

---

## 🚀 **Installation Guide**

### Method 1: Docker Setup (Recommended)
```bash
# Clone the easy Docker setup
git clone https://github.com/AbdBarho/stable-diffusion-webui-docker.git
cd stable-diffusion-webui-docker

# Start with GPU support
docker compose --profile download up --build
docker compose --profile auto up --build

# Access WebUI at http://localhost:7860
```

### Method 2: Direct Installation
```bash
# Clone AUTOMATIC1111 WebUI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# Install ControlNet extension
git clone https://github.com/Mikubill/sd-webui-controlnet.git extensions/sd-webui-controlnet

# Run setup
./webui.sh --api --listen
```

---

## 🎨 **Best Models for Sports Cartoons**

### Top Cartoon Models (Download from Civitai.com)

**1. RealCartoon3D** ⭐ **RECOMMENDED**
- **Best for**: Realistic cartoon style (perfect for sports)
- **Prompt**: `cartoon, sports player, professional quality`
- **Download**: [Civitai RealCartoon3D](https://civitai.com/models/94809/realcartoon3d)

**2. ReV Animated** 
- **Best for**: High-quality animated style
- **Used by**: Millions of users
- **Style**: Video game character quality

**3. Anything V5**
- **Best for**: Versatile anime/cartoon styles
- **Advantage**: Works with minimal prompting
- **Quality**: Powerhouse model

### Model Installation
```bash
# Place downloaded .safetensors files in:
stable-diffusion-webui/models/Stable-diffusion/

# Models are 2-7GB each
```

---

## 🎛️ **ControlNet Setup for Face Preservation**

### Required ControlNet Models
```bash
# Download these ControlNet models:
1. control_v11p_sd15_canny.pth          # Edge detection
2. control_v11f1p_sd15_depth.pth        # Depth mapping  
3. ip-adapter-plus-face_sd15.pth        # Face preservation
4. control_v11p_sd15_openpose.pth       # Pose detection

# Place in: stable-diffusion-webui/models/ControlNet/
```

### ControlNet Configuration
- **Preprocessor**: `canny` or `openpose_face`
- **Model**: Match preprocessor (canny → control_canny)
- **Control Weight**: 0.7-1.0
- **Control Mode**: `Balanced`

---

## ⚙️ **Optimal Settings for Player Cartoons**

### Generation Settings
```yaml
# Image Settings
Width: 512px (faster) or 768px (higher quality)
Height: 512px or 768px  
Batch Count: 1 (for automation)
Batch Size: 4-8 (depending on VRAM)

# Quality Settings  
Sampling Method: DPM++ 2M Karras
Sampling Steps: 20-30
CFG Scale: 7-11
Denoising Strength: 0.7-0.9 (for img2img)

# ControlNet Settings
Control Weight: 0.8
Starting Control Step: 0.0
Ending Control Step: 1.0
```

### Perfect Prompt Template
```
cartoon, sports player, {TEAM_NAME} uniform, professional headshot, 
high quality, detailed face, {PLAYER_DESCRIPTION}, 
sports marketing style, clean background, 
masterpiece, best quality

Negative: blurry, low quality, distorted, ugly, bad anatomy, 
extra limbs, watermark, signature
```

---

## 🤖 **Python Automation Script**

### Batch Processing Script
```python
#!/usr/bin/env python3
"""
Stable Diffusion Batch Player Cartoon Generator
Process 1,682 players automatically using AUTOMATIC1111 API
"""

import requests
import base64
import json
from pathlib import Path
import time

# AUTOMATIC1111 API endpoint
API_URL = "http://localhost:7860"

def generate_player_cartoon(image_path: str, player_name: str, team: str):
    """Generate cartoon using Stable Diffusion API"""
    
    # Encode input image
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    # Create prompt
    prompt = f"""cartoon, sports player, {team} uniform, professional headshot, 
    high quality, detailed face, sports marketing style, clean background, 
    masterpiece, best quality"""
    
    # API payload
    payload = {
        "init_images": [image_b64],
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy",
        "steps": 25,
        "cfg_scale": 8,
        "width": 512,
        "height": 512,
        "denoising_strength": 0.8,
        "sampler_name": "DPM++ 2M Karras",
        
        # ControlNet configuration
        "controlnet_args": [
            {
                "input_image": image_b64,
                "module": "canny",
                "model": "control_v11p_sd15_canny",
                "weight": 0.8,
                "guidance_start": 0.0,
                "guidance_end": 1.0
            }
        ]
    }
    
    # Generate image
    response = requests.post(f"{API_URL}/sdapi/v1/img2img", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        cartoon_b64 = result['images'][0]
        
        # Save cartoon
        output_dir = Path("player_cartoons")
        output_dir.mkdir(exist_ok=True)
        
        safe_name = player_name.lower().replace(' ', '-')
        output_path = output_dir / f"{safe_name}-cartoon.png"
        
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(cartoon_b64))
        
        return str(output_path)
    
    return None

def batch_process_all_players():
    """Process all 1,682 players"""
    
    # Get player photos
    photo_dir = Path("static/mlb-photos")
    
    success_count = 0
    
    for photo_path in photo_dir.glob("*.jpg"):
        player_name = photo_path.stem.replace('-', ' ').title()
        
        print(f"Processing {player_name}...")
        
        result = generate_player_cartoon(str(photo_path), player_name, "MLB")
        
        if result:
            success_count += 1
            print(f"✅ Generated: {result}")
        else:
            print(f"❌ Failed: {player_name}")
        
        # Rate limiting
        time.sleep(2)
        
        # Progress update
        if success_count % 50 == 0:
            print(f"📊 Progress: {success_count} cartoons generated")
    
    print(f"🎉 Complete! Generated {success_count} cartoons")

if __name__ == "__main__":
    batch_process_all_players()
```

---

## 📊 **Performance & Costs**

### Processing Time
- **Single Image**: 10-30 seconds (depending on GPU)
- **1,682 Players**: ~14-28 hours total
- **Optimization**: Run overnight or use multiple GPUs

### Resource Usage
- **VRAM**: 6-12GB per generation
- **Storage**: ~2MB per cartoon (1,682 × 2MB = 3.4GB)
- **Electricity**: GPU-dependent (~$5-20 for full batch)

### Cost Comparison
- **Stable Diffusion**: ~$0.003 per image (electricity only)
- **OpenAI DALL-E**: ~$0.19 per image ($319 total)
- **Midjourney**: ~$0.05 per image ($84 total)

**Stable Diffusion Total Cost**: ~$5-20 (98% cheaper!)

---

## 🎯 **Quality Optimization**

### Face Preservation Tips
1. **Use IP-Adapter Face**: Maintains facial likeness
2. **Lower Denoising**: 0.7-0.8 preserves more original features  
3. **Higher Control Weight**: 0.8-1.0 for stronger face guidance
4. **Multiple ControlNets**: Combine canny + openpose_face

### Team Uniform Accuracy
```python
team_prompts = {
    'PHI': 'Philadelphia Phillies red and white uniform, P logo cap',
    'NYY': 'New York Yankees pinstripe uniform, NY logo cap',
    'LAD': 'Los Angeles Dodgers blue and white uniform, LA logo cap',
    # Add all 30 teams...
}
```

### Quality Control
- **Preview Mode**: Test 10-20 players first
- **A/B Testing**: Compare different models/settings
- **Manual Review**: Check results every 100 generations

---

## 🔧 **Troubleshooting**

### Common Issues
- **CUDA Out of Memory**: Reduce batch size or image resolution
- **Slow Generation**: Check GPU utilization, upgrade hardware
- **Poor Quality**: Adjust CFG scale, try different models
- **API Errors**: Restart WebUI, check endpoint availability

### Optimization Tips
- **Use fp16**: Reduces VRAM usage by 50%
- **xFormers**: Speeds up generation significantly
- **Model Caching**: Keep models loaded in VRAM
- **Batch Processing**: Generate multiple images per API call

---

## 🎉 **Expected Results**

With this setup, you'll generate:
- ✅ **1,682 high-quality sports cartoons**
- ✅ **Consistent style** across all players
- ✅ **Preserved facial features** and team uniforms
- ✅ **Professional quality** suitable for website use
- ✅ **Full control** over the generation process
- ✅ **No API restrictions** or account bans

**Timeline**: 1-2 days setup + 1-2 days generation = Complete cartoon system in under a week!

---

*This guide provides everything needed to generate professional sports cartoons at scale using Stable Diffusion. The system is more powerful, cheaper, and unrestricted compared to cloud alternatives.*