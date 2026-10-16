#!/usr/bin/env python3
"""Genera versiones autónomas (standalone) de ambos dashboards.

Toma los HTML actuales que cargan data.js y aging.js externos, los reemplaza
por bloques <script>...</script> con el contenido embebido. Además embebe
chart.js para que no se necesite internet. El resultado son dos archivos
independientes que NO necesitan la carpeta _internal ni conexión.

Salida (en la carpeta padre, junto a los HTML livianos):
- "Dashboard Ventas (autónomo).html"
- "Dashboard Ventas - Vendedores (autónomo).html"

Este script se invoca desde actualizar.py automáticamente cuando se ejecuta
actualizar.bat. También se puede correr a mano desde la raíz del proyecto con:
    python scripts/build/inline_dashboards.py
"""
import os, re, sys
from pathlib import Path

# El script vive en scripts/build/ y resuelve todas las rutas desde la raíz del proyecto.
SCRIPT_DIR = Path(__file__).parent.resolve()
BASE = SCRIPT_DIR.parents[1]

DATA_DIR = BASE / "data" / "processed"
LOCAL_DIR = BASE / "dist" / "local"
STANDALONE_DIR = BASE / "dist" / "standalone"
DATA_JS = DATA_DIR / "data.js"
AGING_JS = DATA_DIR / "aging.js"
CHART_JS = BASE / "src" / "vendor" / "chart.umd.js"

INPUTS = [
    ('Dashboard Ventas.html', 'Dashboard Ventas (autónomo).html'),
    ('Dashboard Ventas - Vendedores.html', 'Dashboard Ventas - Vendedores (autónomo).html'),
]

# Validaciones de archivos requeridos
for required in [DATA_JS, AGING_JS, CHART_JS]:
    if not required.exists():
        print(f"ERROR: falta {required.name} en {required.parent}")
        sys.exit(1)

print(f"[1/4] Leyendo data.js ({DATA_JS.stat().st_size/1024/1024:.1f} MB)...")
with open(DATA_JS, 'r', encoding='utf-8') as f:
    data_js = f.read()

print(f"[2/4] Leyendo aging.js ({AGING_JS.stat().st_size/1024:.1f} KB)...")
with open(AGING_JS, 'r', encoding='utf-8') as f:
    aging_js = f.read()

print(f"[2b/4] Leyendo chart.umd.js ({CHART_JS.stat().st_size/1024:.1f} KB)...")
with open(CHART_JS, 'r', encoding='utf-8') as f:
    chart_js = f.read()

# Construir bloque inline con data + aging
inline_block = (
    '<script>\n'
    '/* === EMBEDDED: data.js (autónomo) === */\n'
    + data_js +
    '\n/* === EMBEDDED: aging.js (autónomo) === */\n'
    + aging_js +
    '\n</script>'
)

# Reemplazo target: las dos líneas <script src="_internal/data.js"></script>
# y <script src="_internal/aging.js"></script>, posiblemente separadas por
# whitespace/newlines.
PATTERN = re.compile(
    r'<script\s+src="_internal/data\.js"></script>\s*<script\s+src="_internal/aging\.js"></script>'
)

# Bloque para reemplazar Chart.js (CDN externo) por uno embebido.
CHART_PATTERN = re.compile(
    r'<script\s+src="https://cdn\.jsdelivr\.net/npm/chart\.js@[^"]+"></script>'
)
chart_inline = (
    '<script>\n'
    '/* === EMBEDDED: chart.js v4.4.0 UMD (autónomo, sin CDN) === */\n'
    + chart_js +
    '\n</script>'
)

STANDALONE_DIR.mkdir(parents=True, exist_ok=True)
for src_name, out_name in INPUTS:
    src_path = LOCAL_DIR / src_name
    out_path = STANDALONE_DIR / out_name
    if not src_path.exists():
        print(f"  WARNING No existe {src_name}; omitiendo. (Corré actualizar.bat para regenerarlo.)")
        continue
    print(f"[3/4] Procesando {src_name}...")
    with open(src_path, 'r', encoding='utf-8') as f:
        html = f.read()
    # 1) Reemplazar Chart.js externo por inline
    # Usamos lambdas para evitar que re interprete \1 \s etc en el reemplazo
    html, nC = CHART_PATTERN.subn(lambda m: chart_inline, html, count=1)
    if nC != 1:
        print(f"  WARNING No se pudo embeber Chart.js en {src_name} (matches={nC})")
        sys.exit(1)
    # 2) Reemplazar data.js + aging.js por bloque inline
    html, n = PATTERN.subn(lambda m: inline_block, html, count=1)
    if n != 1:
        print(f"  WARNING No se pudo reemplazar data/aging en {src_name} (matches={n})")
        sys.exit(1)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    sz = out_path.stat().st_size
    print(f"  OK Escrito: {out_name} ({sz/1024/1024:.1f} MB)")

print("[4/4] Listo. Versiones autónomas regeneradas.")
