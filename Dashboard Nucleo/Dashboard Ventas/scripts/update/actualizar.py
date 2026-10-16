#!/usr/bin/env python3
"""
Actualizador de Dashboards Ventas Núcleo
==========================================

Procesa los archivos Excel en esta carpeta y regenera los dashboards HTML
con la fecha de actualización en el header.

USO:
    1. Poné los archivos Excel nuevos en la carpeta docs/data/input/:
       - Detalle de Venta*.xlsx  (incremental o completo)
       - Detalle - aging.xlsx       (foto actual del aging por buckets)
       - (legacy: Detalle sin rotacion.xlsx — solo se usa si no hay aging)
    2. Ejecutá este script: python scripts/update/actualizar.py
       (o doble-click en actualizar.bat en Windows)
    3. El script:
       a) Archiva en docs/data/archive/ los archivos que ya no se usan
       b) Mergea el histórico con los datos nuevos
       c) Regenera los dos HTML con la fecha de hoy

REQUISITOS:
    - Python 3.8+
    - pip install openpyxl
"""
import os
import sys
import shutil
import json
import subprocess
from datetime import datetime, date
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("ERROR: Falta instalar openpyxl. Ejecutá:  pip install openpyxl")
    sys.exit(1)

# ============================================================
# Paths — el script está PENSADO para correr desde la carpeta
# "Ventas Nucleo" del usuario.
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = SCRIPT_DIR / "docs" / "data" / "input"
OLD_DIR = SCRIPT_DIR / "docs" / "data" / "archive"
OLD_DIR.mkdir(parents=True, exist_ok=True)

# Python scripts that transform template -> final HTML live here (next to the
# template). They accept the data+sin-rot JSON from SCRIPT_DIR as input.
# In the Cowork environment they live in /sessions/…/; for local use the user
# should have them alongside.
TEMPLATE_DIR = SCRIPT_DIR / "src" / "templates"

# ============================================================
# 1. Detect and classify xlsx files
# ============================================================
print("=" * 60)
print("ACTUALIZADOR DASHBOARD VENTAS NÚCLEO")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 60)

# Excluir lockfiles de Excel (~$archivo.xlsx) y temporales
xlsx_files = [f for f in INPUT_DIR.glob("*.xlsx") if not f.name.startswith("~$")]
print(f"\nArchivos Excel encontrados: {len(xlsx_files)}")
for f in xlsx_files:
    print(f"  - {f.name} ({f.stat().st_size // 1024} KB)")

# Classify: Detalle de Venta files and sin rotación / aging files
detalle_files = []
sinrot_files = []
aging_files = []

for f in xlsx_files:
    name = f.name.lower()
    if "aging" in name:
        aging_files.append(f)
    elif "sin rotacion" in name or "sin-rotacion" in name or "sin_rotacion" in name:
        sinrot_files.append(f)
    elif "detalle" in name and "venta" in name:
        detalle_files.append(f)

def _safe_archive(f, label):
    """Mueve f a docs/data/archive/. Si falla (permisos, archivo abierto), avisa y sigue."""
    dest = OLD_DIR / f.name
    try:
        if dest.exists(): dest.unlink()
        shutil.move(str(f), str(dest))
        print(f"  {label} archivado en docs/data/archive/: {f.name}")
    except Exception as e:
        print(f"  No pude archivar {f.name} en docs/data/archive/ ({e}). Lo ignoro y sigo con el más reciente.")

# Si hay varios aging, quedarse con el MÁS RECIENTE y archivar el resto en docs/data/archive/
aging_file = None
if aging_files:
    aging_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    aging_file = aging_files[0]
    for old_aging in aging_files[1:]:
        _safe_archive(old_aging, "Aging viejo")

# Mismo trato para sin rotación (legacy)
sinrot_file = None
if sinrot_files:
    sinrot_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    sinrot_file = sinrot_files[0]
    for old_sr in sinrot_files[1:]:
        _safe_archive(old_sr, "Sin rotación viejo")

if not detalle_files:
    print("\nERROR: No se encontró ningún archivo 'Detalle de Venta*.xlsx'")
    sys.exit(1)
