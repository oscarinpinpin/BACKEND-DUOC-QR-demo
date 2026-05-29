-- ============================================================
--  Sistema QR Inteligente – Duoc UC San Carlos de Apoquindo 2
--  Script de base de datos PostgreSQL
--  Equipo Base de Datos – EA3
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  0. LIMPIEZA (útil para re-ejecutar en desarrollo)
-- ────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS usuarios          CASCADE;
DROP TABLE IF EXISTS escaneos          CASCADE;
DROP TABLE IF EXISTS ubicacion_servicios CASCADE;
DROP TABLE IF EXISTS codigos_qr        CASCADE;
DROP TABLE IF EXISTS servicios         CASCADE;
DROP TABLE IF EXISTS ubicaciones       CASCADE;
DROP TABLE IF EXISTS tipos_espacio     CASCADE;
DROP TABLE IF EXISTS pisos             CASCADE;


-- ────────────────────────────────────────────────────────────
--  1. TABLAS
-- ────────────────────────────────────────────────────────────

-- Pisos del edificio
CREATE TABLE pisos (
    id          SERIAL       PRIMARY KEY,
    numero      INTEGER      NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- Categorías de espacio (sala, laboratorio, baño, etc.)
CREATE TABLE tipos_espacio (
    id     SERIAL      PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    icono  VARCHAR(50)                    -- nombre de ícono (ej. "lab", "classroom")
);

-- Espacios/ubicaciones del edificio
CREATE TABLE ubicaciones (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    descripcion TEXT,
    capacidad   VARCHAR(50),              -- ej. "30 personas"
    piso_id     INTEGER      NOT NULL REFERENCES pisos(id)         ON DELETE RESTRICT,
    tipo_id     INTEGER               REFERENCES tipos_espacio(id) ON DELETE SET NULL
);

-- Códigos QR vinculados a una ubicación
CREATE TABLE codigos_qr (
    id            SERIAL       PRIMARY KEY,
    codigo        VARCHAR(255) NOT NULL UNIQUE,
    ubicacion_id  INTEGER      NOT NULL REFERENCES ubicaciones(id) ON DELETE CASCADE,
    activo        BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en     TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Servicios cercanos (baños, cafetería, fotocopiadora, etc.)
CREATE TABLE servicios (
    id      SERIAL      PRIMARY KEY,
    nombre  VARCHAR(120) NOT NULL,
    tipo    VARCHAR(80),                  -- ej. "sanitario", "alimentacion", "tecnologia"
    piso_id INTEGER REFERENCES pisos(id) ON DELETE SET NULL
);

-- Relación muchos-a-muchos: ubicación ↔ servicios cercanos
CREATE TABLE ubicacion_servicios (
    ubicacion_id INTEGER NOT NULL REFERENCES ubicaciones(id) ON DELETE CASCADE,
    servicio_id  INTEGER NOT NULL REFERENCES servicios(id)   ON DELETE CASCADE,
    PRIMARY KEY (ubicacion_id, servicio_id)
);

-- Usuarios del sistema (autenticación y permisos)
CREATE TABLE usuarios (
    id         SERIAL       PRIMARY KEY,
    username   VARCHAR(80)  NOT NULL UNIQUE,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,          -- hash BCrypt
    rol        VARCHAR(20)  NOT NULL DEFAULT 'USER',  -- 'ADMIN' | 'USER'
    activo     BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Historial de escaneos (opcional, desafío avanzado)
CREATE TABLE escaneos (
    id           SERIAL      PRIMARY KEY,
    qr_id        INTEGER     NOT NULL REFERENCES codigos_qr(id) ON DELETE CASCADE,
    escaneado_en TIMESTAMP   NOT NULL DEFAULT NOW(),
    dispositivo  VARCHAR(200)           -- user-agent del cliente, opcional
);


-- ────────────────────────────────────────────────────────────
--  2. ÍNDICES
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_codigos_qr_codigo      ON codigos_qr(codigo);
CREATE INDEX idx_codigos_qr_ubicacion   ON codigos_qr(ubicacion_id);
CREATE INDEX idx_ubicaciones_piso       ON ubicaciones(piso_id);
CREATE INDEX idx_escaneos_qr            ON escaneos(qr_id);
CREATE INDEX idx_escaneos_fecha         ON escaneos(escaneado_en);
CREATE INDEX idx_usuarios_username      ON usuarios(username);


-- ────────────────────────────────────────────────────────────
--  3. DATOS DE PRUEBA
-- ────────────────────────────────────────────────────────────

-- Pisos
INSERT INTO pisos (numero, nombre, descripcion) VALUES
    (1, 'Primer piso',   'Entrada principal, administración y cafetería'),
    (2, 'Segundo piso',  'Salas de clases y biblioteca'),
    (3, 'Tercer piso',   'Laboratorios de computación'),
    (4, 'Cuarto piso',   'Laboratorios especializados y talleres');

-- Tipos de espacio
INSERT INTO tipos_espacio (nombre, icono) VALUES
    ('Sala de clases',   'classroom'),
    ('Laboratorio',      'lab'),
    ('Biblioteca',       'library'),
    ('Baño',             'restroom'),
    ('Cafetería',        'cafeteria'),
    ('Administración',   'admin'),
    ('Taller',           'workshop');

-- Ubicaciones
INSERT INTO ubicaciones (nombre, descripcion, capacidad, piso_id, tipo_id) VALUES
    ('Sala 201',        'Sala de clases general, proyector y pizarrón',        '35 personas', 2, 1),
    ('Sala 202',        'Sala de clases con mesas grupales',                   '30 personas', 2, 1),
    ('Sala 203',        'Sala de reuniones pequeña',                           '15 personas', 2, 1),
    ('Laboratorio 301', 'Laboratorio de computación, 30 PCs con Linux/Windows','30 personas', 3, 2),
    ('Laboratorio 302', 'Laboratorio de redes y servidores',                   '20 personas', 3, 2),
    ('Laboratorio 401', 'Laboratorio de electrónica y hardware',               '25 personas', 4, 2),
    ('Biblioteca',      'Colección de libros técnicos y sala de estudio',      '50 personas', 2, 3),
    ('Cafetería',       'Servicio de colación y café',                         '80 personas', 1, 5),
    ('Administración',  'Secretaría académica y caja',                         NULL,          1, 6),
    ('Taller 401',      'Taller de fabricación digital y prototipado',         '20 personas', 4, 7);

-- Códigos QR (uno por ubicación)
INSERT INTO codigos_qr (codigo, ubicacion_id) VALUES
    ('QR-SALA-201',    1),
    ('QR-SALA-202',    2),
    ('QR-SALA-203',    3),
    ('QR-LAB-301',     4),
    ('QR-LAB-302',     5),
    ('QR-LAB-401',     6),
    ('QR-BIBLIOTECA',  7),
    ('QR-CAFETERIA',   8),
    ('QR-ADMIN',       9),
    ('QR-TALLER-401', 10);

-- Servicios
INSERT INTO servicios (nombre, tipo, piso_id) VALUES
    ('Baño hombres P1',    'sanitario',    1),
    ('Baño mujeres P1',    'sanitario',    1),
    ('Baño hombres P2',    'sanitario',    2),
    ('Baño mujeres P2',    'sanitario',    2),
    ('Baño hombres P3',    'sanitario',    3),
    ('Baño mujeres P3',    'sanitario',    3),
    ('Cafetería',          'alimentacion', 1),
    ('Fotocopiadora P2',   'tecnologia',   2),
    ('Fotocopiadora P3',   'tecnologia',   3),
    ('Extintor P1',        'seguridad',    1),
    ('Extintor P2',        'seguridad',    2),
    ('Extintor P3',        'seguridad',    3),
    ('Extintor P4',        'seguridad',    4);

-- Servicios cercanos por ubicación
INSERT INTO ubicacion_servicios (ubicacion_id, servicio_id) VALUES
    -- Sala 201 (piso 2)
    (1, 3), (1, 4), (1, 8), (1, 11),
    -- Sala 202 (piso 2)
    (2, 3), (2, 4), (2, 8), (2, 11),
    -- Sala 203 (piso 2)
    (3, 3), (3, 4), (3, 8), (3, 11),
    -- Laboratorio 301 (piso 3)
    (4, 5), (4, 6), (4, 9), (4, 12),
    -- Laboratorio 302 (piso 3)
    (5, 5), (5, 6), (5, 9), (5, 12),
    -- Laboratorio 401 (piso 4)
    (6, 13),
    -- Biblioteca (piso 2)
    (7, 3), (7, 4), (7, 8), (7, 11),
    -- Cafetería (piso 1)
    (8, 1), (8, 2), (8, 10),
    -- Administración (piso 1)
    (9, 1), (9, 2), (9, 10),
    -- Taller 401 (piso 4)
    (10, 13);

-- Escaneos de ejemplo
INSERT INTO escaneos (qr_id, dispositivo) VALUES
    (4, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)'),
    (4, 'Mozilla/5.0 (Android 14; Mobile)'),
    (1, 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5)'),
    (7, 'Mozilla/5.0 (Linux; Android 13)'),
    (4, NULL),
    (2, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1)');


-- ────────────────────────────────────────────────────────────
--  4. VISTAS ÚTILES PARA EL BACKEND
-- ────────────────────────────────────────────────────────────

-- Vista completa de un QR con toda la info de la ubicación
CREATE OR REPLACE VIEW vista_qr_completo AS
SELECT
    cq.codigo              AS qr_codigo,
    cq.id                  AS qr_id,
    cq.activo              AS qr_activo,
    u.id                   AS ubicacion_id,
    u.nombre               AS ubicacion_nombre,
    u.descripcion          AS ubicacion_descripcion,
    u.capacidad,
    p.numero               AS piso_numero,
    p.nombre               AS piso_nombre,
    te.nombre              AS tipo_espacio
FROM codigos_qr cq
JOIN ubicaciones  u  ON cq.ubicacion_id = u.id
JOIN pisos        p  ON u.piso_id       = p.id
LEFT JOIN tipos_espacio te ON u.tipo_id = te.id;

-- Vista de servicios por ubicación
CREATE OR REPLACE VIEW vista_servicios_por_ubicacion AS
SELECT
    u.id            AS ubicacion_id,
    u.nombre        AS ubicacion_nombre,
    s.nombre        AS servicio_nombre,
    s.tipo          AS servicio_tipo,
    p.numero        AS piso_numero
FROM ubicacion_servicios us
JOIN ubicaciones u ON us.ubicacion_id = u.id
JOIN servicios   s ON us.servicio_id  = s.id
JOIN pisos       p ON u.piso_id       = p.id
ORDER BY u.id, s.tipo;

-- Vista de escaneos con info del QR y ubicación
CREATE OR REPLACE VIEW vista_historial_escaneos AS
SELECT
    e.id             AS escaneo_id,
    e.escaneado_en,
    cq.codigo        AS qr_codigo,
    u.nombre         AS ubicacion,
    p.numero         AS piso,
    e.dispositivo
FROM escaneos   e
JOIN codigos_qr cq ON e.qr_id         = cq.id
JOIN ubicaciones u ON cq.ubicacion_id = u.id
JOIN pisos       p ON u.piso_id       = p.id
ORDER BY e.escaneado_en DESC;


-- ────────────────────────────────────────────────────────────
--  5. CONSULTAS DE VERIFICACIÓN
-- ────────────────────────────────────────────────────────────
-- Descomenta para probar:

-- SELECT * FROM vista_qr_completo WHERE qr_codigo = 'QR-LAB-301';
-- SELECT * FROM vista_servicios_por_ubicacion WHERE ubicacion_id = 4;
-- SELECT * FROM vista_historial_escaneos LIMIT 10;
-- SELECT COUNT(*) FROM escaneos GROUP BY qr_id ORDER BY count DESC;
