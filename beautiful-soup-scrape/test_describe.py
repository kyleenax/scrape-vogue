import requests
import re
import os
import csv
import time
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO, StringIO
from openai import OpenAI
from collections import defaultdict

client = OpenAI(api_key="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")  # Replace with your actual key

output_dir = "test_brand_csvs"
os.makedirs(output_dir, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[^\w\-_]', '_', name.strip().lower())

def scrape_images_from_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"❌ Failed to access {url}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.select(".hbwssY, #gallery-collection .responsive-image__image")

        image_urls = []
        for img in img_tags:
            img_url = img.get("src") or img.get("data-src")
            if img_url and img_url.startswith("http"):
                image_urls.append(img_url)

        return image_urls

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

def filter_valid_image_urls(image_urls):
    seen = set()
    valid_urls = []
    for url in image_urls:
        if any(x in url for x in ['undefined', 'limit/undefined', 'logo', 'icon', 'banner']):
            continue
        if url in seen:
            continue
        seen.add(url)
        valid_urls.append(url)
    return valid_urls

def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def analyze_images_batch(image_urls, source_url):
    try:
        image_content = [{"type": "image_url", "image_url": {"url": url}} for url in image_urls]
        user_message = [
            {"type": "text", "text": f"These images are looks from the same fashion collection on {source_url}. Analyze them and return one row of CSV per image, including headers only once."}
        ] + image_content

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fashion analyst. Given a set of fashion look images, respond ONLY with CSV (no preamble, no extra text). "
                        "Include headers once. Each image should correspond to one row of CSV. "
                        "Headers: Look Number, Designer, Season, Gender Presentation, Garments, Accessories, Silhouette, Style Keywords, Notes. "
                        "Wrap all comma-containing fields in double quotes. Do not use markdown or code blocks.\n\n"
                        "Example:\n"
                        "Look Number,Designer,Season,Gender Presentation,Garments,Accessories,Silhouette,Style Keywords,Notes\n"
                        "1,Gucci,Fall 2023,Masculine,\"Black wool coat, white turtleneck, gray slacks\",\"Black gloves, silver chain necklace\",\"Boxy, structured\",\"Minimalist, modern\",\"Strong shoulders, monochrome layering\""
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Error analyzing image batch: {e}")
        return None

def save_csv_by_designer(image_data, output_dir):
    designer_groups = defaultdict(list)
    for row in image_data:
        designer = row.get("Designer", "unknown").strip()
        designer_filename = sanitize_filename(designer)
        designer_groups[designer_filename].append(row)

    for designer_filename, records in designer_groups.items():
        filepath = os.path.join(output_dir, f"{designer_filename}.csv")
        df = pd.DataFrame(records)

        if os.path.exists(filepath):
            existing = pd.read_csv(filepath)
            df = pd.concat([existing, df], ignore_index=True)

        df.to_csv(filepath, index=False)
        print(f"✅ Appended {len(records)} rows to {filepath}")

# Main runner
input_csv = "tidy_v1.csv"
df = pd.read_csv(input_csv)

for index, row in df.iterrows():
    url = row['url']
    print(f"\n🔍 Processing: {url}")

    image_urls = filter_valid_image_urls(scrape_images_from_url(url))
    image_data = []

    for chunk in chunked(image_urls, 3):  # Batching in groups of 3
        csv_text = analyze_images_batch(chunk, url)
        if not csv_text:
            continue

        cleaned = re.sub(r"```csv|```", "", csv_text, flags=re.IGNORECASE).strip()
        try:
            csv_buffer = StringIO(cleaned)
            reader = csv.DictReader(csv_buffer)
            for row in reader:
                image_data.append(row)
        except Exception as e:
            print(f"⚠️ CSV parsing error: {e}")
            print("Raw output:\n", cleaned)

    if image_data:
        save_csv_by_designer(image_data, output_dir)

print("\n🎉 All scraping and analysis complete.")
