const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Configuración de la conexión a MySQL
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root', // Cambia por tu usuario de MySQL
  password: '', // Cambia por tu contraseña de MySQL
  database: 'gestion_productos'
});

// Conectar a la base de datos
db.connect((err) => {
  if (err) throw err;
  console.log('Conectado a la base de datos MySQL');
});

// Endpoint para obtener productos
app.get('/api/products', (req, res) => {
  db.query('SELECT * FROM products', (err, results) => {
    if (err) throw err;
    res.json(results);
  });
});

// Endpoint para agregar un producto
app.post('/api/products', (req, res) => {
  const { name, price, category } = req.body;
  db.query(
    'INSERT INTO products (name, price, category) VALUES (?, ?, ?)',
    [name, price, category],
    (err, results) => {
      if (err) throw err;
      res.json({ id: results.insertId, name, price, category });
    }
  );
});

// Endpoint para autenticación (simulada)
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  if (username === 'admin' && password === 'admin') {
    // Simulamos la autenticación con un token JWT falso
    res.json({ token: 'fake-jwt-token' });
  } else {
    res.status(401).json({ message: 'Credenciales inválidas' });
  }
});

// Iniciar el servidor
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
