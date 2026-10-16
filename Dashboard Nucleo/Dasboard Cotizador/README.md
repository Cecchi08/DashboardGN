# Cotizador y catálogo

Aplicación estática para consultar artículos, preparar cotizaciones y exportar listados. Los archivos Excel se procesan durante la generación; el resultado es un HTML autocontenido que se puede abrir sin servidor.

## Estructura del proyecto

```text
.
├── docs/                 # Excel de entrada y archive/ para versiones anteriores
├── dist/                 # Entregables generados
│   └── cotizador.html
├── scripts/              # Build, watcher y accesos directos de Windows
├── src/
│   ├── app/
│   │   ├── scripts/      # Interfaz separada por funcionalidad
│   │   ├── styles/       # Estilos
│   │   └── template.html
│   └── data/             # Lectura de Excel y normalización
├── package.json
└── README.md
```

### Código de interfaz

Los scripts de `src/app/scripts/` se ensamblan en orden numérico para mantener un solo script clásico en el HTML final:

- `01-runtime.js`: datos, estado y utilidades compartidas.
- `02-catalog.js`: búsqueda, filtros y renderizado del catálogo.
- `03-quote.js`: carrito y cotización.
- `04-listing.js`: filtrado y renderizado del listado.
- `05-export.js`: impresión, PDF y correo.
- `06-app.js`: eventos e inicialización.

El orden de ensamblado se configura en `scripts/build.js`, ya que los módulos comparten estado en el ámbito global del navegador.

## Requisitos y comandos

- Node.js 18 o superior.
- Ejecutar `npm install` una vez para instalar dependencias.

```bash
npm run build  # Genera dist/cotizador.html
npm run watch  # Vigila docs/ y regenera el cotizador al cambiar un Excel
```

En Windows también se pueden usar `scripts/Actualizar.bat` para generar y abrir el cotizador, o `scripts/Vigilar.bat` para dejar activo el seguimiento.

## Datos de entrada

Guardar en `docs/` las exportaciones:

- `Articulos lista 5 y 8*.xlsx`: stock por depósito, datos del artículo y listas de precios.
- `Detalle Aging*.xlsx`: buckets de antigüedad, PM y precios unitarios en pesos y dólares.

El generador selecciona el archivo más reciente de cada tipo, ignora los temporales `~$...` y mueve versiones anteriores a `docs/archive/` al completar el build. Los Excel archivados ya no se usan como entrada.

La consolidación combina stock, depósitos, precios en ambas monedas y antigüedad por código. El tipo de cambio implícito se estima con la mediana de las relaciones de precio entre pesos y dólares. También incluye artículos presentes solo en el archivo de aging, sin depósitos.

## Flujo de generación

1. `scripts/build.js` localiza y lee los Excel mediante `src/data/input-files.js`.
2. `src/data/normalizers.js` limpia números y texto para el proceso de consolidación.
3. El generador integra los datos, estilos y scripts de la aplicación en la plantilla.
4. Se escribe `dist/cotizador.html` como archivo único, listo para compartir.

Los cambios de interfaz se hacen en `src/app/`. Si Power BI cambia los nombres de los archivos, actualizar los patrones al inicio de `src/data/input-files.js` y `scripts/watch.js`.