# Preferimos aging; sin rotación es legacy/fallback
if not aging_file and not sinrot_file:
    print("\nERROR: No se encontró 'Detalle - aging.xlsx' ni 'Detalle sin rotacion.xlsx'")
    sys.exit(1)

# Clasificación: "anuales" (Detalle de Venta año YYYY.xlsx) vs "incrementales"
# (cualquier otro Detalle de Venta — típicamente un export reciente con
# nombre tipo "(1).xlsx" que sólo trae días recientes).
import re as _re
year_files = []   # uno por año, se concatenan todos
incr_files = []   # cada uno reemplaza su rango de fechas en el merged
for f in detalle_files:
    if _re.search(r'a[ñn]o\s*\d{4}', f.name, _re.IGNORECASE):
        year_files.append(f)
    else:
        incr_files.append(f)
year_files.sort(key=lambda f: f.name)
incr_files.sort(key=lambda f: f.stat().st_mtime)
print(f"\nArchivos anuales:       {len(year_files)}")
for f in year_files:
    print(f"  - {f.name}")
print(f"Archivos incrementales: {len(incr_files)}")
for f in incr_files:
    print(f"  - {f.name}")
if aging_file:
    print(f"Aging:                  {aging_file.name}")
if sinrot_file:
    print(f"Sin rotación (legacy):  {sinrot_file.name}")
if not year_files and incr_files:
    # No hay anuales — usar el incremental más grande como base (compat con flujos viejos)
    incr_files.sort(key=lambda f: f.stat().st_size, reverse=True)
    year_files = [incr_files[0]]
    incr_files = incr_files[1:]
    print(f"  (sin anuales: uso {year_files[0].name} como base)")

# ============================================================
# 2. Archive files that are clearly obsolete (Venta por Cliente, etc.)
# ============================================================
obsolete_patterns = ["venta por cliente", "venta por subcategoria", "data.xlsx"]
archived = []
for f in xlsx_files:
    name = f.name.lower()
    if any(p in name for p in obsolete_patterns):
        dest = OLD_DIR / f.name
        if dest.exists(): dest.unlink()
        shutil.move(str(f), str(dest))
        archived.append(f.name)
if archived:
    print(f"\nArchivados en docs/data/archive/: {', '.join(archived)}")

# ============================================================
# 3. Process all Detalle files merged
# ============================================================
EPOCH = date(2019, 1, 1)

# ============================================================
# Cache de lectura de Excel.
# Parsear un Detalle de Venta de 90k filas con openpyxl tarda ~30 segundos.
# Como los archivos anuales (año YYYY) ya no cambian, cacheamos el resultado
# en data/cache/excel/<stem>.pkl. La key de invalidación es (mtime, size) del
# Excel original — si esos no cambian, asumimos que el Excel es el mismo.
# ============================================================
import pickle as _pickle
CACHE_DIR = SCRIPT_DIR / "data" / "cache" / "excel"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_VERSION = 1  # bump si cambia el shape de lo que devuelve read_transactions

def _read_transactions_raw(xlsx_path):
    """Read Detalle xlsx, return list of (fecha, row_dict)."""
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows_iter = ws.iter_rows(values_only=True)
    header = list(next(rows_iter))
    idx_header = {c: i for i, c in enumerate(header)}
    out = []
    min_d, max_d = None, None
    for r in rows_iter:
        if r is None or all(v is None for v in r):
            continue
        ifec = idx_header.get('Fecha')
        if ifec is None or ifec >= len(r):
            continue
        fec = r[ifec]
        if not isinstance(fec, datetime):
            continue  # skip footer / total rows
        out.append((fec.date(), r, header))
        if min_d is None or fec.date() < min_d: min_d = fec.date()
        if max_d is None or fec.date() > max_d: max_d = fec.date()
    return out, min_d, max_d

