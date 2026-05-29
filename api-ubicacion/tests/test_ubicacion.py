from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "api-ubicacion"


def test_get_ubicaciones_empty():
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.fetchall.return_value = []

    with patch("main.engine.connect", return_value=mock_conn):
        response = client.get("/api/ubicaciones")
    assert response.status_code == 200
    assert response.json() == []


def test_ubicacion_not_found():
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.fetchone.return_value = None

    with patch("main.engine.connect", return_value=mock_conn):
        response = client.get("/api/ubicaciones/9999")
    assert response.status_code == 404


def test_ubicacion_found():
    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.nombre = "Laboratorio 301"
    mock_row.piso = 3
    mock_row.descripcion = "Laboratorio de computación"
    mock_row.qr_code = "QR-LAB-301"

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.fetchone.return_value = mock_row

    with patch("main.engine.connect", return_value=mock_conn):
        response = client.get("/api/ubicaciones/1")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Laboratorio 301"
