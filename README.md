# Sistema QR Inteligente — Duoc UC San Carlos de Apoquindo 2

Proyecto EA3 · Software Factory FullStack · Arquitectura de Microservicios

## Estructura del proyecto

```
qr-duoc-sca2//
├── docker-compose.yml
├── .env.example
├── database/
│   └── init.sql              # Esquema y datos semilla
├── api-qr/                   # Microservicio QR OFICIAL — FastAPI + JWT (puerto 8001)
│   ├── main.py               #   GET /api/qr/{id} + login/usuarios/permisos
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/                #   test_qr.py + test_auth.py
├── backend/                  # [ALTERNATIVA] Mismo servicio en Java/Spring Boot
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/                  # cl.duoc.qr_service (no se usa en docker-compose)
├── api-ubicacion/            # Microservicio Ubicación — Python/FastAPI (puerto 8002)
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
└── frontend/                 # React + Vite (puerto 5173)
    ├── index.html
    ├── vite.config.js
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── App.jsx
        ├── App.css
        └── pages/
            ├── Home.jsx
            ├── Scanner.jsx
            ├── RoomInfo.jsx
            └── ErrorQR.jsx
```

## Levantar con Docker Compose

```bash
# Copiar variables de entorno
cp .env.example .env

# Construir e iniciar todos los servicios
docker compose up --build
```

| Servicio       | URL                          |
|----------------|------------------------------|
| Frontend       | http://localhost:5173        |
| API QR         | http://localhost:8001/docs   |
| API Ubicación  | http://localhost:8002/docs   |
| PostgreSQL     | localhost:5432               |

## Endpoints

### API QR (FastAPI · puerto 8001)
| Método | Ruta                  | Acceso            | Descripción                                  |
|--------|-----------------------|-------------------|----------------------------------------------|
| GET    | `/`                   | Público           | Estado del servicio                          |
| GET    | `/api/qr/{id}`        | Público           | Valida el QR y retorna id, ubicación y piso  |
| POST   | `/api/auth/login`     | Público           | Login; retorna un token JWT                  |
| GET    | `/api/usuarios/me`    | Autenticado       | Perfil del usuario del token                 |
| GET    | `/api/usuarios`       | Solo **ADMIN**    | Lista de usuarios                            |
| POST   | `/api/usuarios`       | Solo **ADMIN**    | Crea un usuario                              |

**Autenticación:** envía el token en la cabecera `Authorization: Bearer <token>`.
Usuarios de prueba (creados automáticamente al arrancar): `admin` / `admin123` (ADMIN) y `usuario` / `user123` (USER).

### API Ubicación (Python/FastAPI · puerto 8002)
| Método | Ruta                    | Descripción                        |
|--------|-------------------------|------------------------------------|
| GET    | `/api/ubicaciones`      | Lista todas las ubicaciones        |
| GET    | `/api/ubicaciones/{id}` | Detalle de una ubicación           |

## Ejecutar tests

API QR (Python) — incluye tests de QR y de autenticación:
```bash
cd api-qr
pip install -r requirements.txt
pytest tests/
```

API Ubicación (Python):
```bash
cd api-ubicacion
pip install -r requirements.txt
pytest tests/
```

Alternativa Java (Spring Boot, requiere JDK 21):
```bash
cd backend
./mvnw test          # en Windows: .\mvnw.cmd test
```

## Stack tecnológico

- **Frontend:** React 18 + Vite + html5-qrcode
- **API QR (oficial):** Python 3.11 + FastAPI + SQLAlchemy + PyJWT + bcrypt
- **API Ubicación:** Python 3.11 + FastAPI + SQLAlchemy
- **Alternativa QR:** Java 21 + Spring Boot 3.3 + Spring Security + JWT (jjwt)
- **Base de datos:** PostgreSQL 15
- **DevOps:** Docker + Docker Compose
- **Testing:** Pytest (Python) · JUnit 5 + Spring Test (Java)
