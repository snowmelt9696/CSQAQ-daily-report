/**
 * CSQAQ Kilowatt Case Data Scraper
 * Uses Playwright to extract goods data from csqaq.com
 * Saves results to data/goods_data.json
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const GOODS_ID = 19521;
const PAGE_URL = `https://csqaq.com/goods/${GOODS_ID}`;
const API_URL = `https://csqaq.com/proxies/api/v1/info/good?id=${GOODS_ID}`;
const OUTPUT_DIR = path.join(__dirname, "..", "data");
const OUTPUT_FILE = path.join(OUTPUT_DIR, "goods_data.json");

async function scrape() {
  console.log(`[${new Date().toISOString()}] Launching browser...`);

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  });

  const page = await context.newPage();

  // Collect API responses
  let goodsData = null;
  let chartData = null;

  page.on("response", async (response) => {
    const url = response.url();
    try {
      if (url.includes("/proxies/api/v1/info/good?id=")) {
        const body = await response.text();
        const json = JSON.parse(body);
        if (json.code === 200) {
          goodsData = json.data;
          console.log(`  -> Captured goods data`);
        }
      }
      if (url.includes("/proxies/api/v1/info/chart")) {
        const body = await response.text();
        const json = JSON.parse(body);
        if (json.code === 200) {
          chartData = json.data;
          console.log(`  -> Captured chart data`);
        }
      }
    } catch (e) {
      // Ignore non-JSON or failed responses
    }
  });

  console.log(`Navigating to ${PAGE_URL}...`);
  await page.goto(PAGE_URL, {
    waitUntil: "networkidle",
    timeout: 30000,
  });

  // Wait extra time for dynamic API calls to complete
  await page.waitForTimeout(5000);

  await browser.close();

  if (!goodsData) {
    console.error("ERROR: Failed to capture goods data from API");
    process.exit(1);
  }

  // Build output
  const result = {
    scraped_at: new Date().toISOString(),
    goods_id: GOODS_ID,
    goods_info: goodsData.goods_info,
    container: goodsData.container || [],
    statistic_list: goodsData.statistic_list || [],
    chart: chartData
      ? {
          timestamps: chartData.timestamp || [],
          prices: chartData.main_data || [],
          volumes: chartData.num_data || [],
        }
      : null,
  };

  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(result, null, 2), "utf-8");
  console.log(
    `Data saved to ${OUTPUT_FILE} (${JSON.stringify(result).length} bytes)`
  );
  console.log(`Done! Goods: ${result.goods_info.name} (${result.goods_info.market_hash_name})`);
}

scrape().catch((err) => {
  console.error("Scrape failed:", err);
  process.exit(1);
});

