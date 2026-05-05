

## Prompt para el diagrama A4

```text
CREA UNA IMAGEN DE ARQUITECTURA EJECUTIVO CON LAS SIGUIENTES ESPECIFICACIONES:

TÍTULO: "Integraciones Actuales - Estado Actual"

ORIENTACIÓN: Horizontal (16:9)

FONDO: Blanco

ESTILO GENERAL:
Diagrama de integraciones con caos controlado y estructura clara.
Cada sistema debe percibirse como una unidad lógica (aplicación + base de datos).
El antipatrón debe ser evidente sin necesidad de texto explicativo.
Sin párrafos largos.

TODAS LAS LÍNEAS:
- Mismo grosor
- Sin variación de espesor
- Diferenciación SOLO por color y estilo (continua vs punteada)

---

AGRUPACIÓN POR SISTEMA (UNIDAD VISUAL)

Cada sistema se representa como un contenedor con borde punteado suave.

Dentro de cada contenedor:
- Aplicación (rectángulo superior)
- Base de datos (cilindro inferior)
- Línea interna entre app y BD (gris claro, discreta)

SISTEMAS:

1. Core Legacy
   - App: "Core Legacy 🔴" (gris oscuro, texto blanco)
   - BD: "Sybase"

2. ERP Tercero
   - App: "ERP Tercero" (gris medio, texto blanco)
   - BD: "Oracle"

3. App Interna 1
   - App: "App Interna 1" (azul)
   - BD: "SQL Server"

4. App Interna 2
   - App: "App Interna 2" (azul)
   - BD: "PostgreSQL"

5. App Interna 3
   - App: "App Interna 3" (azul)
   - BD: "MongoDB"

Sistema adicional:
- "Sistema Tercero B" (azul claro, más pequeño, SIN base de datos)

IMPORTANTE:
- Los cilindros SOLO llevan el nombre de la base de datos
- No agregar texto adicional dentro de cilindros

---

DISTRIBUCIÓN

- Core Legacy y ERP Tercero centrados y ligeramente más grandes
- Debe existir un espacio vacío claro ENTRE ambos (sin líneas ni elementos)
- Apps internas distribuidas alrededor (izquierda y derecha)
- Sistema Tercero B en zona periférica derecha

---

ESPECIFICACIÓN VISUAL DE LÍNEAS

- Línea roja continua → Antipatrón
- Línea amarilla continua → Integración frágil
- Línea gris punteada → Integración inestable
- Línea negra punteada → Tráfico de usuarios
- Línea gris claro continua → Relación App → su BD

---

CONEXIONES

RELACIONES INTERNAS:
- Cada App conectada a su BD (gris claro, discreta)

INTEGRACIONES ENTRE APLICACIONES:
- Core Legacy ↔ ERP Tercero (amarilla)
- App Interna 1 ↔ App Interna 3 (amarilla)
- App Interna 2 ↔ ERP Tercero (gris punteada)
- Sistema Tercero B ↔ App Interna 2 (gris punteada)
- Sistema Tercero B ↔ ERP Tercero (amarilla)

ANTIPATRONES (ROJO – CLAVE VISUAL):
- App Interna 1 → Sybase (cruza hacia Core Legacy)
- App Interna 3 → Sybase (cruza hacia Core Legacy)
- ERP Tercero → PostgreSQL (cruza hacia App interna 2)

REGLA CRÍTICA:
- NO dibujar ninguna conexión entre App Interna 3 y Oracle
- NO existe línea de ningún tipo entre App Interna 3 y la BD del ERP

---

ESPACIO VACÍO CENTRAL

Entre Core Legacy y ERP Tercero:
- SIN líneas
- SIN elementos
- Área limpia claramente visible

Representa ausencia de integración centralizada.

---

ACTORES Y CONSUMO DE SISTEMAS

Ubicar en la parte inferior dos actores claramente visibles:

1. Oficina Principal (70%)
   - Icono de usuario
   - Etiqueta: "Oficina Principal (70%)"
   - Conecta con:
     - Core Legacy
     - ERP Tercero
     - App Interna 2
   - Dibujar líneas negras punteadas hacia esos sistemas

2. Sucursales (30%)
   - Icono de usuario
   - Etiqueta: "Sucursales (30%)"
   - Conecta con:
     - Core Legacy
     - App Interna 1
     - App Interna 3
   - Dibujar líneas negras punteadas hacia esos sistemas

REGLAS VISUALES DE ACTORES:
- Líneas negras punteadas
- Menos visibles que las integraciones
- No deben confundirse con integraciones entre aplicaciones

---

LEYENDA (ESQUINA INFERIOR DERECHA)

Recuadro limpio con borde sutil.

Mostrar líneas con su estilo visual + etiqueta:

- Línea roja continua — Antipatrón
- Línea amarilla continua — Integración frágil
- Línea gris punteada — Integración inestable
- Línea negra punteada — Tráfico de usuarios

---

VALIDACIÓN FINAL

El diagrama es correcto si:

- Cada app está claramente asociada a su BD
- Las conexiones internas no generan ruido visual
- Existen DOS líneas rojas cruzando hacia Sybase (desde App 1 y App 3)
- NO existe ninguna línea entre App Interna 3 y Oracle
- Core Legacy y ERP Tercero dominan el centro
- Existe un vacío claro entre ellos
- Se entiende qué actor consume qué sistemas
- No hay saturación visual
- El antipatrón se identifica en menos de 10 segundos
```

