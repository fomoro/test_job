"""
app/main.py - Punto de entrada principal de la aplicación CCS
"""

import logging
from contextlib import asynccontextmanager

import uvicorn

from infrastructure.state import state
from api.routes import create_app

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ccs_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """
    Lifespan manager para FastAPI.
    
    Inicializa el estado global al inicio y lo limpia al final.
    """
    logger.info("🔄 Iniciando lifespan manager...")
    await state.initialize()
    yield
    logger.info("🔄 Finalizando lifespan manager...")
    await state.shutdown()


# Crear aplicación FastAPI con lifespan
app = create_app()
app.lifespan = lifespan


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        limit_concurrency=1000,
        timeout_keep_alive=30,
        access_log=True,
        reload=True  # Para desarrollo
    )