# PROMPT: A3. Topología Cloud y Datos Objetivo (To-Be)

CREA UN DIAGRAMA DE ARQUITECTURA EJECUTIVO CON LAS SIGUIENTES ESPECIFICACIONES:

**TÍTULO:** "Topología Cloud y Datos Objetivo - To-Be"  
**ORIENTACIÓN:** Horizontal (16:9)  
**FONDO:** Blanco  

**ESTILO GENERAL:**  
Diagrama de bloques limpio, ejecutivo y ordenado.  
Debe transmitir centralización, gobierno del multicloud, separación de cargas y visión unificada de datos.  
Contraste directo con la topología fragmentada del diagnóstico.

---

## ESTRUCTURA VISUAL

### 1. ZONA CENTRAL DOMINANTE: Microsoft Azure - Landing Zone

Gran contenedor azul claro con borde visible.  
Debe ocupar el centro y lado derecho del diagrama.

Dentro de Azure, mostrar dos subzonas separadas:

**A. Capa de Integración**
- Rectángulo azul fuerte.
- Texto: "API Gateway + Eventos + ACL"
- Ubicación: borde izquierdo interno de Azure.
- Rol visual: puerta de entrada obligatoria desde otras nubes.

**B. Capa Analítica / Data Lake**
- Rectángulo verde o gris claro.
- Textos internos:
  - "Data Lake / Capa Analítica"
  - "Visión Gerencial Unificada"
  - "Lectura Desacoplada"

---

### 2. ZONA PERIFÉRICA: Nubes Secundarias / Sistemas Transaccionales

Ubicadas a la izquierda, fuera del bloque principal de Azure.

**IBM Cloud**
- Contiene: "Core Legacy 🔴"
- BD: cilindro "Sybase" con candado discreto 🔒

**AWS**
- Contiene: "ERP Tercero"
- BD: cilindro "Oracle" con candado discreto 🔒

**GCP / Otros**
- Bloque pequeño opcional.
- Contiene: "App Interna 2" o "Sistemas secundarios"
- BD: cilindro "PostgreSQL" con candado discreto 🔒

---

## FLUJOS DE DATOS

Todas las flechas son unidireccionales de izquierda a derecha.

Dibujar únicamente estos flujos:

1. Core Legacy / IBM → Capa de Integración / Azure
2. ERP Tercero / AWS → Capa de Integración / Azure
3. GCP / Otros → Capa de Integración / Azure
4. Capa de Integración → Capa Analítica / Data Lake
5. Capa Analítica / Data Lake → Gerencia

**Regla visual adicional:**
- El actor "Gerencia" debe ubicarse en el extremo derecho del diagrama.
- No dibujar flechas desde Gerencia hacia el sistema.
- La Gerencia solo consume información.

---

## PROHIBICIONES VISUALES

- NO conectar IBM directamente con AWS.
- NO conectar sistemas directamente al Data Lake.
- NO conectar bases de datos transaccionales directamente al Data Lake.
- NO dibujar flujos de retorno.
- NO mostrar consultas directas a Sybase, Oracle o PostgreSQL.

---

## MENSAJE VISUAL

Debe quedar claro sin explicación:

- Azure actúa como centro de gobierno del ecosistema.
- Las nubes secundarias quedan contenidas y controladas.
- Las bases de datos transaccionales están encapsuladas.
- La gerencia consume información desde una capa analítica, no desde los sistemas operativos.
- Se separa operación 24/7 de lectura analítica.

---

## LEYENDA MÍNIMA

- 🔒 Base de datos encapsulada
- → Flujo gobernado
- 🟩 Capa analítica: visión de negocio

---

## VALIDACIÓN FINAL

El diagrama es correcto si:

- Azure se percibe como centro de gravedad.
- El Data Lake solo recibe datos vía capa de integración.
- No hay conexiones punto a punto entre nubes.
- No hay acceso directo a bases de datos transaccionales.
- El flujo visual va de operación a decisión: sistemas → integración → analítica → gerencia.
- Se entiende la separación entre operación y analítica en menos de 10 segundos.