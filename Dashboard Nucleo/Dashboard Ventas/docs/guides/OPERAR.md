# Cómo actualizar el dashboard — paso a paso

Esta es la rutina cuando llegan datos nuevos del sistema. **Toda la operación toma 3-5 minutos.**

---

## URLs del dashboard (compartir al equipo)

- **Con precios** (uso interno): https://lemon-sand-0f572020f.7.azurestaticapps.net
- **Sin precios** (vendedores): https://lemon-sand-0f572020f.7.azurestaticapps.net/vendedores

Solo entran cuentas `@gruponucleo.com.ar`. Cualquiera de la organización con el link puede acceder, no hace falta agregar usuarios.

---

## Rutina cuando llegan datos nuevos

### Paso 1 — Poner los archivos nuevos en `docs/data/input/`

Según qué te llegó:

| Archivo nuevo | Qué hacer |
|---|---|
| `Detalle aging.xlsx` actualizado | Pegalo en `docs/data/input/`. El script archiva versiones anteriores en `docs/data/archive/`. |
| `Detalle de Venta (1).xlsx` (incremental con días recientes) | Pegalo en `docs/data/input/`. Si ya hay un `(1).xlsx` viejo, podés sobreescribirlo. |
| `Detalle de Venta año 2026.xlsx` actualizado (mismo año, más días) | Reemplazá el archivo en `docs/data/input/`. El script detecta el cambio y reparsea. |
| `Detalle de Venta año 2027.xlsx` (año nuevo) | Pegalo en `docs/data/input/`. El script lo suma al merge. |

### Paso 2 — Doble-click en `scripts/windows/actualizar.bat`

Lo que pasa adentro:
- Lee los Excel anuales (rápido si no cambiaron — usa caché).
- Aplica el incremental (solo los días posteriores al último anual).
- **Chequeo de seguridad**: si las transacciones quedan menos que la corrida anterior, ABORTA sin tocar nada.
- Regenera los 4 HTMLs.

Vas a ver mensajes tipo:
```
[CACHE] Anual Detalle de Venta año 2025.xlsx        90,142 filas   ...
[parsed] Anual Detalle de Venta año 2026.xlsx        17,438 filas   ...
[parsed] Incremental Detalle de Venta (1).xlsx       2,692 filas   (+93 nuevas, 2,599 ya cubiertas)
MERGED:       847,199 filas   2019-01-02 → 2026-04-25
```

Si ves "✓ ACTUALIZACIÓN COMPLETA" al final → todo OK, seguí al Paso 3.

### Paso 3 — Doble-click en `scripts/windows/subir_a_azure.bat`

Sube los HTMLs y los datos a Azure (~1-2 minutos para el `data.js` de ~87 MB). Termina con "Subida completa".

### Paso 4 — Verificar

Abrí el dashboard en el navegador y refrescá (Ctrl+F5 para forzar recarga sin caché). Mirá:
- En Resumen, los KPIs reflejan los números nuevos.
- En la pestaña Evolución, el último mes muestra los días que agregaste.
- En Aging, las cantidades cambiaron si subiste un aging nuevo.

### Paso 5 (opcional) — Avisar al equipo

Mensaje corto en el grupo: "Dashboard actualizado al [fecha]". Quien tenga la pestaña abierta solo refresca y ve los datos nuevos.

---

## Si algo falla

### `scripts/windows/actualizar.bat` aborta con "el merge quedó con N transacciones MENOS"

Significa que el merge nuevo tiene menos transacciones que el anterior. Causas típicas:
- Borraste sin querer un `Detalle de Venta año YYYY.xlsx` de la carpeta.
- Un Excel quedó vacío o corrupto al copiarlo.
- El nombre no matchea (debe decir "año YYYY" en los anuales — si lo renombraste, se cuenta como incremental).

Solución: asegurate de tener los 8 anuales (uno por año desde 2019) y volvé a correr.

### `scripts/windows/subir_a_azure.bat` dice "ERROR: no encuentro el archivo .azure-config.json"

Te falta el archivo `config/.azure-config.json`. Mirá `LEEME-AZURE.md` Paso 7 para crearlo (necesitás tu tenant ID y el deployment token de Azure).

### El dashboard no se actualiza después de subir

- Forzá refresco del navegador con **Ctrl+F5** (no solo F5 — Ctrl+F5 ignora la caché).
- Si seguís viendo datos viejos, abrí en ventana incógnita.

### Login pide credenciales en loop

Esto pasó una vez en el setup inicial y se arregló. Si vuelve a pasar:
1. Cerrá TODAS las ventanas del navegador (incluso las que no son del dashboard).
2. Volvé a abrir y entrá a la URL.
3. Si persiste, es un problema de la configuración de Azure → escribirle al que armó el setup.

---

## Tareas eventuales

### Cuando cierra un año (enero/febrero del año siguiente)

Cuando el sistema te dé el export DEFINITIVO del año recién terminado:
1. Reemplazá el `Detalle de Venta año YYYY.xlsx` en la carpeta con la versión final.
2. Corré `scripts/windows/actualizar.bat`. El caché detecta que cambió y reparsea ese año.
3. Corré `scripts/windows/subir_a_azure.bat`.

### Cuando se vence el client secret de Azure (cada 24 meses)

Te llega un mail de Azure ~30 días antes del vencimiento. Para renovarlo:
1. Microsoft Entra ID → App registrations → `nucleo-ventas-auth` → Certificados y secretos.
2. Crear un secret nuevo (mismo procedimiento que el LEEME-AZURE Paso 5).
3. Copiar el "Valor" del nuevo secret.
4. Volver al SWA → Configuración → Variables de entorno → editar `AAD_CLIENT_SECRET` con el valor nuevo → Guardar.
5. (Opcional) Borrar el secret viejo.

---

## Archivos importantes en esta carpeta

- `scripts/windows/actualizar.bat` — procesa Excel y regenera los HTMLs (paso 2).
- `scripts/windows/subir_a_azure.bat` — sube a Azure (paso 3).
- `config/.azure-config.json` — credenciales de deploy. **NO compartir, NO subir a ningún lado.**
- `docs/manuals/Manual Dashboard Ventas.docx` — documentación completa con changelog de versiones.
- `LEEME-AZURE.md` — guía de configuración inicial de Azure (no lo necesitás de nuevo si todo funciona).
- `OPERAR.md` — este archivo.
- `data/processed/` y `src/` — scripts y datos. **No tocar.**
- `docs/data/archive/` — archivos viejos archivados automáticamente.

---

## Resumen visual del flujo

```
   Excel nuevo en carpeta
            ↓
   actualizar.bat                    ← regenera datos + 4 HTMLs (locales)
            ↓
   subir_a_azure.bat                 ← sube a Azure (~1-2 min)
            ↓
   Equipo refresca el navegador      ← ve los datos nuevos
```

Cualquier duda, abrir el `docs/manuals/Manual Dashboard Ventas.docx` que tiene todo explicado en detalle con capturas.
