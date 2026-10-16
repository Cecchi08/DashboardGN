#!/usr/bin/env python3
"""Arma la carpeta `dist/cloudflare/` con los HTMLs livianos apuntando a la
URL base de datos (R2 público o GitHub Pages — lo que esté configurado).

Lee la configuración de .cloudflare-config.json:
    {
      "dataBaseUrl": "https://USUARIO.github.io/REPO",   <- ej GitHub Pages
      "pagesProject": "nucleo-ventas",
      ...
    }

Si usás GitHub Pages, dataBaseUrl es algo como:
    "https://ariel-username.github.io/nucleo-data"

Si usás R2 público, dataBaseUrl es algo como:
    "https://pub-XXXXXXXX.r2.dev"
"""
import json, re, shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
BASE = SCRIPT_DIR.parents[1]
DIST = BASE / "dist" / "cloudflare"
CONFIG_FILE = BASE / "config" / ".cloudflare-config.json"

required = {
    "Dashboard Ventas.html": BASE / "dist" / "local" / "Dashboard Ventas.html",
    "Dashboard Ventas - Vendedores.html": BASE / "dist" / "local" / "Dashboard Ventas - Vendedores.html",
    "_internal/data.js": BASE / "data" / "processed" / "data.js",
    "_internal/aging.js": BASE / "data" / "processed" / "aging.js",
    "_internal/chart.umd.js": BASE / "src" / "vendor" / "chart.umd.js",
}
for label, p in required.items():
    if not p.exists():
        print(f"ERROR: falta {label}. Corré actualizar.bat primero.")
        raise SystemExit(1)

if not CONFIG_FILE.exists():
    print(f"ERROR: falta {CONFIG_FILE.name}. Lo crea subir_a_cloudflare.bat la primera vez.")
    raise SystemExit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

# Aceptar dataBaseUrl (nuevo nombre) o r2PublicUrl (compatibilidad hacia atrás)
data_url = cfg.get("dataBaseUrl") or cfg.get("r2PublicUrl") or ""
data_url = data_url.rstrip('/')
if not data_url or not data_url.startswith("https://"):
    print("ERROR: .cloudflare-config.json no tiene dataBaseUrl válido (debe arrancar con https://).")
    print("       Ej GitHub Pages: https://tu-usuario.github.io/nucleo-data")
    print("       Ej R2 público:    https://pub-XXX.r2.dev")
    raise SystemExit(1)

# Limpiar y recrear DIST
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir(parents=True)

# Patrones de reemplazo en cada HTML
chart_pattern = re.compile(r'<script\s+src="https://cdn\.jsdelivr\.net/npm/chart\.js@[^"]+"></script>')
data_pattern = re.compile(r'<script\s+src="_internal/data\.js"></script>')
aging_pattern = re.compile(r'<script\s+src="_internal/aging\.js"></script>')

chart_new = f'<script src="{data_url}/chart.umd.js"></script>'
data_new = f'<script src="{data_url}/data.js"></script>'
aging_new = f'<script src="{data_url}/aging.js"></script>'

inputs = [
    ('Dashboard Ventas.html', 'index.html'),
    ('Dashboard Ventas - Vendedores.html', 'vendedores.html'),
]

for src_name, out_name in inputs:
    src_path = BASE / "dist" / "local" / src_name
    out_path = DIST / out_name
    with open(src_path, 'r', encoding='utf-8') as f:
        h = f.read()
    h2, n1 = chart_pattern.subn(chart_new, h, count=1)
    h2, n2 = data_pattern.subn(data_new, h2, count=1)
    h2, n3 = aging_pattern.subn(aging_new, h2, count=1)
    if n1 + n2 + n3 < 3:
        print(f"  WARNING {src_name}: chart={n1}, data={n2}, aging={n3} (se esperaba 1+1+1)")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(h2)
    sz = out_path.stat().st_size
    print(f"  OK {out_name}  ({sz/1024:.1f} KB)")

# _headers de Cloudflare Pages
headers_path = DIST / "_headers"
with open(headers_path, 'w', encoding='utf-8') as f:
    f.write(
        "/*\n"
        "  X-Frame-Options: SAMEORIGIN\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "\n"
        "/*.html\n"
        "  Cache-Control: public, max-age=300, must-revalidate\n"
    )

print(f"\nOK dist/cloudflare/ listo en {DIST}")
print(f"  index.html      -> Dashboard con precios")
print(f"  vendedores.html -> Dashboard Vendedores")
print(f"  JS referenciados desde: {data_url}/")