def read_transactions(xlsx_path, use_cache=True):
    """Wrapper con caché por (mtime, size) del archivo fuente.
    Devuelve (data, min_d, max_d, was_cached_bool).
    """
    cache_file = CACHE_DIR / (xlsx_path.stem + ".pkl")
    src_stat = xlsx_path.stat()
    src_key = (CACHE_VERSION, src_stat.st_mtime, src_stat.st_size)
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, 'rb') as fp:
                cached = _pickle.load(fp)
            if cached.get('key') == src_key:
                return cached['data'], cached['min_d'], cached['max_d'], True
        except Exception:
            pass  # cache corrupto: reparseo
    data, min_d, max_d = _read_transactions_raw(xlsx_path)
    if use_cache:
        try:
            with open(cache_file, 'wb') as fp:
                _pickle.dump({'key': src_key, 'data': data,
                              'min_d': min_d, 'max_d': max_d},
                             fp, protocol=_pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"  (No pude guardar caché para {xlsx_path.name}: {e})")
    return data, min_d, max_d, False

# Limpiar cachés huérfanos (de archivos que ya no existen en la carpeta)
known_stems = {f.stem for f in xlsx_files}
for cf in CACHE_DIR.glob("*.pkl"):
    if cf.stem not in known_stems:
        try:
            cf.unlink()
            print(f"  Caché huérfano borrado: {cf.name}")
        except Exception:
            pass

print("\n--- Leyendo archivos de ventas ---")
# 1) Concatenar TODOS los archivos anuales (cada uno trae un año distinto).
#    Los anuales son INTOCABLES: lo histórico no se modifica.
#    Usan caché en data/cache/excel/ — solo se reparsean si el Excel cambió.
merged = []
yearly_max = None  # último día cubierto por los anuales
for yf in year_files:
    yd, ymin, ymax, was_cached = read_transactions(yf)
    tag = "[CACHE]" if was_cached else "[parsed]"
    print(f"  {tag} Anual {yf.name:<35} {len(yd):>8,} filas   {ymin} -> {ymax}")
    merged.extend(yd)
    if yearly_max is None or ymax > yearly_max:
        yearly_max = ymax

# 2) Aplicar cada incremental: SOLO se agregan las filas cuya fecha es
#    POSTERIOR al último día de los anuales. Lo viejo no se toca.
#    Los incrementales también se cachean (igual son chicos, pero ¿por qué no?).
if incr_files:
    if yearly_max is None:
        # No hay anuales: el incremental es la base.
        cutoff = None
        print(f"  (Sin anuales: el incremental se incluye entero)")
    else:
        cutoff = yearly_max
        print(f"  Cutoff: anuales cubren hasta {yearly_max}. Los incrementales solo aportan días posteriores.")
    for inc_file in incr_files:
        inc_data, inc_min, inc_max, was_cached = read_transactions(inc_file)
        tag = "[CACHE]" if was_cached else "[parsed]"
        if cutoff is None:
            new_rows = inc_data
            ignored = 0
        else:
            new_rows = [x for x in inc_data if x[0] > cutoff]
            ignored = len(inc_data) - len(new_rows)
        print(f"  {tag} Incremental {inc_file.name:<28} {len(inc_data):>8,} filas   {inc_min} -> {inc_max}   (+{len(new_rows):,} nuevas, {ignored:,} ya cubiertas)")
        merged.extend(new_rows)
        # Avanzar el cutoff por si llegan varios incrementales
        if new_rows:
            new_max = max(x[0] for x in new_rows)
            if cutoff is None or new_max > cutoff:
                cutoff = new_max

all_txns = merged
txns_min = min(t[0] for t in all_txns)
txns_max = max(t[0] for t in all_txns)
print(f"  MERGED:      {len(all_txns):>8,} filas   {txns_min} -> {txns_max}")

# ============================================================
# SAFETY CHECK: nunca permitir que el dataset se achique.
# Lee el data_raw_v2.json anterior (si existe) y compara totales.
# Si el nuevo es MENOR, aborta sin sobreescribir nada.
# ============================================================
INTERNAL_DIR_CHECK = SCRIPT_DIR / "data" / "processed"
PREV_JSON = INTERNAL_DIR_CHECK / "data_raw_v2.json"
prev_total = None
prev_max_date = None
if PREV_JSON.exists():
    try:
        with open(PREV_JSON, 'r', encoding='utf-8') as fp_prev:
            prev_meta = json.load(fp_prev).get('meta', {})
        prev_total = prev_meta.get('total_rows')
        prev_max_date = prev_meta.get('max_date')
    except Exception as e:
        print(f"  (No pude leer data_raw_v2.json anterior: {e}). Omito el chequeo de seguridad.")

