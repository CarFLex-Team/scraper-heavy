from playwright.async_api import async_playwright, Browser
from fastapi.concurrency import run_in_threadpool
from typing import Optional
import random
import asyncio
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
import requests
import json
import re
import warnings
from datetime import datetime, timezone
from fastapi.responses import FileResponse
import pandas as pd
import time
import uuid
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


URLKIJII = "https://www.kijiji.ca/b-cars-trucks/sudbury/c174l1700245"

PARAMSKIJII = {
    "address": "Spanish, ON",
    "for-sale-by": "ownr",
    "ll": "46.1947959,-82.3422779",
    "price": "0__",
    "radius": "988.0",
    "view": "list",
}

HEADERSKIJII = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html",
}

COOKIESKIJII = {
    "kjses": "a3ada55c-3dda-4d3b-a2f1-5a2dc3e6d11e",
}
URL = "https://www.autotrader.ca/lst"

NEW_AUT_URL = (
    "https://www.autotrader.ca/lst"
    "?atype=C&custtype=P&cy=CA&damaged_listing=exclude"
    "&desc=1&lat=46.20007&lon=-82.34984"
    "&offer=U&size=40&sort=age&ustate=N,U"
    "&zip=Spanish,%20ON&zipr=1000"
)
PARAMS = {
    "atype": "C",
    "custtype": "P",
    "cy": "CA",
    "damaged_listing": "exclude",
    "desc": "1",
    "lat": "46.20007",
    "lon": "-82.34984",
    "offer": "U",
    "size": "40",
    "sort": "age",
    "ustate": "N,U",
    "zip": "Spanish, ON",
    "zipr": "1000"
}

HEADERS = {
    'Host': 'www.autotrader.ca',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not_A Brand";v="99", "Chromium";v="142"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Accept-Language': 'en-US,en;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Priority': 'u=0, i',
}

