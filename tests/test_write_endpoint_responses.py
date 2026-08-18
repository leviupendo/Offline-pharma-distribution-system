from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models.models import Role, User

client = TestClient(app)


def _admin_headers():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "response_test_admin").first():
            db.add(User(
                username="response_test_admin",
                password_hash=hash_password("TestPassword!123"),
                role=Role.SYSTEM_ADMIN,
            ))
        db.commit()
    finally:
        db.close()

    token = client.post(
        "/api/auth/login", json={"username": "response_test_admin", "password": "TestPassword!123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_product_returns_full_body_not_empty():
    """Regression: SQLAlchemy's default expire_on_commit=True expired
    every attribute right after db.commit(), so by the time FastAPI
    serialized the returned ORM object, jsonable_encoder's vars(obj)
    fallback found nothing left and every write endpoint silently
    returned `{}` with a 200 status — the write succeeded, but the
    caller had no way to know the new resource's id."""
    h = _admin_headers()
    r = client.post("/api/products", json={
        "code": "RESP-TEST-PRODUCT", "name": "Response Test Product",
        "packaging_type": "UNIT_DOSE_PACKET", "standard_fill_weight_grams": 1.0,
    }, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body != {}
    assert body["code"] == "RESP-TEST-PRODUCT"
    assert "id" in body and body["id"] is not None


def test_create_batch_and_qc_decision_return_full_body():
    h = _admin_headers()
    product_id = [
        p for p in client.get("/api/products", headers=h).json()
        if p["code"] == "RESP-TEST-PRODUCT"
    ][0]["id"]

    r = client.post("/api/batches", json={
        "batch_id": "RESP-TEST-BATCH", "product_id": product_id,
        "production_date": "2026-01-01T00:00:00Z", "expiry_date": "2027-01-01T00:00:00Z",
        "bulk_quantity_tons": 1.0,
    }, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body != {}
    assert body["batch_id"] == "RESP-TEST-BATCH"
    assert body["status"] == "QUARANTINE"
    batch_pk = body["id"]

    r = client.post(f"/api/batches/{batch_pk}/qc", json={
        "decision": "RELEASED", "qc_results": "passed all checks",
    }, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body != {}
    assert body["status"] == "RELEASED"


def test_order_allocate_response_reflects_actual_allocations():
    """Regression, related to the above: even after fixing the empty-
    body issue, OrderAllocation rows created via db.add(OrderAllocation(
    order_line_id=line.id, ...)) weren't visible on the already-loaded
    `line.allocations` collection, so the allocate response showed an
    empty allocations list despite the allocation having actually
    happened (confirmed by inventory correctly decrementing)."""
    h = _admin_headers()
    product_id = [
        p for p in client.get("/api/products", headers=h).json()
        if p["code"] == "RESP-TEST-PRODUCT"
    ][0]["id"]

    client.post("/api/customers", json={
        "customer_ref": "RESP-TEST-CUST", "display_name": "Response Test Customer",
    }, headers=h)

    r = client.post("/api/batches", json={
        "batch_id": "RESP-TEST-BATCH-2", "product_id": product_id,
        "production_date": "2026-01-01T00:00:00Z", "expiry_date": "2027-01-01T00:00:00Z",
        "bulk_quantity_tons": 1.0,
    }, headers=h)
    batch_pk = r.json()["id"]
    client.post(f"/api/batches/{batch_pk}/qc", json={"decision": "RELEASED", "qc_results": "ok"}, headers=h)
    client.post("/api/inventory/packaging", params={
        "packet_lot_id": "RESP-TEST-LOT", "batch_id": batch_pk, "number_of_packets": 10,
        "fill_weight_grams": 1.0, "packaging_date": "2026-01-05T00:00:00Z",
    }, headers=h)

    r = client.post("/api/orders", json={
        "order_id": "RESP-TEST-ORD", "customer_ref": "RESP-TEST-CUST",
        "lines": [{"requested_quantity": 4}],
    }, headers=h)
    order_pk = r.json()["id"]

    r = client.post(f"/api/orders/{order_pk}/allocate", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ALLOCATED"
    assert len(body["lines"]) == 1
    allocations = body["lines"][0]["allocations"]
    assert len(allocations) == 1
    assert allocations[0]["quantity"] == 4