if prev_total is not None:
    print(f"\n--- Chequeo de seguridad ---")
    print(f"  Transacciones anteriores: {prev_total:,}   (hasta {prev_max_date})")
    print(f"  Transacciones nuevas:     {len(all_txns):,}   (hasta {txns_max})")
    if len(all_txns) < prev_total:
        diff = prev_total - len(all_txns)
        print()
        print("  " + "=" * 56)
        print(f"  ERROR ABORTADO: el merge quedó con {diff:,} transacciones MENOS")
        print(f"    que el dataset anterior. Esto suele pasar si:")
        print(f"      - faltó algún archivo anual en la carpeta")
        print(f"      - alguno de los Excel está vacío o corrupto")
        print(f"      - los nombres no matchean (debe decir 'año YYYY' en")
        print(f"        los anuales y cualquier otro nombre en incrementales)")
        print(f"    NO SE ACTUALIZA NADA. Tus HTMLs siguen como estaban.")
        print("  " + "=" * 56)
        sys.exit(1)
    elif len(all_txns) == prev_total:
        print(f"  WARNING Igual cantidad que antes. Posiblemente no agregaste nada nuevo.")
    else:
        print(f"  OK +{len(all_txns) - prev_total:,} transacciones nuevas. Sigo con la actualización.")

# ============================================================
# 4. Build the unified JSON (data_raw_v2.json format)
# ============================================================
print("\n--- Construyendo data_raw_v2.json ---")

str_lookups = {k: {} for k in ['subcat', 'cat', 'marca', 'plat', 'prov', 'suc',
                                'vend', 'clase', 'cond', 'ym', 'codigo', 'clienteName']}

def get_idx(lk, val):
    if val is None or (isinstance(val, str) and not val.strip()):
        val = None
    if val not in lk:
        lk[val] = len(lk)
    return lk[val]

def strn(v):
    return v.strip() if isinstance(v, str) else v

cliente_id_map = {}
articulos_master = {}
transactions = []

for fec_date, r, header in all_txns:
    idx = {c: i for i, c in enumerate(header)}
    def g(key):
        i = idx.get(key)
        if i is None or i >= len(r): return None
        return r[i]

    fecha = g('Fecha')
    cliente = strn(g('Cliente')) or "(sin dato)"
    id_cliente = g('IdCliente')
    cat = strn(g('Categoria'))
    sub = strn(g('SubCategoria'))
    marca = strn(g('Marca'))
    plat = strn(g('Plataforma'))
    vend = strn(g('Vendedor'))
    prov = strn(g('Provincia'))
    suc = strn(g('Sucursal'))
    cond = strn(g('Condicion'))
    clase = strn(g('ClaseCliente'))
    vend_cli = strn(g('VendedorCliente'))
    cantidad = g('Cantidad') or 0
    ventas = g('Importe') or 0
    profit = g('Profit') or 0
    codigo = g('Codigo')
    articulo = strn(g('Articulo'))
    ym = fecha.strftime("%Y-%m")
    days = (fecha.date() - EPOCH).days

    cliNameIdx = get_idx(str_lookups['clienteName'], cliente)
    subIdx = get_idx(str_lookups['subcat'], sub)
    catIdx = get_idx(str_lookups['cat'], cat)
    marcaIdx = get_idx(str_lookups['marca'], marca)
    platIdx = get_idx(str_lookups['plat'], plat)
    provIdx = get_idx(str_lookups['prov'], prov)
    sucIdx = get_idx(str_lookups['suc'], suc)
    vendIdx = get_idx(str_lookups['vend'], vend)
    claseIdx = get_idx(str_lookups['clase'], clase)
    condIdx = get_idx(str_lookups['cond'], cond)
    ymIdx = get_idx(str_lookups['ym'], ym)
    codIdx = get_idx(str_lookups['codigo'], str(codigo) if codigo is not None else None)

    cliIdI = id_cliente if id_cliente else -1
    if id_cliente:
        cliente_id_map[id_cliente] = {
            "id": id_cliente, "nombre": cliente,
            "provincia": prov, "clase": clase, "vendedor": vend_cli
        }

    if codigo is not None:
        ck = str(codigo)
        if ck not in articulos_master:
            articulos_master[ck] = {"articulo": articulo, "marca": marca, "subcat": sub, "cat": cat}

    transactions.append([
        cliNameIdx, cliIdI, subIdx, catIdx, marcaIdx, platIdx, provIdx, sucIdx,
        vendIdx, claseIdx, condIdx, ymIdx, codIdx,
        round(cantidad or 0, 2), round(ventas or 0, 2), round(profit or 0, 2),
        days
    ])

