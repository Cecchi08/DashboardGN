# Dashboard Ventas

Aplicación separada en frontend React/TypeScript y backend Node.js/Express. React recibe las ventas históricas y el aging desde endpoints JSON de la API.

## Estructura

```text
backend/         API Express; imagen de ejecución Node.js
frontend/        Componentes React, TypeScript, Vite y Nginx
docs/data/input/ Excel fuente para regenerar los datos
scripts/update/  Proceso de consolidación de ventas y aging
src/templates/   Plantillas del proceso de datos existente
src/vendor/      Recursos locales usados por la transformación
```

Durante la construcción de la imagen, un paso auxiliar de Python conserva el procesamiento Excel actual y crea JSON optimizado. Python no queda instalado en el backend de ejecución. Los Excel fuente no se incluyen en Git ni en la imagen final; deben estar en `docs/data/input/` en la computadora que construye las imágenes.

## Docker Compose

Desde la raíz del repositorio:

```sh
docker compose up --build -d ventas-api ventas-web
```

- Frontend: `http://IP-DE-LA-COMPUTADORA:5321`
- API: `http://IP-DE-LA-COMPUTADORA:4321/api/health`

La primera compilación puede tardar unos minutos por el procesamiento del histórico. Para actualizar los datos, reemplazá los Excel y ejecutá de nuevo el comando de Compose.
