#!/usr/bin/env python3
"""Apply ONLY the technical improvements to the original Dashboard Ventas.html
(keeping prices and billing intact).

Improvements applied:
- Universal DOM sort for all tables (incl. modals)
- Precomputed maps (NAME_TO_IDX, CODIGO_TO_IDX, SUBCAT_TO_IDX) for performance
- Precomputed VEND_RECIENTE map (used in vendor filter and where useful)
- CSS: table-layout fixed, no horizontal scroll, sort arrow indicators
- Dynamic titles for "top N" tables (show actual count)
- Vendor filter in Clientes Oportunidad
- Replace LK.X.indexOf calls with map lookups
"""
import re
from pathlib import Path

# Paths relativos al script: vive en scripts/build/ y genera el HTML en dist/local/.
_SCRIPT_DIR = Path(__file__).parent.resolve()  # .../Dashboard Ventas/scripts/build
_BASE = _SCRIPT_DIR.parents[1]
SRC_TEMPLATE = str(_BASE / 'src' / 'templates' / 'dashboard_template.html')
OUT_FILE = str(_BASE / 'dist' / 'local' / 'Dashboard Ventas.html')
DATA_FILE = str(_BASE / 'data' / 'processed' / 'data_raw_v2.json')
SR_FILE = str(_BASE / 'data' / 'processed' / 'sin_rotacion.json')

with open(SRC_TEMPLATE, 'r', encoding='utf-8') as f:
    html = f.read()

# ============================================================
# CSS: tabla con scroll solo vertical, anchos ajustables, sort arrows
# ============================================================
css_extra = '''
  /* === Mejoras v2: scroll solo vertical, sort universal === */
  .table-wrap { overflow-x: hidden; }
  table { table-layout: fixed; }
  td { white-space: normal; word-wrap: break-word; overflow-wrap: anywhere; }
  th { white-space: normal; }
  td.nowrap, th.nowrap { white-space: nowrap; }
  td.num { white-space: nowrap; }
  th[onclick] { cursor: pointer; }
  th[onclick]:hover { background: #475569; }
  th.sortable::after { content: " ↕"; opacity: 0.3; font-size: 9px; }
  th.sortable.sorted-asc::after { content: " ▲"; opacity: 1; color: var(--accent); }
  th.sortable.sorted-desc::after { content: " ▼"; opacity: 1; color: var(--accent); }
'''
html = html.replace('  /* Sin rotación */', css_extra + '  /* Sin rotación */')

