# Servicios bajo Demanda - Propuesta de Implementación

**Estado:** Propuesta / Futura implementación  
**Fecha:** 2026-09-02  
**Relacionado:** `docs/presentation.html` (slides 9-12)

---

## Visión General

Expandir Elite Intel hacia una **plataforma de servicios automatizados** donde el cliente solicita un servicio específico desde una página web, y el servidor privado ejecuta la acción correspondiente de forma automática, sin intervención manual.

**Concepto clave:** El cliente pide, el servidor ejecuta.

---

## Objetivo

- Crear una página web pública donde los clientes seleccionen y soliciten servicios.
- Ejecutar automáticamente las acciones en el servidor local (recargas, impresiones, etc.).
- Escalar a nuevos servicios sin modificar la plataforma base.
- Mantener control total: los datos y la ejecución quedan en el servidor privado.

---

## Arquitectura General

```
┌─────────────────────────────────────────────────┐
│           Cliente (Web / Móvil)                 │
│     Solicita servicio → Página web pública      │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────┐
│        API Cloud (FastAPI en VPS)               │
│  ┌─────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Auth / JWT  │  │  Cola    │  │ Rate Limit│  │
│  └─────────────┘  └──────────┘  └───────────┘  │
└──────────────────────┬──────────────────────────┘
                       │ WebSocket / Polling
                       ▼
┌─────────────────────────────────────────────────┐
│      Elite Intel Server (On-Premise)            │
│                                                 │
│  ┌──────────────┐    ┌────────────────────┐     │
│  │ FastAPI Local│◄──►│ Servicios          │     │
│  └──────────────┘    │ ┌────────────────┐ │     │
│                      │ │ Recargas       │ │     │
│                      │ │ Impresiones    │ │     │
│                      │ │ Futuros...     │ │     │
│                      │ └────────────────┘ │     │
│                      └────────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

## Flujo de Ejemplo: Recarga Telefónica

```
1. Cliente accede a → elite-intel.com/recargas
2. Ingresa número + monto + proveedor
3. Clic en "Solicitar recarga"
4. API Cloud recibe → valida → registra → notifica al servidor local
5. Servidor local abre → plataforma de recargas del proveedor
6. Número y monto precargados → ejecuta la recarga
7. Confirmación → cliente recibe notificación de éxito
```

## Flujo de Ejemplo: Impresión de Documento

```
1. Cliente accede a → elite-intel.com/impresiones
2. Sube el documento (PDF, imagen, texto)
3. Selecciona configuración (cantidad, color/B&N, tamaño)
4. Clic en "Imprimir"
5. API Cloud recibe → valida → almacena temporalmente → notifica al servidor local
6. Servidor local recibe → descarga el archivo → ejecuta Ctrl+P automáticamente
7. Documento se imprime → confirmación al cliente
```

---

## Servicios Propuestos

### Fase 1 - Servicios Core

| Servicio | Descripción | Datos requeridos | Ejecución automática |
|----------|-------------|------------------|---------------------|
| **Recargas** | Recargas telefónicas | Número, monto, proveedor | Abrir plataforma de recargas con datos precargados |
| **Impresiones** | Impresión de documentos | Archivo, cantidad, configuración | Recibir archivo → ejecutar impresión local |

### Fase 2 - Servicios Expandidos

| Servicio | Descripción | Datos requeridos | Ejecución automática |
|----------|-------------|------------------|---------------------|
| **Pagos** | Pago de servicios | Tipo de servicio, monto, referencia | Abrir plataforma de pago con datos precargados |
| **Consultas** | Consulta de información | Tipo de consulta, parámetros | Ejecutar consulta → retornar resultado |
| **Trámites** | Gestión de documentos | Tipo de trámite, archivos | Procesar documentos → generar resultados |

---

## Endpoints de la API Cloud

### Servicios

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/services` | Lista de servicios disponibles | JWT por cliente |
| `POST` | `/api/v1/services/recargas` | Solicitar recarga telefónica | JWT + rate limit |
| `POST` | `/api/v1/services/impresiones` | Solicitar impresión de documento | JWT + rate limit |
| `POST` | `/api/v1/services/{type}` | Solicitar servicio genérico | JWT + rate limit |

### Estado de Servicios

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/status/{request_id}` | Estado de una solicitud | JWT por cliente |
| `GET` | `/api/v1/history` | Historial de servicios del cliente | JWT por cliente |
| `WebSocket` | `/ws/status/{request_id}` | Estado en tiempo real | JWT por cliente |

### Administración

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/admin/services` | Servicios configurados | JWT admin |
| `POST` | `/api/v1/admin/services` | Registrar nuevo servicio | JWT admin |
| `GET` | `/api/v1/admin/logs` | Logs de ejecución | JWT admin |
| `GET` | `/api/v1/health` | Estado del servicio | Ninguna |

---

## Seguridad

- **Autenticación JWT:** Cada cliente tiene un token con permisos específicos por servicio.
- **Rate Limiting:** Máximo de solicitudes por minuto para evitar abuso.
- **Validación de datos:** Cada servicio valida los datos de entrada antes de ejecutar.
- **Logs de Auditoría:** Cada solicitud y ejecución queda registrada con timestamp.
- **Cifrado HTTPS:** Toda comunicación en tránsito cifrada.
- **Cola de ejecución:** Las solicitudes se procesan en orden, evitando conflictos.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| API Cloud | FastAPI (Python) | Misma stack que el backend local |
| Base de datos cloud | PostgreSQL | Metadata de clientes y solicitudes |
| Cola de tareas | Celery + Redis | Ejecución asíncrona de servicios |
| Auth | JWT + bcrypt | Estándar de la industria |
| Deploy | VPS (DigitalOcean / Hetzner) | Costo bajo, control total |
| WebSocket | FastAPI WebSockets | Estado en tiempo real al cliente |

---

## Costos Estimados

| Componente | Costo mensual | Notas |
|-----------|---------------|-------|
| VPS básico | $5-10 | DigitalOcean / Hetzner |
| Dominio + SSL | $1-2 | Cloudflare (gratis) |
| PostgreSQL managed | $0-5 | Incluido en algunos VPS |
| **Total** | **$6-17/mes** | Escalable según tráfico |

---

## Fases de Implementación

### FASE 01 - Infraestructura Cloud
- Deploy del VPS con FastAPI
- Configuración de dominio y SSL
- Autenticación JWT de clientes
- Estructura base de la API REST
- **Duración estimada:** 1-2 semanas

### FASE 02 - Servicios Core
- Implementación de servicio de recargas
- Implementación de servicio de impresiones
- Integración con el servidor local de Elite Intel
- Cola de ejecución con Celery
- **Duración estimada:** 2-3 semanas

### FASE 03 - Panel y Escalabilidad
- Panel de administración para gestionar servicios
- Métricas de uso y rendimiento
- Expansión a nuevos servicios según demanda
- Optimización de rendimiento
- **Duración estimada:** 2-4 semanas

---

## Consideraciones Técnicas

- **Conectividad local ↔ cloud:** El servidor local necesita una conexión estable con el VPS. WebSocket o polling cada 30 segundos.
- **Resiliencia:** Si el servidor local se desconecta, las solicitudes quedan en cola y se procesan cuando vuelve.
- **Escalabilidad:** Un solo VPS soporta cientos de clientes simultáneos con Celery.
- **Rollback:** Si la API cloud falla, el sistema local de Elite Intel sigue funcionando normalmente.

---

## Referencia Visual

Ver slides 9-12 de `docs/presentation.html` para la propuesta visual presentada al cliente.
