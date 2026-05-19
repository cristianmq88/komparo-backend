"""Tests de autenticación: registro, login, lockout, reset, verify, perfil."""
from tests.conftest import register_and_login


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


def test_register_login_me_flow(client):
    headers, user = register_and_login(client, "a@x.com")
    assert user["email"] == "a@x.com"
    assert user["email_verified"] is False

    r = client.post("/auth/login", data={"username": "a@x.com", "password": "testpass123"})
    assert r.status_code == 200

    me = client.get("/auth/me", headers=headers).json()
    assert me["email"] == "a@x.com"


def test_register_rejects_short_password(client):
    r = client.post("/auth/register", json={"email": "b@x.com", "password": "short", "name": "B"})
    assert r.status_code == 422


def test_register_rejects_duplicate_email(client):
    register_and_login(client, "c@x.com")
    r = client.post(
        "/auth/register",
        json={"email": "c@x.com", "password": "testpass123", "name": "Dup"},
    )
    assert r.status_code == 400


def test_login_lockout_after_failed_attempts(client):
    register_and_login(client, "lock@x.com")
    # 5 fallidos → debe bloquear al 5º
    statuses = []
    for _ in range(6):
        r = client.post(
            "/auth/login", data={"username": "lock@x.com", "password": "wrong"}
        )
        statuses.append(r.status_code)
    assert statuses.count(401) >= 1
    assert 429 in statuses

    # Incluso con contraseña correcta sigue bloqueado
    r = client.post(
        "/auth/login", data={"username": "lock@x.com", "password": "testpass123"}
    )
    assert r.status_code == 429


def test_forgot_password_is_neutral(client):
    register_and_login(client, "fp@x.com")
    r1 = client.post("/auth/forgot-password", json={"email": "fp@x.com"})
    r2 = client.post("/auth/forgot-password", json={"email": "nope@x.com"})
    # Mismo código y mensaje neutro: no revela qué emails existen
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


def test_reset_password_with_invalid_token(client):
    r = client.post(
        "/auth/reset-password",
        json={"token": "tokeninvalido1234", "new_password": "nueva123pass"},
    )
    assert r.status_code == 400


def test_verify_email_with_invalid_token(client):
    r = client.post("/auth/verify-email", json={"token": "tokeninvalido1234"})
    assert r.status_code == 400


def test_update_profile(client):
    headers, _ = register_and_login(client, "u@x.com")
    r = client.put(
        "/auth/me",
        headers=headers,
        json={"name": "Nuevo Nombre", "city": "Barcelona"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Nuevo Nombre"
    assert body["city"] == "Barcelona"


def test_change_password(client):
    headers, _ = register_and_login(client, "cp@x.com")
    r = client.put(
        "/auth/password",
        headers=headers,
        json={"current_password": "testpass123", "new_password": "nueva12345"},
    )
    assert r.status_code == 200

    # Login con la antigua debe fallar
    r = client.post(
        "/auth/login", data={"username": "cp@x.com", "password": "testpass123"}
    )
    assert r.status_code == 401

    # Login con la nueva debe funcionar
    r = client.post(
        "/auth/login", data={"username": "cp@x.com", "password": "nueva12345"}
    )
    assert r.status_code == 200


def test_change_password_wrong_current(client):
    headers, _ = register_and_login(client, "cpw@x.com")
    r = client.put(
        "/auth/password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "nueva12345"},
    )
    assert r.status_code == 401


def test_delete_account(client):
    headers, _ = register_and_login(client, "del@x.com")
    r = client.request(
        "DELETE", "/auth/me", headers=headers, json={"password": "testpass123"}
    )
    assert r.status_code == 200
    # El token ya no debe funcionar (usuario no existe)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 401


def test_delete_account_wrong_password(client):
    headers, _ = register_and_login(client, "dw@x.com")
    r = client.request(
        "DELETE", "/auth/me", headers=headers, json={"password": "wrong"}
    )
    assert r.status_code == 401


def test_unauthenticated_endpoints_reject(client):
    assert client.get("/auth/me").status_code == 401
    assert client.put("/auth/me", json={"name": "x"}).status_code == 401
    r = client.request("DELETE", "/auth/me", json={"password": "x"})
    assert r.status_code == 401
