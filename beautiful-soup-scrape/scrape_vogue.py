from playwright.sync_api import sync_playwright
import pandas as pd

# ✅ Define the list of fashion shows
FASHION_SHOWS = [
    "fall-1999-ready-to-wear",
    "spring-1999-ready-to-wear",
    "fall-1998-ready-to-wear",
    "spring-1998-ready-to-wear",
    "fall-1997-ready-to-wear",
    "spring-1997-ready-to-wear",
    "fall-1996-ready-to-wear",
    "spring-1996-ready-to-wear",
    "fall-1995-ready-to-wear",
    "spring-1995-ready-to-wear",
    "fall-1994-ready-to-wear",
    "spring-1994-ready-to-wear",
    "fall-1993-ready-to-wear",
    "spring-1993-ready-to-wear",
    "fall-1992-ready-to-wear",
    "spring-1992-ready-to-wear",
    "fall-1991-ready-to-wear",
    "spring-1991-ready-to-wear",
    "fall-1990-ready-to-wear",
    "spring-1990-ready-to-wear"
]


BASE_URL = "https://www.vogue.com/fashion-shows/"

def scrape_vogue_shows():
    fashion_data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Change to True for silent mode
        page = browser.new_page()

        for show in FASHION_SHOWS:
            show_url = BASE_URL + show
            print(f"🔍 Visiting: {show_url}")

            # ✅ Visit the show page
            page.goto(show_url, wait_until="domcontentloaded")

            # ✅ Save only the season and URL
            fashion_data.append({"season": show.replace("-", " ").title(), "url": show_url})

        browser.close()

    # ✅ Save results to CSV (only season and URL)
    df = pd.DataFrame(fashion_data)
    df.to_csv("v4.csv", index=False)
    print("✅ Scraping completed! Data saved to `v4.csv`")

# Run the scraper
scrape_vogue_shows()
