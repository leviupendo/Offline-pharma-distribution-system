from fastapi.testclient import TestClient

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.main import app
from app.models.models import Product, Role, User

client = TestClient(app)


def _ensure_seed_user():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "test_admin").first():
            db.add(
                User(
                    username="test_admin",
                    password_hash=hash_password("TestPassword!123"),
                    role=Role.SYSTEM_ADMIN,
                )
            )
        if not db.query(Product).filter(Product.code == "TEST-001").first():
            db.add(
                Product(
                    code="TEST-001",
                    name="Test Product",
                    packaging_type="UNIT_DOSE_PACKET",
                    standard_fill_weight_grams=1.0,
                )
            )
        db.commit()
    finally:
        db.close()


def test_login_succeeds_and_issues_usable_token():
    _ensure_seed_user()

    response = client.post(
        "/api/auth/login",
        json={"username": "test_admin", "password": "TestPassword!123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["role"] == "SYSTEM_ADMIN"

    # The token must actually work against a protected route, not just
    # be returned. This is the check that catches settings/config drift
    # between token issuance and token verification.
    protected = client.get(
        "/api/products/",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert protected.status_code == 200


def test_login_rejects_wrong_password():
    _ensure_seed_user()

    response = client.post(
        "/api/auth/login",
        json={"username": "test_admin", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_route_rejects_missing_token():
    response = client.get("/api/products/")
    assert response.status_code in (401, 403)


def test_protected_route_rejects_garbage_token():
    response = client.get(
        "/api/products/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_account_locks_after_max_attempts_and_unlocks_after_expiry():
    """Regression: after 5 failed logins set locked_until on the user
    row, the *next* login attempt (even with the correct password)
    crashed with a 500 — "can't compare offset-naive and offset-aware
    datetimes" — because SQLite drops the tz offset on
    DateTime(timezone=True) columns across a round trip, so the
    freshly-reloaded locked_until came back naive while
    datetime.now(timezone.utc) is aware.
    """
    import datetime as dt_module
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models.models import Role, User

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "lockout_test_user").first():
            db.add(User(
                username="lockout_test_user",
                password_hash=hash_password("RealPassword!123"),
                role=Role.WAREHOUSE,
            ))
            db.commit()
    finally:
        db.close()

    for _ in range(5):
        r = client.post("/api/auth/login", json={"username": "lockout_test_user", "password": "wrong"})
        assert r.status_code == 401

    # Previously this line raised an unhandled 500 instead of a clean 423.
    r = client.post("/api/auth/login", json={"username": "lockout_test_user", "password": "RealPassword!123"})
    assert r.status_code == 423

    # Backdate the lockout to simulate it having expired, then confirm
    # a normal login succeeds again afterward.
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "lockout_test_user").first()
        user.locked_until = dt_module.datetime.now(dt_module.timezone.utc) - dt_module.timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"username": "lockout_test_user", "password": "RealPassword!123"})
    assert r.status_code == 200