# ============================================================
# Inject precomputed indexes + universal sort right after EPOCH_MS
# ============================================================
optimizations_js = '''
// ==== Optimizaciones: índices precalculados (evitan indexOf O(N)) ========
const NAME_TO_IDX = new Map();
LK.clienteName.forEach((n, i) => { if (n != null) NAME_TO_IDX.set(n, i); });
const CODIGO_TO_IDX = new Map();
LK.codigo.forEach((c, i) => { if (c != null) CODIGO_TO_IDX.set(c, i); });
const SUBCAT_TO_IDX = new Map();
LK.subcat.forEach((s, i) => { if (s != null) SUBCAT_TO_IDX.set(s, i); });

// ==== Vendedor reciente (últimos 3 meses) — pre-calculado ===============
// Se usa en el filtro de vendedor de Clientes Oportunidad y permite
// migrar fácilmente a "vendedor reciente" si querés.
const VEND_WINDOW_DAYS = 90;
const TODAY_DAYS = Math.floor((Date.now() - EPOCH_MS) / 86400000);
const VEND_CUTOFF = TODAY_DAYS - VEND_WINDOW_DAYS;
const VEND_RECIENTE = new Map();
(function precomputeVendedor() {
    const cliVendCounts = new Map();
    for (let i=0; i<ROWS.length; i++) {
        const r = ROWS[i];
        if (r[C.days] < VEND_CUTOFF) continue;
        const cli = r[C.cli];
        const vend = r[C.vend];
        let m = cliVendCounts.get(cli);
        if (!m) { m = new Map(); cliVendCounts.set(cli, m); }
        m.set(vend, (m.get(vend)||0) + 1);
    }
    cliVendCounts.forEach((m, cli) => {
        let best = -1, bestCount = 0;
        m.forEach((c, v) => { if (c > bestCount) { bestCount = c; best = v; } });
        if (best >= 0) VEND_RECIENTE.set(cli, LK.vend[best] || null);
    });
})();
function vendedorReciente(cliNameIdx, fallback) {
    if (cliNameIdx == null || cliNameIdx < 0) return fallback || null;
    const v = VEND_RECIENTE.get(cliNameIdx);
    return v || fallback || null;
}

// ==== Universal table sort (DOM-based) ===================================
// Aplica sort clickeable a CUALQUIER tabla del documento, incluyendo
// las que aparecen dentro de modales. No interfiere con las tablas que
// ya tienen sus propios handlers (mantienen el sort basado en datos).
function _stripFormatAR(s) {
    // Quita prefijos tipo "USD ", "ARS ", "$", "%", espacios; convierte
    // separador de miles "." → vacío y decimal "," → "."
    return s.replace(/[A-Za-z\\$%\\s]/g, '').replace(/\\./g, '').replace(',', '.');
}
function _parseCellValue(cell, isNum, isDate) {
    const text = (cell.textContent || '').trim();
    if (isDate || /^\\d{4}-\\d{2}-\\d{2}$/.test(text)) return text;
    if (isNum) {
        const n = parseFloat(_stripFormatAR(text));
        return isNaN(n) ? -Infinity : n;
    }
    const tryNum = parseFloat(_stripFormatAR(text));
    if (!isNaN(tryNum) && /^[\\$\\d.,\\-%\\s]+$/.test(text)) return tryNum;
    return text.toLowerCase();
}
function _isTotalRow(row) {
    if (!row) return false;
    const style = (row.getAttribute('style') || '').replace(/\\s/g, '');
    if (style.includes('font-weight:bold') || style.includes('background:var(--bg-3)')) return true;
    const t = (row.textContent || '').toUpperCase();
    return t.startsWith('TOTAL') || t.includes('TOTAL (');
}
function sortTableByColumn(table, colIdx, th) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const allRows = Array.from(tbody.querySelectorAll(':scope > tr'));
    let totalRow = null;
    if (allRows.length > 0 && _isTotalRow(allRows[allRows.length - 1])) {
        totalRow = allRows.pop();
    }
    const cur = th.dataset.uSortDir;
    const newDir = cur === 'desc' ? 'asc' : 'desc';
    table.querySelectorAll('thead th').forEach(h => {
        if (h !== th) {
            h.dataset.uSortDir = '';
            const a = h.querySelector('.u-sort-arrow');
            if (a) { a.textContent = '↕'; a.style.opacity = '0.35'; a.style.color = ''; }
        }
    });
    th.dataset.uSortDir = newDir;
    const arrow = th.querySelector('.u-sort-arrow');
    if (arrow) {
        arrow.textContent = newDir === 'desc' ? '▼' : '▲';
        arrow.style.opacity = '1';
        arrow.style.color = 'var(--accent)';
    }
    const isNum = th.classList.contains('num');
    const headerText = (th.textContent || '').toLowerCase();
    const isDate = /fecha|última|primera|compra|mes/.test(headerText) && !isNum;
    const m = newDir === 'desc' ? -1 : 1;
    allRows.sort((ra, rb) => {
        const va = _parseCellValue(ra.children[colIdx], isNum, isDate);
        const vb = _parseCellValue(rb.children[colIdx], isNum, isDate);
        if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * m;
        return String(va).localeCompare(String(vb)) * m;
    });
    const frag = document.createDocumentFragment();
    allRows.forEach(r => frag.appendChild(r));
    if (totalRow) frag.appendChild(totalRow);
    tbody.appendChild(frag);
}
function makeTableUniversallySortable(table) {
    if (table.dataset.uSortAttached) return;
    table.dataset.uSortAttached = '1';
    const ths = table.querySelectorAll('thead th');
    ths.forEach((th, idx) => {
        if (th.hasAttribute('onclick')) return;
        if ((th.textContent || '').trim() === '' && !th.querySelector('span,a,b')) return;
        th.style.cursor = 'pointer';
        th.style.userSelect = 'none';
        th.title = 'Click para ordenar';
        if (!th.querySelector('.u-sort-arrow')) {
            const arrow = document.createElement('span');
            arrow.className = 'u-sort-arrow';
            arrow.textContent = '↕';
            arrow.style.cssText = 'margin-left:4px; opacity:.35; font-size:9px; vertical-align:middle;';
            th.appendChild(arrow);
        }
        th.addEventListener('click', (ev) => {
            if (ev.target.closest('button,a,input,select')) return;
            sortTableByColumn(table, idx, th);
        });
        th.addEventListener('mouseenter', () => { th.style.background = '#475569'; });
        th.addEventListener('mouseleave', () => { th.style.background = ''; });
    });
}
const _tableObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
        m.addedNodes.forEach(n => {
            if (n.nodeType !== 1) return;
            if (n.tagName === 'TABLE') makeTableUniversallySortable(n);
            n.querySelectorAll && n.querySelectorAll('table').forEach(makeTableUniversallySortable);
        });
    }
});
document.addEventListener('DOMContentLoaded', () => {
    _tableObserver.observe(document.body, { childList: true, subtree: true });
    document.querySelectorAll('table').forEach(makeTableUniversallySortable);
});

// ==== Helper: arrowClass para columnas ya sortables (de los handlers existentes)
function arrowClass(tab, key) {
    const s = STATE.sort[tab];
    if (!s || s.key !== key) return 'sortable';
    return s.dir==='desc' ? 'sortable sorted-desc' : 'sortable sorted-asc';
}
function arrowSR(view, key) {
    const s = STATE.sort[view] || {key:null, dir:'desc'};
    if (s.key === key) return s.dir==='desc' ? 'sortable sorted-desc' : 'sortable sorted-asc';
    return 'sortable';
}
'''
html = html.replace(
    '''const EPOCH_MS = Date.parse(D.meta.epoch + 'T00:00:00Z');''',
    '''const EPOCH_MS = Date.parse(D.meta.epoch + 'T00:00:00Z');\n''' + optimizations_js
)