def lk_to_arr(lk):
    arr = [None] * len(lk)
    for k, v in lk.items():
        arr[v] = k
    return arr

total_v = sum(t[14] for t in transactions)
total_p = sum(t[15] for t in transactions)
total_q = sum(t[13] for t in transactions)

OUT = {
    "meta": {
        'total_rows': len(transactions),
        'total_ventas': total_v,
        'total_profit': total_p,
        'total_qty': total_q,
        'min_date': txns_min.isoformat(),
        'max_date': txns_max.isoformat(),
        'epoch': '2019-01-01',
        'update_date': datetime.now().strftime('%Y-%m-%d'),
    },
    "lookups": {k: lk_to_arr(lk) for k, lk in str_lookups.items()},
    "articulosMaster": articulos_master,
    "clientesById": cliente_id_map,
    "rows": transactions,
}

INTERNAL_DIR = SCRIPT_DIR / "data" / "processed"
INTERNAL_DIR.mkdir(parents=True, exist_ok=True)
DATA_JSON = INTERNAL_DIR / "data_raw_v2.json"
with open(DATA_JSON, 'w', encoding='utf-8') as fp:
    json.dump(OUT, fp, ensure_ascii=False, separators=(',', ':'))
# También escribir data.js (para que los HTML lo carguen via <script src>)
DATA_JS = INTERNAL_DIR / "data.js"
with open(DATA_JS, 'w', encoding='utf-8') as fp:
    fp.write('const __DATA__ = ')
    json.dump(OUT, fp, ensure_ascii=False, separators=(',', ':'))
    fp.write(';')

print(f"  data_raw_v2.json: {DATA_JSON.stat().st_size // 1024} KB")
print(f"  Transacciones:    {len(transactions):,}")
print(f"  Período:          {txns_min} -> {txns_max}")
print(f"  Ventas:           ${total_v:,.2f}")
print(f"  Profit:           ${total_p:,.2f}  ({total_p*100/total_v:.2f}% margen)")

