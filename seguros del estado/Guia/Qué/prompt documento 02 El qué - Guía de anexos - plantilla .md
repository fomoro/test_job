# Especificación de Anexos Visuales – Diagnóstico (EL QUÉ)

**Caso:** Seguros del Estado  
**Objetivo:** Definir cómo construir los diagramas del estado actual (As-Is), asegurando claridad visual y foco en el problema estructural.

---

## A1. Mapa de Capacidades vs Aplicaciones (Heatmap)

**Objetivo:**  
Evidenciar duplicidad funcional y sobrecostos operativos.

**Formato:**  
Tabla matricial (heatmap visual).

**Cómo construirlo:**
- Filas (Procesos Core):
  - Indemnizaciones  
  - Talento Humano  
  - Suscripción  
  - Emisión de Pólizas  
  - Facturación  
  - CRM / Atención  

- Columnas (Sistemas):
  - App Interna 1, App Interna 2  
  - ERP Tercero  
  - Sistema Legacy  
  - App Sucursales  

- Marcar con:
  - X o color donde exista soporte funcional  
  - Usar colores intensos cuando haya duplicidad  
  - Identificar aplicaciones **Core (24/7)** con color rojo o etiqueta

**Qué resaltar (clave del caso):**
- Indemnizaciones y Suscripción con múltiples sistemas (3–4 apps)  
- Duplicidad en procesos críticos (no solo en secundarios)  
- ERP + apps internas haciendo lo mismo  

**Nota visual:**
> "Duplicidad funcional: múltiples sistemas soportando el mismo proceso → incremento de costos y complejidad."

---

## A2. Inventario de Aplicaciones

**Objetivo:**  
Mostrar el desorden estructurado del ecosistema y evidenciar riesgos operativos.

**Formato:**  
Tabla con semáforo (Rojo / Amarillo / Verde).

**Columnas:**
- Sistema  
- Proceso  
- Criticidad  
- Nube  
- Base de datos  
- Origen (Interno / Tercero)  
- Antigüedad (años)

**Cómo construirlo:**
- Usar 8–10 sistemas representativos  
- Aplicar colores por criticidad y riesgo  

**Qué resaltar (clave del caso):**
- Sistemas críticos (24/7) en tecnologías obsoletas  
- Sistemas antiguos (alta antigüedad) en procesos core  
- Mezcla de motores de BD  
- Dependencia de terceros en procesos críticos  

**Nota visual:**
> "Alta heterogeneidad tecnológica (nubes, motores, antigüedad, origen) → alto TCO y complejidad operativa."

---

## A3. Topología Cloud y Datos (Estado Actual)

**Objetivo:**  
Evidenciar fragmentación multicloud y silos de información.

**Formato:**  
Diagrama de bloques (arquitectura conceptual).

**Cómo construirlo:**
- Dibujar 4 bloques:
  - Azure (principal)  
  - AWS  
  - GCP  
  - IBM Cloud  

- Proporción:
  - Azure debe ocupar ~60–70% del espacio  
  - AWS, GCP e IBM deben ser bloques pequeños laterales  

- Dentro de cada bloque:
  - Aplicaciones  
  - Bases de datos (Oracle, Sybase, SQL, Postgres, Mongo)

- Agregar:
  - Usuarios: Oficina Principal (70%) y Sucursales (30%)  
  - Símbolos de advertencia ⚠️ entre nubes  

**Qué resaltar (clave del caso):**
- Azure como estándar de facto  
- Otras nubes como excepción que genera complejidad  
- Nubes operando en silos  
- Multiplicidad de motores de datos  

**Nota visual:**
> "Silos de datos fragmentados: imposible construir una visión unificada del negocio."

---

## A4. Mapa de Integraciones (Diagrama de Espagueti)

**Objetivo:**  
Mostrar la complejidad e inestabilidad de las integraciones actuales.

**Formato:**  
Diagrama caótico intencional (red punto a punto).

**Cómo construirlo:**
- Nodos: aplicaciones  
- Conexiones:
  - Líneas cruzadas  
  - Integraciones punto a punto  
  - Conexiones directas a bases de datos  

- Agregar:
  - Flechas rojas para conexiones críticas  
  - Íconos de falla (fuego/explosión) en puntos sensibles  
  - Cruces desordenados intencionales  

**Qué resaltar (clave del caso):**
- Dependencias múltiples  
- Integraciones frágiles  
- Falta de control central  
- Riesgo de fallas en cascada  

**Nota visual (obligatoria):**
> "Ausencia de API Gateway o Bus de Integración (ESB): las conexiones punto a punto generan riesgo de caída en cascada y falta de trazabilidad."

---

## Reglas de construcción

1. 80% visual / 20% texto  
2. Comprensible en menos de 10 segundos  
3. Priorizar impacto sobre estética  
4. Evitar detalle técnico innecesario  
5. Usar colores de forma consistente:
   - 🔴 Rojo → crítico  
   - 🟡 Amarillo → riesgo  
   - ⚪ Gris → obsoleto  

---

## Checklist de validación

- [ ] ¿Se entiende el problema sin explicación verbal?  
- [ ] ¿Se evidencian duplicidad, fragmentación y riesgo?  
- [ ] ¿Están presentes actores (70% principal / 30% sucursal)?  
- [ ] ¿Se mencionan tecnologías reales (Azure, Oracle, Mongo, etc.)?  
- [ ] ¿El diagrama de integraciones se percibe caótico?  

---

## Objetivo final de los anexos

Hacer evidente que el problema es estructural:

- Duplicidad  
- Desorden  
- Fragmentación  
- Riesgo operativo  

El evaluador debe entender la necesidad de una solución sin que aún se la expliques.