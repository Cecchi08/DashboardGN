# Dashboard Cotizador

Aplicación separada en frontend React con TypeScript/TSX y API Node.js/Express. React consume el catálogo desde `/api/catalog`; la API lo prepara durante la construcción de su imagen Docker a partir de los Excel de `data/input/`.

## Estructura

```text
backend/       API Express y Dockerfile multietapa
frontend/      Componentes React, TypeScript, Vite y Nginx
data/input/    Excel de artículos y aging usados para generar el catálogo
scripts/       Consolidación de datos del catálogo
src/data/      Lectura y normalización de los archivos fuente
```

## Docker Compose

Desde la raíz del repositorio:

```sh
docker compose up --build -d cotizador-api cotizador-web
```

- Frontend: `http://IP-DE-LA-COMPUTADORA:1235`
- API: `http://IP-DE-LA-COMPUTADORA:1234/api/health`

La primera compilación instala dependencias y procesa los Excel. Para refrescar los datos, reemplazá los Excel en `data/input/` y repetí el comando de Compose.