# ============================================================
# 5. Process aging (preferido) o sin rotación (legacy)
# ============================================================
if aging_file:
    print("\n--- Construyendo aging.js (con buckets) ---")
    wb = openpyxl.load_workbook(str(aging_file), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows_iter = ws.iter_rows(values_only=True)
    header = list(next(rows_iter))
    idx = {c: i for i, c in enumerate(header)}
    def g_ag(row, key):
        i = idx.get(key)
        if i is None or i >= len(row): return None
        return row[i]

    BUCKETS = ['0a30', '30a60', '60a90', '90a150', '150a365', 'Mas365']
    aging_data = {}
    for r in rows_iter:
        if r is None or all(v is None for v in r): continue
        cod = g_ag(r, 'Codigo')
        if cod is None: continue
        cat_v = g_ag(r, 'Categoria')
        if isinstance(cat_v, str) and ('Total' in cat_v or 'Filtros' in cat_v or 'Exported' in cat_v):
            continue
        ck = str(cod).strip()
        units = []; ars = []; usd = []
        for b in BUCKETS:
            units.append(round(g_ag(r, f'Ag{b}') or 0, 2))
            ars.append(round(g_ag(r, f'Costo{b}') or 0, 2))
            usd.append(round(g_ag(r, f'Costo{b}Dolar') or 0, 2))
        if sum(units) <= 0: continue
        fis = g_ag(r, 'StockFisico') or 0
        pot = g_ag(r, 'StockPotencial') or 0
        pm = g_ag(r, 'PM') or '(sin asignar)'
        suc = g_ag(r, 'SucursalItem') or ''
        tipo = g_ag(r, 'TipoArticulo') or ''
        if ck in aging_data:
            e = aging_data[ck]
            e['ag'] += sum(units); e['fis'] += fis; e['pot'] += pot
            for i in range(6):
                e['b'][i] += units[i]; e['ba'][i] += ars[i]; e['bu'][i] += usd[i]
            if pm and pm not in e['pm']: e['pm'].append(pm)
            if suc and suc not in e['deps']: e['deps'].append(suc)
        else:
            aging_data[ck] = {'ag': sum(units), 'fis': fis, 'pot': pot,
                              'b': units, 'ba': ars, 'bu': usd,
                              'pm': [pm] if pm else [], 'deps': [suc] if suc else [],
                              'tipo': tipo}
    # Round + compute oldest bucket
    for ck, e in aging_data.items():
        e['ag'] = round(e['ag'], 0); e['fis'] = round(e['fis'], 0); e['pot'] = round(e['pot'], 0)
        for i in range(6):
            e['b'][i] = round(e['b'][i], 0)
            e['ba'][i] = round(e['ba'][i], 0)
            e['bu'][i] = round(e['bu'][i], 0)
        e['ars'] = sum(e['ba']); e['usd'] = sum(e['bu'])
        e['old'] = -1
        for i in range(5, -1, -1):
            if e['b'][i] > 0: e['old'] = i; break

    # SIN_ROT-compatible (sr=ag) for existing code
    sr_compat = {ck: {'sr': e['ag'], 'fis': e['fis'], 'pot': e['pot'], 'deps': e['deps'], 'pm': e['pm']}
                 for ck, e in aging_data.items()}

    AG_JS = INTERNAL_DIR / "aging.js"
    with open(AG_JS, 'w', encoding='utf-8') as fp:
        fp.write('const __SIN_ROT__ = ' + json.dumps(sr_compat, ensure_ascii=False, separators=(',', ':')) + ';\n')
        fp.write('const __AGING__ = ' + json.dumps(aging_data, ensure_ascii=False, separators=(',', ':')) + ';\n')
        fp.write('const __AGING_BUCKETS__ = ["0-30 días","30-60 días","60-90 días","90-150 días","150-365 días","+365 días"];\n')
        fp.write('const __AGING_COLORS__ = ["#10b981","#84cc16","#eab308","#f59e0b","#ef4444","#7c2d12"];\n')

    total_units = sum(e['ag'] for e in aging_data.values())
    total_ars = sum(e['ars'] for e in aging_data.values())
    total_usd = sum(e['usd'] for e in aging_data.values())
    print(f"  aging.js:            {AG_JS.stat().st_size // 1024} KB")
    print(f"  Códigos en aging:    {len(aging_data)}")
    print(f"  Unidades en aging:   {total_units:,.0f}")
    print(f"  Costo ARS:           ${total_ars:,.2f}")
    print(f"  Costo USD:           ${total_usd:,.2f}")
elif sinrot_file:
    print("\n--- Construyendo sin_rotacion.js (legacy) ---")
    wb = openpyxl.load_workbook(str(sinrot_file), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows_iter = ws.iter_rows(values_only=True)
    header = list(next(rows_iter))
    idx = {c: i for i, c in enumerate(header)}
    def g_sr(row, key):
        i = idx.get(key)
        if i is None or i >= len(row): return None
        return row[i]
    by_codigo = {}
    for r in rows_iter:
        if r is None or all(v is None for v in r): continue
        cod = g_sr(r, 'Codigo')
        if cod is None: continue
        cat_v = g_sr(r, 'Categoria')
        if isinstance(cat_v, str) and ('Total' in cat_v or 'Filtros' in cat_v or 'Exported' in cat_v): continue
        ck = str(cod).strip()
        sr = g_sr(r, 'Sin Rotacion') or 0
        fis = g_sr(r, 'Fisico') or 0
        pot = g_sr(r, 'Potencial') or 0
        pm = g_sr(r, 'PM'); dep = g_sr(r, 'Deposito')
        if ck not in by_codigo:
            by_codigo[ck] = {"sr": 0, "fis": 0, "pot": 0, "deps": set(), "pm": set()}
        e = by_codigo[ck]
        e["sr"] += sr; e["fis"] += fis; e["pot"] += pot
        if dep: e["deps"].add(dep)
        if pm: e["pm"].add(pm)
    sr_out = {k: {"sr": round(v["sr"],0), "fis": round(v["fis"],0), "pot": round(v["pot"],0),
                  "deps": sorted(v["deps"]), "pm": sorted(v["pm"])}
              for k, v in by_codigo.items() if v["sr"] > 0}
    AG_JS = INTERNAL_DIR / "aging.js"
    with open(AG_JS, 'w', encoding='utf-8') as fp:
        fp.write('const __SIN_ROT__ = ' + json.dumps(sr_out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f"  Códigos sin rotación: {len(sr_out)}")
    print(f"  Unidades muertas:     {sum(v['sr'] for v in sr_out.values()):,.0f}")

# ============================================================
# 6. Rebuild the HTML dashboards
# ============================================================
print("\n--- Generando HTMLs ---")

# Template and build scripts live in src/templates/ and scripts/build/.
template = TEMPLATE_DIR / "dashboard_template.html"
build_dir = SCRIPT_DIR / "scripts" / "build"
build_dash = build_dir / "build_dashboard.py"
build_vend = build_dir / "build_vendedores.py"

if not template.exists() or not build_dash.exists() or not build_vend.exists():
    print("  ADVERTENCIA: No se encontró el template o los scripts de build.")
    print(f"    Template:     {template} ({'OK' if template.exists() else 'FALTA'})")
    print(f"    build_dash:   {build_dash} ({'OK' if build_dash.exists() else 'FALTA'})")
    print(f"    build_vend:   {build_vend} ({'OK' if build_vend.exists() else 'FALTA'})")
    print("  Los JSON están actualizados; sólo falta rebuildear los HTMLs.")
    print("  Pedile a quien te preparó el dashboard que los vuelva a generar.")
    sys.exit(0)

# Run both builds
env = os.environ.copy()
for script in [build_dash, build_vend]:
    print(f"  Corriendo {script.name}...")
    result = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR en {script.name}:")
        print(result.stderr)
        sys.exit(1)
    print(f"  {result.stdout.strip()}")

# Los HTML locales cargan estos recursos relativos desde dist/local/_internal/.
local_assets = SCRIPT_DIR / "dist" / "local" / "_internal"
local_assets.mkdir(parents=True, exist_ok=True)
for asset in (DATA_JS, AG_JS):
    shutil.copy2(asset, local_assets / asset.name)

# ============================================================
# 7. Regenerar las versiones autónomas (HTML standalone)
#    si está el script inline_dashboards.py
# ============================================================
inline_script = build_dir / "inline_dashboards.py"
if inline_script.exists():
    print("\n--- Regenerando versiones autónomas (standalone) ---")
    result = subprocess.run([sys.executable, str(inline_script)], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ADVERTENCIA: falló la regeneración de los autónomos:")
        print(result.stderr)
        # No es fatal — los livianos siguen actualizados
    else:
        print(result.stdout.strip())
else:
    print("\n(No se encontró scripts/build/inline_dashboards.py — se omite la regeneración de los autónomos.)")

print("\n" + "=" * 60)
print("OK ACTUALIZACIÓN COMPLETA")
print(f"  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(f"  Transacciones: {len(transactions):,}")
print(f"  Período: {txns_min} -> {txns_max}")
print("=" * 60)
print("\nAbrí los dashboards:")
print(f"  - dist/local/Dashboard Ventas.html                       (liviano)")
print(f"  - dist/local/Dashboard Ventas - Vendedores.html          (liviano)")
if inline_script.exists():
    print(f"  - dist/standalone/Dashboard Ventas (autónomo).html            (~88 MB)")
    print(f"  - dist/standalone/Dashboard Ventas - Vendedores (autónomo).html  (~88 MB)")