# ============================================================
# Replace LK.X.indexOf with map lookups (perf optimization)
# ============================================================
html = html.replace('LK.clienteName.indexOf(', 'NAME_TO_IDX.get(')
html = html.replace('LK.codigo.indexOf(', 'CODIGO_TO_IDX.get(')
html = html.replace('LK.subcat.indexOf(', 'SUBCAT_TO_IDX.get(')

# Patch the < 0 checks (Map.get returns undefined, not -1)
html = html.replace(
    'if (cliIdx < 0) { alert(\'Cliente no encontrado\'); return; }',
    'if (cliIdx == null) { alert(\'Cliente no encontrado\'); return; }'
)
html = html.replace('if (cliIdx<0 || codIdx<0)', 'if (cliIdx==null || codIdx==null)')
html = html.replace(
    'if (subIdx<0) { alert(\'Subcat no encontrada\'); return; }',
    'if (subIdx==null) { alert(\'Subcat no encontrada\'); return; }'
)
html = html.replace(
    'if (codIdx<0) { alert(\'Código no encontrado\'); return; }',
    'if (codIdx==null) { alert(\'Código no encontrado\'); return; }'
)
html = html.replace('const hasSales = codIdx >= 0;', 'const hasSales = codIdx != null;')

# ============================================================
# Add visible sort arrow CSS classes to existing sortable headers
# ============================================================
# Clientes
html = html.replace(
    '''<th onclick="sortBy('clientes','id')">ID${arr('id')}</th>
        <th onclick="sortBy('clientes','nombre')">Cliente${arr('nombre')}</th>
        <th class="num" onclick="sortBy('clientes','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('clientes','profit')">Profit${arr('profit')}</th>
        <th class="num" onclick="sortBy('clientes','cantidad')">Cantidad${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('clientes','trans')">Trans.${arr('trans')}</th>
        <th class="num">Margen</th>
        <th onclick="sortBy('clientes','provincia')">Provincia${arr('provincia')}</th>
        <th onclick="sortBy('clientes','clase')">Clase${arr('clase')}</th>
        <th>Vendedor</th>''',
    '''<th class="${arrowClass('clientes','id')}" onclick="sortBy('clientes','id')" style="width:6%">ID</th>
        <th class="${arrowClass('clientes','nombre')}" onclick="sortBy('clientes','nombre')" style="width:18%">Cliente</th>
        <th class="num ${arrowClass('clientes','ventas')}" onclick="sortBy('clientes','ventas')" style="width:11%">Ventas</th>
        <th class="num ${arrowClass('clientes','profit')}" onclick="sortBy('clientes','profit')" style="width:10%">Profit</th>
        <th class="num ${arrowClass('clientes','cantidad')}" onclick="sortBy('clientes','cantidad')" style="width:8%">Cantidad</th>
        <th class="num ${arrowClass('clientes','trans')}" onclick="sortBy('clientes','trans')" style="width:7%">Trans.</th>
        <th class="num" style="width:7%">Margen</th>
        <th class="${arrowClass('clientes','provincia')}" onclick="sortBy('clientes','provincia')" style="width:9%">Provincia</th>
        <th class="${arrowClass('clientes','clase')}" onclick="sortBy('clientes','clase')" style="width:8%">Clase</th>
        <th style="width:16%">Vendedor</th>'''
)

