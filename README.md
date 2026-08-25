# Elite Intel

Elite Intel es un panel de control de escritorio on-premise para la gestión operativa y financiera del negocio.
Centraliza ingresos, egresos, indicadores de ahorro y catálogo con precios y existencias en una sola aplicación.
Está construido con FastAPI, React y Electron y persiste los datos localmente en SQLite por equipo, sin dependencia de nube ni suscripciones.

> Presentación institucional para cliente: [Ver presentación para cliente](docs/presentation.html).

## Características principales

- **Dashboard con KPIs financieros** en tiempo real: ingresos, egresos, balance neto, ahorro estimado y tasa de ahorro del período.
- **Catálogo operativo** con 148 artículos de referencia: alta, edición, filtros y control de estado activo.
- **Actualización masiva de existencias** (`POST /products/stock/bulk`) con transacción atómica desde una vista consolidada.
- **Administración masiva de precios** (`POST /products/prices/bulk`) y edición puntual (`PATCH /products/{id}`).
- **Sincronización bidireccional con Excel**: todo cambio de precio o stock se replica en `PRECIOS_PRODUCTOS_PAPELERIA.xlsx` conservando su estructura original.
- **Series temporales** por día, semana y mes (`GET /dashboard/timeseries`) y desglose por categorías (`GET /dashboard/categories`).
- **Períodos configurables** con soporte de zona horaria y validación de rangos.
- **Instalación de escritorio** en Windows con un solo ejecutable (`elite-intel.exe`) y acceso directo en el escritorio, sin requerir conectividad.

## Stack tecnológico

`FastAPI · React · Electron · SQLite (por equipo) · Python 3.12 · Node 20`.
En desarrollo se utiliza `docker-compose.yml` con Postgres, backend y frontend.
En producción de escritorio el backend corre con entorno virtual Python local y base SQLite.

## API — Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/dashboard/summary` | Resumen financiero del período (ingresos, egresos, balance, ahorro y tasa). |
| GET | `/dashboard/categories` | Desglose por categorías con filtro opcional por tipo. |
| GET | `/dashboard/timeseries` | Serie temporal por `day`, `week` o `month`. |
| GET | `/products` | Lista de productos con filtros por categoría y estado. |
| POST | `/products` | Crea un producto. |
| PATCH | `/products/{id}` | Actualiza nombre y precios de un producto. |
| GET | `/products/{id}` | Obtiene un producto por id. |
| PATCH | `/products/{id}/stock` | Actualiza el stock de un producto. |
| POST | `/products/stock/bulk` | Actualización masiva de existencias. |
| POST | `/products/prices/bulk` | Actualización masiva de precios. |
| GET | `/transactions` | Lista paginada con filtros por fecha, tipo, categoría y búsqueda. |
| POST | `/transactions` | Crea una transacción. |
| GET | `/transactions/{id}` | Obtiene una transacción. |
| PUT | `/transactions/{id}` | Actualiza una transacción. |
| DELETE | `/transactions/{id}` | Elimina una transacción. |
| GET | `/categories` | Lista de categorías con filtro por tipo y estado. |
| POST | `/categories` | Crea una categoría. |
| PUT | `/categories/{id}` | Actualiza una categoría. |
| DELETE | `/categories/{id}` | Desactiva una categoría (borrado lógico). |

Documentación detallada en `docs/api/` y especificación OpenAPI en `docs/api/openapi.json`.

## Capturas — API en funcionamiento

![Elite Intel Dashboard](docs/images/endpoints/1.png)

*Dashboard operativo en producción con KPIs, desglose por categorías y serie temporal verificables contra la base local.*

## Instalación

1. Vaya al equipo donde se ejecutará la aplicación.
2. Obtenga el código:
   - Clone por HTTPS: `git clone https://github.com/macreat/elite-intel.git`
   - O descargue el ZIP desde GitHub y descomprímalo.
3. Asegúrese de que el proyecto quede en una carpeta local de Windows (por ejemplo `C:\elite-intel`), no en una ruta de red como `\\wsl.localhost\...`.
4. Haga doble clic en `install.bat` (o en `install.sh` si los archivos `.sh` ya están asociados a Git Bash en ese equipo).
5. Acepte la única confirmación solicitada.
   Luego el instalador continúa de forma desatendida: instala Node.js y Python si faltan, instala dependencias, compila el panel, empaqueta `elite-intel.exe` y crea el acceso directo en el escritorio.
6. Inicie la aplicación desde el ícono `elite-intel` en el escritorio.

## Ubicación de datos

- **Catálogo de precios**: `backend/data/raw/PRECIOS_PRODUCTOS_PAPELERIA.xlsx`.
  Esta planilla es la fuente de verdad para los precios de productos.
  Las actualizaciones de stock y precios realizadas en la aplicación se escriben de vuelta en este mismo archivo, por lo que siempre refleja el catálogo vigente.
- **Transacciones 2026**: se registran en la base SQLite en `backend/elite.db` (base de producción de la aplicación, creada en el primer inicio) y se replican en el CSV de libro diario en `backend/data/raw/2026-2.csv`.
  Cada transacción nueva registrada en la aplicación se guarda en ambos destinos.

## Desarrollo

Consulte `backend/README.md` y `frontend/src/README.md` para notas de desarrollo de API y panel, y `docker-compose.yml` para el stack de desarrollo basado en Docker (Postgres + backend + frontend).
El build de escritorio descrito arriba no utiliza Docker: ejecuta el backend directamente con un entorno virtual Python local y base de datos SQLite.
