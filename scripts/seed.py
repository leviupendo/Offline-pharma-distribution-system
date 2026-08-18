import sys
from pathlib import Path

# Allow `python scripts/seed.py` to work from the repo root without
# requiring PYTHONPATH to be set manually.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.models import User, Product, Customer, Role

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(User).filter(User.username == "admin").first():
    db.add(User(username="admin", password_hash=hash_password("ChangeMe!12345"), role=Role.SYSTEM_ADMIN))

if not db.query(Product).filter(Product.code == "DEMO-001").first():
    db.add(Product(code="DEMO-001", name="Demonstration Product", packaging_type="UNIT_DOSE_PACKET", standard_fill_weight_grams=1.0))

if not db.query(Customer).filter(Customer.customer_ref == "CUST-001").first():
    db.add(Customer(customer_ref="CUST-001", display_name="Demo Customer"))

db.commit()
db.close()
print("Seed complete. Development admin: admin / ChangeMe!12345")
