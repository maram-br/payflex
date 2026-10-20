from fastapi.testclient import TestClient
from app.main import app, payments

client = TestClient(app)


def setup_function():
    """Vide le stockage avant chaque test pour qu'ils soient indépendants."""
    payments.clear()


# ---------- /health ----------
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------- POST /payments ----------
def test_create_payment_ok():
    r = client.post("/payments", json={"account_id": "A1", "amount": 50.0})
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert body["account_id"] == "A1"
    assert body["amount"] == 50.0
    assert body["currency"] == "EUR"   # valeur par défaut


def test_create_payment_custom_currency():
    r = client.post("/payments", json={"account_id": "A2", "amount": 10, "currency": "USD"})
    assert r.status_code == 201
    assert r.json()["currency"] == "USD"


def test_create_payment_negative_amount():
    r = client.post("/payments", json={"account_id": "A1", "amount": -5})
    assert r.status_code == 400
    assert r.json()["detail"] == "Montant invalide"


def test_create_payment_zero_amount():
    r = client.post("/payments", json={"account_id": "A1", "amount": 0})
    assert r.status_code == 400


def test_create_payment_missing_field():
    r = client.post("/payments", json={"amount": 10})   # account_id manquant
    assert r.status_code == 422


# ---------- GET /payments/{id} ----------
def test_get_existing_payment():
    created = client.post("/payments", json={"account_id": "A1", "amount": 20}).json()
    r = client.get(f"/payments/{created['id']}")
    assert r.status_code == 200
    assert r.json()["amount"] == 20


def test_get_unknown_payment():
    r = client.get("/payments/does-not-exist")
    assert r.status_code == 404
    assert r.json()["detail"] == "Introuvable"