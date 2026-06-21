/**
 * CSQAQ Multi-Goods Data Scraper
 * Uses Playwright to extract goods data from csqaq.com for multiple items.
 * Set GOODS_IDS env var (comma-separated) to target specific items.
 * Saves individual results to data/goods_{id}.json and manifest to data/manifest.json.
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const GOODS_IDS = (process.env.GOODS_IDS || "19521")
  .split(",")
  .map((id) => id.trim())
  .filter(Boolean);

const OUTPUT_DIR = path.join(__dirname, "..", "data");

async function scrapeGoods(browser, goodsId) {
  const pageUrl = `https://csqaq.com/goods/${goodsId}`;

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  });

  const page = await context.newPage();

  let goodsData = null;
  let chartData = null;

  page.on("response", async (response) => {
    const url = response.url();
    try {
      if (url.includes(`/proxies/api/v1/info/good?id=${goodsId}`)) {
        const body = await response.text();
        const json = JSON.parse(body);
        if (json.code === 200) {
          goodsData = json.data;
          console.log(`  -> Captured goods data for ID ${goodsId}`);
        }
      }
      if (url.includes("/proxies/api/v1/info/chart")) {
        const body = await response.text();
        const json = JSON.parse(body);
        if (json.code === 200) {
          chartData = json.data;
          console.log(`  -> Captured chart data for ID ${goodsId}`);
        }
      }
    } catch (e) {
      // Ignore non-JSON or failed responses
    }
  });

  console.log(`  Navigating to ${pageUrl}...`);
  await page.goto(pageUrl, {
    waitUntil: "networkidle",
    timeout: 30000,
  });
  await page.waitForTimeout(5000);

  await context.close();

  if (!goodsData) {
    console.error(`  ERROR: Failed to capture goods data for ID ${goodsId}`);
    return null;
  }

  return {
    scraped_at: new Date().toISOString(),
    goods_id: goodsId,
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
}

async function scrape() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  console.log(`[${new Date().toISOString()}] Launching browser...`);
  console.log(`Target goods IDs: ${GOODS_IDS.join(", ")}`);

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const manifest = [];

  for (const goodsId of GOODS_IDS) {
    console.log(`\n--- Scraping goods ID: ${goodsId} ---`);
    const data = await scrapeGoods(browser, goodsId);

    if (data) {
      const filename = `goods_${goodsId}.json`;
      const filepath = path.join(OUTPUT_DIR, filename);
      fs.writeFileSync(filepath, JSON.stringify(data, null, 2), "utf-8");
      console.log(`  Saved to ${filename} (${JSON.stringify(data).length} bytes)`);
      console.log(`  Goods: ${data.goods_info.name} (${data.goods_info.market_hash_name})`);

      manifest.push({
        id: goodsId,
        name: data.goods_info.name,
        market_hash_name: data.goods_info.market_hash_name,
        file: filename,
      });
    }
  }

  await browser.close();

  if (manifest.length === 0) {
    console.error("ERROR: No goods data captured for any ID");
    process.exit(1);
  }

  const manifestPath = path.join(OUTPUT_DIR, "manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");
  console.log(`\nManifest saved to manifest.json (${manifest.length} items)`);
  console.log("Done!");
}

scrape().catch((err) => {
  console.error("Scrape failed:", err);
  process.exit(1);
});