# Articulos
html = html.replace(
    '''<th onclick="sortBy('articulos','codigo')">Código${arr('codigo')}</th>
        <th onclick="sortBy('articulos','articulo')">Artículo${arr('articulo')}</th>
        <th onclick="sortBy('articulos','marca')">Marca${arr('marca')}</th>
        <th onclick="sortBy('articulos','subcat')">SubCategoría${arr('subcat')}</th>
        <th class="num" onclick="sortBy('articulos','sr')">Sin Rot${arr('sr')}</th>
        <th class="num" onclick="sortBy('articulos','fis')">Stock${arr('fis')}</th>
        <th class="num" onclick="sortBy('articulos','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('articulos','profit')">Profit${arr('profit')}</th>
        <th class="num">Margen</th>
        <th class="num" onclick="sortBy('articulos','cantidad')">Cant.${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('articulos','trans')">Trans.${arr('trans')}</th>''',
    '''<th class="${arrowClass('articulos','codigo')}" onclick="sortBy('articulos','codigo')" style="width:6%">Código</th>
        <th class="${arrowClass('articulos','articulo')}" onclick="sortBy('articulos','articulo')" style="width:26%">Artículo</th>
        <th class="${arrowClass('articulos','marca')}" onclick="sortBy('articulos','marca')" style="width:10%">Marca</th>
        <th class="${arrowClass('articulos','subcat')}" onclick="sortBy('articulos','subcat')" style="width:12%">SubCategoría</th>
        <th class="num ${arrowClass('articulos','sr')}" onclick="sortBy('articulos','sr')" style="width:6%">Sin Rot</th>
        <th class="num ${arrowClass('articulos','fis')}" onclick="sortBy('articulos','fis')" style="width:6%">Stock</th>
        <th class="num ${arrowClass('articulos','ventas')}" onclick="sortBy('articulos','ventas')" style="width:9%">Ventas</th>
        <th class="num ${arrowClass('articulos','profit')}" onclick="sortBy('articulos','profit')" style="width:8%">Profit</th>
        <th class="num" style="width:6%">Margen</th>
        <th class="num ${arrowClass('articulos','cantidad')}" onclick="sortBy('articulos','cantidad')" style="width:6%">Cant.</th>
        <th class="num ${arrowClass('articulos','trans')}" onclick="sortBy('articulos','trans')" style="width:5%">Trans.</th>'''
)

