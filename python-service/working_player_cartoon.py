#!/usr/bin/env python3
"""
WORKING Player Cartoon Generator
Uses GPT-4o Vision to analyze photo + DALL-E 3 to generate cartoon
This is the correct API approach for 2025
"""

import openai
import base64
import requests
from pathlib import Path
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_working_cartoon(image_path: str, player_name: str) -> dict:
    """
    WORKING APPROACH: GPT-4o Vision analysis + DALL-E 3 generation
    """
    print(f"🎨 Creating cartoon for {player_name} (WORKING VERSION)...")
    print(f"📷 Source image: {image_path}")
    
    try:
        base64_image = encode_image_to_base64(image_path)
        
        # Step 1: Analyze the photo with GPT-4o Vision
        print("👁️ Step 1: Analyzing photo with GPT-4o Vision...")
        
        vision_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"""Analyze this MLB player photo of {player_name} and provide a detailed description for creating a cartoon. Include:

PHYSICAL APPEARANCE:
- Skin tone (be specific: light, medium, dark, etc.)
- Facial structure and features
- Hair color, style, length
- Facial hair (beard, mustache, goatee, clean-shaven)
- Eye color if visible
- Any distinctive features

UNIFORM DETAILS:
- Team name and colors
- Jersey color and style
- Cap color and logo
- Any visible text or numbers

POSE & COMPOSITION:
- Camera angle and framing
- Facial expression
- Head position

Be very specific about his actual appearance - this will be used to create an accurate cartoon."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=600
        )
        
        detailed_description = vision_response.choices[0].message.content
        print(f"📝 Vision Analysis Complete!")
        print(f"🔍 Description: {detailed_description[:300]}...")
        
        # Step 2: Create cartoon with DALL-E 3 using the detailed description
        print("🎨 Step 2: Creating cartoon with DALL-E 3...")
        
        cartoon_prompt = f"""Create a hyper-realistic cartoon/animated version of this MLB player based on this detailed analysis:

{detailed_description}

Style Requirements:
- High-quality sports video game character style (like NBA 2K or FIFA)
- Professional sports marketing quality
- Maintain exact physical appearance described above
- Keep same uniform colors and team details
- Same headshot composition and angle
- Realistic proportions (not exaggerated or caricature)
- Clean, polished 3D animated look

IMPORTANT: Match the exact skin tone, facial features, and uniform details from the description."""

        print(f"🎯 DALL-E 3 Prompt: {cartoon_prompt[:200]}...")
        
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=cartoon_prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        cartoon_url = image_response.data[0].url
        revised_prompt = getattr(image_response.data[0], 'revised_prompt', 'No revised prompt available')
        
        print(f"✅ Cartoon generated successfully!")
        print(f"🖼️ Image URL: {cartoon_url}")
        
        return {
            'success': True,
            'cartoon_url': cartoon_url,
            'vision_analysis': detailed_description,
            'dalle_prompt': cartoon_prompt,
            'revised_prompt': revised_prompt,
            'player_name': player_name
        }
        
    except Exception as e:
        print(f"❌ Error in working cartoon generation: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'player_name': player_name
        }

def download_cartoon(cartoon_url: str, player_name: str) -> str:
    """Download the generated cartoon and save locally"""
    try:
        response = requests.get(cartoon_url)
        if response.status_code == 200:
            # Create output directory
            output_dir = Path("cartoon_output_working")
            output_dir.mkdir(exist_ok=True)
            
            # Create filename
            safe_name = player_name.lower().replace(' ', '-').replace('.', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_working_{timestamp}.png"
            
            output_path = output_dir / filename
            
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"💾 Cartoon saved: {output_path}")
            return str(output_path)
        else:
            print(f"❌ Failed to download cartoon: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return None

def test_working_cartoon():
    """Test the WORKING cartoon generation approach"""
    print("⚡ WORKING PLAYER CARTOON GENERATOR")
    print("=" * 60)
    print("GPT-4o Vision Analysis → DALL-E 3 Generation")
    
    # Test with Jose Alvarado's photo
    test_image = "static/mlb-photos/jose-alvarado-621237.jpg"
    test_player = "Jose Alvarado"
    
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"🎯 Testing with: {test_player}")
    print(f"📸 Image: {test_image}")
    print()
    
    # Generate cartoon
    result = create_working_cartoon(test_image, test_player)
    
    if result['success']:
        print(f"\\n🎉 SUCCESS! Generated cartoon for {test_player}")
        print(f"🔗 Cartoon URL: {result['cartoon_url']}")
        
        # Show the vision analysis
        print(f"\\n👁️ Vision Analysis:")
        print(f"{result['vision_analysis']}")
        
        # Download the cartoon
        local_path = download_cartoon(result['cartoon_url'], test_player)
        if local_path:
            print(f"\\n✅ Working test complete! Check {local_path}")
            print(f"💰 Cost: ~$0.19 for DALL-E 3 HD + ~$0.01 for GPT-4o Vision")
            print(f"⏱️ This approach should create an accurate cartoon!")
        
    else:
        print(f"\\n❌ FAILED! Error: {result['error']}")

if __name__ == "__main__":
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    print("🚀 Starting WORKING player cartoon test...")
    test_working_cartoon()
    print("\\n✅ Working test complete!")