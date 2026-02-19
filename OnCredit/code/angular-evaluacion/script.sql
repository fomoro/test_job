CREATE DATABASE gestion_productos;
USE gestion_productos;

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  category VARCHAR(255) NOT NULL
);

INSERT INTO products (name, price, category) VALUES
('Producto 1', 50.00, 'Categoría A'),
('Producto 2', 150.00, 'Categoría B'),
('Producto 3', 75.00, 'Categoría A'),
('Producto 4', 200.00, 'Categoría C'),
('Producto 5', 90.00, 'Categoría B'),
('Producto 6', 120.00, 'Categoría A'),
('Producto 7', 300.00, 'Categoría C'),
('Producto 8', 60.00, 'Categoría B'),
('Producto 9', 180.00, 'Categoría A'),
('Producto 10', 250.00, 'Categoría C');
