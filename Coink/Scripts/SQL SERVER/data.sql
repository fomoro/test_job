-- Insertar países
INSERT INTO Paises (Nombre) VALUES
('Colombia'),
('Estados Unidos'),
('México');

-- Insertar departamentos para Colombia
INSERT INTO Departamentos (Nombre, PaisId) VALUES
('Antioquia', 1),
('Cundinamarca', 1),
('Valle del Cauca', 1),
('Atlántico', 1),
('Bolívar', 1);

-- Insertar departamentos para Estados Unidos
INSERT INTO Departamentos (Nombre, PaisId) VALUES
('California', 2),
('Texas', 2),
('Florida', 2),
('New York', 2),
('Illinois', 2);

-- Insertar departamentos para México
INSERT INTO Departamentos (Nombre, PaisId) VALUES
('CDMX', 3),
('Jalisco', 3),
('Nuevo León', 3),
('Puebla', 3),
('Yucatán', 3);

-- Insertar municipios para cada departamento de Colombia
INSERT INTO Municipios (Nombre, DepartamentoId) VALUES
-- Antioquia
('Medellín', 1),
('Bello', 1),
-- Cundinamarca
('Bogotá', 2),
('Soacha', 2),
-- Valle del Cauca
('Cali', 3),
('Palmira', 3),
-- Atlántico
('Barranquilla', 4),
('Soledad', 4),
-- Bolívar
('Cartagena', 5),
('Magangué', 5);

-- Insertar municipios para cada departamento de Estados Unidos
INSERT INTO Municipios (Nombre, DepartamentoId) VALUES
-- California
('Los Angeles', 6),
('San Francisco', 6),
-- Texas
('Houston', 7),
('Dallas', 7),
-- Florida
('Miami', 8),
('Orlando', 8),
-- New York
('New York City', 9),
('Buffalo', 9),
-- Illinois
('Chicago', 10),
('Springfield', 10);

-- Insertar municipios para cada departamento de México
INSERT INTO Municipios (Nombre, DepartamentoId) VALUES
-- CDMX
('CDMX', 11),
('Coyoacán', 11),
-- Jalisco
('Guadalajara', 12),
('Zapopan', 12),
-- Nuevo León
('Monterrey', 13),
('San Nicolás', 13),
-- Puebla
('Puebla', 14),
('Tehuacán', 14),
-- Yucatán
('Mérida', 15),
('Valladolid', 15);

-- Insertar usuarios para Colombia
INSERT INTO Usuarios (Nombre, Telefono, Direccion, MunicipioId) VALUES
('Juan Pérez', '3001234567', 'Calle 123, Medellín', 1),
('Ana Gómez', '3002345678', 'Calle 456, Bello', 2),
('Carlos Rodríguez', '3003456789', 'Calle 789, Bogotá', 3),
('Sofía Fernández', '3004567890', 'Calle 101, Cali', 4),
('Miguel Ramírez', '3005678901', 'Calle 202, Barranquilla', 5);

-- Insertar usuarios para Estados Unidos
INSERT INTO Usuarios (Nombre, Telefono, Direccion, MunicipioId) VALUES
('John Doe', '4081234567', '123 Main St, Los Angeles', 6),
('Jane Smith', '4082345678', '456 Oak St, San Francisco', 7),
('Alice Johnson', '5123456789', '789 Pine St, Houston', 8),
('Bob Brown', '5124567890', '101 Maple St, Dallas', 9),
('Emily White', '3055678901', '202 Elm St, Miami', 10);

-- Insertar usuarios para México
INSERT INTO Usuarios (Nombre, Telefono, Direccion, MunicipioId) VALUES
('José Martínez', '5512345678', 'Av. Reforma, CDMX', 11),
('María López', '5533456789', 'Calle 12, Coyoacán', 12),
('Carlos Sánchez', '5554567890', 'Avenida 1, Guadalajara', 13),
('Laura Pérez', '5555678901', 'Calle 34, Zapopan', 14),
('Luis González', '5566789012', 'Calle 56, Monterrey', 15);
