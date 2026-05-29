import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


# ── Helper: construir mock de conexión ───────────────────────────────────────

def make_mock_conn(fetchone_result):
    """Crea un mock de engine.connect() que retorna fetchone_result."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.fetchone.return_value = fetchone_result
    return mock_conn


# ── Test 1: Health check ──────────────────────────────────────────────────────

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "api-qr"
    assert response.json()["status"] == "ok"


# ── Test 2: QR válido → retorna id, ubicacion, piso ──────────────────────────

def test_qr_valido():
    mock_row = MagicMock()
    mock_row.qr_id        = 4
    mock_row.qr_activo    = True
    mock_row.ubicacion_id = 4
    mock_row.ubicacion_nombre = "Laboratorio 301"
    mock_row.piso_numero  = 3

    with patch("main.engine.connect", return_value=make_mock_conn(mock_row)):
        response = client.get("/api/qr/QR-LAB-301")

    assert response.status_code == 200
    data = response.json()
    assert data["id"]       == 4
    assert data["ubicacion"] == "Laboratorio 301"
    assert data["piso"]     == 3


# ── Test 3: QR no existe → 404 ───────────────────────────────────────────────

def test_qr_no_encontrado():
    with patch("main.engine.connect", return_value=make_mock_conn(None)):
        response = client.get("/api/qr/QR-INVALIDO")

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


# ── Test 4: QR inactivo → 403 ────────────────────────────────────────────────

def test_qr_inactivo():
    mock_row = MagicMock()
    mock_row.qr_id        = 1
    mock_row.qr_activo    = False   # ← desactivado
    mock_row.ubicacion_id = 1
    mock_row.ubicacion_nombre = "Sala 201"
    mock_row.piso_numero  = 2

    with patch("main.engine.connect", return_value=make_mock_conn(mock_row)):
        response = client.get("/api/qr/QR-SALA-201")

    assert response.status_code == 403
    assert "desactivado" in response.json()["detail"]


# ── Test 5: Error de base de datos → 500 ─────────────────────────────────────

def test_error_base_de_datos():
    from sqlalchemy.exc import SQLAlchemyError

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__  = MagicMock(return_value=False)
    mock_conn.execute.side_effect = SQLAlchemyError("fallo de conexión")

    with patch("main.engine.connect", return_value=mock_conn):
        response = client.get("/api/qr/QR-LAB-301")

    assert response.status_code == 500
    assert "base de datos" in response.json()["detail"]