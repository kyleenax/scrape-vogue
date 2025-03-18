from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import openai  # Ensure you have OpenAI API access

# ✅ OpenAI API Key (Replace with your own)
OPENAI_API_KEY = "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"

# ✅ Path for output CSV
OUTPUT_CSV = "fashion_looks_with_descriptions.csv"

# ✅ Function to analyze images with ChatGPT
def generate_description(image_url):
    """Send an image URL to ChatGPT for a fashion look description."""
    prompt = f"Describe the fashion look in this image: {image_url}. Focus on color, style, texture, and overall aesthetic."
    
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "user", "content": prompt}],
        api_key=OPENAI_API_KEY
    )
    
    return response["choices"][0]["message"]["content"].strip()

# ✅ Function to scrape fashion images and generate descriptions
def scrape_fashion_looks(input_csv):
    """Scrape all images from each brand's collection page and analyze with ChatGPT."""
    
    df = pd.read_csv(input_csv)
    look_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for _, row in df.iterrows():
            season = row["season"]
            brand_url = row["url"]
            brand_name = row["brand"].strip()

            print(f"🔍 Scraping looks for: {brand_name} ({brand_url})")

            try:
                # ✅ Go to the brand's collection page
                page.goto(brand_url, timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(2)  # Allow time for images to load

                # ✅ Extract image URLs
                image_elements = page.query_selector_all("#gallery-collection .responsive-image__image")
                image_urls = [img.get_attribute("src") for img in image_elements if img.get_attribute("src")]

                for idx, img_url in enumerate(image_urls):
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url  # Fix protocol-less URLs

                    # ✅ Generate a description using AI
                    description = generate_description(img_url)

                    # ✅ Save data
                    look_data.append({
                        "season": season,
                        "brand": brand_name,
                        "look_number": idx + 1,
                        "image_url": img_url,
                        "description": description
                    })

                    print(f"📸 Look {idx + 1}: {description}")

            except Exception as e:
                print(f"❌ Error scraping {brand_name}: {e}")

        browser.close()

    # ✅ Save results to CSV
    df_output = pd.DataFrame(look_data)
    df_output.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Scraping & AI analysis complete! Data saved in `{OUTPUT_CSV}`")

# ✅ Run the function
scrape_fashion_looks("tidy_v1.csv")
