# Dashboards Núcleo

Ambos sistemas se ejecutan en Docker Compose y quedan disponibles para los equipos de la red local.

## Servicios y puertos

| Aplicación | Frontend React | API Express |
| --- | ---: | ---: |
| Dashboard Cotizador | 1235 | 1234 |
| Dashboard Ventas | 5321 | 4321 |

Desde la computadora que ejecuta Docker, abrir `http://localhost:1235` o `http://localhost:5321`. Desde otros equipos, reemplazar `localhost` por la dirección IP de la computadora servidor. Si no conecta, permitir los puertos 1235 y 5321 en el firewall de Windows; los puertos API 1234 y 4321 también están publicados.

## Iniciar y detener

Abrir una terminal en la raíz del repositorio y ejecutar:

```sh
docker-compose up --build -d
docker-compose ps
docker-compose down
```

Compose compila las dos interfaces y genera los datos desde los Excel durante la compilación de las imágenes. La primera ejecución demora más. Para actualizar los datos, reemplazar los Excel fuente y reconstruir el servicio correspondiente:

Los Excel de Ventas se conservan fuera de Git para no publicar datos comerciales. Al clonar el proyecto en otra computadora, copiar esos archivos a `Dashboard Nucleo/Dashboard Ventas/docs/data/input/` antes de compilar.

```sh
docker-compose up --build -d cotizador-api cotizador-web
docker-compose up --build -d ventas-api ventas-web
```

Las instrucciones y estructura de cada desarrollo están en `Dashboard Nucleo/Dashboard Cotizador/README.md` y `Dashboard Nucleo/Dashboard Ventas/README.md`.
