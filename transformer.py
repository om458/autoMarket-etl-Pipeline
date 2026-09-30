import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)] %(message)s')
logger = logging.getLogger(__name__)

def transform_market_data(raw_records: list[dict], current_year: int = 2026) -> pd.DataFrame:
    """
    Cleans raw scraper records and applies financial metrics and Z-score market valuations.
    """
    if not raw_records:
        logger.warning("Transformation received empty records list")
        return pd.DataFrame()

    df = pd.DataFrame(raw_records)

    # 1. Enforce Correct Data Types
    df['id'] = df['id'].astype(str)
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['mileage'] = pd.to_numeric(df['mileage'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    #Drop rows with critical missing numerical values
    df = df.dropna(subset=['price', 'mileage', 'year']).copy()

    # 2. Derive Vehicle Age:
    df['age_years'] = np.maximum(0, current_year - df['year'])

    # 3. Financial Metrics: Price-per-mile and Estimated Annul Usage
    df['price_per_mile'] = np.where(df['mileage'] > 0, df['price'] / df['mileage'], np.nan)
    df['price_per_mile'] = df["price_per_mile"].round(4)

    df['annual_mileage'] = np.where(df['age_years'] > 0, df['mileage']/ df['age_years'], df['mileage'])
    df['annual_mileage'] = df['annual_mileage'].round(0)

    # 4. Statistical Anomaly Detection (Z-score by model)
    # Calculate group-level statictics per model
    df['model_mean_price'] = df.groupby('model')['price'].transform('mean')
    df['model_std_price'] = df.groupby('model')['price'].transform('std').fillna(1.0)

    # Avoid zero division if all cars in group have the exact same price
    df['model_std_price'] = np.where(df['model_std_price'] == 0, 1.0, df['model_std_price'])

    # Computer Z-score: (price - Group Mean) / Group_Std
    df['price_zscore'] = (df['price'] - df['model_mean_price']) / df['model_std_price']
    df['price_zscore'] = df['price_zscore'].round(2)

    #Classify market valuations based on standard deviation distance
    conditions = [
        df['price_zscore'] <= -1.2,
        (df['price_zscore'] > -1.2) & (df['price_zscore'] < 1.2),
        df['price_zscore'] >= 1.2
    ]
    choices = ['GREAT_DEAL','FAIR_MARKET', 'OVERPRICED']
    df['market_valuation'] = np.select(conditions, choices, default="FAIR_MARKET")

    # Drop intermediate statistical calculation helper columns
    df = df.drop(columns=['model_mean_price', 'model_std_price'])

    logger.info('Successfully transformed %d vehicle records.', len(df))
    return df

if __name__ == '__main__':
    # Local unit test with sample data
    mock_listings = [
        {'id': '101', 'make': 'SEAT', 'model': 'Leon', 'year': 2018, 'mileage': 51627, 'price': 10300.0, 'dealer': 'Independent Seller', 'url': 'https://autotrader.co.uk'},
        {'id': '102', 'make': 'SEAT', 'model': 'Leon', 'year': 2021, 'mileage': 21000, 'price': 14500.0, 'dealer': 'Franchised Seller', 'url': 'https://autotrader.co.uk'},
        {'id': '103', 'make': 'SEAT', 'model': 'Leon', 'year': 2015, 'mileage': 85000, 'price': 4200.0, 'dealer': 'Independent Seller', 'url': 'https://autotrader.co.uk'},
        {'id': '104', 'make': 'SEAT', 'model': 'Leon', 'year': 2017, 'mileage': 137654, 'price': 3499.0, 'dealer': 'Independent Seller', 'url': 'https://autotrader.co.uk'}
    ]

    transformed_df = transform_market_data(mock_listings)
    print(transformed_df[['id', 'model', 'price', 'mileage', 'age_years', 'price_per_mile', 'price_zscore', 'market_valuation']])




