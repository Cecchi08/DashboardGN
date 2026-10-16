# Subir el dashboard a Azure Static Web Apps (org-only)

Esta guía es **una sola vez**. Después actualizás todo con un solo `scripts/windows/subir_a_azure.bat`.

Resultado final: una URL del estilo `https://nucleo-ventas.azurestaticapps.net/` que solo abre la gente de tu organización (login obligatorio con su cuenta de Microsoft 365).

---

## Lo que vas a necesitar

- Cuenta de Azure activa (✅ ya la tenés).
- Permisos para registrar una app en Entra ID de tu organización. Si no los tenés, se los pedís a tu admin de IT — es 1 minuto.
- **Node.js** instalado en tu PC (lo necesita el SWA CLI). Si no lo tenés, el `scripts/windows/subir_a_azure.bat` te avisa y te abre la página de descarga.

---

## Paso 1 — Crear el Static Web App en Azure

1. Entrá a [https://portal.azure.com](https://portal.azure.com).
2. Buscá **"Static Web Apps"** en la barra de búsqueda de arriba y entrá.
3. Click en **+ Create**.
4. Llenar el formulario:
   - **Subscription**: tu suscripción.
   - **Resource Group**: creá uno nuevo, llamalo `rg-nucleo-dashboards` (o lo que quieras).
   - **Name**: `nucleo-ventas` (o el que prefieras — esto es parte de la URL final).
   - **Plan type**: **Free**.
   - **Region**: **East US 2** (o West Europe — elegí la más cercana).
   - **Source**: **Other**. ⚠ Importante: NO elijas GitHub ni Azure DevOps porque vamos a deployar desde tu PC.
5. Click **Review + create** → **Create**. Esperá 30 segundos a que diga "Your deployment is complete".
6. Click **Go to resource**.

## Paso 2 — Sacar el Deployment Token

1. En la página de tu Static Web App recién creada, en el menú izquierdo buscá **Overview**.
2. Arriba a la derecha vas a ver un botón **"Manage deployment token"**. Click.
3. Aparece una ventana con un token largo. Click en el ícono de copiar 📋.
4. **No cierres esta ventana todavía** — vas a necesitar el token en el Paso 5.

Tip: el token NO es un password — solo sirve para subir archivos a este SWA específico. No le da acceso a nada más de tu cuenta.

## Paso 3 — Sacar el Tenant ID de tu organización

1. En el portal de Azure, buscá **"Microsoft Entra ID"** y entrá.
2. En el menú izquierdo, click en **Overview**.
3. Vas a ver el **Tenant ID** (un GUID tipo `abc12345-1234-1234-1234-1234567890ab`). Copialo.

## Paso 4 — Registrar una App en Entra ID (para el login)

1. Sin salir de Microsoft Entra ID, en el menú izquierdo click en **App registrations** → **+ New registration**.
2. Llenar:
   - **Name**: `nucleo-ventas-auth` (interno, lo ves solo vos).
   - **Supported account types**: **Accounts in this organizational directory only (Single tenant)**. ⬅ Esto restringe el login solo a tu organización.
   - **Redirect URI**:
     - Plataforma: **Web**
     - URL: `https://<el-nombre-de-tu-app>.azurestaticapps.net/.auth/login/aad/callback`
       - Reemplazá `<el-nombre-de-tu-app>` por lo que pusiste en el Paso 1 (ejemplo: `nucleo-ventas.azurestaticapps.net`).
       - El URL exacto lo encontrás en la página Overview del Static Web App, en el campo "URL".
3. Click **Register**.
4. Una vez creada, vas a estar en la página de la app. Anotá:
   - **Application (client) ID** (otro GUID, en la página principal de la app).

## Paso 5 — Crear el Client Secret

1. En la app que acabás de registrar, en el menú izquierdo click en **Certificates & secrets**.
2. Tab **Client secrets** → **+ New client secret**.
3. **Description**: `nucleo-ventas-secret`. **Expires**: 24 months (o el máximo que te deje).
4. Click **Add**.
5. **⚠ COPIÁ EL VALUE AHORA**. Es lo único que vas a ver una sola vez. Si cerrás la página, tenés que crear otro secret.

## Paso 6 — Configurar las variables del Static Web App

1. Volvé a la página de tu Static Web App (Paso 1).
2. En el menú izquierdo: **Settings** → **Environment variables** (o "Configuration" en algunas versiones).
3. Agregar dos variables:
   - **Name**: `AAD_CLIENT_ID` · **Value**: el Application (client) ID del Paso 4.
   - **Name**: `AAD_CLIENT_SECRET` · **Value**: el Value del client secret del Paso 5.
4. Click **Save**.

## Paso 7 — Crear `config/.azure-config.json`

En la carpeta `config/` dentro del proyecto, creá un archivo nuevo llamado **`.azure-config.json`** con este contenido (reemplazando los valores):

```json
{
  "tenantId": "ACA-EL-TENANT-ID-DEL-PASO-3",
  "deploymentToken": "ACA-EL-DEPLOYMENT-TOKEN-DEL-PASO-2"
}
```

Guardá el archivo como `config/.azure-config.json`.

## Paso 8 — Subir el dashboard

Doble click en **`scripts/windows/subir_a_azure.bat`**. La primera vez:
1. Te avisa si te falta Node.js y abre la página de descarga.
2. Instala el Azure SWA CLI (`npm install -g @azure/static-web-apps-cli`).
3. Prepara la carpeta con los archivos.
4. Sube todo a Azure.

Las siguientes veces es directo: prepara y sube, ~1-2 minutos.

## Paso 9 — Probar

Abrí la URL de tu Static Web App (Paso 1, Overview > URL). Deberías:
1. Ver una pantalla de login de Microsoft.
2. Loguearte con tu cuenta de la organización.
3. Aparece el dashboard con precios.

Para la versión Vendedores (sin precios), agregale `/vendedores` al final de la URL:
`https://nucleo-ventas.azurestaticapps.net/vendedores`

**Si tu equipo intenta entrar con una cuenta personal (gmail, hotmail) o de otra organización, va a recibir un error de login. Solo cuentas de tu tenant entran.**

---

## Flujo de actualización diario

```
┌─────────────────────────┐
│ 1. actualizar.bat       │  ← procesa los Excel nuevos, regenera los HTMLs
├─────────────────────────┤
│ 2. subir_a_azure.bat    │  ← sube los archivos nuevos a Azure
└─────────────────────────┘
```

Después de eso, todos los que tienen el link ven los datos nuevos al refrescar la página.

---

## Costos

- Plan **Free** de Static Web Apps: GRATIS hasta 100 GB de transferencia/mes.
- Para 30-50 vendedores que abren el dashboard todos los días: andás holgado.
- Si te pasás de 100 GB, el sitio se "pausa" hasta el mes siguiente (Azure no te cobra extra sin avisar). Si necesitás más, el plan Standard cuesta ~USD 9/mes.

## Problemas comunes

**"Login failed" / "AADSTS50020"** — el usuario no es del tenant. Esto es lo esperado para cuentas externas; significa que la restricción funciona.

**"Welcome to Azure Static Web Apps" en vez de tu dashboard** — el deploy todavía no terminó o falló. Esperá 1-2 minutos y refrescá. Si persiste, revisá la consola del `scripts/windows/subir_a_azure.bat` por errores.

**"401 Unauthorized" infinito en loop** — chequeá que `AAD_CLIENT_ID` y `AAD_CLIENT_SECRET` estén bien configurados en el SWA (Paso 6). Si copiaste mal el secret, se ve solo una vez y no podés recuperarlo, tenés que crear uno nuevo.

**"Cannot find module" cuando corro subir_a_azure.bat** — falta Node.js. Instalalo desde [nodejs.org](https://nodejs.org/) (la opción LTS).

---

## Cómo dar de baja la app (por las dudas)

1. Portal Azure → Static Web Apps → tu app → **Delete**.
2. Microsoft Entra ID → App registrations → tu app → **Delete**.
3. Borrar el `config/.azure-config.json` de la carpeta.

Sin huellas. La cuenta de Azure no te cobra mientras esté en plan Free.
