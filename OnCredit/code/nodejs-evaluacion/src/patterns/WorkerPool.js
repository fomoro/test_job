// src/patterns/WorkerPool.js
import { Worker } from 'worker_threads';

export class WorkerPool {
  constructor() {
    this.workers = [];
  }

  executeTask(workerFile, data) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(workerFile, { workerData: data });

      worker.on('message', resolve);
      worker.on('error', reject);
      worker.on('exit', (code) => {
        if (code !== 0) reject(new Error(`Worker stopped with exit code ${code}`));
      });
    });
  }
}