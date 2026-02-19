#!/usr/bin/env python3
"""
Create a simple LarlBot logo for the dashboard
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_larlbot_logo():
    # Create a 300x300 image with transparent background
    img = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Purple/gold gradient circle background
    center = (150, 150)
    radius = 140
    
    # Draw a purple circle
    draw.ellipse([10, 10, 290, 290], fill=(138, 85, 247), outline=(245, 158, 11), width=8)
    
    # Try to use a system font or default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 80)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw "🎰" emoji as text (may not work on all systems)
    draw.text((150, 100), "🎰", font=font, fill=(255, 255, 255), anchor="mm")
    
    # Draw "777" below
    draw.text((150, 180), "777", font=small_font, fill=(245, 158, 11), anchor="mm")
    
    # Draw "LarlBot" text
    draw.text((150, 220), "LarlBot", font=small_font, fill=(255, 255, 255), anchor="mm")
    
    # Save the image
    img.save('/Users/macmini/.openclaw/workspace/larlbot_logo.png', 'PNG')
    print("✅ LarlBot logo created successfully!")

if __name__ == "__main__":
    create_larlbot_logo()