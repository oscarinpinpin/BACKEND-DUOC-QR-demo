import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
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

# ── Configuración JWT ───────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "duoc-qr-secret-cambia-esto-en-produccion-1234567890")
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "86400"))  # 24 h

security = HTTPBearer(auto_error=False)


# ── Helpers de contraseña (bcrypt) ──────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


# ── Helpers JWT ─────────────────────────────────────────────────────────────

def create_token(username: str, rol: str) -> str:
    payload = {
        "sub": username,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_EXP_SECONDS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Valida el JWT del header Authorization: Bearer <token>."""
    if creds is None:
        raise HTTPException(status_code=401, detail="No autenticado. Token ausente.")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return {"username": payload.get("sub"), "rol": payload.get("rol")}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Exige que el usuario autenticado tenga rol ADMIN."""
    if user.get("rol") != "ADMIN":
        raise HTTPException(status_code=403, detail="No tienes permisos para este recurso.")
    return user


# ── Modelos de petición ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    rol: str | None = None  # "ADMIN" | "USER" (por defecto USER)


# ── Seeding de usuarios por defecto al arrancar ─────────────────────────────

def _seed_usuarios() -> None:
    with engine.begin() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        if total and total > 0:
            return
        defaults = [
            ("admin", "admin@duoc.cl", "admin123", "ADMIN"),
            ("usuario", "usuario@duoc.cl", "user123", "USER"),
        ]
        for username, email, password, rol in defaults:
            conn.execute(
                text("""
                    INSERT INTO usuarios (username, email, password, rol, activo)
                    VALUES (:u, :e, :p, :r, TRUE)
                """),
                {"u": username, "e": email, "p": hash_password(password), "r": rol},
            )


@app.on_event("startup")
def on_startup() -> None:
    try:
        _seed_usuarios()
    except Exception as exc:  # no frenar el arranque si la BD aún no está lista
        print(f"[seed] aviso: no se pudieron crear los usuarios por defecto: {exc}")


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


# ── POST /api/auth/login ────────────────────────────────────────────────────

@app.post("/api/auth/login")
def login(req: LoginRequest):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT username, password, rol, activo FROM usuarios WHERE username = :u"),
            {"u": req.username},
        ).fetchone()

    if not row or not row.activo or not verify_password(req.password, row.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")

    token = create_token(row.username, row.rol)
    return {"token": token, "tipo": "Bearer", "username": row.username, "rol": row.rol}


# ── Usuarios ──────────────────────────────────────────────────────────────────

@app.get("/api/usuarios")
def listar_usuarios(_: dict = Depends(require_admin)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, username, email, rol FROM usuarios ORDER BY id")
        ).fetchall()
    return [
        {"id": r.id, "username": r.username, "email": r.email, "rol": r.rol}
        for r in rows
    ]


@app.get("/api/usuarios/me")
def mi_perfil(user: dict = Depends(get_current_user)):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, email, rol FROM usuarios WHERE username = :u"),
            {"u": user["username"]},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"id": row.id, "username": row.username, "email": row.email, "rol": row.rol}


@app.post("/api/usuarios", status_code=201)
def crear_usuario(req: RegisterRequest, _: dict = Depends(require_admin)):
    rol = (req.rol or "USER").upper()
    with engine.begin() as conn:
        existe = conn.execute(
            text("SELECT 1 FROM usuarios WHERE username = :u"),
            {"u": req.username},
        ).fetchone()
        if existe:
            raise HTTPException(status_code=409, detail=f"El usuario '{req.username}' ya existe.")

        row = conn.execute(
            text("""
                INSERT INTO usuarios (username, email, password, rol, activo)
                VALUES (:u, :e, :p, :r, TRUE)
                RETURNING id, username, email, rol
            """),
            {"u": req.username, "e": req.email, "p": hash_password(req.password), "r": rol},
        ).fetchone()

    return {"id": row.id, "username": row.username, "email": row.email, "rol": row.rol}
