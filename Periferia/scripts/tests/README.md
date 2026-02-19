# Scripts de Testing - CCS

Scripts automatizados para ejecución y análisis de tests del sistema CCS.

## 📋 Scripts Disponibles

### `run_tests.sh` - Ejecución de Tests

```bash
# Ejecutar todos los tests
./scripts/tests/run_tests.sh

# Solo tests unitarios
./scripts/tests/run_tests.sh unit

# Solo tests de integración
./scripts/tests/run_tests.sh integration

# Tests rápidos (sin integration/slow)
./scripts/tests/run_tests.sh fast

# Test específico
./scripts/tests/run_tests.sh specific tests/unit/test_models.py

# Abrir reporte de cobertura
./scripts/tests/run_tests.sh coverage

# Mostrar ayuda
./scripts/tests/run_tests.sh help