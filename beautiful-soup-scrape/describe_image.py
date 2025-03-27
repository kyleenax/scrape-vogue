import requests
import re
import os
import csv
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO, StringIO
from openai import OpenAI

client = OpenAI(api_key="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")  # Replace with your actual key

# Create output directory if it doesn't exist
output_dir = "brand_csvs"
os.makedirs(output_dir, exist_ok=True)

def sanitize_filename(url):
    return re.sub(r'[^\w\-_]', '_', url)

def scrape_images_from_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to access {url}")
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
        print(f"Error scraping {url}: {e}")
        return []

def analyze_images_as_csv(image_urls, source_url):
    try:
        image_input = [{"type": "image_url", "image_url": {"url": url}} for url in image_urls]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fashion analyst. Given a list of fashion look images, respond ONLY with a CSV table. "
                        "The CSV should have the following headers: Look Number, Designer, Season, Gender Presentation, Garments, "
                        "Accessories, Silhouette, Style Keywords, Notes. Each row corresponds to one image. Wrap all comma-containing fields in double quotes. "
                        "Do not include image URLs. Do not include any explanations, markdown, or commentary — just the CSV."
                    )
                },
                {
                    "role": "user",
                    "content": image_input + [{"type": "text", "text": f"Analyze these fashion looks from {source_url} and return a single CSV table."}]
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error analyzing images: {e}")
        return None

# Read input CSV file containing Vogue URLs
input_csv = "tidy_v4.csv"
df = pd.read_csv(input_csv)

for index, row in df.iterrows():
    url = row['url']
    print(f"\n🔍 Processing: {url}")

    brand_name = sanitize_filename(url)
    brand_csv_path = os.path.join(output_dir, f"{brand_name}.csv")

    image_urls = scrape_images_from_url(url)
    if not image_urls:
        continue

    description = analyze_images_as_csv(image_urls, url)
    image_data = []

    if description:
        try:
            cleaned = re.sub(r"```csv|```", "", description, flags=re.IGNORECASE).strip()
            csv_buffer = StringIO(cleaned)
            reader = csv.DictReader(csv_buffer)
            image_data = list(reader)

        except Exception as e:
            print(f"⚠️ CSV parsing error for page: {url} — {e}")
            print("Raw output:\n", description)
        if description:
            try:
                # Remove markdown code block formatting if present
                cleaned = re.sub(r"```csv|```", "", description, flags=re.IGNORECASE).strip()
                csv_buffer = StringIO(cleaned)
                reader = csv.reader(csv_buffer)
                headers = next(reader)
                values = next(reader)

                if len(headers) == len(values):
                    record = dict(zip(headers, values))
                    image_data.append(record)
                else:
                    print(f"⚠️ Column mismatch for image: {image_url}")
                    print("Headers:", headers)
                    print("Values :", values)
                    print("Raw output:\n", description)

            except Exception as e:
                print(f"⚠️ CSV parsing error for image: {image_url} — {e}")
                print("Raw output:\n", description)

    if image_data:
        output_df = pd.DataFrame(image_data)
        output_df.to_csv(brand_csv_path, index=False)
        print(f"✅ Saved {len(image_data)} looks to {brand_csv_path}")

print("\n🎉 Scraping and analysis complete. All brand data saved.")
