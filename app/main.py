from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, users, products, batches, inventory, customers, orders, audit, reports, validation, recalls, change_control, monitoring, system

# Refuse to start with placeholder secrets outside development.
settings.validate_production_secrets()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Offline Pharmaceutical Distribution System",
    version="0.3.0",
    description="Local-first production, QC, packaging, inventory and distribution platform."
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(batches.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(recalls.router, prefix="/api")
app.include_router(change_control.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(system.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/templates/index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
def health():
    return {"status": "ok", "offline_mode": True}
