from playwright.async_api import async_playwright, Browser
from typing import Optional
import random
import asyncio
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import warnings
from playwright.sync_api import sync_playwright
import time
warnings.filterwarnings("ignore")
app = FastAPI(title=" Scraping API")


class TextInput(BaseModel):
    text: str


# =============================
# CONFIGURATION
# =============================
MIN_DELAY = 5     # seconds
MAX_DELAY = 10    # seconds
MAX_SCRAPES_PER_BROWSER = 6
COOLDOWN_ON_BLOCK = 45  # seconds
_playwright = None
_browser: Optional[Browser] = None
_scrape_count = 0


NEW_AUT_URL = (
    "https://www.autotrader.ca/lst"
    "?atype=C&custtype=P&cy=CA&damaged_listing=exclude"
    "&desc=1&lat=46.20007&lon=-82.34984"
    "&offer=U&size=40&sort=age&ustate=N,U"
    "&zip=Spanish,%20ON&zipr=1000"
)


AUTH_STATE = {
    "cookies": [
        {"name": "datr", "value": "xxx", "domain": ".facebook.com", "path": "/", "expires": 1805640586, "httpOnly": True, "secure": True, "sameSite": "None"},
        {"name": "c_user", "value": "xxx", "domain": ".facebook.com", "path": "/", "expires": 1802616603, "httpOnly": False, "secure": True, "sameSite": "None"},
        {"name": "xs", "value": "xxx", "domain": ".facebook.com", "path": "/", "expires": 1802616603, "httpOnly": True, "secure": True, "sameSite": "None"}
    ],
    "origins": []
}

CITIES = [
    "London",
    "Toronto",
    "Barrie",
    "Sudbury",
    "Sault Ste. Marie",
    "Timmins",
    "Windsor"
]

# ---------------------------
# BROWSER LIFECYCLE
# ---------------------------


async def start_browser():
    global _playwright, _browser, _scrape_count

    if _browser:
        return

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    _scrape_count = 0
    print("✅ Browser started")


async def restart_browser():
    global _browser, _playwright, _scrape_count

    try:
        if _browser:
            await _browser.close()
        if _playwright:
            await _playwright.stop()
    except Exception:
        pass

    _browser = None
    _playwright = None
    _scrape_count = 0
    print("🔄 Browser restarted")


# ---------------------------
# CORE SCRAPER
# ---------------------------

async def scrape_autotrader_once():
    global _scrape_count

    await start_browser()

    context = await _browser.new_context(
        locale="en-CA",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    )

    # Block heavy assets (keep JS)
    await context.route(
        "**/*.{png,jpg,jpeg,webp,svg,woff,woff2}",
        lambda route: asyncio.create_task(route.abort())
    )

    page = await context.new_page()

    try:
        await page.goto(
            NEW_AUT_URL,
            wait_until="domcontentloaded",
            timeout=120_000
        )

        data = await page.evaluate("""
        () => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }
        """)

        if not data:
            raise RuntimeError("NEXT_DATA missing (throttled or interstitial)")

        page_props = data["props"]["pageProps"]
        cars = page_props.get("listings", [])
        total_results = page_props.get("numberOfResults", 0)

        results = []

        for car in cars:
            vehicle = car.get("vehicle", {})
            price_data = car.get("price", {})
            location = car.get("location", {})

            results.append({
                "title": f"{vehicle.get('modelYear', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}".strip(),
                "price": price_data.get("priceFormatted"),
                "city": location.get("city"),
                "mileage_km": vehicle.get("mileageInKm"),
                "image": car["images"][0] if car.get("images") else None,
                "url": car.get("url"),
                "description": (car.get("description") or "").split("<br")[0],
                "make": vehicle.get("make"),
                "model": vehicle.get("model"),
                "year": vehicle.get("modelYear"),
            })

        _scrape_count += 1

        return {
            "success": True,
            "total_results": total_results,
            "scraped_count": len(results),
            "source": "AutoTrader",
            "cars": results
        }

    finally:
        await context.close()

        # Human-like delay
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        # Restart browser after threshold
        if _scrape_count >= MAX_SCRAPES_PER_BROWSER:
            print("⚠️ Scrape limit reached, cooling down…")
            await restart_browser()
            await asyncio.sleep(COOLDOWN_ON_BLOCK)

# =============================
# FASTAPI ENDPOINTS
# =============================


@app.get("/")
def read_root():
    return {
        "message": "Scraping API",
        "endpoints": {
          
         
            
            "/scrape_New_Autotrader": "GET - Scrape New Autotrader listings"
        }
    }




@app.get("/scrape_new_autotrader_listings")
async def scrape():
    try:
        return await scrape_autotrader_once()
    except Exception as e:
        await restart_browser()
        raise HTTPException(
            status_code=503,
            detail=f"Autotrader scrape failed: {str(e)}"
        )

@app.get("/scrape-marketplace")
def scrape():

    start = time.time()
    results = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = browser.new_context(
            storage_state=AUTH_STATE,
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        pages = []

        for city in CITIES:
            page = context.new_page()
            url = f"https://www.facebook.com/marketplace/{city}"
            page.goto(url, timeout=60000)
            pages.append((city, page))

        for city, page in pages:

            page.wait_for_timeout(4000)

            posts = page.locator("a[href*='/marketplace/item']")
            count = posts.count()

            for i in range(min(count, 25)):
                link = posts.nth(i).get_attribute("href")

                if link:
                    results.append({
                        "city": city,
                        "link": link
                    })

        browser.close()

    end = time.time()

    return {
        "status": "ok",
        "cities": len(CITIES),
        "total_items": len(results),
        "time_seconds": round(end - start, 2),
        "data": results
    }
@app.on_event("shutdown")
async def shutdown():
    await restart_browser()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "autotrader_scraper"}


