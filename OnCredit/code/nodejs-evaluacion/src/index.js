// src/index.js
import { WorkerPool } from './patterns/WorkerPool.js';
import { SumStrategy } from './strategies/SumStrategy.js';
import { MultiplyStrategy } from './strategies/MultiplyStrategy.js';
import { Calculator } from './patterns/Calculator.js';
import express from 'express';

// Singleton para manejar Workers
const workerPool = new WorkerPool();

// Express API
const app = express();
app.use(express.json());

// Endpoint para cálculos simples
app.post('/calculate', async (req, res) => {
  const { a, b, operation } = req.body;

  let strategy;
  if (operation === 'sum') {
    strategy = new SumStrategy();
  } else if (operation === 'multiply') {
    strategy = new MultiplyStrategy();
  } else {
    return res.status(400).json({ error: 'Invalid operation' });
  }

  const calculator = new Calculator(strategy);
  const result = calculator.calculate(a, b);
  return res.json({ result });
});

// Endpoint para cálculo intensivo usando Worker Threads
app.post('/heavy-task', async (req, res) => {
  try {
    const result = await workerPool.executeTask('./src/workers/worker.js', req.body.number);
    res.json({ result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoint corregido (sin bug en el Event Loop)
app.get('/buggy-endpoint', async (req, res) => {
  console.log('Start request');
  let stop = false;

  setTimeout(() => {
    console.log('Timeout executed');
    stop = true;
    res.send('Response reached!');
  }, Math.random() * 100);
});

app.listen(3000, () => console.log('Server running on port 3000'));