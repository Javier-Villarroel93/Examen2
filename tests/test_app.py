import pytest

from app import USER_STORE, app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_users():
    USER_STORE.clear()
    yield
    USER_STORE.clear()


def test_health(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ok"


def test_expression_calc(client):
    rv = client.post("/api/calc", json={"input": "2 + 3 * 4"})
    assert rv.status_code == 200
    payload = rv.get_json()
    assert payload["mode"] == "expression"
    assert payload["result"] == 14


def test_nlp_calc(client):
    rv = client.post("/api/calc", json={"input": "suma 5 y 7"})
    assert rv.status_code == 200
    payload = rv.get_json()
    assert payload["mode"] == "nlp"
    assert payload["result"] == 12


def test_invalid_input(client):
    rv = client.post("/api/calc", json={"input": "esta frase no tiene numeros"})
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_register_and_login(client):
    reg = client.post("/api/register", json={"username": "ana", "password": "secreto"})
    assert reg.status_code == 201
    assert reg.get_json()["username"] == "ana"

    login = client.post("/api/login", json={"username": "ana", "password": "secreto"})
    assert login.status_code == 200
    payload = login.get_json()
    assert payload["username"] == "ana"
    assert "token" in payload


def test_register_duplicate(client):
    first = client.post("/api/register", json={"username": "pepe", "password": "clave123"})
    assert first.status_code == 201
    dup = client.post("/api/register", json={"username": "pepe", "password": "clave123"})
    assert dup.status_code == 400
    assert "error" in dup.get_json()


def test_login_fails_for_unknown_user(client):
    login = client.post("/api/login", json={"username": "ghost", "password": "clave123"})
    assert login.status_code == 401
    assert "error" in login.get_json()
