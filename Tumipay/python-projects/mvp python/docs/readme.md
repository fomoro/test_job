# 🚀 TumiPay Transaction Mock - Guía de Instalación

Este repositorio contiene un simulador de orquestación de pagos (PayIn) desarrollado con **Python** y **FastAPI**. El proyecto demuestra patrones de diseño avanzados (Adapter, Strategy, Factory) y validaciones de reglas de negocio sin necesidad de configurar una base de datos externa para su ejecución local.

## 📋 Prerrequisitos

Antes de comenzar, asegúrate de tener instalado en tu sistema:

* **Python 3.9** o superior.
* **pip** (Gestor de paquetes de Python).
* Una terminal o consola de comandos (CMD, PowerShell, Bash).

---

## 🛠️ Instalación y Configuración

Sigue estos pasos para preparar el entorno de desarrollo.

### 1. Clonar o Descargar el Proyecto
Descarga el código fuente y ubícate en la carpeta del proyecto. Asegúrate de que el archivo principal se llame `main.py`.

### 2. Crear un Entorno Virtual (Recomendado)
Es una buena práctica aislar las dependencias del proyecto.

* **En Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

* **En macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Instalar Dependencias
Instala las librerías necesarias ejecutando el siguiente comando:

```bash
pip install fastapi uvicorn faker email-validator pydantic
```

## ▶️ Ejecución del Proyecto

Para iniciar el servidor de desarrollo, utiliza **Uvicorn**. Tienes dos opciones según cómo quieras correrlo:

### Opción 1: Ejecución Básica (Recomendada)
Este comando inicia el servidor en el puerto 8000 y habilita el "Hot Reload" (se actualiza solo si cambias el código).

```bash
uvicorn main:app --reload
```


### Opción 2: 
con puerto
```bash
uvicorn main:app --reload --port 8080
```