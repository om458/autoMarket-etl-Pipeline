import re 
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def parse_card_specs(card_text: str):
    """Parses raw listing card text into structured numerical values."""
    year_match = re.search(r'\b(20\d\d|19\d\d)\b', card_text)
    year = int(year_match.group(1)) if year_match else 2020

    mileage_match = re.search(r'([\d,]+)\s*miles', card_text, re.IGNORECASE)
    mileage = int(mileage_match.group(1).replace(',', '')) if mileage_match else 35000

    price_match = re.search(r'£\s*([\d,]+)', card_text)
    price = float(price_match.group(1).replace(',', '')) if price_match else 0.0

    return year, mileage, price

def extract_market_listings(target_url: str) -> list[dict]:
    """Navigates to AutoTrader search listings and extracts structured vehicle data."""
    records = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled', 
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 1000},
            locale='en-GB',
            extra_http_headers={
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        )
        page = context.new_page()
        page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        try:
            logger.info('Navigating to %s', target_url)
            page.goto(target_url, wait_until='domcontentloaded', timeout=60000)

            # Dismiss cookie banner
            for cookie_btn in ['#onetrust-accept-btn-handler', 'button:has-text("Accept All")', 'button:has-text("Accept all")']:           
                try:
                    if page.locator(cookie_btn).is_visible(timeout=2500):
                        page.locator(cookie_btn).click()
                        break
                except Exception:
                    pass

            # Scroll progressively
            for _ in range(4):
                page.evaluate('window.scrollBy(0, 1000);')
                page.wait_for_timeout(600)

            car_links = page.locator('a[href*="/car-details/"]').all()
            logger.info(f'Discovered {len(car_links)} prospective listing anchors.')

            seen_ids = set()

            for link in car_links:
                try:
                    href = link.get_attribute('href')
                    if not href or '/car-details/' not in href:
                        continue

                    raw_id = href.split('/car-details/')[1].split('?')[0].split('#')[0]
                    if not raw_id.isdigit() or raw_id in seen_ids:
                        continue

                    # Ascend strictly to the immediate parent listing container
                    container = link.locator('xpath=ancestor::*[contains(@data-testid, "listing") or self::article or self::li][1]')
                    if not container.count():
                        continue

                    card_text = container.inner_text()

                    # STRICT SANITY CHECK: Ensure the card container text actually contains the targeted make/model keywords
                    # If an adjacent ad or recommended car (like an Audi) was caught, reject it instantly
                    if not any(brand in card_text.lower() for brand in ['seat', 'volkswagen', 'vw', 'leon', 'golf', 'ibiza', 'polo', 'ateca', 'arona']):
                        continue

                    year, mileage, price = parse_card_specs(card_text)
                    if price < 500:
                        continue

                    seen_ids.add(raw_id)

                    # Classify Model
                    model = 'Leon'
                    for candidate in ['Leon', 'Ibiza', 'Arona', 'Ateca', 'Golf', 'Polo', 'Tiguan']:
                        if candidate.lower() in card_text.lower():
                            model = candidate
                            break

                    # Extract dealer name
                    dealer_elem = container.locator('[data-testid*="seller-name"], [data-testid*="dealer-name"]').first
                    dealer_name = (
                        dealer_elem.inner_text().strip()
                        if dealer_elem.count()
                        else 'Independent Seller'
                    )

                    records.append({
                        'id': raw_id,
                        'make': 'SEAT' if model in ['Leon', 'Ibiza', 'Arona', 'Ateca'] else 'Volkswagen',
                        'model': model,
                        'year': year,
                        'mileage': mileage,
                        'price': price,
                        'dealer': dealer_name,
                        'url': f"https://www.autotrader.co.uk/car-details/{raw_id}"
                    })

                except Exception as ex:
                    logger.debug(f'Failed parsing card: {ex}')
        finally:
            browser.close()

    return records