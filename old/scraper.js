const fs = require('fs');
const { chromium } = require('playwright');
const path = require('path');
const BASE_URL = "https://www.vogue.com/fashion-shows/";

// List of seasons to scrape
const SEASONS = ["fall-2024-couture", "spring-2024-couture"];

// CSV File setup
const CSV_FILE = "vogue_fashion_analysis.csv";

// Function to simulate AI analysis (replace this with real AI if needed)
async function analyzeImageWithGPT(imageUrl) {
    return {
        top: "Silk blouse with floral patterns",
        bottom: "High-waisted trousers",
        accessories: "Gold chain necklace",
        other: "Red stiletto heels"
    };
}

const { chromium } = require('playwright');
const fs = require('fs');

async function scrapeWithCookies() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();

    // ✅ Load cookies from the file
    const cookies = JSON.parse(fs.readFileSync('cookies.json', 'utf8'));
    await context.addCookies(cookies);

    const page = await context.newPage();
    
    console.log("🔍 Navigating to Vogue Fashion Shows...");
    await page.goto("https://www.vogue.com/fashion-shows", { waitUntil: "domcontentloaded" });

    // ✅ Check if login was successful by printing the page title
    console.log("Page Title:", await page.title());

    // ✅ Save the page as proof that it worked
    await page.screenshot({ path: "vogue_home.png", fullPage: true });

    await browser.close();
    console.log("✅ Scraping completed successfully!");
}

scrapeWithCookies();




// Function to scrape look details from a brand page
async function scrapeLookDetails(page, brandUrl, brandName, seasonName, csvStream) {
    await page.goto(brandUrl, { waitUntil: "domcontentloaded", timeout: 60000 });

    console.log(`Scraping brand: ${brandName}`);

    // Find total number of looks
    try {
        await page.waitForSelector("div.Slideshow__Nav span");
        const totalLooksText = await page.locator("div.Slideshow__Nav span").innerText();
        const totalLooks = parseInt(totalLooksText.split("/").pop().trim(), 10);

        // Iterate through each look
        for (let lookNumber = 1; lookNumber <= totalLooks; lookNumber++) {
            const lookUrl = `${brandUrl}/slideshow/collection#${lookNumber}`;
            await page.goto(lookUrl, { waitUntil: "domcontentloaded", timeout: 60000 });

            // Extract image URL
            const imageElement = await page.$("img");
            const imageUrl = imageElement ? await imageElement.getAttribute("src") : "";

            // Analyze look
            let analysis = { top: "", bottom: "", accessories: "", other: "" };
            if (imageUrl) {
                analysis = await analyzeImageWithGPT(imageUrl);
            }

            // Save to CSV
            csvStream.write(`${seasonName},${brandName},${lookNumber},${imageUrl},${analysis.top},${analysis.bottom},${analysis.accessories},${analysis.other}\n`);
            console.log(`✅ Scraped ${seasonName} - ${brandName} - Look ${lookNumber}/${totalLooks}`);
        }
    } catch (error) {
        console.error(`⚠️ Error scraping ${brandName}: ${error.message}`);
    }
}

// Main scraping function
async function scrape() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Log in to Vogue
    await loginVogue(page);

    // Create CSV file and write headers
    const csvStream = fs.createWriteStream(path.join(__dirname, CSV_FILE), { flags: 'w' });
    csvStream.write("season,brand,look_number,image_url,top,bottom,accessories,other\n");

    for (const season of SEASONS) {
        const seasonUrl = `${BASE_URL}${season}`;
        console.log(`\n🔍 Scraping season: ${season}...`);
        
        await page.goto(seasonUrl, { waitUntil: "domcontentloaded", timeout: 60000 });

        // Extract brand links
        const brandElements = await page.$$("a.NavigationInternalLink-cWEaeo");
        for (const brandElement of brandElements) {
            const brandHref = await brandElement.getAttribute("href");
            if (brandHref) {
                const brandName = brandHref.split("/").pop();
                const brandUrl = `https://www.vogue.com${brandHref}`;

                // Scrape brand's collection
                await scrapeLookDetails(page, brandUrl, brandName, season, csvStream);
            }
        }
    }

    // Close everything
    csvStream.end();
    await browser.close();
    console.log("\n✅ Scraping complete! Data saved to", CSV_FILE);
}

// Run the scraper
scrape();
