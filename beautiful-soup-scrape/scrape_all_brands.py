from playwright.sync_api import sync_playwright
import pandas as pd
import time

# ✅ Load shows from CSV
shows_df = pd.read_csv("v1.csv")

# ✅ Dictionary to store season-wise brand names
season_brands = {}

def scrape_brands():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set False for debugging
        page = browser.new_page()

        for _, row in shows_df.iterrows():
            season = row["season"]
            show_url = row["url"]

            print(f"🔍 Scraping brands for {season} ({show_url})")
            try:
                page.goto(show_url, timeout=1200000)  # 60 seconds timeout
                time.sleep(2)  # Allow extra time to load content

                print("querying in progress")

                # ✅ Find brand links using `#main-content .navigation__link`
                brand_elements = page.query_selector_all("#main-content .navigation__link")

                brands = [brand.inner_text().strip() for brand in brand_elements if brand.inner_text().strip()]

                # ✅ Store brand names as a comma-separated string
                season_brands[season] = ", ".join(brands)
                print(f"📌 Brands found for {season}: {season_brands[season]}")

            except Exception as e:
                print(f"❌ Error scraping {season}: {e}")
                season_brands[season] = "Error"

        browser.close()

    # ✅ Merge scraped brand names into the original CSV
    shows_df["list-of-brands"] = shows_df["season"].map(season_brands)
    shows_df.to_csv("v1.csv", index=False)
    print("✅ Scraping completed! Data updated in `v1.csv`")

# ✅ Run the scraper
scrape_brands()
