from database import init_db, Dealership, Vehicle, PriceHistory

# 1. Initialize DB and get session
session = init_db()

# 2. Insert mock dealer 
dealer = Dealership(name='Barlow Motors SEAT Wolverhampton')
session.add(dealer)
session.flush() 

# 3. Insert mock vehicle
car = Vehicle(
    id='1234567890',
    make='SEAT',
    model='Leon',
    year=2020,
    mileage=15000,
    url='https://www.autotrader.co.uk/car-details/1234567890',
    dealership_id=dealer.id
)
session.add(car)

# 4. Insert mock price point
price = PriceHistory(vehicle_id=car.id, price=15000.00)
session.add(price)

# 5. Commit to SQLite
session.commit()

#Read back out to verify
saved = session.query(Vehicle).filter_by(id='1234567890').first()
if saved :
    print('\n--- DATABASE CHECK SUCCESSFUL ---')
    print(f'Vehicle saved: {saved.year} {saved.make} {saved.model}')
    print(f'Dealership: {saved.dealership.name}')
    print(f'Price: £{saved.prices[0].price:.2f}\n')
else:
    print('Record not found in database.')