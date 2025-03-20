
import os
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from openai import OpenAI

client = OpenAI(api_key="")


# Set OpenAI API key (or use another vision API)
  # Replace with your actual API key

# Function to scrape images from a given Vogue webpage
def scrape_images_from_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to access {url}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all("img")

        image_urls = []
        for img in img_tags:
            img_url = img.get("src")
            if img_url and img_url.startswith("http"):
                image_urls.append(img_url)

        return image_urls

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# Function to analyze image using OpenAI Vision
def analyze_image(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        # Call OpenAI Vision API (or another vision model)
        response = client.chat.completions.create(model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": "Analyze the clothing in the image and provide details about color, fabric, and clothing type."
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": image_url},
                    {"type": "text", "text": "Describe the clothing in this image, focusing on color, fabric, and type of clothing."}
                ]
            }
        ])

        description = response.choices[0].message.content
        return description

    except Exception as e:
        print(f"Error analyzing image {image_url}: {e}")
        return None

# Function to extract key attributes from AI-generated descriptions
def extract_attributes(description):
    color, fabric, clothing_type = "Unknown", "Unknown", "Unknown"

    if "color" in description.lower():
        color = description.split("color:")[1].split(".")[0].strip()
    if "fabric" in description.lower():
        fabric = description.split("fabric:")[1].split(".")[0].strip()
    if "clothing type" in description.lower():
        clothing_type = description.split("clothing type:")[1].split(".")[0].strip()

    return color, fabric, clothing_type

# Read CSV file containing URLs
input_csv = "tidy_v1.csv"  # Change to your actual file
output_csv = "vogue_image_descriptions1.csv"

df = pd.read_csv(input_csv)
image_data = []

for index, row in df.iterrows():
    url = row['url']  # Adjust column name if different
    print(f"Processing: {url}")

    image_urls = scrape_images_from_url(url)
    for image_url in image_urls:
        description = analyze_image(image_url)
        if description:
            color, fabric, clothing_type = extract_attributes(description)
            image_data.append([url, image_url, description, color, fabric, clothing_type])

# Save results to CSV
output_df = pd.DataFrame(image_data, columns=["Website", "Image URL", "Description", "Color", "Fabric", "Clothing Type"])
output_df.to_csv(output_csv, index=False)

print(f"Scraping and analysis complete. Data saved to {output_csv}")
