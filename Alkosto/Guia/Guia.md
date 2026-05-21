Entrega Arquitectónica - Caso Entelgy

1. Resumen Ejecutivo
   - Objetivo del negocio
   - Problema a resolver
   - Alcance de la solución
   - Principios de arquitectura:
     - Baja latencia
     - Precisión en stock/precio
     - Escalabilidad
     - Seguridad
     - Evolución por fases

2. Contexto del Negocio
   - Canal actual vs. nuevo canal conversacional
   - Necesidad de asesoría personalizada 24/7
   - Rol de WhatsApp, Yalo y Mulesoft
   - Métricas de éxito esperadas

3. Arquitectura AS-IS
   - Sistemas actuales:
     - Search / Algolia
     - SAP PCM
     - SAP OMS
     - SIRV
     - Promotions Cloud
     - Mulesoft
     - Yalo
   - Responsabilidad actual de cada sistema
   - Limitaciones actuales:
     - Información distribuida
     - Latencia por múltiples consultas
     - Diferencia entre datos batch y datos en tiempo real
     - Catálogo con atributos variables por categoría

4. Arquitectura TO-BE
   - WhatsApp como canal de entrada
   - Yalo como agente conversacional
   - Mulesoft como capa de orquestación
   - APIs desacopladas por dominio
   - Cache para datos de baja volatilidad
   - Consulta en tiempo real para stock, precio y promociones
   - Modelo canónico de producto para respuesta unificada

5. Diagrama de Solución
   - Diagrama lógico de componentes
   - Diagrama de secuencia:
     Usuario WhatsApp
     Yalo
     Experience API
     Process API
     Search API
     SAP PCM API
     SAP OMS API
     Promotions API
     SIRV

6. Estrategia de Integración
   - Patrón API-Led Connectivity:
     - Experience API para Yalo
     - Process API para búsqueda y recomendación
     - System APIs para SAP PCM, SAP OMS, Promotions, Search y SIRV
   - Orquestación vs. coreografía
   - Manejo de latencia:
     - Consultas paralelas
     - Cache distribuido
     - Timeouts controlados
     - Circuit breakers
     - Fallbacks funcionales
     - Separación entre datos referenciales y datos transaccionales

7. Modelo Canónico de Producto
   - Identificadores:
     - sku
     - ean
     - productId
   - Datos comerciales:
     - nombre
     - marca
     - categoría
     - descripción
   - Datos de búsqueda:
     - keywords
     - score
     - highlights
   - Datos transaccionales:
     - precio final
     - promociones
     - disponibilidad
     - tienda
   - Datos visuales:
     - imágenes desde SIRV
   - Datos técnicos:
     - specifications dinámicas por categoría

8. Gestión de Atributos Dinámicos
   - Ficha técnica flexible mediante specifications {}
   - Normalización por categoría
   - Diccionario de atributos
   - Alias semánticos para el agente de IA
   - Validación mínima por tipo de producto
   - Ejemplo:
     - Laptop: RAM, procesador, almacenamiento
     - Nevera: litros, eficiencia energética, tipo de enfriamiento

9. Seguridad
   - OAuth 2.0 Client Credentials entre Yalo y Mulesoft
   - TLS 1.2+
   - API Gateway con rate limiting y throttling
   - Validación de scopes por API
   - Manejo seguro de PII
   - Enmascaramiento de datos sensibles en logs
   - Observabilidad y auditoría
   - Protección contra abuso del canal conversacional

10. Observabilidad y Operación
   - Correlation ID end-to-end
   - Logs técnicos y funcionales
   - Métricas:
     - latencia por sistema
     - tasa de error
     - cache hit ratio
     - disponibilidad de APIs
     - precisión de recomendación
   - Alertas por degradación de SAP OMS, Promotions o Search

11. Visión de Futuro
   - Fase 1: Búsqueda y asesoría
   - Fase 2: Selección de método de pago
   - Fase 3: Creación de pedido en SAP
   - Fase 4: Facturación electrónica
   - Fase 5: Postventa conversacional
   - Preparación arquitectónica:
     - APIs versionadas
     - Modelo canónico extensible
     - Event-driven architecture para órdenes y facturación
     - Idempotencia en creación de pedidos
     - Separación de dominios comerciales y transaccionales

12. Conclusiones
   - Beneficio para negocio
   - Beneficio técnico
   - Riesgos principales
   - Recomendación de implementación incremental