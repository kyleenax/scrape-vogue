from playwright.sync_api import sync_playwright
import json

def get_vogue_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Keep browser visible to debug
        context = browser.new_context()
        page = context.new_page()

        print("🔍 Navigating to Vogue login page...")
        page.goto("https://www.vogue.com/fashion-shows", wait_until="domcontentloaded")
        page.click('button[type="submit"]')

        # ✅ Wait for the login form to load
        page.wait_for_selector('input[name="email"]')

        # ✅ Enter login details
        page.fill('input[name="email"]', 'kx63@cornell.edu')  # Change this
        page.fill('input[name="password"]', '123456')  # Change this
        page.click('button[type="submit"]')

        # ✅ Wait for login to complete
        page.wait_for_load_state("networkidle")

        # ✅ Extract cookies
        cookies = context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f, indent=4)

        print("✅ Cookies saved successfully!")
        browser.close()

# Run the function
get_vogue_cookies()

