# Cómo actualizar el dashboard online (paso a paso diario)

Después de hacer el setup inicial de `LEEME-CLOUDFLARE.md`, **el flujo diario son solo 2 doble-clicks**.

## Resumen visual

```
1. Copiar el Excel nuevo en `docs/data/input/`
2. Doble-click → scripts/windows/actualizar.bat              (1-3 min)
3. Doble-click → scripts/windows/subir_a_la_nube.bat      (2-4 min)
4. Esperar 2 minutos
5. Avisar al equipo → Ctrl+F5 en el navegador
```

**Total: ~5-7 minutos de tu tiempo activo.**

---

## Paso 1 — Copiar el Excel nuevo

Dejá el archivo de Detalle de Venta nuevo (mes incremental) en `docs/data/input/`, junto con los otros. **No borres los anteriores** — el pipeline necesita los archivos por año para mergear.

## Paso 2 — scripts/windows/actualizar.bat

Doble-click. Esto:

- Lee los Excel nuevos.
- Mergea con los datos históricos (no toca los años 2019-2024, solo agrega días posteriores al último ya cargado).
- Hace chequeo de seguridad: si el total de transacciones nuevas es MENOR al anterior, frena (sería pérdida de datos).
- Regenera los 4 HTMLs locales:
  - `dist/local/Dashboard Ventas.html` (con precios, liviano)
  - `dist/local/Dashboard Ventas - Vendedores.html` (sin precios, liviano)
  - `dist/standalone/Dashboard Ventas (autónomo).html` (88 MB, todo embebido)
  - `dist/standalone/Dashboard Ventas - Vendedores (autónomo).html` (88 MB, todo embebido)

**Si querés ver los datos vos primero** antes de publicar, abrí `dist/local/Dashboard Ventas.html` con doble click. Si está todo bien, seguís con el paso 3.

## Paso 3 — scripts/windows/subir_a_la_nube.bat

> ℹ️ El script se llama `scripts/windows/subir_a_la_nube.bat` (antes era `subir_a_cloudflare.bat`). Norton bloquea la creación/edición de un archivo con ese nombre viejo, por eso quedó con nombre nuevo. Hace exactamente lo mismo.

Doble-click. Esto:

1. Verifica que tenés Python, Node.js (v22+), GitHub CLI y Git instalados.
2. Verifica que estés logueado en Cloudflare y GitHub (la primera vez te abre el navegador; después no).
3. Prepara los HTMLs apuntando a las URLs de GitHub Pages.
4. **Sube `data.js`, `aging.js`, `chart.umd.js`** al repo de GitHub vía `git push` (1-3 min — el grueso es el data.js de ~88 MB).
5. **Sube los HTMLs livianos** a Cloudflare Pages vía Wrangler (10-30 seg).

Al final te muestra:

```
Tu dashboard esta en:
  https://nucleo-ventas.pages.dev
```

## Paso 4 — Esperar 2 minutos

GitHub Pages tarda 1-2 min en propagar los archivos nuevos por su red de CDN global.

## Paso 5 — Avisar al equipo

Que apreten **Ctrl+F5** (refresh duro, ignora cache del navegador). Pueden seguir trabajando, pero si refrescan antes de los 2 min puede que vean los datos viejos.

---

## URLs del equipo

**Para vendedores (sin precios ni márgenes):**
👉 https://nucleo-ventas.pages.dev/vendedores

**Para gerencia (versión completa, con precios y profit):**
👉 https://nucleo-ventas.pages.dev

Las dos están protegidas por login email. Solo entran cuentas que terminen en `@gruponucleo.com.ar` (y la tuya `Pabrivarola@gmail.com` que agregamos explícitamente como excepción).

**Cómo entran ellos la primera vez:**
1. Abren la URL.
2. Cloudflare les pide email → escriben el suyo de Grupo Núcleo.
3. Reciben un PIN de 6 dígitos por mail.
4. Pegan el PIN → entran al dashboard.
5. La sesión les dura **1 semana** (configurable).

---

## Problemas que pueden aparecer

### "El dashboard muestra los datos de ayer"

GitHub Pages a veces tarda más de 2 min en propagar. Esperá 5 min más y refrescá con Ctrl+F5. Si sigue así, verificá que el bat terminó con `✓ Push a GitHub completado`.

### Norton bloquea o borra el .bat

Si Norton (u otro antivirus) marca `scripts/windows/subir_a_la_nube.bat`, agregalo como excepción, o deshabilitá la protección un momento para correrlo. El .bat solo llama scripts de Python y a `git`/`wrangler`; no tiene nada raro.

### "Login en loop, no me deja entrar"

Sesión vieja en cache. Abrí una ventana incógnita nueva.

### Un nuevo miembro del equipo no puede entrar

Su email no está en la policy de Cloudflare. Entrá a Cloudflare → Zero Trust → Access → Applications → "Dashboard Núcleo" → editás la policy "Solo Grupo Núcleo" y agregás otra regla con su email exacto (o ya está cubierta si termina en `@gruponucleo.com.ar`).

### Te pide login en Cloudflare/GitHub aunque ya lo hiciste antes

El token se vencerá cada tantos meses. Volvé a loguear cuando te lo pida — los datos quedan exactamente igual.

### Hay un error en el bat que no entendés

Sacale screenshot al CMD y pasámelo en la próxima conversación. Casi todos los errores tienen fix de 1 min.

---

## Si querés volver atrás (apagar todo)

Está documentado en `LEEME-CLOUDFLARE.md`, sección "Cómo dar de baja todo". Resumen: borrás el repo GitHub, borrás el proyecto Cloudflare Pages, borrás la app de Zero Trust, borrás `config/.cloudflare-config.json`. Cero huella, ninguna cuenta cobra nada.
