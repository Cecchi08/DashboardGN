# Subir el dashboard a Cloudflare + GitHub Pages (100% gratis, sin tarjeta)

Esta guía es **una sola vez**. Después actualizás con un solo `scripts/windows/subir_a_la_nube.bat`.

**Arquitectura:**
- **GitHub Pages** (gratis, sin tarjeta) hostea los archivos pesados de datos (`data.js`, `aging.js`, `chart.umd.js`).
- **Cloudflare Pages** (gratis, sin tarjeta) hostea los HTMLs livianos.
- **Cloudflare Zero Trust Access** (gratis hasta 50 usuarios) protege la URL con login email.

Cero tarjeta de crédito en ninguno de los servicios.

URL final: `https://nucleo-ventas.pages.dev` — solo gente con email `@gruponucleo.com.ar` puede entrar.

---

## Lo que vas a necesitar

- Cuenta GitHub (gratis).
- Cuenta Cloudflare (gratis).
- **Node.js** instalado (lo necesita Wrangler CLI).
- **GitHub CLI (gh)** instalado (sube los JS sin necesidad de tener Git local).
- ~20 minutos.

---

## Paso 1 — Crear cuenta GitHub (si no tenés)

1. Andá a [https://github.com/signup](https://github.com/signup).
2. Registrate con un mail (puede ser personal o el de la org).
3. Verificá el mail.

## Paso 2 — Crear un repo PÚBLICO para los datos

1. Una vez logueado, click en **"+"** arriba a la derecha → **New repository**.
2. **Repository name**: `nucleo-data` (o el nombre que quieras, lo vamos a usar después).
3. Marcá **Public** (necesario para que GitHub Pages funcione gratis).
4. Marcá **"Add a README file"** (para que el repo no esté vacío).
5. Click **Create repository**.

> 🔒 Importante: el repo es público pero el dashboard que lo consume va a estar protegido por login Cloudflare. Las URLs de los archivos van a ser algo como `https://tu-usuario.github.io/nucleo-data/data.js` — técnicamente accesibles, pero no las publica nadie ni aparecen en búsquedas.

## Paso 3 — Activar GitHub Pages en el repo

1. Dentro del repo recién creado, click en pestaña **Settings**.
2. Menú izquierdo: **Pages**.
3. **Source**: "Deploy from a branch".
4. **Branch**: `main`, carpeta `/ (root)`. Click **Save**.
5. Esperá 1 minuto. GitHub te muestra la URL: `https://tu-usuario.github.io/nucleo-data/`. **Anotala**.

## Paso 4 — Crear cuenta Cloudflare (si no tenés)

1. Andá a [https://dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up).
2. Registrate con tu mail. Sin tarjeta.
3. Verificá el mail.

## Paso 5 — Crear el proyecto Pages en Cloudflare

1. Menú izquierdo del dashboard Cloudflare: **Workers & Pages** → **Create application** → pestaña **Pages** → **Upload assets**.
2. **Project name**: `nucleo-ventas` (este nombre va a estar en el URL final).
3. Para crear el proyecto, te pide subir algo. Subí cualquier archivo dummy (un HTML cualquiera de prueba) — después lo vamos a sobreescribir desde la PC.
4. Click **Deploy site**.
5. Tu URL queda: `https://nucleo-ventas.pages.dev`. **Anotala**.

## Paso 6 — Activar Zero Trust Access (login org-only)

1. Menú izquierdo Cloudflare: **Zero Trust**.
2. La primera vez te pide nombre de equipo y plan. Elegí **Free**.
3. Dentro de Zero Trust: **Access** → **Applications** → **Add an application** → **Self-hosted**.
4. **Application name**: `Dashboard Núcleo`.
5. **Application domain**: subdomain `nucleo-ventas`, domain `pages.dev` (resulta en `nucleo-ventas.pages.dev`).
6. **Next**.
7. **Add a policy**:
   - **Policy name**: `Solo Grupo Nucleo`
   - **Action**: Allow
   - **Configure rules** → **Include** → **Emails ending in**: `@gruponucleo.com.ar`
8. **Next** → **Add application**.

## Paso 7 — Instalar Node.js y GitHub CLI

Si no los tenés:

- **Node.js**: bajá desde [https://nodejs.org/](https://nodejs.org/) la versión LTS (botón verde grande). Instalá normal.
- **GitHub CLI**: bajá desde [https://cli.github.com/](https://cli.github.com/). Para Windows hay un instalador `.msi`.

Después de instalar ambos, **cerrá y abrí** la terminal/CMD para que se actualicen los PATH.

## Paso 8 — Editar `config/.cloudflare-config.json`

Abrí `config/.cloudflare-config.json` y reemplazá los valores:

```json
{
  "pagesProject": "nucleo-ventas",
  "githubRepo": "tu-usuario-github/nucleo-data",
  "githubBranch": "main",
  "dataBaseUrl": "https://tu-usuario-github.github.io/nucleo-data",
  "orgEmailDomain": "gruponucleo.com.ar"
}
```

- `githubRepo`: tu usuario de GitHub + `/` + nombre del repo (Paso 2).
- `dataBaseUrl`: la URL de GitHub Pages (Paso 3), sin barra al final.
- `pagesProject`: el nombre del proyecto Cloudflare (Paso 5).

Guardá el archivo (borrá la línea `__readme__` si está).

## Paso 9 — Primera subida

Doble-click en **`scripts/windows/subir_a_la_nube.bat`**.

> ℹ️ Se llama `scripts/windows/subir_a_la_nube.bat` (no `subir_a_cloudflare.bat`) porque Norton bloquea ese nombre. Si Norton lo marca, agregalo como excepción o deshabilitá la protección mientras lo corrés.

La primera vez:

1. Verifica que tenés Node.js y gh CLI. Si falta alguno te dice cuál.
2. Instala **Wrangler CLI** (`npm install -g wrangler`).
3. Abre navegador para login en Cloudflare (una vez).
4. Abre navegador para login en GitHub (una vez).
5. Prepara los HTMLs apuntando a GitHub Pages.
6. Sube `data.js`, `aging.js`, `chart.umd.js` al repo GitHub vía API (commits automáticos).
7. Sube los HTMLs a Cloudflare Pages.

Al final te muestra la URL: `https://nucleo-ventas.pages.dev`.

> ⏱ La primera vez `data.js` tarda 1-3 min en subir (88 MB). GitHub Pages tarda otros 1-2 min en propagar el cambio.

## Paso 10 — Probar

1. Abrí la URL en una ventana incógnita.
2. Aparece pantalla de login de Cloudflare Access.
3. Ingresá tu email `@gruponucleo.com.ar`.
4. Llega un PIN de 6 dígitos al mail.
5. Pegalo → entrás al dashboard.

Para versión Vendedores: `https://nucleo-ventas.pages.dev/vendedores`

---

## Flujo de actualización diario

```
1. actualizar.bat              (procesa Excel + regenera HTMLs locales)
2. subir_a_la_nube.bat      (sube a GitHub + Cloudflare ~3-4 min)
3. Equipo refresca con Ctrl+F5 (datos nuevos)
```

---

## Costos

- **GitHub Pages**: 1 GB storage + 100 GB bandwidth/mes gratis.
- **Cloudflare Pages**: ilimitado.
- **Cloudflare Zero Trust**: hasta 50 usuarios/mes.

Todo gratis sin tarjeta de crédito.

## Problemas comunes

**"npm: command not found"** — falta Node.js. Instalalo desde [nodejs.org](https://nodejs.org/).

**"gh: command not found"** — falta GitHub CLI. Instalalo desde [cli.github.com](https://cli.github.com/).

**"413 Payload Too Large" al subir data.js** — pasaste de 100 MB por archivo. Pedile a Ariel para ver si conviene dividir el archivo.

**El dashboard muestra datos viejos** — GitHub Pages cachea agresivo. Esperá 2 min después de `scripts/windows/subir_a_la_nube.bat`, después Ctrl+F5 en el navegador.

**"GitHub API rate limit exceeded"** — pasó el límite de la API. Esperá 1 hora.

**Login en loop** — sesión vieja en cache. Ventana incógnita nueva.

---

## Cómo dar de baja todo

1. GitHub: Settings del repo → **Delete this repository**.
2. Cloudflare: Workers & Pages → tu proyecto → Settings → **Delete project**.
3. Cloudflare: Zero Trust → Access → tu app → Delete.
4. Borrar `config/.cloudflare-config.json` de la carpeta.

Sin huellas. Ninguna cuenta cobra nada.