# Generic dim tables
html = html.replace(
    '''<th onclick="sortBy('${tab}','nombre')">${label}${arr('nombre')}</th>
        <th class="num" onclick="sortBy('${tab}','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('${tab}','profit')">Profit${arr('profit')}</th>
        <th class="num">Margen</th>
        <th class="num">% Total</th>
        <th class="num" onclick="sortBy('${tab}','cantidad')">Cantidad${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('${tab}','trans')">Trans.${arr('trans')}</th>
        <th class="num">Ticket</th>''',
    '''<th class="${arrowClass(tab,'nombre')}" onclick="sortBy('${tab}','nombre')" style="width:30%">${label}</th>
        <th class="num ${arrowClass(tab,'ventas')}" onclick="sortBy('${tab}','ventas')" style="width:13%">Ventas</th>
        <th class="num ${arrowClass(tab,'profit')}" onclick="sortBy('${tab}','profit')" style="width:11%">Profit</th>
        <th class="num" style="width:8%">Margen</th>
        <th class="num" style="width:8%">% Total</th>
        <th class="num ${arrowClass(tab,'cantidad')}" onclick="sortBy('${tab}','cantidad')" style="width:9%">Cantidad</th>
        <th class="num ${arrowClass(tab,'trans')}" onclick="sortBy('${tab}','trans')" style="width:8%">Trans.</th>
        <th class="num" style="width:13%">Ticket</th>'''
)

# Sin Rotación: PMs ranking
html = html.replace(
    '''<th onclick="sortSR('srpms','pm')">PM Responsable</th>
        <th class="num" onclick="sortSR('srpms','codigos')">Códigos sin rot</th>
        <th class="num" onclick="sortSR('srpms','units')">Unidades muertas</th>
        <th class="num" onclick="sortSR('srpms','fis')">Stock físico</th>
        <th class="num" onclick="sortSR('srpms','share')">% muerto</th>
        <th class="num">% del total</th>
        <th></th>''',
    '''<th class="${arrowSR('srpms','pm')}" onclick="sortSR('srpms','pm')">PM</th>
        <th class="num ${arrowSR('srpms','codigos')}" onclick="sortSR('srpms','codigos')">Códigos</th>
        <th class="num ${arrowSR('srpms','units')}" onclick="sortSR('srpms','units')">Uds muertas</th>
        <th class="num ${arrowSR('srpms','fis')}" onclick="sortSR('srpms','fis')">Stock</th>
        <th class="num ${arrowSR('srpms','share')}" onclick="sortSR('srpms','share')">% muerto</th>
        <th class="num">% total</th>
        <th></th>'''
)

# Sin Rotación: Oport
html = html.replace(
    '''<th onclick="sortSR('sropor','cliente')">Cliente</th>
        <th onclick="sortSR('sropor','vendedor')">Vendedor</th>
        <th onclick="sortSR('sropor','provincia')">Provincia</th>
        <th class="num" onclick="sortSR('sropor','srArticulos')">Art. SR comprados</th>
        <th class="num" onclick="sortSR('sropor','units')">Cant. histórica</th>
        <th class="num" onclick="sortSR('sropor','ventas')">Ventas (de art. SR)</th>
        <th class="num" onclick="sortSR('sropor','ventasTotales')">Ventas totales</th>
        <th onclick="sortSR('sropor','ultima')">Última compra (de art. SR)</th>
        <th class="num" onclick="sortSR('sropor','dias')">Días</th>
        <th></th>''',
    '''<th class="${arrowSR('sropor','cliente')}" onclick="sortSR('sropor','cliente')" style="width:17%">Cliente</th>
        <th class="${arrowSR('sropor','vendedor')}" onclick="sortSR('sropor','vendedor')" style="width:11%">Vendedor</th>
        <th class="${arrowSR('sropor','provincia')}" onclick="sortSR('sropor','provincia')" style="width:9%">Provincia</th>
        <th class="num ${arrowSR('sropor','srArticulos')}" onclick="sortSR('sropor','srArticulos')" style="width:7%">Art. SR</th>
        <th class="num ${arrowSR('sropor','units')}" onclick="sortSR('sropor','units')" style="width:8%">Cant. hist.</th>
        <th class="num ${arrowSR('sropor','ventas')}" onclick="sortSR('sropor','ventas')" style="width:10%">Ventas SR</th>
        <th class="num ${arrowSR('sropor','ventasTotales')}" onclick="sortSR('sropor','ventasTotales')" style="width:11%">Ventas totales</th>
        <th class="${arrowSR('sropor','ultima')}" onclick="sortSR('sropor','ultima')" style="width:9%">Última compra SR</th>
        <th class="num ${arrowSR('sropor','dias')}" onclick="sortSR('sropor','dias')" style="width:5%">Días</th>
        <th style="width:13%"></th>'''
)

