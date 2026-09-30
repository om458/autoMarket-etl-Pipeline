import logging
from extractor import extract_market_listings
from transformer import transform_market_data
from loader import load_transformed_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_URL = 'https://www.autotrader.co.uk/car-search?postcode=LE11AA&make=SEAT&model=Leon'
def run_pipeline(target_url: str = DEFAULT_URL):
    """
    Executes the end-to-end ETL pipeline:
    1. Extract: Scrapes raw listings using Playwright
    2. Transform: Cleans data and calculates Z-score deal valuatiosns using Pandas
    3. Load: Upserts vehicles, dealerships, and price logs into SQLite.
    """

    logger.info("=== STARTING ETL PIPELINE RUN ===")

    # 1. Extract
    logger.info('Phase 1: Extracting raw market listings...')
    raw_data = extract_market_listings(target_url)

    if not raw_data:
        logger.warning('Pipeline terminated: No listings were extracted.')
        return

    # 2. Transform
    logger.info('Phase 2: Transformation data and computing financial metrics...')
    transformed_df = transform_market_data(raw_data)

    # 3. Load
    logger.info('Phase 3: Loading transformed records into SQLite database...')
    load_transformed_data(transformed_df)
    logger.info('=== ETL PIPELINE RUN COMPLETED SUCCESSFULLY ===')

if __name__ == '__main__':
    run_pipeline()




