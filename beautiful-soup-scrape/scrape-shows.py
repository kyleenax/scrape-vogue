from playwright.sync_api import sync_playwright
import pandas as pd
import time

# ✅ Load shows from CSV
shows_df = pd.read_csv("vogue_fashion_shows.csv")

# ✅ List to store brand details
brand_data = []

def scrape_brands():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set False for debugging
        page = browser.new_page()

        for _, row in shows_df.iloc.iterrows():
            season = row["season"]
            show_url = row["url"]

            print(f"🔍 Scraping brands for {season} ({show_url})")
            try:
                page.goto(show_url, timeout=60000)  # 60 seconds timeout
                page.wait_for_load_state("networkidle")
                time.sleep(2)  # Allow extra time to load content

                # ✅ Find brand links (modify selector if necessary)
                brand_elements = page.query_selector_all("a[data-testid='GalleryFeedItem']")
                for brand_element in brand_elements:
                    brand_href = brand_element.get_attribute("href")
                    if brand_href:
                        brand_name = brand_href.split("/")[-1].replace("-", " ").title()
                        brand_url = f"https://www.vogue.com{brand_href}"
                        
                        print(f"📌 Found: {brand_name} ({brand_url})")

                        # ✅ Save brand details
                        brand_data.append({
                            "season": season,
                            "brand": brand_name,
                            "brand_url": brand_url
                        })

            except Exception as e:
                print(f"❌ Error scraping {season}: {e}")

        browser.close()

    # ✅ Save results to CSV
    df = pd.DataFrame(brand_data)
    df.to_csv("vogue_fashion_brands.csv", index=False)
    print("✅ Scraping completed! Data saved to `vogue_fashion_brands.csv`")

# ✅ Run the scraper
scrape_brands()


