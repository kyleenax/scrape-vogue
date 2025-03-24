import time
import requests
import re
import os
import csv
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO, StringIO
from openai import OpenAI

client = OpenAI(api_key="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"
)  # Replace with your actual key

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

def analyze_image_as_csv(image_url, source_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        for attempt in range(3):  # Retry mechanism
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a fashion analyst. Given an image of a fashion look, respond ONLY with one row of CSV (no preamble, no extra text). "
                                "The CSV should have the following headers: Website, Look Number, Designer, Season, Gender Presentation, Garments, "
                                "Accessories, Silhouette, Style Keywords, Notes. Each field should be concise and consistent. Garments should combine type, color, and texture. "
                                "Wrap all comma-containing fields in double quotes. Do not include an Image URL column. Do not use markdown or code blocks."
                            )

                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": image_url}},
                                {"type": "text", "text": f"Analyze this fashion look from {source_url} and return one single row of CSV including the headers."}
                            ]
                        }
                    ],
                    temperature=0.3
                )

                return response.choices[0].message.content.strip()

            except Exception as e:
                if "429 Too Many Requests" in str(e):
                    wait_time = 10 * (attempt + 1)
                    print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Error analyzing image {image_url}: {e}")
                    return None

    except Exception as e:
        print(f"Error analyzing image {image_url}: {e}")
        return None

# Read input CSV file containing Vogue URLs
input_csv = "tidy_v1.csv"
df = pd.read_csv(input_csv)

for index, row in df.iterrows():
    url = row['url']
    print(f"\nProcessing: {url}")

    brand_name = sanitize_filename(url)
    brand_csv_path = os.path.join(output_dir, f"{brand_name}.csv")

    image_urls = scrape_images_from_url(url)
    image_data = []

    for image_url in image_urls:
        if "undefined" in image_url or "limit/undefined" in image_url:
            print(f"Skipping invalid image URL: {image_url}")
            continue

        description = analyze_image_as_csv(image_url, url)
        if description:
            description_clean = description.strip("`").strip()
    try:
        csv_buffer = StringIO(description_clean)
        reader = csv.reader(csv_buffer)
        headers = next(reader)
        values = next(reader)

        if len(headers) == len(values):
            record = dict(zip(headers, values))
            record['Website'] = source_url  # Ensure correct URL
            # Optionally drop 'Image URL' if GPT includes it
            record.pop("Image URL", None)
            image_data.append(record)
        else:
            print(f"⚠️ Column mismatch for image: {image_url}")
            print("Headers:", headers)
            print("Values :", values)
            print("Raw output:\n", description_clean)

    except Exception as e:
        print(f"⚠️ CSV parsing error for image: {image_url} — {e}")
        print("Raw output:\n", description_clean)

    if image_data:
        output_df = pd.DataFrame(image_data)
        output_df.to_csv(brand_csv_path, index=False)
        print(f"✅ Saved data for {url} to {brand_csv_path}")

print("\n✅ Scraping and analysis complete. All brand data saved.")

