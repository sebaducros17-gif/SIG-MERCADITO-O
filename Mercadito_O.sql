USE mercadito_o;

CREATE TABLE IF NOT EXISTS gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME,
    usuario VARCHAR(50),
    concepto VARCHAR(150), 
    monto DECIMAL(10, 2)
);

USE mercadito_o;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE,
    password VARCHAR(50),
    rol VARCHAR(20)
);


INSERT IGNORE INTO usuarios (usuario, password, rol) VALUES ('admin', 'admin', 'Administrador');
INSERT IGNORE INTO usuarios (usuario, password, rol) VALUES ('cajero1', '1234', 'Cajero');
INSERT IGNORE INTO usuarios (usuario, password, rol) VALUES ('cajero2', '5678', 'Cajero');

USE mercadito_o;

-- 1. TABLA USUARIOS (Para el Login)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE,
    password VARCHAR(50),
    rol VARCHAR(20)
);

-- 2. INSERTAR USUARIO ADMIN 

INSERT IGNORE INTO usuarios (usuario, password, rol) VALUES ('admin', 'admin', 'Administrador');
INSERT IGNORE INTO usuarios (usuario, password, rol) VALUES ('cajero1', '1234', 'Cajero');

-- 3. TABLA GASTOS (Para la pestaña nueva)
CREATE TABLE IF NOT EXISTS gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME,
    usuario VARCHAR(50),
    concepto VARCHAR(150),
    categoria VARCHAR(50),
    monto DECIMAL(10, 2)
);

-- 4. TABLA CORTE DE CAJA (Para el cierre)
CREATE TABLE IF NOT EXISTS corte_caja (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME,
    usuario VARCHAR(50),
    ventas_sistema DECIMAL(10,2),
    dinero_real DECIMAL(10,2),
    diferencia DECIMAL(10,2)
);
