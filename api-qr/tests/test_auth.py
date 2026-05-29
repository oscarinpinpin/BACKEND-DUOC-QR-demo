import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import bcrypt

import main
from main import app, create_token

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def mock_conn_fetchone(result):
    m = MagicMock()
    m.__enter__ = lambda s: s
    m.__exit__ = MagicMock(return_value=False)
    m.execute.return_value.fetchone.return_value = result
    return m


def mock_conn_fetchall(rows):
    m = MagicMock()
    m.__enter__ = lambda s: s
    m.__exit__ = MagicMock(return_value=False)
    m.execute.return_value.fetchall.return_value = rows
    return m


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_ok():
    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    row = MagicMock(username="admin", password=hashed, rol="ADMIN", activo=True)

    with patch("main.engine.connect", return_value=mock_conn_fetchone(row)):
        res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    assert res.status_code == 200
    data = res.json()
    assert data["token"]
    assert data["tipo"] == "Bearer"
    assert data["rol"] == "ADMIN"


def test_login_password_incorrecta():
    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    row = MagicMock(username="admin", password=hashed, rol="ADMIN", activo=True)

    with patch("main.engine.connect", return_value=mock_conn_fetchone(row)):
        res = client.post("/api/auth/login", json={"username": "admin", "password": "incorrecta"})

    assert res.status_code == 401


def test_login_usuario_inexistente():
    with patch("main.engine.connect", return_value=mock_conn_fetchone(None)):
        res = client.post("/api/auth/login", json={"username": "fantasma", "password": "x"})

    assert res.status_code == 401


# ── Permisos sobre /api/usuarios ───────────────────────────────────────────────

def test_usuarios_sin_token():
    res = client.get("/api/usuarios")
    assert res.status_code == 401


def test_usuarios_como_user_prohibido():
    token = create_token("usuario", "USER")
    res = client.get("/api/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_usuarios_como_admin():
    token = create_token("admin", "ADMIN")
    rows = [MagicMock(id=1, username="admin", email="admin@duoc.cl", rol="ADMIN")]

    with patch("main.engine.connect", return_value=mock_conn_fetchall(rows)):
        res = client.get("/api/usuarios", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert res.json()[0]["username"] == "admin"


def test_perfil_propio():
    token = create_token("usuario", "USER")
    row = MagicMock(id=2, username="usuario", email="usuario@duoc.cl", rol="USER")

    with patch("main.engine.connect", return_value=mock_conn_fetchone(row)):
        res = client.get("/api/usuarios/me", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res.json()["username"] == "usuario"
    assert res.json()["rol"] == "USER"


def test_token_invalido():
    res = client.get("/api/usuarios/me", headers={"Authorization": "Bearer token-falso"})
    assert res.status_code == 401
