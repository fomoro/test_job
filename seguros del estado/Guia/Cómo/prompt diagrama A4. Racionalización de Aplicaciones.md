# PROMPT: A4. Racionalización de Aplicaciones (Matriz de Transición)

CREA UNA MATRIZ VISUAL EJECUTIVA CON LAS SIGUIENTES ESPECIFICACIONES:

**TÍTULO:** "Racionalización de Aplicaciones (As-Is vs To-Be)"  
**ORIENTACIÓN:** Horizontal (16:9)  
**FONDO:** Blanco  

**ESTILO GENERAL:**  
Tabla de transición ejecutiva, limpia y de alto contraste.  
Debe evidenciar eliminación de duplicidad, reducción del portafolio y convergencia hacia servicios gobernados.

---

## ESTRUCTURA DE LA MATRIZ (4 COLUMNAS)

| Sistema Actual (As-Is) | Proceso Clave | Decisión de Arquitectura | Estado Objetivo |

Filas:

- Core Legacy (IBM) → Indemnizaciones / Suscripción → Encapsular vía ACL + exponer APIs → 🟡 TRANSICIÓN  
- ERP Tercero (AWS) → Facturación → Integrar vía API Gateway → 🟢 MANTENER  
- App Interna 1 (Azure) → Indemnizaciones (Duplicado) → Retirar (consolidado en APIs Core) → 🔴 RETIRAR  
- App Interna 2 (GCP) → Talento Humano → Mantener e integrar al Bus → 🟢 MANTENER  
- App Interna 3 (Azure) → Suscripción (Duplicado) → Retirar (consolidado en APIs Core) → 🔴 RETIRAR  
- Sistema Tercero B (Azure) → CRM / Atención → Mantener e integrar al Bus → 🟢 MANTENER  

---

## REGLAS VISUALES OBLIGATORIAS

- **Duplicidad visible:**  
  Indemnizaciones y Suscripción deben aparecer repetidos claramente.

- **Filas eliminadas:**  
  App Interna 1 y App Interna 3:
  - Fondo rojizo suave o texto tachado
  - Deben destacar visualmente como eliminación

- **Convergencia visual:**  
  En “Decisión de Arquitectura” deben repetirse:
  - “APIs”
  - “Bus”
  - “ACL”

- **Semáforo claro:**  
  Usar 🟢 🟡 🔴 como elemento dominante de lectura rápida

---

## MENSAJE VISUAL

Debe ser evidente sin explicación:

- Dos sistemas desaparecen por duplicidad  
- Las capacidades se concentran en menos componentes  
- Todo lo que queda pasa por integración gobernada  

---

## RESULTADO (DESTACADO INFERIOR)

"RESULTADO: Eliminación de sistemas redundantes, reducción del TCO y 100% de los sistemas sobrevivientes integrados bajo gobierno central."

---

## VALIDACIÓN FINAL

El diagrama es correcto si:

- Se identifican inmediatamente los sistemas a retirar  
- Se percibe reducción del portafolio  
- Se entiende que las capacidades convergen en APIs  
- Se conecta con A1 (integración) y A2 (flujo gobernado)  
- Se lee en menos de 10 segundos