COOKIES = {
    'as24Visitor': 'c3c760d9-0878-408d-a19b-2180d1931375',
    'ab_test_lp': '%7B%22abTest740ComparisonFeature%22%3A%22abtest-740_variation_a%22%7D',
    'visid_incap_820541': 'PKiQE+rTTnqperHoTPBa4tLDEWkAAAAAQUIPAAAAAADlg8tQIlw7MRuZnv64x+pW',
    'nlbi_820541_3122371': '5Qbyek4Vd00I5av4pRL4bAAAAAA9PPLlUlcN+ZpBnL9/m2b9',
    'incap_ses_1776_820541': 'uW+LcvEvkjXjMEPdFJ+lGNPDEWkAAAAAlBI2pxFRiGU/kcvWgd8hPg==',
    'nlbi_820541_3120041': 'pmRoSFKMVAJRVvvOpRL4bAAAAADfZdw2B4NIGxW0/vooNruv',
    'nlbi_820541_3127200': '1mNKGNNWJya6qtEdpRL4bAAAAABvgkYRJ8QHpATlKN0ZRp6c',
    'culture': 'en-CA',
    'fallback-zip': '%7B%22label%22%3A%22N5X0E2%20London%2C%20ON%22%2C%22lat%22%3A43.029117584228516%2C%22lon%22%3A-81.26272583007812%7D',
    'nlbi_820541_3163786': 'jHOsYtqQaQfhsKOFpRL4bAAAAADh1E3Y04D6Lc6xys2DCcl6',
    'as24-gtmSearchCrit': '0010001-0020000:cc|cy|rn|cu',
    'at_as24_site_exp': 'onemp',
    '_cq_duid': '1.1762771930.cdR0NwW6AZPpu8aK',
    '_cq_suid': '1.1762771930.MoGQGNTaKdpzGwnI',
    '_gcl_au': '1.1.1886041771.1762771930',
    '_ga': 'GA1.1.83325848.1762771931',
    'FPID': 'FPID2.2.2IqdjODDjA3wGmtH4ZCNeesz9Gjk23y%2FPi3uMiuMmoI%3D.1762771931',
    'FPLC': 'AW%2FNnyvZubMKO1%2FcghoA01cRyrAQ8iyffLogr3pk6IX%2B%2BV7rkhW5%2B7MA3AcRI7CI9lOyOaI1Xd3icyFAuEH%2B2PqS%2FbE4A9vJH%2B%2FR6OesPvOLJKnb21uz8YHqc%2F4pcA%3D%3D',
    'FPAU': '1.1.1886041771.1762771930',
    '_gtmeec': 'e30%3D',
    '_fbp': 'fb.1.1762771930982.1774960817',
    'nlbi_820541_3156894': 'cK7GZnlkmFBu4USEpRL4bAAAAABXW0bE1BNblaqCh8sJN0Ca',
    '__T2CID__': 'eb28b989-4140-452d-ac76-75c851c5f553',
    '_clck': 'v16eb9%5E2%5Eg0w%5E0%5E2140',
    '_cc_id': '853619dbd287e54c74355720e04e8ef7',
    'panoramaId': '1506e8abdd2ecdef53769d165cfea9fb927aad097ec22e82e8edcadb259f59ca',
    'panoramaIdType': 'panoDevice',
    'cc_audpid': '853619dbd287e54c74355720e04e8ef7',
    'nlbi_820541_3181253': 'Rsj2QfBuZB3xaiPxpRL4bAAAAABiz5XD8ZEuqjsmv5JIS5pp',
    '___iat_ses': '5474ECF60E041E03',
    'cbnr': '1',
    '__gads': 'ID=56760f4de69aba99:T=1762771964:RT=1762771964:S=ALNI_MY4KTjzzmGwdjMdJAwTuJNiFkIs-A',
    '__gpi': 'UID=000012c7020b9b88:T=1762771964:RT=1762771964:S=ALNI_MZrhXe8JdXVj_z1BschzbBh3W2k6g',
    '__eoi': 'ID=ef85606016a43971:T=1762771964:RT=1762771964:S=AA-AfjZ1d4CgH4oLZI_zGwocyQTS',
    '_asse': 'cm:eyJzbSI6WyIxfDE3NjI3NzE5Mjk2NjJ8MHwwfDM5MTA0fG4iLDE4MjU4NDM5Njg3NjZdfQ==',
    '_uetsid': '50f7c550be2311f0940e9bfe639c74a4',
    '_uetvid': '50f7e640be2311f080c395e793823310',
    '_cq_pxg': '3|p7540524170993107026644946499',
    'FCCDCF': '%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%226d740418-bc8a-4f2a-bd34-bf1c2ecf5a85%5C%22%2C%5B1762771964%2C96000000%5D%5D%22%5D%5D%5D',
    'FCNEC': '%5B%5B%22AKsRol-5W8HZTX4B77SYl3I8RPx6vsdRq-o5IStvZsI-6goTReUCK5zkW1N-2I2eJv-UppQNQxOlM9z6oAEQr6WeCCPwNhMiJq06SplepUnGNCzzAfpPVqUGRaDGODvxhnMO2aHzLvt_4OYVUkhJOIxx7FsJO_HsSA%3D%3D%22%5D%5D',
    'last-search-feed': 'atype%3DC%26custtype%3DP%26cy%3DCA%26damaged_listing%3Dexclude%26desc%3D1%26lat%3D43.029117584228516%26lon%3D-81.26272583007812%26offer%3DU%26size%3D40%26sort%3Dage%26ustate%3DN%252CU%26zip%3DN5X0E2%2520London%252C%2520ON%26zipr%3D1000',
    '_ga_YKMVVRSW3Y': 'GS2.1.s1762771931$o1$g1$t1762772105$j10$l0$h0',
    '_ga_TX2QRVWP93': 'GS2.1.s1762771931$o1$g1$t1762772105$j60$l0$h987418783',
    '___iat_vis': '5474ECF60E041E03.d365e08ebc04d931d71f0f6e5c8b9051.1762772106907.6f92ff3b6ad04d7a6960250481c51d7a.ROAIMMMOOZ.11111111.1-0.d365e08ebc04d931d71f0f6e5c8b9051',
    '_clsk': '1husmi%5E1762772107776%5E3%5E0%5Eo.clarity.ms%2Fcollect',
    'panoramaId_expiry': '1762858506944',
}

