#!/usr/bin/env python3
"""Arma la carpeta `dist/azure/` con todo lo necesario para subir a Azure
Static Web Apps. Incluye los dos HTMLs livianos, los JS de datos, y un
staticwebapp.config.json con autenticación de Entra ID restringida al tenant
configurado en .azure-config.json (lo crea subir_a_azure.bat).

Estructura resultante:
    dist/azure/
        index.html              <- Dashboard Ventas (con precios)
        vendedores.html         <- Dashboard Ventas Vendedores
        _internal/
            data.js
            aging.js
        staticwebapp.config.json
"""
import json, shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
BASE = SCRIPT_DIR.parents[1]
DIST = BASE / "dist" / "azure"
CONFIG_FILE = BASE / "config" / ".azure-config.json"

# Validaciones
required = {
    "Dashboard Ventas.html": BASE / "dist" / "local" / "Dashboard Ventas.html",
    "Dashboard Ventas - Vendedores.html": BASE / "dist" / "local" / "Dashboard Ventas - Vendedores.html",
    "_internal/data.js": BASE / "data" / "processed" / "data.js",
    "_internal/aging.js": BASE / "data" / "processed" / "aging.js",
}
for label, path in required.items():
    if not path.exists():
        print(f"ERROR: falta {label}. Corré actualizar.bat primero.")
        raise SystemExit(1)

if not CONFIG_FILE.exists():
    print(f"ERROR: falta {CONFIG_FILE.name}. Lo crea subir_a_azure.bat la primera vez.")
    raise SystemExit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

tenant_id = cfg.get("tenantId")
if not tenant_id:
    print("ERROR: .azure-config.json no tiene tenantId. Editalo a mano.")
    raise SystemExit(1)

# Recrear DIST limpio
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir(parents=True)
(DIST / "_internal").mkdir()

# Copiar archivos
shutil.copy2(required["Dashboard Ventas.html"], DIST / "index.html")
shutil.copy2(required["Dashboard Ventas - Vendedores.html"], DIST / "vendedores.html")
shutil.copy2(required["_internal/data.js"], DIST / "_internal" / "data.js")
shutil.copy2(required["_internal/aging.js"], DIST / "_internal" / "aging.js")

# Generar staticwebapp.config.json
# - openIdIssuer apunta al tenant específico -> bloquea logins de otros tenants
# - allowedRoles=["authenticated"] en /* -> todo requiere login
# - 401 -> redirect a login automáticamente
swa_config = {
    "auth": {
        "identityProviders": {
            "azureActiveDirectory": {
                "registration": {
                    "openIdIssuer": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                    "clientIdSettingName": "AAD_CLIENT_ID",
                    "clientSecretSettingName": "AAD_CLIENT_SECRET"
                }
            }
        }
    },
    "routes": [
        {"route": "/login", "rewrite": "/.auth/login/aad"},
        {"route": "/logout", "redirect": "/.auth/logout"},
        {"route": "/.auth/login/github", "statusCode": 404},
        {"route": "/vendedores", "rewrite": "/vendedores.html"},
        {"route": "/*", "allowedRoles": ["authenticated"]}
    ],
    "responseOverrides": {
        "401": {"redirect": "/.auth/login/aad", "statusCode": 302}
    },
    # SPA-style fallback: requests sin extensión van a index.html
    # (lo que arregla el loop en la URL raíz "/")
    "navigationFallback": {
        "rewrite": "/index.html",
        "exclude": ["/_internal/*", "/*.{js,css,html,ico,png,jpg,svg,json,map}"]
    }
    # Nota: NO ponemos globalHeaders Cache-Control porque cachea los redirects
    # 302 a login y rompe el flujo de auth en navegadores. SWA ya aplica gzip
    # por defecto a archivos grandes, así que data.js se transmite comprimido.
}
with open(DIST / "staticwebapp.config.json", 'w', encoding='utf-8') as f:
    json.dump(swa_config, f, indent=2, ensure_ascii=False)

# Resumen
total_size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
print(f"OK dist/azure/ listo:")
print(f"    index.html          -> Dashboard con precios")
print(f"    vendedores.html     -> Dashboard Vendedores")
print(f"    _internal/data.js   -> {(DIST / '_internal' / 'data.js').stat().st_size / 1024 / 1024:.1f} MB")
print(f"    _internal/aging.js  -> {(DIST / '_internal' / 'aging.js').stat().st_size / 1024:.1f} KB")
print(f"    staticwebapp.config.json   (auth Entra ID, tenant {tenant_id[:8]}...)")
print(f"    Total a subir: {total_size / 1024 / 1024:.1f} MB")
