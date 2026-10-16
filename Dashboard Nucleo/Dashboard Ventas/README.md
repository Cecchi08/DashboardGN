# Dashboard Ventas

Dashboard de ventas con una versión completa para uso interno y otra versión para vendedores. El actualizador consolida exportaciones Excel y genera páginas HTML locales y paquetes para Azure Static Web Apps o Cloudflare Pages.

## Estructura

```text
.
├── config/                 # Configuración local de Azure y Cloudflare
├── data/
│   ├── cache/excel/         # Caché de lectura de los archivos fuente
│   └── processed/           # JSON y JavaScript generados para los dashboards
├── dist/
│   ├── local/               # HTMLs livianos y recursos locales
│   ├── standalone/          # HTMLs autónomos, con los datos embebidos
│   ├── azure/               # Paquete listo para Azure Static Web Apps
│   └── cloudflare/          # Paquete listo para Cloudflare Pages
├── docs/
│   ├── data/input/          # Exportaciones Excel vigentes
│   ├── data/archive/        # Exportaciones históricas y obsoletas
│   ├── guides/              # Guías operativas y de publicación
│   ├── manuals/             # Manuales de usuario
│   └── reference/           # Notas auxiliares
├── scripts/
│   ├── build/               # Construcción de dashboards y versiones autónomas
│   ├── deploy/              # Preparación y publicación de paquetes
│   ├── update/              # Actualización y consolidación de datos
│   └── windows/             # Accesos directos para Windows y macOS
├── src/
│   ├── templates/           # Plantilla HTML principal
│   └── vendor/              # Librerías de terceros
└── requirements.txt
```

Las credenciales de despliegue se guardan en `config/` y están excluidas del control de versiones. Los Excel y los datos generados también se excluyen para evitar subir información comercial por accidente.

## Actualización de datos

1. Copiar las exportaciones nuevas en `docs/data/input/`. Mantener allí los archivos anuales requeridos para el merge.
2. Ejecutar `scripts/windows/actualizar.bat` en Windows o `scripts/windows/actualizar.command` en macOS. También se puede ejecutar `python scripts/update/actualizar.py` desde la raíz del proyecto.
3. Revisar las versiones locales en `dist/local/`. El proceso genera también las versiones autónomas en `dist/standalone/`.

El actualizador conserva la caché de Excel en `data/cache/excel/`, los archivos consolidados en `data/processed/` y archiva entradas obsoletas en `docs/data/archive/`.

## Publicación

- Azure: ejecutar `scripts/windows/subir_a_azure.bat`. El paquete de publicación se prepara en `dist/azure/`.
- Cloudflare Pages y GitHub Pages: ejecutar `scripts/windows/subir_a_la_nube.bat`. Los archivos de Cloudflare quedan en `dist/cloudflare/`; el contenido pesado de datos se publica desde el repositorio configurado.

Las configuraciones locales esperadas son `config/.azure-config.json` y `config/.cloudflare-config.json`. Las guías paso a paso están en `docs/guides/`.

## Requisitos

- Python 3.8 o superior.
- Dependencia Python: `python -m pip install -r requirements.txt` (el actualizador también detecta e instala `openpyxl` si falta).
- Para publicar: Node.js y las herramientas de Azure o Cloudflare/GitHub indicadas en las guías.
