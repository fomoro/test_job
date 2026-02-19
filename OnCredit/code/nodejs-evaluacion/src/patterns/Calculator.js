// src/patterns/Calculator.js
export class Calculator {
    strategy;
  
    constructor(strategy) {
      this.strategy = strategy;
    }
  
    calculate(a, b) {
      return this.strategy.execute(a, b);
    }
  }