# Por SubCategoría / Marca
html = html.replace(
    '''<table><thead><tr><th>Tipo</th><th>Nombre</th><th class="num">Códigos sin rot</th><th class="num">Unidades muertas</th><th class="num">Stock físico</th><th class="num">% muerto</th></tr></thead><tbody>''',
    '''<table><thead><tr><th style="width:8%">Tipo</th><th style="width:32%">Nombre</th><th class="num" style="width:14%">Códigos</th><th class="num" style="width:18%">Uds muertas</th><th class="num" style="width:14%">Stock físico</th><th class="num" style="width:14%">% muerto</th></tr></thead><tbody>'''
)

# ============================================================
# Vendor filter in Clientes Oportunidad
# ============================================================
html = html.replace(
    '''        <select id="oportRecency" class="filter-select">
          <option value="0">Cualquier antigüedad</option>
          <option value="365">Última compra ≤ 1 año</option>
          <option value="180">Última compra ≤ 6 meses</option>
          <option value="90">Última compra ≤ 3 meses</option>
        </select>
        <button class="btn" onclick="exportSinRotExcel('oport')" style="background:var(--accent)">⬇ Exportar a Excel</button>''',
    '''        <select id="oportRecency" class="filter-select">
          <option value="0">Cualquier antigüedad</option>
          <option value="365">Última compra ≤ 1 año</option>
          <option value="180">Última compra ≤ 6 meses</option>
          <option value="90">Última compra ≤ 3 meses</option>
        </select>
        <select id="oportVendedor" class="filter-select"><option value="">Todos los vendedores</option></select>
        <button class="btn" onclick="exportSinRotExcel('oport')" style="background:var(--accent)">⬇ Exportar a Excel</button>'''
)

# Apply vendor filter in renderSROport
html = html.replace(
    '''    const q = (document.getElementById('searchSROport')?.value||'').toLowerCase().trim();
    const topN = +(document.getElementById('oportTopN')?.value||500);
    const recency = +(document.getElementById('oportRecency')?.value||0);
    const idx = buildSRIndexes();''',
    '''    const q = (document.getElementById('searchSROport')?.value||'').toLowerCase().trim();
    const topN = +(document.getElementById('oportTopN')?.value||500);
    const recency = +(document.getElementById('oportRecency')?.value||0);
    const vendFiltro = (document.getElementById('oportVendedor')?.value||'').trim();
    const idx = buildSRIndexes();'''
)

html = html.replace(
    '''        rows.push({
            cliente: name, nIdx,
            vendedor: idx.nameToVendedor.get(nIdx) || '(sin asignar)',
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units, ventas: e.ventas, profit: e.profit,
            ultima: fmtDate(e.lastDays), dias, ventasTotales: idx.nameToTotal.get(nIdx)||0,
            count: e.count
        });''',
    '''        const vendAsig = idx.nameToVendedor.get(nIdx) || '(sin asignar)';
        if (vendFiltro && vendAsig !== vendFiltro) return;
        rows.push({
            cliente: name, nIdx,
            vendedor: vendAsig,
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units, ventas: e.ventas, profit: e.profit,
            ultima: fmtDate(e.lastDays), dias, ventasTotales: idx.nameToTotal.get(nIdx)||0,
            count: e.count
        });'''
)

