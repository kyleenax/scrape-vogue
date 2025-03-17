import openai
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# ✅ Replace with your OpenAI API key
openai.api_key = "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"

def analyze_fashion_image(image_url):
    """
    Sends an image to GPT-4 Vision and gets a fashion description.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "Describe the outfit in the image with details about top, bottom, accessories, and overall style."},
            {"role": "user", "content": image_url}
        ]
    )
    return response["choices"][0]["message"]["content"]

# ✅ Example Image URL (Replace with actual Vogue runway images)
image_url = "https://www.vogue.com/fashion-shows/resort-2026/row/slideshow/collection#1"

# ✅ Analyze the image
description = analyze_fashion_image(image_url)
print("📝 Fashion Analysis:\n", description)

