from extractor import extract_market_listings

# Target autoTrader search for SEAT Leon models around leicester
test_url = 'https://www.autotrader.co.uk/car-search?postcode=LE11AA&make=SEAT&model=Leon'

print('Starting market extraction...')
results = extract_market_listings(test_url)

print(f'\n---SUCCESS: Scraped {len(results)} listings from AutoTrader---\n')
for car in results:
    print(f'[{car["id"]}] {car["year"]} {car["make"]} {car["model"]} - £{car["price"]:.2f} - {car["mileage"]} miles - Dealer: {car["dealer"]} - URL: {car["url"]}')