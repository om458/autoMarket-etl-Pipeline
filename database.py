from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Dealership(Base):
    __tablename__ = 'dealerships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    # 1-to-many relationship:: One dealership can have many cars
    vehicles = relationship('Vehicle', back_populates='dealership')

class Vehicle(Base):
    __tablename__ = 'vehicles'

    #Use AutoTrader unique ID as primary key
    id = Column(String(64), primary_key=True)
    make = Column(String(64), default='SEAT')
    model = Column(String(64), nullable=False)
    year = Column(Integer, nullable=False)
    mileage = Column(Integer, nullable=False)
    url = Column(String(512), nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)

    dealership_id = Column(Integer, ForeignKey('dealerships.id'), nullable=True)

    dealership = relationship('Dealership', back_populates='vehicles')
    prices = relationship('PriceHistory', back_populates='vehicle', cascade='all, delete-orphan')

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    vehicle_id = Column(String(64), ForeignKey('vehicles.id'), nullable=False)

    vehicle = relationship('Vehicle', back_populates='prices')

def init_db(db_url: str = 'sqlite:///market_data.db'):
    """" Creates tables if they do not exist and returns a session."""

    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()