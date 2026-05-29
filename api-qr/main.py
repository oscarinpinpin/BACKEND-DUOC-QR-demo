import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(title="API QR", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/qr_duoc"
)
engine = create_engine(DATABASE_URL)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "api-qr", "status": "ok"}


# ── GET /api/qr/{id} ──────────────────────────────────────────────────────────
# El QR se identifica por su código (ej. "QR-LAB-301"); el path param se llama
# {id} para cumplir el contrato del endpoint.

@app.get("/api/qr/{id}")
def get_qr(id: str, request: Request):
    """
    Recibe el código QR escaneado, valida que exista y esté activo,
    registra el escaneo y devuelve la info de la ubicación.
    """
    codigo = id
    try:
        with engine.connect() as conn:

            # 1. Buscar QR usando la vista completa
            row = conn.execute(
                text("""
                    SELECT
                        qr_id,
                        qr_activo,
                        ubicacion_id,
                        ubicacion_nombre,
                        piso_numero
                    FROM vista_qr_completo
                    WHERE qr_codigo = :codigo
                """),
                {"codigo": codigo}
            ).fetchone()

            # 2. QR no existe
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"QR '{codigo}' no encontrado"
                )

            # 3. QR existe pero está inactivo
            if not row.qr_activo:
                raise HTTPException(
                    status_code=403,
                    detail=f"QR '{codigo}' está desactivado"
                )

            # 4. Registrar escaneo en tabla escaneos
            dispositivo = request.headers.get("User-Agent", None)
            conn.execute(
                text("""
                    INSERT INTO escaneos (qr_id, dispositivo)
                    VALUES (:qr_id, :dispositivo)
                """),
                {"qr_id": row.qr_id, "dispositivo": dispositivo}
            )
            conn.commit()

            # 5. Devolver respuesta que espera el frontend
            return {
                "id":       row.ubicacion_id,
                "ubicacion": row.ubicacion_nombre,
                "piso":     row.piso_numero
            }

    except HTTPException:
        raise

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Error al conectar con la base de datos"
        )
