import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Vehicle, PriceHistory, Dealership

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DB_URL = 'sqlite:///autotrader.db'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def load_transformed_data(df: pd.DataFrame):
    """
    Ingest transformed Pandas DataFrame records into SQLite tables,
    updating vehicles, dealerships, and logging historical price observations.
    """
    if df.empty:
        logger.info('No records provided to load')
        return

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        inserted_prices = 0
        updated_vehicles = 0
        dealer_cache = {}

        for _, row in df.iterrows():
            dealer_name = str(row.get('dealer', 'Independent Seller')).strip()

            # 1. Upsert Dealership (using in-memory cache + DB query)
            if dealer_name in dealer_cache:
                dealer = dealer_cache[dealer_name]
            else:
                dealer = session.query(Dealership).filter_by(name=dealer_name).first()
                if not dealer:
                    dealer = Dealership(name=dealer_name)
                    session.add(dealer)
                    session.flush() # Populates dealer.id for foreign key assignment
                dealer_cache[dealer_name] = dealer

            # 2. Upsert Vehicle
            car_id = str(row['id'])
            vehicle = session.query(Vehicle).filter_by(id=car_id).first()

            if not vehicle:
                vehicle = Vehicle(
                    id=car_id,
                    make=str(row['make']),
                    model=str(row['model']),
                    year=int(row['year']),
                    mileage=int(row['mileage']),
                    dealership_id=dealer.id,
                    url=str(row['url'])
                )
                session.add(vehicle)
                updated_vehicles += 1
            else:
                vehicle.mileage = int(row['mileage']) # type: ignore

            # 3. Log Price History Entry
            price_entry = PriceHistory(
                vehicle_id=car_id,
                price=float(row['price'])
            )
            session.add(price_entry)
            inserted_prices += 1

            session.commit()
            logger.info(f'Successfully loaded {inserted_prices} price logs and updated {updated_vehicles} vehicles in autotrader.db')

    except Exception as e:
        session.rollback()
        logger.error(f'Failed to load data into database: {e}')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    test_df = pd.DataFrame([{
        'id': '2026000111',
        'make': 'SEAT',
        'model': 'Leon',
        'year': 2021,
        'mileage': 32000,
        'price': 125500.0,
        'dealer': 'Franchised Dealer',
        'url': 'https://www.autotrader.co.uk/car-details/2026000111'
    }])

    load_transformed_data(test_df)