# Hook up vendor select + populate it
html = html.replace(
    '''        document.getElementById('searchSROport').addEventListener('input', () => debounce(renderSROport));
        document.getElementById('oportTopN').addEventListener('change', renderSROport);
        document.getElementById('oportRecency').addEventListener('change', renderSROport);''',
    '''        document.getElementById('searchSROport').addEventListener('input', () => debounce(renderSROport));
        document.getElementById('oportTopN').addEventListener('change', renderSROport);
        document.getElementById('oportRecency').addEventListener('change', renderSROport);
        document.getElementById('oportVendedor').addEventListener('change', renderSROport);
        // Populate vendedor dropdown
        (function populateOportVendedor() {
            const idx = buildSRIndexes();
            const vends = new Set();
            idx.cliMap.forEach((e, nIdx) => {
                const v = idx.nameToVendedor.get(nIdx) || '(sin asignar)';
                vends.add(v);
            });
            const sorted = [...vends].sort((a,b)=>{
                if (a === '(sin asignar)') return 1;
                if (b === '(sin asignar)') return -1;
                return a.localeCompare(b);
            });
            const sel = document.getElementById('oportVendedor');
            sorted.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v; opt.textContent = v;
                sel.appendChild(opt);
            });
        })();'''
)

# ============================================================
# Dynamic titles for "top N" tables (show actual count)
# ============================================================
# Articulo modal: "Top 20 Clientes que más compraron"
html = html.replace(
    '''        body += `<h3 style="margin:14px 0 8px">👥 Top 20 Clientes que más compraron</h3>''',
    '''        const titleTopArt = topCli.length === cliArr.length
            ? `👥 ${cliArr.length===1?'Cliente que':cliArr.length+' clientes que'} compraron`
            : `👥 Top ${topCli.length} de ${cliArr.length} clientes`;
        body += `<h3 style="margin:14px 0 8px">${titleTopArt}</h3>'''
)

# Articulo modal: "Últimos 10 clientes que compraron"
# (the original showArticuloDetail has the original count of 10 in the title)
html = html.replace(
    '''        body += `<h3 style="margin:14px 0 8px">📞 Últimos 10 clientes que compraron — para ofrecer</h3>''',
    '''        body += `<h3 style="margin:14px 0 8px">📞 ${last10.length===lastBuyArr.length?(last10.length===1?'Cliente que compró':last10.length+' clientes que compraron'):'Últimos '+last10.length+' de '+lastBuyArr.length+' que compraron'} — para ofrecer</h3>'''
)

# Subcat modal: "Top 100 Clientes"
html = html.replace(
    '''        <h3 style="margin:14px 0 8px">👥 Top 100 Clientes</h3>''',
    '''        <h3 style="margin:14px 0 8px">👥 ${cliArr.length<=top100.length?(cliArr.length===1?'Cliente que compró':cliArr.length+' clientes que compraron'):'Top '+top100.length+' de '+cliArr.length+' clientes'}</h3>'''
)

# Cliente modal: "Top SubCategorías compradas (top 30)"
html = html.replace(
    '''        <h3 style="margin:14px 0 8px">📦 SubCategorías compradas — click para ver artículos</h3>''',
    '''        <h3 style="margin:14px 0 8px">📦 ${subArr.length===1?'1 SubCategoría comprada':subArr.length+' SubCategorías compradas'} — click para ver artículos</h3>'''
)

# Cliente×Subcat: "Artículos comprados (X)"
# Already dynamic in original — leave as is

# ============================================================
# Data is loaded via external script tags in the template (no inline)
# ============================================================
final = html
Path(OUT_FILE).parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write(final)

import os
sz = os.path.getsize(OUT_FILE)
print(f"Saved: {OUT_FILE}")
print(f"Size: {sz:,} bytes ({sz/1024/1024:.2f} MB)")
