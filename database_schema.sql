-- =============================================================================
-- ESTRUCTURA DE BASE DE DATOS PARA ALGORITMO GENÉTICO
-- =============================================================================
-- Este script crea la estructura necesaria para el algoritmo genético
-- Ejecuta este script en MySQL Workbench o línea de comandos

-- Crear base de datos (opcional, cámbiala por el nombre que prefieras)
CREATE DATABASE IF NOT EXISTS evaluaciones_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE evaluaciones_db;

-- =============================================================================
-- TABLA: Usuario
-- =============================================================================
CREATE TABLE IF NOT EXISTS Usuario (
    idUser INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(40) NOT NULL,
    curp VARCHAR(20) UNIQUE,
    fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_usuario (usuario),
    INDEX idx_curp (curp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- TABLA: Habilidad
-- =============================================================================
CREATE TABLE IF NOT EXISTS Habilidad (
    idHabilidad INT PRIMARY KEY AUTO_INCREMENT,
    habilidad VARCHAR(50) NOT NULL,
    descripcion TEXT,
    activa BOOLEAN DEFAULT TRUE,
    fechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_habilidad (habilidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- TABLA: Reactivo
-- =============================================================================
CREATE TABLE IF NOT EXISTS Reactivo (
    idReactivo INT PRIMARY KEY AUTO_INCREMENT,
    reactivo VARCHAR(30) NOT NULL,
    descripcion TEXT,
    dificultad ENUM('Fácil', 'Medio', 'Difícil') DEFAULT 'Medio',
    activo BOOLEAN DEFAULT TRUE,
    fechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reactivo (reactivo),
    INDEX idx_dificultad (dificultad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- TABLA: Evaluacion
-- =============================================================================
CREATE TABLE IF NOT EXISTS Evaluacion (
    idEvaluacion INT PRIMARY KEY AUTO_INCREMENT,
    idUser INT NOT NULL,
    idHabilidad INT NOT NULL,
    idReactivo INT NOT NULL,
    calificacion DECIMAL(5,2) NOT NULL CHECK (calificacion >= 0 AND calificacion <= 10),
    fechaEvaluacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tiempoRespuesta INT NOT NULL DEFAULT 0, -- tiempo en segundos
    intentos INT DEFAULT 1,
    observaciones TEXT,
    
    -- Claves foráneas
    FOREIGN KEY (idUser) REFERENCES Usuario(idUser) ON DELETE CASCADE,
    FOREIGN KEY (idHabilidad) REFERENCES Habilidad(idHabilidad) ON DELETE CASCADE,
    FOREIGN KEY (idReactivo) REFERENCES Reactivo(idReactivo) ON DELETE CASCADE,
    
    -- Índices para mejorar rendimiento
    INDEX idx_user_habilidad (idUser, idHabilidad),
    INDEX idx_calificacion (calificacion),
    INDEX idx_fecha (fechaEvaluacion),
    INDEX idx_habilidad_calificacion (idHabilidad, calificacion),
    INDEX idx_user_fecha (idUser, fechaEvaluacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- DATOS DE EJEMPLO (OPCIONAL)
-- =============================================================================
-- Descomenta y ejecuta esta sección si quieres datos de prueba

/*
-- Insertar usuarios de ejemplo
INSERT INTO Usuario (usuario, curp) VALUES
('Juan Pérez', 'PEJR900101HDFRRN01'),
('María García', 'GAMA850615MDFRRR02'),
('Carlos López', 'LOPC920330HDFPPR03'),
('Ana Rodríguez', 'RODA880720MDFDRN04'),
('Luis Martínez', 'MALR910512HDFRRR05'),
('Sofia Hernández', 'HESO930804MDFRRR06'),
('Miguel Torres', 'TOMI870925HDFRRR07'),
('Laura Flores', 'FLOL940218MDFRRR08'),
('David Silva', 'SILD860707HDFRRR09'),
('Carmen Jiménez', 'JICR910403MDFRRR10');

-- Insertar habilidades de ejemplo
INSERT INTO Habilidad (habilidad, descripcion) VALUES
('Matemáticas', 'Operaciones básicas y resolución de problemas matemáticos'),
('Comprensión Lectora', 'Capacidad de entender y analizar textos escritos'),
('Lógica', 'Razonamiento lógico y resolución de problemas'),
('Ciencias Naturales', 'Conocimientos básicos de biología, física y química'),
('Historia', 'Conocimientos de eventos históricos importantes'),
('Geografía', 'Conocimientos de geografía mundial y nacional'),
('Inglés', 'Comprensión y uso del idioma inglés'),
('Programación', 'Conceptos básicos de programación y algoritmos');

-- Insertar reactivos de ejemplo
INSERT INTO Reactivo (reactivo, descripcion, dificultad) VALUES
('Suma básica', 'Operaciones de suma con números enteros', 'Fácil'),
('Multiplicación', 'Operaciones de multiplicación básica', 'Fácil'),
('Ecuaciones lineales', 'Resolución de ecuaciones de primer grado', 'Medio'),
('Geometría', 'Cálculo de áreas y perímetros', 'Medio'),
('Álgebra avanzada', 'Ecuaciones cuadráticas y sistemas', 'Difícil'),
('Texto narrativo', 'Comprensión de textos narrativos', 'Fácil'),
('Texto expositivo', 'Análisis de textos informativos', 'Medio'),
('Texto argumentativo', 'Evaluación de argumentos y conclusiones', 'Difícil'),
('Silogismos', 'Razonamiento deductivo básico', 'Medio'),
('Paradojas lógicas', 'Resolución de paradojas complejas', 'Difícil');

-- Insertar evaluaciones de ejemplo (esto generará muchos registros)
-- Se pueden usar procedimientos almacenados para generar más datos
INSERT INTO Evaluacion (idUser, idHabilidad, idReactivo, calificacion, tiempoRespuesta) VALUES
(1, 1, 1, 8.5, 120),
(1, 1, 2, 7.2, 180),
(1, 2, 6, 6.8, 240),
(2, 1, 1, 9.2, 90),
(2, 1, 3, 5.5, 300),
(2, 3, 9, 7.8, 150),
(3, 2, 7, 4.2, 420),
(3, 1, 4, 6.5, 200),
(4, 3, 10, 3.8, 480),
(5, 1, 5, 2.1, 600);
*/

-- =============================================================================
-- VISTAS ÚTILES PARA ANÁLISIS
-- =============================================================================

-- Vista para estadísticas por habilidad
CREATE OR REPLACE VIEW vw_estadisticas_habilidad AS
SELECT 
    h.idHabilidad,
    h.habilidad,
    COUNT(e.idEvaluacion) as total_evaluaciones,
    ROUND(AVG(e.calificacion), 2) as promedio_calificacion,
    ROUND(MIN(e.calificacion), 2) as min_calificacion,
    ROUND(MAX(e.calificacion), 2) as max_calificacion,
    ROUND(STDDEV(e.calificacion), 2) as desviacion_estandar,
    COUNT(DISTINCT e.idUser) as usuarios_evaluados
FROM Habilidad h
LEFT JOIN Evaluacion e ON h.idHabilidad = e.idHabilidad
GROUP BY h.idHabilidad, h.habilidad
ORDER BY h.habilidad;

-- Vista para peores calificaciones por habilidad
CREATE OR REPLACE VIEW vw_peores_calificaciones AS
SELECT 
    h.habilidad,
    u.usuario,
    r.reactivo,
    e.calificacion,
    e.tiempoRespuesta,
    e.fechaEvaluacion,
    RANK() OVER (PARTITION BY h.idHabilidad ORDER BY e.calificacion ASC) as ranking_peor
FROM Evaluacion e
INNER JOIN Usuario u ON e.idUser = u.idUser
INNER JOIN Habilidad h ON e.idHabilidad = h.idHabilidad
INNER JOIN Reactivo r ON e.idReactivo = r.idReactivo
ORDER BY h.habilidad, e.calificacion ASC;

-- =============================================================================
-- PROCEDIMIENTOS ALMACENADOS ÚTILES
-- =============================================================================

-- Procedimiento para generar datos de prueba
DELIMITER //
CREATE PROCEDURE GenerarDatosPrueba()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE j INT DEFAULT 1;
    DECLARE usuario_id INT;
    DECLARE habilidad_id INT;
    DECLARE reactivo_id INT;
    DECLARE calificacion_random DECIMAL(5,2);
    DECLARE tiempo_random INT;
    
    -- Generar evaluaciones aleatorias
    WHILE i <= 10 DO -- 10 usuarios
        SET j = 1;
        WHILE j <= 50 DO -- 50 evaluaciones por usuario
            SET usuario_id = i;
            SET habilidad_id = FLOOR(1 + RAND() * 8); -- Asumiendo 8 habilidades
            SET reactivo_id = FLOOR(1 + RAND() * 10); -- Asumiendo 10 reactivos
            SET calificacion_random = ROUND(RAND() * 10, 2);
            SET tiempo_random = FLOOR(60 + RAND() * 480); -- Entre 60 y 540 segundos
            
            INSERT INTO Evaluacion (idUser, idHabilidad, idReactivo, calificacion, tiempoRespuesta)
            VALUES (usuario_id, habilidad_id, reactivo_id, calificacion_random, tiempo_random);
            
            SET j = j + 1;
        END WHILE;
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

-- =============================================================================
-- CONSULTAS DE VERIFICACIÓN
-- =============================================================================

-- Verificar estructura de tablas
-- SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH 
-- FROM information_schema.TABLES 
-- WHERE TABLE_SCHEMA = 'evaluaciones_db';

-- Verificar integridad referencial
-- SELECT 
--     'Evaluaciones sin usuario' as problema,
--     COUNT(*) as cantidad
-- FROM Evaluacion e 
-- LEFT JOIN Usuario u ON e.idUser = u.idUser 
-- WHERE u.idUser IS NULL
-- UNION ALL
-- SELECT 
--     'Evaluaciones sin habilidad' as problema,
--     COUNT(*) as cantidad
-- FROM Evaluacion e 
-- LEFT JOIN Habilidad h ON e.idHabilidad = h.idHabilidad 
-- WHERE h.idHabilidad IS NULL
-- UNION ALL
-- SELECT 
--     'Evaluaciones sin reactivo' as problema,
--     COUNT(*) as cantidad
-- FROM Evaluacion e 
-- LEFT JOIN Reactivo r ON e.idReactivo = r.idReactivo 
-- WHERE r.idReactivo IS NULL;

-- =============================================================================
-- NOTAS FINALES
-- =============================================================================
-- 1. Asegúrate de que el usuario de MySQL tenga permisos SELECT sobre estas tablas
-- 2. Para mejor rendimiento, considera añadir más índices según tus consultas frecuentes
-- 3. Los datos de ejemplo son opcionales - descoméntalos si los necesitas
-- 4. Ejecuta CALL GenerarDatosPrueba(); para crear evaluaciones aleatorias