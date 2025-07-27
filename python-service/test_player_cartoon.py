#!/usr/bin/env python3
"""
Standalone Player Cartoon Generator
Uses GPT-4o Vision + Native Image Generation to create cartoon versions of player photos

TEST ONLY - Not integrated with main system
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
    api_key=os.getenv('OPENAI_API_KEY', 'your-api-key-here')
)

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_player_cartoon(image_path: str, player_name: str) -> dict:
    """
    Create a cartoon version of a player photo using GPT-4o
    """
    print(f"🎨 Creating cartoon for {player_name}...")
    print(f"📷 Source image: {image_path}")
    
    try:
        # Encode the image
        base64_image = encode_image_to_base64(image_path)
        
        # Create the prompt for cartoon generation
        cartoon_prompt = f"""
        I'm uploading a professional MLB player headshot photo. Please analyze this image and create a hyper-realistic cartoon version of this player that:

        1. **Maintains facial features and likeness** - Keep the player's distinctive facial structure, eye shape, nose, and overall appearance
        2. **Preserves team uniform details** - Keep the team colors, logo, and uniform style accurate
        3. **Creates cartoon style** - Transform into a polished, hyper-realistic cartoon/animated style similar to Pixar or high-end sports video game graphics
        4. **Professional quality** - Make it look like official sports marketing material
        5. **Same pose and framing** - Keep similar headshot composition and angle

        Style reference: Think premium sports video game character design - realistic proportions but with clean, polished cartoon rendering. Not overly stylized or exaggerated.

        Player name for reference: {player_name}
        """
        
        # Call GPT-4o with vision and image generation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": cartoon_prompt
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
            max_tokens=500
        )
        
        # Get the response
        analysis = response.choices[0].message.content
        print(f"🧠 GPT-4o Analysis: {analysis[:200]}...")
        
        # Now generate the cartoon image using the new native image generation
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=f"""Create a hyper-realistic cartoon version of this MLB player: {analysis}
            
            Style: Premium sports video game character design, realistic proportions with clean polished cartoon rendering.
            Quality: Professional sports marketing material quality.
            Composition: Headshot format similar to official MLB photos.
            """,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        cartoon_url = image_response.data[0].url
        revised_prompt = getattr(image_response.data[0], 'revised_prompt', 'No revised prompt')
        
        print(f"✅ Cartoon generated successfully!")
        print(f"🖼️ Image URL: {cartoon_url}")
        
        return {
            'success': True,
            'cartoon_url': cartoon_url,
            'analysis': analysis,
            'revised_prompt': revised_prompt,
            'player_name': player_name
        }
        
    except Exception as e:
        print(f"❌ Error creating cartoon for {player_name}: {str(e)}")
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
            output_dir = Path("cartoon_output")
            output_dir.mkdir(exist_ok=True)
            
            # Create filename
            safe_name = player_name.lower().replace(' ', '-').replace('.', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_cartoon_{timestamp}.png"
            
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

def test_player_cartoon():
    """Test the cartoon generation with a real player"""
    print("🧪 PLAYER CARTOON GENERATOR TEST")
    print("=" * 50)
    
    # Test with Jose Alvarado's photo
    test_image = "static/mlb-photos/jose-alvarado-621237.jpg"
    test_player = "Jose Alvarado"
    
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        print("Available images:")
        for img in Path("static/mlb-photos").glob("*.jpg"):
            if "jose" in img.name.lower():
                print(f"  - {img}")
        return
    
    print(f"🎯 Testing with: {test_player}")
    print(f"📸 Image: {test_image}")
    print()
    
    # Generate cartoon
    result = create_player_cartoon(test_image, test_player)
    
    if result['success']:
        print(f"\\n🎉 SUCCESS! Generated cartoon for {test_player}")
        print(f"🔗 Cartoon URL: {result['cartoon_url']}")
        print(f"📝 Analysis: {result['analysis'][:200]}...")
        
        # Download the cartoon
        local_path = download_cartoon(result['cartoon_url'], test_player)
        if local_path:
            print(f"✅ Test complete! Check {local_path}")
            
            # Show usage estimate
            print(f"\\n💰 Estimated cost: ~$0.19 (HD quality)")
            print(f"⏱️ Processing time: ~10-30 seconds")
        
    else:
        print(f"\\n❌ FAILED! Error: {result['error']}")

if __name__ == "__main__":
    # Check API key
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your-api-key-here':
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-actual-api-key'")
        exit(1)
    
    print("🚀 Starting player cartoon test...")
    test_player_cartoon()
    print("\\n✅ Test complete!")