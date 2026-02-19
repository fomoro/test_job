// src/workers/worker.js
const { parentPort, workerData } = require('worker_threads');

function heavyTask(number) {
  let result = 1;
  for (let i = 1; i <= number; i++) {
    result *= i;
  }
  return result;
}

const result = heavyTask(workerData);
parentPort.postMessage(result);