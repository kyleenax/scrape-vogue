const { chromium } = require('playwright');

async function loginVogue(page) {
    await page.goto('https://www.vogue.com/account/login');

    // Enter credentials
    await page.fill('input[name="email"]', 'kx63@cornell.edu');  // Replace
    await page.fill('input[name="password"]', '123456');  // Replace
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForLoadState('networkidle');

    // Save session cookies
    return await page.context().cookies();
}

async function scrape() {
    const browser = await chromium.launch({ headless: false });  // Debugging mode
    const context = await browser.newContext();
    const page = await context.newPage();

    // ✅ Login first
    const cookies = await loginVogue(page);
    await context.addCookies(cookies);

    // ✅ Now visit the runway collections page
    await page.goto('https://www.vogue.com/fashion-shows/fall-2024-couture');
    console.log(await page.title());  // Should show Vogue page title

    await browser.close();
}

// Run the script
scrape();
