import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

app = FastAPI(title="API Ubicación", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/qr_duoc")
engine = create_engine(DATABASE_URL)


@app.get("/")
def root():
    return {"service": "api-ubicacion", "status": "ok"}


# El número de piso vive en la tabla "pisos" (via piso_id) y el código QR
# en la tabla "codigos_qr". Se resuelven con JOINs manteniendo la misma
# forma de respuesta: id, nombre, piso, descripcion, qr_code.
_BASE_QUERY = """
    SELECT u.id,
           u.nombre,
           p.numero      AS piso,
           u.descripcion,
           cq.codigo     AS qr_code
    FROM ubicaciones u
    JOIN pisos        p  ON u.piso_id = p.id
    LEFT JOIN codigos_qr cq ON cq.ubicacion_id = u.id
"""


@app.get("/api/ubicaciones")
def get_ubicaciones():
    with engine.connect() as conn:
        rows = conn.execute(
            text(_BASE_QUERY + " ORDER BY p.numero, u.nombre")
        ).fetchall()
    return [
        {"id": r.id, "nombre": r.nombre, "piso": r.piso, "descripcion": r.descripcion, "qr_code": r.qr_code}
        for r in rows
    ]


@app.get("/api/ubicaciones/{id}")
def get_ubicacion(id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text(_BASE_QUERY + " WHERE u.id = :id"),
            {"id": id},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    return {"id": row.id, "nombre": row.nombre, "piso": row.piso, "descripcion": row.descripcion, "qr_code": row.qr_code}
