
## Prompt para el diagrama A3

```text
CREA UN DIAGRAMA DE ARQUITECTURA EJECUTIVO CON LAS SIGUIENTES ESPECIFICACIONES:

TÍTULO: "Topología Cloud y Datos - Estado Actual"

ORIENTACIÓN: Horizontal (16:9)

FONDO: Blanco

ESTILO GENERAL:
Minimalista, ejecutivo, institucional.
Sin párrafos. Sin explicaciones.
El problema debe entenderse solo con formas, colores y conexiones.

---

BLOQUE PRINCIPAL - MICROSOFT AZURE

- Ubicación: lado izquierdo / centro
- Tamaño: 60–70% del ancho total (dominante)
- Color: Azul #0072C6
- Borde: fino, limpio

Contenido interno (ordenado y alineado):
- Rectángulo: "App Interna 1"
  → conectado visualmente a cilindro "SQL Server"

- Rectángulo: "App Interna 3"
  → conectado visualmente a cilindro "MongoDB"

- Rectángulo: "Sistema Tercero B (SaaS)"

Diseño interno limpio, alineado, estructurado (contraste con el resto del diagrama)

---

BLOQUES PERIFÉRICOS - SILOS TECNOLÓGICOS (lado derecho, separados verticalmente)

Separados con espacio en blanco claro (sensación de aislamiento)

IBM CLOUD (arriba):
- Color: Gris oscuro #5C5C5C
- Rectángulo: "Core Legacy" con indicador 🔴
- Conectado a cilindro "Sybase"

AWS (medio):
- Color: Gris medio #7A7A7A
- Rectángulo: "ERP Tercero"
- Conectado a cilindro "Oracle"

GCP (abajo):
- Color: Gris claro #9A9A9A
- Rectángulo: "App Interna 2"
- Conectado a cilindro "PostgreSQL"

---

BARRERAS DE INTEGRACIÓN (ELEMENTO CLAVE)

Entre Azure y cada nube:

- Línea roja gruesa discontinua
- Icono ⚠️ cerca de la línea

NO agregar texto

Debe percibirse claramente que:
→ no hay integración
→ los bloques están aislados

---

ACTORES (parte inferior)

OFICINA PRINCIPAL (lado izquierdo inferior):
- Icono simple de usuario
- Etiqueta: "70%"
- Líneas punteadas ligeramente curvas hacia:
  → Azure
  → IBM
  → AWS
  → GCP

Máximo 3–4 líneas (no saturar)

---

SUCURSALES (lado derecho inferior):
- Icono simple de usuario
- Etiqueta: "30%"
- Líneas punteadas hacia:
  → Azure
  → IBM

Máximo 2 líneas

Debe verse claramente:
→ menor alcance
→ dependencia parcial

---

REGLAS DE CONEXIÓN

- Líneas punteadas, suaves, ligeramente curvas
- Evitar cruces innecesarios
- Mostrar complejidad sin perder legibilidad

---

LEYENDA (mínima, esquina inferior)

- ⚠️ = Sin integración
- 🔴 = Crítico 24/7

(No incluir más elementos)

---

REGLAS DE DISEÑO CRÍTICAS

- Azure debe verse dominante y ordenado
- Los otros bloques deben verse pequeños y aislados
- Debe existir espacio en blanco entre nubes (refuerza silos)
- No usar iconografía decorativa
- No incluir textos explicativos largos
- No incluir “mensaje clave” escrito

---

VALIDACIÓN FINAL

El diagrama es correcto si:

- Se percibe que Azure es el centro pero no controla todo
- Se entiende que hay múltiples nubes aisladas
- Se ve que los usuarios dependen de varios sistemas
- Se nota que sucursales tienen menos acceso que oficina principal
- La fragmentación es evidente sin leer texto
```

---