SWOOPA_ACCOUNTS = {
    "primary": {
        "url": "https://backend.getswoopa.com/api/marketplace/",
        "headers": {


            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxMTYxMTg1LCJpYXQiOjE3NzEwNzQ3ODUsImp0aSI6ImU3NTE3ZTY4YTNmODQyNTlhOTAyZTI0M2ViYjE3NDQwIiwidXNlcl9pZCI6Ijk1MjE2In0.hjKM0sZdCWmVWBJ-2vqhvlqgUUvHm_P9hpuorjx6edk",


            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://app.getswoopa.com",
            "Referer": "https://app.getswoopa.com/",
            "User-Agent": "Mozilla/5.0",
        }
    },
    "secondary": {
        "url": "https://backend.getswoopa.com/api/marketplace/",
        "headers": {

            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxMTYxMDk1LCJpYXQiOjE3NzEwNzQ2OTUsImp0aSI6ImNlOTZmYzAyZWE1ZTQ1NWZhNTBlYTQ0YjFjMjNhNTI2IiwidXNlcl9pZCI6Ijk3OTE3In0.qITejVLgc9Zs7AL8lO_ajMShlUCpx0NHXj6lKovCG5w",

            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://app.getswoopa.com",
            "Referer": "https://app.getswoopa.com/",
            "User-Agent": "Mozilla/5.0",
        }
    }
}

# =============================
# HELPER FUNCTIONS
# =============================


def parse_kijiji_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(
            date_str, "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.strptime(
            date_str, "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)


def find_autos_listings(obj, results=None):
    if results is None:
        results = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("AutosListing:"):
                results[k] = v
            else:
                find_autos_listings(v, results)

    elif isinstance(obj, list):
        for item in obj:
            find_autos_listings(item, results)

    return results
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
            "/scrape_autotrader": "GET - Scrape Autotrader listings",
            "/scrape_kijiji": "GET -  Scrape Kijiji listings",
            "/fetch-marketplace-primary": "GET -  Scrape primary marketplace listings",
            "/fetch-marketplace-secondary": "GET -  Scrape secondary marketplace listings",
            "/check-scammer": "POST - Check if text indicates a real person or dealer",
            "/scrape_New_Autotrader": "GET - Scrape New Autotrader listings"
        }
    }


