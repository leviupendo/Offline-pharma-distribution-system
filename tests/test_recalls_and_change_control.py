from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models.models import Customer, Product, Role, User

client = TestClient(app)


def _admin_headers():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "recall_test_admin").first():
            db.add(User(
                username="recall_test_admin",
                password_hash=hash_password("TestPassword!123"),
                role=Role.SYSTEM_ADMIN,
            ))
        if not db.query(Product).filter(Product.code == "RECALL-TEST-PRODUCT").first():
            db.add(Product(
                code="RECALL-TEST-PRODUCT", name="Recall Test Product",
                packaging_type="UNIT_DOSE_PACKET", standard_fill_weight_grams=1.0,
            ))
        if not db.query(Customer).filter(Customer.customer_ref == "RECALL-TEST-CUST").first():
            db.add(Customer(customer_ref="RECALL-TEST-CUST", display_name="Recall Test Customer"))
        db.commit()
    finally:
        db.close()

    token = client.post(
        "/api/auth/login", json={"username": "recall_test_admin", "password": "TestPassword!123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup_released_batch_with_allocated_order(batch_id="RECALL-B-001", order_id="RECALL-ORD-001"):
    h = _admin_headers()
    product_id = [p for p in client.get("/api/products", headers=h).json() if p["code"] == "RECALL-TEST-PRODUCT"][0]["id"]
    client.post("/api/batches", json={
        "batch_id": batch_id, "product_id": product_id,
        "production_date": "2026-01-01T00:00:00Z", "expiry_date": "2027-01-01T00:00:00Z",
        "bulk_quantity_tons": 1.0,
    }, headers=h)
    batch_pk = client.get("/api/batches", headers=h).json()[-1]["id"]
    client.post(f"/api/batches/{batch_pk}/qc", json={"decision": "RELEASED", "qc_results": "ok"}, headers=h)
    client.post("/api/inventory/packaging", params={
        "packet_lot_id": f"{batch_id}-LOT", "batch_id": batch_pk, "number_of_packets": 50,
        "fill_weight_grams": 1.0, "packaging_date": "2026-01-05T00:00:00Z",
    }, headers=h)
    client.post("/api/orders", json={
        "order_id": order_id, "customer_ref": "RECALL-TEST-CUST", "lines": [{"requested_quantity": 10}],
    }, headers=h)
    order_pk = [o for o in client.get("/api/orders", headers=h).json() if o["order_id"] == order_id][0]["id"]
    client.post(f"/api/orders/{order_pk}/allocate", headers=h)
    return h, batch_id


def test_recall_does_not_crash_and_sets_recalled_status():
    """Regression: BatchStatus previously had no RECALLED member, so
    setting batch.status = "RECALLED" raised a SQLAlchemy LookupError
    on every single call to POST /api/recalls."""
    h, batch_id = _setup_released_batch_with_allocated_order(
        batch_id="RECALL-B-002", order_id="RECALL-ORD-002"
    )
    r = client.post("/api/recalls", json={"batch_id": batch_id, "reason": "contamination found"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "RECALLED"


def test_recall_impact_reports_affected_orders_and_does_not_crash():
    """Regression: recall_impact queried Inventory.batch_id, a column
    that does not exist on the Inventory model, and always returned
    an empty "orders" list regardless of actual allocations."""
    h, batch_id = _setup_released_batch_with_allocated_order(
        batch_id="RECALL-B-003", order_id="RECALL-ORD-003"
    )
    client.post("/api/recalls", json={"batch_id": batch_id, "reason": "contamination found"}, headers=h)

    r = client.get(f"/api/recalls/{batch_id}/impact", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["batch_status"] == "RECALLED"
    assert len(body["orders"]) == 1
    assert body["orders"][0]["order_id"] == "RECALL-ORD-003"
    assert body["orders"][0]["affected_quantity"] == 10


def test_recall_rejects_double_recall():
    h, batch_id = _setup_released_batch_with_allocated_order(
        batch_id="RECALL-B-004", order_id="RECALL-ORD-004"
    )
    client.post("/api/recalls", json={"batch_id": batch_id, "reason": "first"}, headers=h)
    r = client.post("/api/recalls", json={"batch_id": batch_id, "reason": "second"}, headers=h)
    assert r.status_code == 409


def test_change_control_list_actually_lists_created_events():
    """Regression: list_change_events had a dead/unreachable query
    (`... if False else []`) and just returned a static note instead
    of the change requests that had actually been created."""
    h = _admin_headers()
    client.post("/api/change-control", json={
        "title": "Regression test change", "reason": "verifying the listing works", "risk_level": "LOW",
    }, headers=h)

    r = client.get("/api/change-control", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert any(item["details"]["title"] == "Regression test change" for item in body)