@app.get("/scrape_autotrader")
def scrape_autotrader():
    """
    Scrape Autotrader listings and return structured data
    """
    try:
        # Make request
        response = requests.get(
            URL,
            params=PARAMS,
            headers=HEADERS,
            cookies=COOKIES,
            verify=False,
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Request failed with status code: {response.status_code}"
            )

        html = response.text
        # Parse embedded JSON
        match = re.search(
            r'<script[^>]+type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )

        if not match:
            raise HTTPException(
                status_code=500,
                detail="Embedded JSON not found in response"
            )

        json_text = match.group(1).replace("&quot;", '"')
        data = json.loads(json_text)

        # Extract data
        page_props = data["props"]["pageProps"]
        number_of_results = page_props["numberOfResults"]
        cars = page_props["listings"]

        results = []

        for car in cars:
            vehicle = car.get("vehicle", {})
            price_data = car.get("price", {})
            location = car.get("location", {})

            make = vehicle.get("make", "")
            model = vehicle.get("model", "")
            year = vehicle.get("modelYear", "")
            mileage = vehicle.get("mileageInKm")

            price = price_data.get("priceFormatted", "")
            city = location.get("city", "")
            url = car.get("url", "")

            image = car["images"][0] if car.get("images") else None
            description = car.get("description", "").split(
                "<br")[0] if car.get("description") else ""

            title = f"{year} {make} {model}".strip()

            car_data = {
                "title": title,
                "price": price,
                "city": city,
                "mileage_km": mileage,
                "image": image,
                "url": url,
                "description": description,
                "make": make,
                "model": model,
                "year": year
            }

            results.append(car_data)

        return {
            "success": True,
            "total_results": number_of_results,
            "scraped_count": len(results),
            "source": "AutoTrader",
            "cars": results
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"JSON parsing error: {str(e)}")
    except KeyError as e:
        raise HTTPException(
            status_code=500, detail=f"Missing expected data field: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}")

#


@app.get("/scrape_kijiji")
def scrape_kijiji():

    r = requests.get(
        URLKIJII,
        params=PARAMSKIJII,
        headers=HEADERSKIJII,
        cookies=COOKIESKIJII,
        timeout=30,
    )

    if r.status_code != 200:
        raise HTTPException(500, "Request failed")

    match = re.search(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        r.text,
        re.DOTALL,
    )

    if not match:
        raise HTTPException(500, "Embedded JSON not found")

    raw_json = (
        match.group(1)
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .strip()
    )

    data = json.loads(raw_json)

    listings_map = find_autos_listings(data)
    now = datetime.now(timezone.utc)

    results = []

    for listing in listings_map.values():
        attributes = listing.get("attributes", {}).get("all", [])

        def get_attr(name):
            for a in attributes:
                if a.get("canonicalName") == name:
                    vals = a.get("canonicalValues")
                    return vals[0] if vals else None
            return None

        activation = parse_kijiji_date(listing.get("activationDate"))
        sorting = parse_kijiji_date(listing.get("sortingDate"))
        amount = listing.get("price", {}).get("amount")

        if isinstance(amount, (int, float)):
            price = amount // 100
        else:
            price = amount
        results.append({
            "title": listing.get("title"),
            "description": listing.get("description"),
            "price": price,
            "currency": "CAD",
            "url": listing.get("url"),
            "images": listing.get("imageUrls") or [],
            "brand": get_attr("carmake"),
            "model": get_attr("carmodel"),
            "year": get_attr("caryear"),
            "mileage_km": get_attr("carmileageinkms"),
            "body_type": get_attr("carbodytype"),
            "color": get_attr("carcolor"),
            "doors": get_attr("noofdoors"),
            "fuel_type": get_attr("carfueltype"),
            "transmission": get_attr("cartransmission"),
            "activation_date": activation.isoformat() if activation else None,
            "sorting_date": sorting.isoformat() if sorting else None,
            "time_since_activation": (
                str(now - activation) if activation else None
            ),
        })

    results.sort(
        key=lambda x: x["sorting_date"] or "",
        reverse=True,
    )

    return {
        "count": len(results),
        "cars": results,
    }


@app.get("/fetch-marketplace-primary")
def fetch_marketplace(
    pages: int = Query(1, ge=1, le=100),
    account: str = Query("primary"),
    export_csv: bool = False
):
    if account not in SWOOPA_ACCOUNTS:
        raise HTTPException(400, "Invalid Swoopa account")

    swoopa = SWOOPA_ACCOUNTS[account]
    url = swoopa["url"]
    headers = swoopa["headers"]

    all_results = []

    for _ in range(pages):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Swoopa {account} request failed: {str(e)}"
            )

        try:
            data = r.json()
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail=f"Swoopa {account} returned non-JSON response"
            )
        all_results.extend(data.get("results", []))

        url = data.get("next")
        if not url:
            break

        time.sleep(1)

    if export_csv:
        file_name = f"swoopa_{account}_{uuid.uuid4().hex}.csv"
        pd.DataFrame(all_results).to_csv(file_name, index=False)
        return FileResponse(file_name, media_type="text/csv", filename=file_name)

    return {

        "count": len(all_results),
        "results": all_results
    }


@app.get("/fetch-marketplace-secondary")
def fetch_marketplace(
    pages: int = Query(1, ge=1, le=100),
    account: str = Query("secondary"),
    export_csv: bool = False
):
    if account not in SWOOPA_ACCOUNTS:
        raise HTTPException(400, "Invalid Swoopa account")

    swoopa = SWOOPA_ACCOUNTS[account]
    url = swoopa["url"]
    headers = swoopa["headers"]

    all_results = []

    for _ in range(pages):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Swoopa {account} request failed: {str(e)}"
            )

        try:
            data = r.json()
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail=f"Swoopa {account} returned non-JSON response"
            )
        all_results.extend(data.get("results", []))

        url = data.get("next")
        if not url:
            break

        time.sleep(1)

    if export_csv:
        file_name = f"swoopa_{account}_{uuid.uuid4().hex}.csv"
        pd.DataFrame(all_results).to_csv(file_name, index=False)
        return FileResponse(file_name, media_type="text/csv", filename=file_name)

    return {

        "count": len(all_results),
        "results": all_results
    }
# @app.post("/check-scammer")
# def check_scammer(input: TextInput):
#     result = classifier(
#         input.text,
#         candidate_labels=["Real", "Dealer"]
#     )

#     is_real = result["labels"][0].strip() == "Real"

#     return {
#         "is_real": is_real,
#         "top_label": result["labels"][0],
#         "scores": dict(zip(result["labels"], result["scores"]))
#     }
# =============================
# HEALTH CHECK
# =============================


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "autotrader_scraper"}


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


@app.on_event("shutdown")
async def shutdown():
    await restart_browser()
