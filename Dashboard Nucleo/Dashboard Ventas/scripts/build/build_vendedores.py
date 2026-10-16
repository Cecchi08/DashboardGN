#!/usr/bin/env python3
"""Transform the main dashboard template into the 'Vendedores' version:
- Strip all $/ventas/profit/margen/ticket references
- Replace assigned vendor with "most frequent vendor in last 3 months"
- Rebuild KPIs, charts, tables, modals to use cantidad/transacciones only
"""
import re, json
from pathlib import Path

# Paths relativos al script: vive en scripts/build/ y genera el HTML en dist/local/.
_SCRIPT_DIR = Path(__file__).parent.resolve()  # .../Dashboard Ventas/scripts/build
_BASE = _SCRIPT_DIR.parents[1]
SRC_TEMPLATE = str(_BASE / 'src' / 'templates' / 'dashboard_template.html')
OUT_FILE = str(_BASE / 'dist' / 'local' / 'Dashboard Ventas - Vendedores.html')
DATA_FILE = str(_BASE / 'data' / 'processed' / 'data_raw_v2.json')
SR_FILE = str(_BASE / 'data' / 'processed' / 'sin_rotacion.json')

with open(SRC_TEMPLATE, 'r', encoding='utf-8') as f:
    html = f.read()

# ============================================================
# Title and header
# ============================================================
html = html.replace('<title>Dashboard de Ventas - Núcleo</title>',
                    '<title>Dashboard Ventas Núcleo - Vendedores</title>')
html = html.replace(
    '<h1>📊 Dashboard de Ventas - Núcleo <span id="updateBadge" style="font-size:11px; background:#10b981; color:#fff; padding:3px 10px; border-radius:12px; margin-left:10px; vertical-align:middle; font-weight:normal"></span></h1>',
    '<h1>👥 Dashboard Ventas Núcleo — Vista Vendedores <span id="updateBadge" style="font-size:11px; background:#10b981; color:#fff; padding:3px 10px; border-radius:12px; margin-left:10px; vertical-align:middle; font-weight:normal"></span></h1>'
)

# ============================================================
# KPIs render - replace the whole function
# ============================================================
old_kpis = '''function renderKPIs() {
    const t = totalsOf();
    const margen = t.v ? (t.p/t.v)*100 : 0;
    const ticket = t.t ? t.v/t.t : 0;
    const f = STATE.filters;
    const parts = [];
    if (f.years.length) parts.push('Año: ' + f.years.join(', '));
    if (f.months.length) parts.push('Mes: ' + f.months.map(m=>String(m).padStart(2,'0')).join(', '));
    if (f.plats.length) parts.push('Plat: ' + f.plats.map(i=>LK.plat[i]).join(', '));
    if (f.prov>=0) parts.push('Prov: '+LK.prov[f.prov]);
    if (f.cat>=0) parts.push('Cat: '+LK.cat[f.cat]);
    if (f.marcas && f.marcas.length) parts.push('Marca: ' + f.marcas.map(i=>LK.marca[i]).join(', '));
    if (f.clases.length) parts.push('Clase: ' + f.clases.map(i=>LK.clase[i]).join(', '));
    if (f.vends && f.vends.length) parts.push('Vendedor: ' + f.vends.map(i=>LK.vend[i]).join(', '));
    const sub1 = parts.length ? parts.join(' · ') : `${D.meta.min_date} → ${D.meta.max_date}`;

    // Unique counts in active scope
    const dims = {
        clientes: aggregateCli().size,
        subcat: aggregate(C.sub).size,
        cat: aggregate(C.cat).size,
        marca: aggregate(C.marca).size,
        art: aggregateArt().size,
    };

    document.getElementById('kpis').innerHTML = `
        <div class="kpi"><div class="label">Ventas</div><div class="value">${fmtMoney(t.v)}</div><div class="sub">${sub1}</div></div>
        <div class="kpi"><div class="label">Profit</div><div class="value pos">${fmtMoney(t.p)}</div><div class="sub">${margen.toFixed(2)}% margen</div></div>
        <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(t.t)}</div><div class="sub">Ticket: ${fmtMoney(ticket)}</div></div>
        <div class="kpi"><div class="label">Cantidad (uds)</div><div class="value">${fmtNum(t.q)}</div></div>
        <div class="kpi"><div class="label">Clientes</div><div class="value">${fmtNum(dims.clientes)}</div></div>
        <div class="kpi"><div class="label">SubCategorías</div><div class="value">${dims.subcat}</div><div class="sub">${dims.cat} categorías</div></div>
        <div class="kpi"><div class="label">Marcas</div><div class="value">${dims.marca}</div></div>
        <div class="kpi"><div class="label">Artículos</div><div class="value">${fmtNum(dims.art)}</div></div>
    `;
}'''

new_kpis = '''function renderKPIs() {
    const t = totalsOf();
    const f = STATE.filters;
    const parts = [];
    if (f.years.length) parts.push('Año: ' + f.years.join(', '));
    if (f.months.length) parts.push('Mes: ' + f.months.map(m=>String(m).padStart(2,'0')).join(', '));
    if (f.plats.length) parts.push('Plat: ' + f.plats.map(i=>LK.plat[i]).join(', '));
    if (f.prov>=0) parts.push('Prov: '+LK.prov[f.prov]);
    if (f.cat>=0) parts.push('Cat: '+LK.cat[f.cat]);
    if (f.marcas && f.marcas.length) parts.push('Marca: ' + f.marcas.map(i=>LK.marca[i]).join(', '));
    if (f.clases.length) parts.push('Clase: ' + f.clases.map(i=>LK.clase[i]).join(', '));
    if (f.vends && f.vends.length) parts.push('Vendedor: ' + f.vends.map(i=>LK.vend[i]).join(', '));
    const sub1 = parts.length ? parts.join(' · ') : `${D.meta.min_date} → ${D.meta.max_date}`;

    const dims = {
        clientes: aggregateCli().size,
        subcat: aggregate(C.sub).size,
        cat: aggregate(C.cat).size,
        marca: aggregate(C.marca).size,
        art: aggregateArt().size,
        plat: aggregate(C.plat).size,
    };
    const pedidosPorCliente = dims.clientes ? (t.t/dims.clientes) : 0;

    document.getElementById('kpis').innerHTML = `
        <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(t.t)}</div><div class="sub">${sub1}</div></div>
        <div class="kpi"><div class="label">Unidades</div><div class="value">${fmtNum(t.q)}</div></div>
        <div class="kpi"><div class="label">Clientes activos</div><div class="value">${fmtNum(dims.clientes)}</div></div>
        <div class="kpi"><div class="label">Pedidos / cliente</div><div class="value">${pedidosPorCliente.toFixed(1)}</div><div class="sub">promedio</div></div>
        <div class="kpi"><div class="label">SubCategorías</div><div class="value">${dims.subcat}</div><div class="sub">${dims.cat} categorías</div></div>
        <div class="kpi"><div class="label">Marcas</div><div class="value">${dims.marca}</div></div>
        <div class="kpi"><div class="label">Artículos</div><div class="value">${fmtNum(dims.art)}</div></div>
        <div class="kpi"><div class="label">Plataformas activas</div><div class="value">${dims.plat}</div></div>
    `;
}'''
assert old_kpis in html, "KPIs anchor not found"
html = html.replace(old_kpis, new_kpis)

# ============================================================
# Resumen charts - rank by quantity instead of ventas
# ============================================================
old_resumen = '''function renderResumenCharts() {
    const topSub = mapToSortedArray(aggregate(C.sub), LK.subcat, 15);
    makeBarChart('chartTopSub', topSub.map(x=>x[0]), topSub.map(x=>x[1]), '#3b82f6', true);
    const topCat = mapToSortedArray(aggregate(C.cat), LK.cat, 15);
    makeBarChart('chartTopCat', topCat.map(x=>x[0]), topCat.map(x=>x[1]), '#06b6d4', true);
    const topMarca = mapToSortedArray(aggregate(C.marca), LK.marca, 10);
    makeBarChart('chartTopMarca', topMarca.map(x=>x[0]), topMarca.map(x=>x[1]), '#10b981', true);
    const topPlat = mapToSortedArray(aggregate(C.plat), LK.plat, 10);
    makeBarChart('chartTopPlat', topPlat.map(x=>x[0]), topPlat.map(x=>x[1]), '#f59e0b', true);

    // Monthly
    const mesMap = aggregateMonth();
    const mesArr = [...mesMap.entries()].map(([k,e])=>[LK.ym[k], e.v, e.p, e.q, e.t]);
    mesArr.sort((a,b)=>a[0].localeCompare(b[0]));
    makeLineChart('chartMes', mesArr.map(x=>x[0]), [{label:'Ventas', data: mesArr.map(x=>x[1]), borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,.2)', tension:.25, fill:true}]);
    makeLineChart('chartMesProfit', mesArr.map(x=>x[0]), [{label:'Profit', data: mesArr.map(x=>x[2]), borderColor:'#10b981', backgroundColor:'rgba(16,185,129,.2)', tension:.25, fill:true}]);

    const topProv = mapToSortedArray(aggregate(C.prov), LK.prov, 10);
    makeBarChart('chartProv', topProv.map(x=>x[0]), topProv.map(x=>x[1]), '#8b5cf6', true);

    // By year
    const byYear = new Map();
    mesMap.forEach((e,k) => {
        const y = YM_YEAR[k];
        const cur = byYear.get(y) || 0;
        byYear.set(y, cur + e.v);
    });
    const ys = [...byYear.keys()].sort();
    makeBarChart('chartYear', ys.map(y=>String(y)), ys.map(y=>byYear.get(y)), '#ef4444');
}'''

# New: rank by CANTIDAD (units) instead of ventas, index 3 instead of 1
new_resumen = '''function renderResumenCharts() {
    // Rank by CANTIDAD (units), not by $
    const topByQ = (map, lookupArr, n) => {
        const arr = [];
        map.forEach((e,k) => arr.push([lookupArr ? (lookupArr[k]||'(sin dato)') : k, e.q, e.t]));
        arr.sort((a,b)=>b[1]-a[1]);
        return arr.slice(0, n);
    };
    const topSub = topByQ(aggregate(C.sub), LK.subcat, 15);
    makeBarChartQty('chartTopSub', topSub.map(x=>x[0]), topSub.map(x=>x[1]), '#3b82f6', true);
    const topCat = topByQ(aggregate(C.cat), LK.cat, 15);
    makeBarChartQty('chartTopCat', topCat.map(x=>x[0]), topCat.map(x=>x[1]), '#06b6d4', true);
    const topMarca = topByQ(aggregate(C.marca), LK.marca, 10);
    makeBarChartQty('chartTopMarca', topMarca.map(x=>x[0]), topMarca.map(x=>x[1]), '#10b981', true);
    const topPlat = topByQ(aggregate(C.plat), LK.plat, 10);
    makeBarChartQty('chartTopPlat', topPlat.map(x=>x[0]), topPlat.map(x=>x[1]), '#f59e0b', true);

    const mesMap = aggregateMonth();
    const mesArr = [...mesMap.entries()].map(([k,e])=>[LK.ym[k], e.q, e.t]);
    mesArr.sort((a,b)=>a[0].localeCompare(b[0]));
    makeLineChartQty('chartMes', mesArr.map(x=>x[0]), [{label:'Unidades', data: mesArr.map(x=>x[1]), borderColor:'#06b6d4', backgroundColor:'rgba(6,182,212,.2)', tension:.25, fill:true}]);
    makeLineChartQty('chartMesProfit', mesArr.map(x=>x[0]), [{label:'Transacciones', data: mesArr.map(x=>x[2]), borderColor:'#8b5cf6', backgroundColor:'rgba(139,92,246,.2)', tension:.25, fill:true}]);

    const topProv = topByQ(aggregate(C.prov), LK.prov, 10);
    makeBarChartQty('chartProv', topProv.map(x=>x[0]), topProv.map(x=>x[1]), '#8b5cf6', true);

    const byYear = new Map();
    mesMap.forEach((e,k) => { const y = YM_YEAR[k]; byYear.set(y, (byYear.get(y)||0) + e.q); });
    const ys = [...byYear.keys()].sort();
    makeBarChartQty('chartYear', ys.map(y=>String(y)), ys.map(y=>byYear.get(y)), '#ef4444');
}

// Bar/Line chart that formats Y axis as number (not money)
function makeBarChartQty(id, labels, values, color, horiz) {
    destroyChart(id); const ctx = document.getElementById(id); if (!ctx) return;
    charts[id] = new Chart(ctx, {
        type:'bar',
        data:{ labels, datasets:[{ data: values, backgroundColor: color, borderRadius:3 }]},
        options:{ indexAxis: horiz?'y':'x', maintainAspectRatio:false, responsive:true,
            plugins:{legend:{display:false}, tooltip:{callbacks:{label: c => fmtNum(c.raw)+' uds'}}},
            scales:{ x:{ticks:{color:'#94a3b8', font:{size:10}, callback: v => horiz ? fmtNum(v) : v}, grid:{color:'#334155'}},
                y:{ticks:{color:'#94a3b8', font:{size:10}, callback: v => horiz ? v : fmtNum(v)}, grid:{color:'#334155'}}} }
    });
}
function makeLineChartQty(id, labels, datasets) {
    destroyChart(id); const ctx = document.getElementById(id); if (!ctx) return;
    charts[id] = new Chart(ctx, {
        type:'line', data:{labels, datasets},
        options:{ maintainAspectRatio:false, responsive:true,
            plugins:{legend:{labels:{color:'#cbd5e1', font:{size:11}}}, tooltip:{callbacks:{label: c => c.dataset.label+': '+fmtNum(c.raw)}}},
            scales:{ x:{ticks:{color:'#94a3b8', font:{size:10}}, grid:{color:'#334155'}},
                y:{ticks:{color:'#94a3b8', font:{size:10}, callback: v => fmtNum(v)}, grid:{color:'#334155'}}} }
    });
}'''
assert old_resumen in html, "resumen anchor not found"
html = html.replace(old_resumen, new_resumen)

# Update Resumen chart titles
html = html.replace('Top 15 SubCategorías por Ventas', 'Top 15 SubCategorías por Unidades')
html = html.replace('Top 15 Categorías por Ventas', 'Top 15 Categorías por Unidades')
html = html.replace('<h3>Ventas por Mes</h3>', '<h3>Unidades por Mes</h3>')
html = html.replace('<h3>Profit por Mes</h3>', '<h3>Transacciones por Mes</h3>')
html = html.replace('Ventas por Provincia (Top 10)', 'Unidades por Provincia (Top 10)')
html = html.replace('<h3>Ventas por Año</h3>', '<h3>Unidades por Año</h3>')

# ============================================================
# Evolución charts & table
# ============================================================
old_evol = '''function renderEvolucionCharts() {
    const mesMap = aggregateMonth();
    const mesArr = [...mesMap.entries()].map(([k,e])=>[LK.ym[k], e.v, e.p, e.q, e.t]);
    mesArr.sort((a,b)=>a[0].localeCompare(b[0]));
    makeLineChart('chartEvolMes', mesArr.map(x=>x[0]), [{label:'Ventas', data:mesArr.map(x=>x[1]), borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,.15)', tension:.2, fill:true}]);
    makeLineChart('chartEvolProfit', mesArr.map(x=>x[0]), [{label:'Profit', data:mesArr.map(x=>x[2]), borderColor:'#10b981', backgroundColor:'rgba(16,185,129,.15)', tension:.2, fill:true}]);
    const margen = mesArr.map(x => x[1] ? +(x[2]*100/x[1]).toFixed(2) : 0);
    makeLineChart('chartEvolMargen', mesArr.map(x=>x[0]), [{label:'Margen %', data:margen, borderColor:'#f59e0b', backgroundColor:'rgba(245,158,11,.15)', tension:.2, fill:true}], v => v+'%');
    destroyChart('chartEvolCant');
    charts['chartEvolCant'] = new Chart(document.getElementById('chartEvolCant'), {
        type:'bar', data:{labels:mesArr.map(x=>x[0]), datasets:[{label:'Cantidad', data:mesArr.map(x=>x[3]), backgroundColor:'#06b6d4'}]},
        options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback: v=>fmtNum(v)}, grid:{color:'#334155'}}}}
    });
    destroyChart('chartEvolTrans');
    charts['chartEvolTrans'] = new Chart(document.getElementById('chartEvolTrans'), {
        type:'bar', data:{labels:mesArr.map(x=>x[0]), datasets:[{label:'Transacciones', data:mesArr.map(x=>x[4]), backgroundColor:'#8b5cf6'}]},
        options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback: v=>fmtNum(v)}, grid:{color:'#334155'}}}}
    });
    // tabla
    const tot = mesArr.reduce((a,m)=>{a.v+=m[1];a.p+=m[2];a.q+=m[3];a.t+=m[4];return a;}, {v:0,p:0,q:0,t:0});
    let html = '<table><thead><tr><th>Mes</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">Margen</th><th class="num">Cantidad</th><th class="num">Trans.</th></tr></thead><tbody>';
    mesArr.forEach(m => {
        const margen = m[1] ? (m[2]*100/m[1]) : 0;
        html += `<tr><td>${m[0]}</td><td class="num">${fmtMoney(m[1])}</td><td class="num pos">${fmtMoney(m[2])}</td><td class="num">${margen.toFixed(2)}%</td><td class="num">${fmtNum(m[3])}</td><td class="num">${fmtNum(m[4])}</td></tr>`;
    });
    html += `<tr style="background:var(--bg-3); font-weight:bold"><td>TOTAL (${mesArr.length})</td><td class="num">${fmtMoney(tot.v)}</td><td class="num pos">${fmtMoney(tot.p)}</td><td class="num">${tot.v?(tot.p*100/tot.v).toFixed(2):'0'}%</td><td class="num">${fmtNum(tot.q)}</td><td class="num">${fmtNum(tot.t)}</td></tr></tbody></table>`;
    document.getElementById('tableMes').innerHTML = html;
}'''

new_evol = '''function renderEvolucionCharts() {
    const mesMap = aggregateMonth();
    const mesArr = [...mesMap.entries()].map(([k,e])=>[LK.ym[k], e.q, e.t]);
    mesArr.sort((a,b)=>a[0].localeCompare(b[0]));
    makeLineChartQty('chartEvolMes', mesArr.map(x=>x[0]), [{label:'Unidades', data:mesArr.map(x=>x[1]), borderColor:'#06b6d4', backgroundColor:'rgba(6,182,212,.15)', tension:.2, fill:true}]);
    makeLineChartQty('chartEvolProfit', mesArr.map(x=>x[0]), [{label:'Transacciones', data:mesArr.map(x=>x[2]), borderColor:'#8b5cf6', backgroundColor:'rgba(139,92,246,.15)', tension:.2, fill:true}]);
    // Uds / trans. en lugar de margen
    const udsPorTrans = mesArr.map(x => x[2] ? +(x[1]/x[2]).toFixed(2) : 0);
    makeLineChartQty('chartEvolMargen', mesArr.map(x=>x[0]), [{label:'Uds / trans.', data:udsPorTrans, borderColor:'#f59e0b', backgroundColor:'rgba(245,158,11,.15)', tension:.2, fill:true}]);
    destroyChart('chartEvolCant');
    charts['chartEvolCant'] = new Chart(document.getElementById('chartEvolCant'), {
        type:'bar', data:{labels:mesArr.map(x=>x[0]), datasets:[{label:'Unidades', data:mesArr.map(x=>x[1]), backgroundColor:'#06b6d4'}]},
        options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback: v=>fmtNum(v)}, grid:{color:'#334155'}}}}
    });
    destroyChart('chartEvolTrans');
    charts['chartEvolTrans'] = new Chart(document.getElementById('chartEvolTrans'), {
        type:'bar', data:{labels:mesArr.map(x=>x[0]), datasets:[{label:'Transacciones', data:mesArr.map(x=>x[2]), backgroundColor:'#8b5cf6'}]},
        options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback: v=>fmtNum(v)}, grid:{color:'#334155'}}}}
    });
    // tabla
    const tot = mesArr.reduce((a,m)=>{a.q+=m[1];a.t+=m[2];return a;}, {q:0,t:0});
    let html = '<table><thead><tr><th>Mes</th><th class="num">Unidades</th><th class="num">Transacciones</th><th class="num">Uds / trans.</th></tr></thead><tbody>';
    mesArr.forEach(m => {
        const udsT = m[2] ? (m[1]/m[2]) : 0;
        html += `<tr><td>${m[0]}</td><td class="num">${fmtNum(m[1])}</td><td class="num">${fmtNum(m[2])}</td><td class="num">${udsT.toFixed(2)}</td></tr>`;
    });
    html += `<tr style="background:var(--bg-3); font-weight:bold"><td>TOTAL (${mesArr.length})</td><td class="num">${fmtNum(tot.q)}</td><td class="num">${fmtNum(tot.t)}</td><td class="num">${tot.t?(tot.q/tot.t).toFixed(2):'0'}</td></tr></tbody></table>`;
    document.getElementById('tableMes').innerHTML = html;
}'''
assert old_evol in html, "evolucion anchor not found"
html = html.replace(old_evol, new_evol)

# Update Evolución titles
html = html.replace('<h3>Ventas mensuales</h3>', '<h3>Unidades mensuales</h3>')
html = html.replace('<h3>Profit mensual</h3>', '<h3>Transacciones mensuales</h3>')
html = html.replace('<h3>Margen % mensual</h3>', '<h3>Pedidos por cliente activo</h3>')
html = html.replace('<h3>Cantidad mensual</h3>', '<h3>Unidades por mes (bar)</h3>')
html = html.replace('<h3>Transacciones mensuales</h3>', '<h3>Transacciones por mes (bar)</h3>')

# ============================================================
# Dim tables - remove $ columns
# ============================================================
old_dim = '''function renderDimTab(tab, colIdx, lookupArr, searchId, tableId, label, isClickable) {
    const q = (document.getElementById(searchId)?.value || '').toLowerCase().trim();
    let rows = buildDimRows(colIdx, lookupArr);
    if (q) rows = rows.filter(r => String(r[0]||'').toLowerCase().includes(q));
    const s = STATE.sort[tab] || {key:'v', dir:'desc'};
    // Column names -> index: name=0,v=1,p=2,q=3,t=4
    const keyMap = {nombre:0, ventas:1, profit:2, cantidad:3, trans:4};
    const idx2 = keyMap[s.key] !== undefined ? keyMap[s.key] : 1;
    sortArr(rows, idx2, s.dir);
    const totV = rows.reduce((a,r)=>a+r[1],0);
    const arr = (k) => arrowOf(tab, k);
    const clickFn = tab==='subcategorias' ? 'showSubcatDetail' : null;
    let html = `<table><thead><tr>
        <th onclick="sortBy('${tab}','nombre')">${label}${arr('nombre')}</th>
        <th class="num" onclick="sortBy('${tab}','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('${tab}','profit')">Profit${arr('profit')}</th>
        <th class="num">Margen</th>
        <th class="num">% Total</th>
        <th class="num" onclick="sortBy('${tab}','cantidad')">Cantidad${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('${tab}','trans')">Trans.${arr('trans')}</th>
        <th class="num">Ticket</th>
    </tr></thead><tbody>`;
    rows.forEach(r => {
        const margen = r[1] ? (r[2]*100/r[1]) : 0;
        const pct = totV ? (r[1]*100/totV) : 0;
        const ticket = r[4] ? r[1]/r[4] : 0;
        const nameCell = clickFn
            ? `<td class="clickable" onclick="${clickFn}('${escAttr(r[0])}')">${r[0]||'(sin dato)'}</td>`
            : `<td>${r[0]||'(sin dato)'}</td>`;
        html += `<tr>${nameCell}
            <td class="num">${fmtMoney(r[1])}</td>
            <td class="num ${r[2]>=0?'pos':'neg'}">${fmtMoney(r[2])}</td>
            <td class="num">${margen.toFixed(1)}%</td>
            <td class="num">${pct.toFixed(2)}%</td>
            <td class="num">${fmtNum(r[3])}</td>
            <td class="num">${fmtNum(r[4])}</td>
            <td class="num">${fmtMoney(ticket)}</td>
        </tr>`;
    });
    html += `<tr style="background:var(--bg-3); font-weight:bold"><td>TOTAL (${rows.length})</td><td class="num">${fmtMoney(totV)}</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>`;
    html += '</tbody></table>';
    document.getElementById(tableId).innerHTML = html;
    // Cache for CSV export
    STATE.lastDim = STATE.lastDim || {};
    STATE.lastDim[tab] = rows;
}'''

new_dim = '''function renderDimTab(tab, colIdx, lookupArr, searchId, tableId, label, isClickable) {
    const q = (document.getElementById(searchId)?.value || '').toLowerCase().trim();
    let rows = buildDimRows(colIdx, lookupArr);
    if (q) rows = rows.filter(r => String(r[0]||'').toLowerCase().includes(q));
    const s = STATE.sort[tab] || {key:'q', dir:'desc'};
    const keyMap = {nombre:0, cantidad:3, trans:4, q:3, t:4};
    const idx2 = keyMap[s.key] !== undefined ? keyMap[s.key] : 3;
    sortArr(rows, idx2, s.dir);
    const totQ = rows.reduce((a,r)=>a+r[3],0);
    const totT = rows.reduce((a,r)=>a+r[4],0);
    const arr = (k) => arrowOf(tab, k);
    const clickFn = tab==='subcategorias' ? 'showSubcatDetail' : null;
    let html = `<table><thead><tr>
        <th onclick="sortBy('${tab}','nombre')">${label}${arr('nombre')}</th>
        <th class="num" onclick="sortBy('${tab}','cantidad')">Unidades${arr('cantidad')}</th>
        <th class="num">% uds</th>
        <th class="num" onclick="sortBy('${tab}','trans')">Transacciones${arr('trans')}</th>
        <th class="num">% trans.</th>
        <th class="num">Uds / trans.</th>
    </tr></thead><tbody>`;
    rows.forEach(r => {
        const pctQ = totQ ? (r[3]*100/totQ) : 0;
        const pctT = totT ? (r[4]*100/totT) : 0;
        const udsPorTrans = r[4] ? (r[3]/r[4]) : 0;
        const nameCell = clickFn
            ? `<td class="clickable" onclick="${clickFn}('${escAttr(r[0])}')">${r[0]||'(sin dato)'}</td>`
            : `<td>${r[0]||'(sin dato)'}</td>`;
        html += `<tr>${nameCell}
            <td class="num">${fmtNum(r[3])}</td>
            <td class="num">${pctQ.toFixed(2)}%</td>
            <td class="num">${fmtNum(r[4])}</td>
            <td class="num">${pctT.toFixed(2)}%</td>
            <td class="num">${udsPorTrans.toFixed(2)}</td>
        </tr>`;
    });
    html += `<tr style="background:var(--bg-3); font-weight:bold"><td>TOTAL (${rows.length})</td><td class="num">${fmtNum(totQ)}</td><td></td><td class="num">${fmtNum(totT)}</td><td></td><td></td></tr>`;
    html += '</tbody></table>';
    document.getElementById(tableId).innerHTML = html;
    STATE.lastDim = STATE.lastDim || {};
    STATE.lastDim[tab] = rows;
}'''
assert old_dim in html, "dim anchor not found"
html = html.replace(old_dim, new_dim)

# ============================================================
# Clientes table - swap cols + use new vendor (we will inject vendorReciente)
# ============================================================
old_clientes_filter = '''      <select id="cliMin" class="filter-select">
        <option value="0">Cualquier monto</option>
        <option value="100000">Ventas ≥ $100K</option>
        <option value="1000000">Ventas ≥ $1M</option>
        <option value="10000000">Ventas ≥ $10M</option>
        <option value="100000000">Ventas ≥ $100M</option>
      </select>'''
new_clientes_filter = '''      <select id="cliMin" class="filter-select">
        <option value="0">Cualquier volumen</option>
        <option value="5">Con 5+ compras</option>
        <option value="20">Con 20+ compras</option>
        <option value="50">Con 50+ compras</option>
      </select>'''
html = html.replace(old_clientes_filter, new_clientes_filter)

old_clientes = '''function renderClientes() {
    const q = document.getElementById('searchClientes').value.toLowerCase().trim();
    const minV = +document.getElementById('cliMin').value;
    const map = aggregateCli();
    const rows = [];
    const todayDays = Math.floor((Date.now() - EPOCH_MS) / 86400000);
    map.forEach((e, id) => {
        const meta = D.clientesById[id] || {};
        const nombre = LK.clienteName[e.nIdx] || meta.nombre || '(sin dato)';
        if (q) {
            if (!(nombre.toLowerCase().includes(q) || String(id).includes(q))) return;
        }
        if (minV && e.v < minV) return;
        rows.push({
            id, nombre, ventas:e.v, profit:e.p, cantidad:e.q, trans:e.t,
            ultimaDays: e.lastDays,
            ultima: (e.lastDays >= 0) ? fmtDate(e.lastDays) : '-',
            dias: (e.lastDays >= 0) ? (todayDays - e.lastDays) : null,
            provincia: meta.provincia || LK.prov[e.provIdx],
            clase: meta.clase || LK.clase[e.claseIdx],
            vendedor: meta.vendedor || LK.vend[e.vendIdx],
        });
    });
    const s = STATE.sort.clientes || {key:'ventas', dir:'desc'};
    rows.sort((a,b)=>{ const va=a[s.key], vb=b[s.key]; const m = s.dir==='desc'?-1:1; if (typeof va==='number') return (va-vb)*m; return String(va||'').localeCompare(String(vb||''))*m; });
    const total = rows.length;
    const sumV = rows.reduce((a,r)=>a+r.ventas,0);
    const page = STATE.page.clientes;
    const slice = rows.slice(page*STATE.pageSize, (page+1)*STATE.pageSize);
    const arr = (k) => arrowOf('clientes', k);
    let html = `<table><thead><tr>
        <th onclick="sortBy('clientes','id')">ID${arr('id')}</th>
        <th onclick="sortBy('clientes','nombre')">Cliente${arr('nombre')}</th>
        <th class="num" onclick="sortBy('clientes','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('clientes','profit')">Profit${arr('profit')}</th>
        <th class="num" onclick="sortBy('clientes','cantidad')">Cantidad${arr('cantidad')}</th>
        <th onclick="sortBy('clientes','ultimaDays')">Última compra${arr('ultimaDays')}</th>
        <th class="num" onclick="sortBy('clientes','dias')">Días atrás${arr('dias')}</th>
        <th class="num" onclick="sortBy('clientes','trans')">Trans.${arr('trans')}</th>
        <th class="num">Margen</th>
        <th onclick="sortBy('clientes','provincia')">Provincia${arr('provincia')}</th>
        <th onclick="sortBy('clientes','clase')">Clase${arr('clase')}</th>
        <th>Vendedor</th>
    </tr></thead><tbody>`;
    slice.forEach(c => {
        const m = c.ventas ? (c.profit*100/c.ventas) : 0;
        const diasColor = c.dias == null ? 'var(--text-dim)' : (c.dias <= 180 ? 'var(--good)' : (c.dias <= 730 ? 'var(--warn)' : 'var(--bad)'));
        html += `<tr>
            <td>${c.id||''}</td>
            <td class="clickable" onclick="showClienteDetail('${escAttr(c.nombre)}', ${c.id||'null'})">${c.nombre}</td>
            <td class="num">${fmtMoney(c.ventas)}</td>
            <td class="num ${c.profit>=0?'pos':'neg'}">${fmtMoney(c.profit)}</td>
            <td class="num">${fmtNum(c.cantidad)}</td>
            <td>${c.ultima}</td>
            <td class="num" style="color:${diasColor}; font-weight:600">${c.dias != null ? fmtNum(c.dias) : '-'}</td>
            <td class="num">${fmtNum(c.trans)}</td>
            <td class="num">${m.toFixed(1)}%</td>
            <td>${c.provincia||''}</td>
            <td>${c.clase||''}</td>
            <td>${c.vendedor||''}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('tableClientes').innerHTML = html;
    STATE.lastClientes = rows;
    renderPagination('clientes', 'pagClientes', total, page, sumV);
}'''

new_clientes = '''function renderClientes() {
    const q = document.getElementById('searchClientes').value.toLowerCase().trim();
    const minV = +document.getElementById('cliMin').value;
    const map = aggregateCli();
    const rows = [];
    const todayDays = Math.floor((Date.now() - EPOCH_MS) / 86400000);
    map.forEach((e, id) => {
        const meta = D.clientesById[id] || {};
        const nombre = LK.clienteName[e.nIdx] || meta.nombre || '(sin dato)';
        if (q) {
            if (!(nombre.toLowerCase().includes(q) || String(id).includes(q))) return;
        }
        if (minV && e.t < minV) return;
        rows.push({
            id, nombre, cantidad:e.q, trans:e.t, nIdx:e.nIdx,
            ultimaDays: e.lastDays,
            ultima: (e.lastDays >= 0) ? fmtDate(e.lastDays) : '-',
            dias: (e.lastDays >= 0) ? (todayDays - e.lastDays) : null,
            provincia: meta.provincia || LK.prov[e.provIdx],
            clase: meta.clase || LK.clase[e.claseIdx],
            vendedor: vendedorReciente(e.nIdx, meta.vendedor || LK.vend[e.vendIdx]),
        });
    });
    const s = STATE.sort.clientes || {key:'trans', dir:'desc'};
    rows.sort((a,b)=>{ const va=a[s.key], vb=b[s.key]; const m = s.dir==='desc'?-1:1; if (typeof va==='number') return (va-vb)*m; return String(va||'').localeCompare(String(vb||''))*m; });
    const total = rows.length;
    const sumT = rows.reduce((a,r)=>a+r.trans,0);
    const sumQ = rows.reduce((a,r)=>a+r.cantidad,0);
    const page = STATE.page.clientes;
    const slice = rows.slice(page*STATE.pageSize, (page+1)*STATE.pageSize);
    const arr = (k) => arrowOf('clientes', k);
    let html = `<table><thead><tr>
        <th onclick="sortBy('clientes','id')">ID${arr('id')}</th>
        <th onclick="sortBy('clientes','nombre')">Cliente${arr('nombre')}</th>
        <th class="num" onclick="sortBy('clientes','cantidad')">Unidades${arr('cantidad')}</th>
        <th onclick="sortBy('clientes','ultimaDays')">Última compra${arr('ultimaDays')}</th>
        <th class="num" onclick="sortBy('clientes','dias')">Días atrás${arr('dias')}</th>
        <th class="num" onclick="sortBy('clientes','trans')">Transacciones${arr('trans')}</th>
        <th class="num">Uds / trans.</th>
        <th onclick="sortBy('clientes','provincia')">Provincia${arr('provincia')}</th>
        <th onclick="sortBy('clientes','clase')">Clase${arr('clase')}</th>
        <th onclick="sortBy('clientes','vendedor')">Vendedor reciente${arr('vendedor')}</th>
    </tr></thead><tbody>`;
    slice.forEach(c => {
        const udsPorTrans = c.trans ? (c.cantidad/c.trans) : 0;
        const diasColor = c.dias == null ? 'var(--text-dim)' : (c.dias <= 180 ? 'var(--good)' : (c.dias <= 730 ? 'var(--warn)' : 'var(--bad)'));
        html += `<tr>
            <td>${c.id||''}</td>
            <td class="clickable" onclick="showClienteDetail('${escAttr(c.nombre)}', ${c.id||'null'})">${c.nombre}</td>
            <td class="num">${fmtNum(c.cantidad)}</td>
            <td>${c.ultima}</td>
            <td class="num" style="color:${diasColor}; font-weight:600">${c.dias != null ? fmtNum(c.dias) : '-'}</td>
            <td class="num">${fmtNum(c.trans)}</td>
            <td class="num">${udsPorTrans.toFixed(2)}</td>
            <td>${c.provincia||''}</td>
            <td>${c.clase||''}</td>
            <td>${c.vendedor||''}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('tableClientes').innerHTML = html;
    STATE.lastClientes = rows;
    renderPaginationCli('clientes', 'pagClientes', total, page, sumT, sumQ);
}
function renderPaginationCli(tab, contId, total, page, sumT, sumQ) {
    const totalPages = Math.ceil(total / STATE.pageSize);
    document.getElementById(contId).innerHTML = `
        <div>${fmtNum(total)} ${tab} · ${fmtNum(sumT)} transacciones · ${fmtNum(sumQ)} unidades · página ${page+1}/${Math.max(1,totalPages)}</div>
        <div class="controls">
            <button class="page-btn" onclick="changePage('${tab}',-1)" ${page===0?'disabled':''}>←</button>
            <button class="page-btn" onclick="changePage('${tab}',1)" ${page>=totalPages-1?'disabled':''}>→</button>
        </div>`;
}'''
assert old_clientes in html, "clientes anchor not found"
html = html.replace(old_clientes, new_clientes)

# ============================================================
# Articulos table - remove $ columns
# ============================================================
old_articulos = '''    let html = `<table><thead><tr>
        <th onclick="sortBy('articulos','codigo')">Código${arr('codigo')}</th>
        <th onclick="sortBy('articulos','articulo')">Artículo${arr('articulo')}</th>
        <th onclick="sortBy('articulos','marca')">Marca${arr('marca')}</th>
        <th onclick="sortBy('articulos','subcat')">SubCategoría${arr('subcat')}</th>
        <th class="num" onclick="sortBy('articulos','sr')">Stock aging${arr('sr')}</th>
        <th class="num" onclick="sortBy('articulos','fis')">Stock${arr('fis')}</th>
        <th class="num" onclick="sortBy('articulos','ventas')">Ventas${arr('ventas')}</th>
        <th class="num" onclick="sortBy('articulos','profit')">Profit${arr('profit')}</th>
        <th class="num">Margen</th>
        <th class="num" onclick="sortBy('articulos','cantidad')">Cant.${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('articulos','trans')">Trans.${arr('trans')}</th>
    </tr></thead><tbody>`;
    slice.forEach(a => {
        const m = a.ventas ? (a.profit*100/a.ventas) : 0;
        const cls = a.sinRot ? ' class="sin-rot"' : '';
        // Badge color por bucket más viejo de aging (verde→rojo oscuro)
        let badge = '';
        if (a.sinRot && typeof __AGING__ !== 'undefined') {
            const ag = __AGING__[a.codigo];
            const colors = ['#10b981','#84cc16','#eab308','#f59e0b','#ef4444','#7c2d12'];
            const labels = ['0-30d','30-60d','60-90d','90-150d','150-365d','+365d'];
            const oldIdx = ag && typeof ag.old === 'number' ? ag.old : 5;
            badge = `<span class="sr-badge" style="background:${colors[oldIdx]||'#7c2d12'}">${labels[oldIdx]||'AGING'}</span>`;
        }
        html += `<tr${cls}>
            <td class="clickable" onclick="showArticuloDetail('${escAttr(a.codigo)}')">${a.codigo}${badge}</td>
            <td class="clickable" onclick="showArticuloDetail('${escAttr(a.codigo)}')">${a.articulo}</td>
            <td>${a.marca}</td>
            <td>${a.subcat}</td>
            <td class="num" style="color:${a.sr?'var(--bad)':'var(--text-dim)'}">${a.sr?fmtNum(a.sr):'-'}</td>
            <td class="num">${a.fis?fmtNum(a.fis):'-'}</td>
            <td class="num">${fmtMoney(a.ventas)}</td>
            <td class="num ${a.profit>=0?'pos':'neg'}">${fmtMoney(a.profit)}</td>
            <td class="num">${m.toFixed(1)}%</td>
            <td class="num">${fmtNum(a.cantidad)}</td>
            <td class="num">${fmtNum(a.trans)}</td>
        </tr>`;
    });'''

new_articulos = '''    let html = `<table><thead><tr>
        <th onclick="sortBy('articulos','codigo')">Código${arr('codigo')}</th>
        <th onclick="sortBy('articulos','articulo')">Artículo${arr('articulo')}</th>
        <th onclick="sortBy('articulos','marca')">Marca${arr('marca')}</th>
        <th onclick="sortBy('articulos','subcat')">SubCategoría${arr('subcat')}</th>
        <th class="num" onclick="sortBy('articulos','sr')">Aging${arr('sr')}</th>
        <th class="num" onclick="sortBy('articulos','fis')">Stock${arr('fis')}</th>
        <th class="num" onclick="sortBy('articulos','cantidad')">Unidades${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('articulos','trans')">Transacciones${arr('trans')}</th>
        <th class="num">Uds / trans.</th>
    </tr></thead><tbody>`;
    slice.forEach(a => {
        const udsT = a.trans ? (a.cantidad/a.trans) : 0;
        const cls = a.sinRot ? ' class="sin-rot"' : '';
        let badge = '';
        if (a.sinRot && typeof __AGING__ !== 'undefined') {
            const ag = __AGING__[a.codigo];
            const colors = ['#10b981','#84cc16','#eab308','#f59e0b','#ef4444','#7c2d12'];
            const labels = ['0-30d','30-60d','60-90d','90-150d','150-365d','+365d'];
            const oldIdx = ag && typeof ag.old === 'number' ? ag.old : 5;
            badge = `<span class="sr-badge" style="background:${colors[oldIdx]||'#7c2d12'}">${labels[oldIdx]||'AGING'}</span>`;
        }
        html += `<tr${cls}>
            <td class="clickable" onclick="showArticuloDetail('${escAttr(a.codigo)}')">${a.codigo}${badge}</td>
            <td class="clickable" onclick="showArticuloDetail('${escAttr(a.codigo)}')">${a.articulo}</td>
            <td>${a.marca}</td>
            <td>${a.subcat}</td>
            <td class="num" style="color:${a.sr?'var(--bad)':'var(--text-dim)'}">${a.sr?fmtNum(a.sr):'-'}</td>
            <td class="num">${a.fis?fmtNum(a.fis):'-'}</td>
            <td class="num">${fmtNum(a.cantidad)}</td>
            <td class="num">${fmtNum(a.trans)}</td>
            <td class="num">${udsT.toFixed(2)}</td>
        </tr>`;
    });'''
assert old_articulos in html, "articulos anchor not found"
html = html.replace(old_articulos, new_articulos)

# Fix pagination of articulos (was also using $ references)
html = html.replace(
    '''        <div>${fmtNum(total)} artículos · ventas: ${fmtMoney(sumV)}${onlySR?' · '+fmtNum(sumSR)+' uds en aging':''} · página ${page+1}/${Math.max(1,totalPages)}</div>''',
    '''        <div>${fmtNum(total)} artículos · ${fmtNum(sumQ)} unidades · ${fmtNum(sumT)} transacciones${onlySR?' · '+fmtNum(sumSR)+' uds en aging':''} · página ${page+1}/${Math.max(1,totalPages)}</div>'''
)
# That pagination also needs sumQ/sumT variables. Find and update:
html = html.replace(
    '''    const total = rows.length;
    const sumV = rows.reduce((a,r)=>a+r.ventas,0);
    const sumSR = rows.reduce((a,r)=>a+(r.sr||0),0);
    const page = STATE.page.articulos;''',
    '''    const total = rows.length;
    const sumV = rows.reduce((a,r)=>a+r.ventas,0);
    const sumQ = rows.reduce((a,r)=>a+r.cantidad,0);
    const sumT = rows.reduce((a,r)=>a+r.trans,0);
    const sumSR = rows.reduce((a,r)=>a+(r.sr||0),0);
    const page = STATE.page.articulos;'''
)

# Default sort for articulos = cantidad
html = html.replace(
    '''    const s = STATE.sort.articulos || {key:'ventas', dir:'desc'};''',
    '''    const s = STATE.sort.articulos || {key:'cantidad', dir:'desc'};''',
    1
)

# ============================================================
# Pagination generic (the renderPagination for articulos uses sumV as $ - replace call site)
# ============================================================
html = html.replace(
    "renderPagination('articulos', 'pagArt', total, page, sumV);",
    "renderPaginationArt('articulos', 'pagArt', total, page, sumQ, sumT, sumSR);"
)
# Remove the old function call pattern for pagination that used sumV for clientes (already replaced in renderClientes)
# Now define renderPaginationArt
html = html.replace(
    '''function renderPagination(tab, contId, total, page, sumV) {
    const totalPages = Math.ceil(total / STATE.pageSize);
    document.getElementById(contId).innerHTML = `
        <div>${fmtNum(total)} ${tab} · suma ventas: ${fmtMoney(sumV)} · página ${page+1}/${Math.max(1,totalPages)}</div>''',
    '''function renderPagination(tab, contId, total, page, sumV) {
    // placeholder — not used in vendedores version
    const totalPages = Math.ceil(total / STATE.pageSize);
    document.getElementById(contId).innerHTML = `
        <div>${fmtNum(total)} ${tab} · página ${page+1}/${Math.max(1,totalPages)}</div>'''
)
# Also hide the $ reference in pagination Art — already replaced via renderPaginationArt above
# We still need to define renderPaginationArt. Inject it right before renderPagination:
html = html.replace(
    '''function renderPagination(tab, contId, total, page, sumV) {
    // placeholder — not used in vendedores version''',
    '''function renderPaginationArt(tab, contId, total, page, sumQ, sumT, sumSR) {
    const totalPages = Math.ceil(total / STATE.pageSize);
    document.getElementById(contId).innerHTML = `
        <div>${fmtNum(total)} artículos · ${fmtNum(sumQ)} unidades · ${fmtNum(sumT)} transacciones${sumSR?' · <span style="color:var(--bad)">'+fmtNum(sumSR)+' uds sin rotación</span>':''} · página ${page+1}/${Math.max(1,totalPages)}</div>
        <div class="controls">
            <button class="page-btn" onclick="changePage('${tab}',-1)" ${page===0?'disabled':''}>←</button>
            <button class="page-btn" onclick="changePage('${tab}',1)" ${page>=totalPages-1?'disabled':''}>→</button>
        </div>`;
}
function renderPagination(tab, contId, total, page, sumV) {
    // placeholder — not used in vendedores version'''
)

# ============================================================
# Cliente detail modal - remove $ KPIs and yearly $ cols
# ============================================================
old_cli_kpis = '''    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:14px">${name}</div><div class="sub">ID: ${cliId||'-'} · ${meta.provincia||''}</div></div>
            <div class="kpi"><div class="label">Ventas</div><div class="value">${fmtMoney(tot.v)}</div></div>
            <div class="kpi"><div class="label">Profit</div><div class="value pos">${fmtMoney(tot.p)}</div><div class="sub">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}% margen</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">Cant: ${fmtNum(tot.q)}</div></div>
            <div class="kpi"><div class="label">Vendedor</div><div class="value" style="font-size:13px">${meta.vendedor||'-'}</div><div class="sub">${meta.clase||''}</div></div>
        </div>`;'''
new_cli_kpis = '''    const vendRec = vendedorReciente(cliNameIdx, meta.vendedor);
    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:14px">${name}</div><div class="sub">ID: ${cliId||'-'} · ${meta.provincia||''}</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div></div>
            <div class="kpi"><div class="label">Unidades</div><div class="value">${fmtNum(tot.q)}</div><div class="sub">${tot.t?(tot.q/tot.t).toFixed(2):'0'} uds/trans.</div></div>
            <div class="kpi"><div class="label">Vendedor reciente</div><div class="value" style="font-size:13px; color:var(--accent-2)">${vendRec||'-'}</div><div class="sub">últimos 3 meses</div></div>
            <div class="kpi"><div class="label">Clase</div><div class="value" style="font-size:13px">${meta.clase||'-'}</div></div>
        </div>`;'''
assert old_cli_kpis in html, "cli kpis anchor not found"
html = html.replace(old_cli_kpis, new_cli_kpis)

old_yrly = '''    if (yrArr.length) {
        body += `<h3 style="margin:14px 0 8px">📅 Evolución por Año <span style="font-size:11px;color:var(--text-dim);font-weight:normal">— click un año para filtrar las subcategorías</span></h3>
            <div class="table-wrap" style="max-height:220px; margin-bottom:10px"><table id="cli-year-table"><thead><tr><th>Año</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">Margen</th><th class="num">Cantidad</th><th class="num">Trans.</th></tr></thead><tbody>`;
        yrArr.forEach(([y,e]) => {
            const m = e.v ? (e.p*100/e.v) : 0;
            body += `<tr style="cursor:pointer" data-cli-year="${y}" onclick="filterClienteByYear(${y})" title="Click para filtrar subcategorías a ${y}"><td>${y}</td><td class="num">${fmtMoney(e.v)}</td><td class="num pos">${fmtMoney(e.p)}</td><td class="num">${m.toFixed(1)}%</td><td class="num">${fmtNum(e.q)}</td><td class="num">${fmtNum(e.t)}</td></tr>`;
        });
        body += '</tbody></table></div>';
    }'''
new_yrly = '''    if (yrArr.length) {
        body += `<h3 style="margin:14px 0 8px">📅 Evolución por Año <span style="font-size:11px;color:var(--text-dim);font-weight:normal">— click un año para filtrar las subcategorías</span></h3>
            <div class="table-wrap" style="max-height:220px; margin-bottom:10px"><table id="cli-year-table"><thead><tr><th>Año</th><th class="num">Unidades</th><th class="num">Transacciones</th><th class="num">Uds / trans.</th></tr></thead><tbody>`;
        yrArr.forEach(([y,e]) => {
            const udsT = e.t ? (e.q/e.t) : 0;
            body += `<tr style="cursor:pointer" data-cli-year="${y}" onclick="filterClienteByYear(${y})" title="Click para filtrar subcategorías a ${y}"><td>${y}</td><td class="num">${fmtNum(e.q)}</td><td class="num">${fmtNum(e.t)}</td><td class="num">${udsT.toFixed(2)}</td></tr>`;
        });
        body += '</tbody></table></div>';
    }'''
assert old_yrly in html, "yearly anchor not found"
html = html.replace(old_yrly, new_yrly)

# Reemplazar la función _cliRenderSubcats por la versión sin precios
# (usa unidades/transacciones en vez de ventas/profit/margen)
old_render_subs = '''function _cliRenderSubcats() {
    const ctx = window._cliCtx;
    if (!ctx) return;
    const wrap = document.getElementById('cli-subcat-wrap');
    if (!wrap) return;
    const idxs = ctx.selectedYear == null ? ctx.allIdxs : (ctx.yrIdxsMap.get(ctx.selectedYear) || []);
    const tot = aggTotals(idxs);
    const subMap = aggOnIndexes(idxs, C.sub);
    const subArr = [...subMap.entries()].map(([k,e])=>[LK.subcat[k]||'(sin dato)', e.v, e.p, e.q, e.t]);
    subArr.sort((a,b)=>b[1]-a[1]);
    const yrLabel = ctx.selectedYear == null
        ? ' — click para ver artículos'
        : ` — <span style="color:var(--accent);font-weight:600">año ${ctx.selectedYear}</span> <a style="color:var(--text-dim);cursor:pointer;font-size:12px;text-decoration:underline;font-weight:normal" onclick="filterClienteByYear(${ctx.selectedYear})">(limpiar filtro)</a>`;
    let html = `<h3 style="margin:14px 0 8px">📦 SubCategorías compradas${yrLabel}</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>SubCategoría</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">% del cliente</th><th class="num">Cant.</th><th class="num">Trans.</th><th></th>
        </tr></thead><tbody>`;
    subArr.forEach(s => {
        const pct = tot.v ? (s[1]*100/tot.v) : 0;
        html += `<tr>
            <td class="clickable" onclick="showClienteSubcatArticulos('${escAttr(ctx.name)}', '${escAttr(s[0])}')">${s[0]}</td>
            <td class="num">${fmtMoney(s[1])}</td>
            <td class="num pos">${fmtMoney(s[2])}</td>
            <td class="num">${pct.toFixed(1)}%</td>
            <td class="num">${fmtNum(s[3])}</td>
            <td class="num">${fmtNum(s[4])}</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteSubcatArticulos('${escAttr(ctx.name)}', '${escAttr(s[0])}')">Ver artículos →</button></td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    wrap.innerHTML = html;
}'''
new_render_subs = '''function _cliRenderSubcats() {
    const ctx = window._cliCtx;
    if (!ctx) return;
    const wrap = document.getElementById('cli-subcat-wrap');
    if (!wrap) return;
    const idxs = ctx.selectedYear == null ? ctx.allIdxs : (ctx.yrIdxsMap.get(ctx.selectedYear) || []);
    const tot = aggTotals(idxs);
    const subMap = aggOnIndexes(idxs, C.sub);
    const subArr = [...subMap.entries()].map(([k,e])=>[LK.subcat[k]||'(sin dato)', e.v, e.p, e.q, e.t]);
    // Sort por unidades (index 3) en lugar de ventas
    subArr.sort((a,b)=>b[3]-a[3]);
    const yrLabel = ctx.selectedYear == null
        ? ' — click para ver artículos'
        : ` — <span style="color:var(--accent);font-weight:600">año ${ctx.selectedYear}</span> <a style="color:var(--text-dim);cursor:pointer;font-size:12px;text-decoration:underline;font-weight:normal" onclick="filterClienteByYear(${ctx.selectedYear})">(limpiar filtro)</a>`;
    let html = `<h3 style="margin:14px 0 8px">📦 SubCategorías compradas${yrLabel}</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>SubCategoría</th><th class="num">Unidades</th><th class="num">% uds cliente</th><th class="num">Transacciones</th><th class="num">% trans. cliente</th><th></th>
        </tr></thead><tbody>`;
    subArr.forEach(s => {
        const pctQ = tot.q ? (s[3]*100/tot.q) : 0;
        const pctT = tot.t ? (s[4]*100/tot.t) : 0;
        html += `<tr>
            <td class="clickable" onclick="showClienteSubcatArticulos('${escAttr(ctx.name)}', '${escAttr(s[0])}')">${s[0]}</td>
            <td class="num">${fmtNum(s[3])}</td>
            <td class="num">${pctQ.toFixed(1)}%</td>
            <td class="num">${fmtNum(s[4])}</td>
            <td class="num">${pctT.toFixed(1)}%</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteSubcatArticulos('${escAttr(ctx.name)}', '${escAttr(s[0])}')">Ver artículos →</button></td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    wrap.innerHTML = html;
}'''
assert old_render_subs in html, "_cliRenderSubcats anchor not found"
html = html.replace(old_render_subs, new_render_subs)

# ============================================================
# showClienteSubcatArticulos modal
# ============================================================
old_csa = '''    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:14px">${cliente}</div></div>
            <div class="kpi"><div class="label">SubCategoría</div><div class="value" style="font-size:14px">${subcat}</div></div>
            <div class="kpi"><div class="label">Ventas</div><div class="value">${fmtMoney(tot.v)}</div></div>
            <div class="kpi"><div class="label">Profit</div><div class="value pos">${fmtMoney(tot.p)}</div><div class="sub">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}% margen</div></div>
            <div class="kpi"><div class="label">Cantidad / Trans.</div><div class="value">${fmtNum(tot.q)} / ${fmtNum(tot.t)}</div></div>
        </div>
        <h3 style="margin:14px 0 8px">🛒 Artículos comprados (${artArr.length}) — click para ver fechas</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>Código</th><th>Artículo</th><th>Marca</th>
            <th class="num">Ventas</th><th class="num">Profit</th><th class="num">Margen</th>
            <th class="num">Cantidad</th><th class="num">Trans.</th><th></th>
        </tr></thead><tbody>`;
    artArr.forEach(a => {
        const m = a.ventas ? (a.profit*100/a.ventas) : 0;
        body += `<tr>
            <td class="clickable" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">${a.codigo}</td>
            <td class="clickable truncate" title="${escAttr(a.articulo)}" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">${a.articulo}</td>
            <td>${a.marca}</td>
            <td class="num">${fmtMoney(a.ventas)}</td>
            <td class="num pos">${fmtMoney(a.profit)}</td>
            <td class="num">${m.toFixed(1)}%</td>
            <td class="num">${fmtNum(a.cantidad)}</td>
            <td class="num">${fmtNum(a.trans)}</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">Ver fechas →</button></td>
        </tr>`;
    });
    body += `<tr style="background:var(--bg-3); font-weight:bold"><td colspan="3">TOTAL</td><td class="num">${fmtMoney(tot.v)}</td><td class="num pos">${fmtMoney(tot.p)}</td><td class="num">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}%</td><td class="num">${fmtNum(tot.q)}</td><td class="num">${fmtNum(tot.t)}</td><td></td></tr>`;
    body += '</tbody></table></div>';'''

new_csa = '''    // Sort by qty
    artArr.sort((a,b)=>b.cantidad-a.cantidad);
    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:14px">${cliente}</div></div>
            <div class="kpi"><div class="label">SubCategoría</div><div class="value" style="font-size:14px">${subcat}</div></div>
            <div class="kpi"><div class="label">Unidades</div><div class="value">${fmtNum(tot.q)}</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">${tot.t?(tot.q/tot.t).toFixed(2):'0'} uds/trans.</div></div>
            <div class="kpi"><div class="label">Artículos distintos</div><div class="value">${artArr.length}</div></div>
        </div>
        <h3 style="margin:14px 0 8px">🛒 Artículos comprados (${artArr.length}) — click para ver fechas</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>Código</th><th>Artículo</th><th>Marca</th>
            <th class="num">Unidades</th><th class="num">Transacciones</th><th class="num">Uds / trans.</th><th></th>
        </tr></thead><tbody>`;
    artArr.forEach(a => {
        const udsT = a.trans ? (a.cantidad/a.trans) : 0;
        body += `<tr>
            <td class="clickable" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">${a.codigo}</td>
            <td class="clickable truncate" title="${escAttr(a.articulo)}" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">${a.articulo}</td>
            <td>${a.marca}</td>
            <td class="num">${fmtNum(a.cantidad)}</td>
            <td class="num">${fmtNum(a.trans)}</td>
            <td class="num">${udsT.toFixed(2)}</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteArticuloFechas('${escAttr(cliente)}', '${escAttr(a.codigo)}')">Ver fechas →</button></td>
        </tr>`;
    });
    body += `<tr style="background:var(--bg-3); font-weight:bold"><td colspan="3">TOTAL</td><td class="num">${fmtNum(tot.q)}</td><td class="num">${fmtNum(tot.t)}</td><td class="num">${tot.t?(tot.q/tot.t).toFixed(2):'0'}</td><td></td></tr>`;
    body += '</tbody></table></div>';'''
assert old_csa in html, "csa anchor not found"
html = html.replace(old_csa, new_csa)

# ============================================================
# showClienteArticuloFechas — detail with dates, no $
# ============================================================
old_fechas = '''    const tot = txns.reduce((a,t)=>{a.v+=t.ventas;a.p+=t.profit;a.q+=t.cantidad;a.t+=1;return a;}, {v:0,p:0,q:0,t:0});
    const precios = txns.map(t => t.cantidad>0 ? t.ventas/t.cantidad : 0).filter(p=>p>0);
    const precioMin = precios.length ? Math.min(...precios) : 0;
    const precioMax = precios.length ? Math.max(...precios) : 0;
    const precioProm = tot.q>0 ? tot.v/tot.q : 0;

    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:13px; line-height:1.3">${cliente}</div></div>
            <div class="kpi"><div class="label">Artículo</div><div class="value" style="font-size:11px; line-height:1.3">${meta.articulo||''}</div><div class="sub">[${codigo}] ${meta.marca||''}</div></div>
            <div class="kpi"><div class="label">Compras totales</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">${fmtNum(tot.q)} unidades</div></div>
            <div class="kpi"><div class="label">Facturado</div><div class="value">${fmtMoney(tot.v)}</div><div class="sub">${fmtMoney(tot.p)} profit (${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}%)</div></div>
            <div class="kpi"><div class="label">Precio unitario</div><div class="value">${fmtMoney(precioProm)}</div><div class="sub">min ${fmtMoney(precioMin)} · max ${fmtMoney(precioMax)}</div></div>
        </div>`;'''
new_fechas = '''    const tot = txns.reduce((a,t)=>{a.q+=t.cantidad;a.t+=1;return a;}, {q:0,t:0});
    const primerCompra = txns.length ? txns[txns.length-1].fecha : '-';
    const ultimaCompra = txns.length ? txns[0].fecha : '-';

    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:13px; line-height:1.3">${cliente}</div></div>
            <div class="kpi"><div class="label">Artículo</div><div class="value" style="font-size:11px; line-height:1.3">${meta.articulo||''}</div><div class="sub">[${codigo}] ${meta.marca||''}</div></div>
            <div class="kpi"><div class="label">Compras</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">${fmtNum(tot.q)} unidades totales</div></div>
            <div class="kpi"><div class="label">Primera compra</div><div class="value" style="font-size:13px">${primerCompra}</div></div>
            <div class="kpi"><div class="label">Última compra</div><div class="value" style="font-size:13px">${ultimaCompra}</div></div>
        </div>`;'''
assert old_fechas in html, "fechas anchor not found"
html = html.replace(old_fechas, new_fechas)

# Fechas table
old_fechas_tbl = '''    body += `<h3 style="margin:14px 0 8px">🧾 Detalle de transacciones (${txns.length}) — ordenadas por fecha (más reciente primero)</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>Fecha</th><th class="num">Cantidad</th><th class="num">Importe</th><th class="num">Precio unit.</th><th class="num">Profit</th><th class="num">Margen</th><th>Plataforma</th><th>Provincia</th><th>Vendedor</th>
        </tr></thead><tbody>`;
    txns.forEach(t => {
        const precioU = t.cantidad>0 ? t.ventas/t.cantidad : 0;
        const margen = t.ventas ? (t.profit*100/t.ventas) : 0;
        body += `<tr>
            <td>${t.fecha}</td>
            <td class="num">${fmtNum(t.cantidad)}</td>
            <td class="num">${fmtMoney(t.ventas)}</td>
            <td class="num">${fmtMoney(precioU)}</td>
            <td class="num ${t.profit>=0?'pos':'neg'}">${fmtMoney(t.profit)}</td>
            <td class="num">${margen.toFixed(1)}%</td>
            <td>${t.plataforma}</td>
            <td>${t.provincia}</td>
            <td>${t.vendedor}</td>
        </tr>`;
    });
    body += `<tr style="background:var(--bg-3); font-weight:bold">
        <td>TOTAL ${txns.length} compras</td>
        <td class="num">${fmtNum(tot.q)}</td>
        <td class="num">${fmtMoney(tot.v)}</td>
        <td class="num">${fmtMoney(precioProm)}</td>
        <td class="num pos">${fmtMoney(tot.p)}</td>
        <td class="num">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}%</td>
        <td colspan="3"></td>
    </tr></tbody></table></div>`;'''

new_fechas_tbl = '''    body += `<h3 style="margin:14px 0 8px">🧾 Detalle de transacciones (${txns.length}) — ordenadas por fecha (más reciente primero)</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>Fecha</th><th class="num">Unidades</th><th>Plataforma</th><th>Provincia</th><th>Vendedor</th>
        </tr></thead><tbody>`;
    txns.forEach(t => {
        body += `<tr>
            <td>${t.fecha}</td>
            <td class="num">${fmtNum(t.cantidad)}</td>
            <td>${t.plataforma}</td>
            <td>${t.provincia}</td>
            <td>${t.vendedor}</td>
        </tr>`;
    });
    body += `<tr style="background:var(--bg-3); font-weight:bold">
        <td>TOTAL ${txns.length} compras</td>
        <td class="num">${fmtNum(tot.q)}</td>
        <td colspan="3"></td>
    </tr></tbody></table></div>`;'''
assert old_fechas_tbl in html, "fechas tbl anchor not found"
html = html.replace(old_fechas_tbl, new_fechas_tbl)

# Drop the per-month charts helper in fechas modal (it referenced v)
html = html.replace(
    '''    // Per-month summary chart
    const byYM = new Map();
    txns.forEach(t => { let e = byYM.get(t.ym); if (!e) { e = {q:0, v:0, count:0}; byYM.set(t.ym, e);} e.q += t.cantidad; e.v += t.ventas; e.count += 1; });
    const ymArr = [...byYM.entries()].sort((a,b)=>a[0].localeCompare(b[0]));

    if (ymArr.length > 1) {
        body += `<h3 style="margin:14px 0 8px">📅 Compras agrupadas por mes</h3>
            <div class="chart-grid" style="grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:10px">
                <div class="chart-card"><div class="chart-container" style="height:200px"><canvas id="modalCliArtMesQty"></canvas></div></div>
                <div class="chart-card"><div class="chart-container" style="height:200px"><canvas id="modalCliArtMesVen"></canvas></div></div>
            </div>`;
    }''',
    '''    // Per-month qty chart only (no $)
    const byYM = new Map();
    txns.forEach(t => { let e = byYM.get(t.ym); if (!e) { e = {q:0, count:0}; byYM.set(t.ym, e);} e.q += t.cantidad; e.count += 1; });
    const ymArr = [...byYM.entries()].sort((a,b)=>a[0].localeCompare(b[0]));

    if (ymArr.length > 1) {
        body += `<h3 style="margin:14px 0 8px">📅 Compras agrupadas por mes</h3>
            <div class="chart-grid" style="grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:10px">
                <div class="chart-card"><div class="chart-container" style="height:200px"><canvas id="modalCliArtMesQty"></canvas></div></div>
                <div class="chart-card"><div class="chart-container" style="height:200px"><canvas id="modalCliArtMesVen"></canvas></div></div>
            </div>`;
    }'''
)
# And the chart renderer for modalCliArtMesVen — change to "Transacciones" instead of $
html = html.replace(
    '''            destroyChart('modalCliArtMesVen');
            charts['modalCliArtMesVen'] = new Chart(document.getElementById('modalCliArtMesVen'), {
                type:'bar',
                data:{ labels:ymArr.map(x=>x[0]), datasets:[{label:'Importe', data:ymArr.map(x=>x[1].v), backgroundColor:'#3b82f6'}]},
                options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>'Importe: '+fmtMoney(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtMoney(v)}, grid:{color:'#334155'}}}}
            });''',
    '''            destroyChart('modalCliArtMesVen');
            charts['modalCliArtMesVen'] = new Chart(document.getElementById('modalCliArtMesVen'), {
                type:'bar',
                data:{ labels:ymArr.map(x=>x[0]), datasets:[{label:'Transacciones', data:ymArr.map(x=>x[1].count), backgroundColor:'#3b82f6'}]},
                options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>'Transacciones: '+fmtNum(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtNum(v)}, grid:{color:'#334155'}}}}
            });'''
)

# ============================================================
# showSubcatDetail — subcat modal with $
# ============================================================
old_sub_modal = '''    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">SubCategoría</div><div class="value" style="font-size:14px">${name}</div></div>
            <div class="kpi"><div class="label">Ventas</div><div class="value">${fmtMoney(tot.v)}</div></div>
            <div class="kpi"><div class="label">Profit</div><div class="value pos">${fmtMoney(tot.p)}</div><div class="sub">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}% margen</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">Cant: ${fmtNum(tot.q)}</div></div>
            <div class="kpi"><div class="label">Clientes únicos</div><div class="value">${fmtNum(cliArr.length)}</div></div>
        </div>
        <h3 style="margin:14px 0 8px">👥 Top 100 Clientes</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>#</th><th>Cliente</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">% subcat</th><th class="num">Cant.</th><th class="num">Trans.</th>
        </tr></thead><tbody>`;
    top100.forEach((c,i) => {
        const pct = tot.v ? (c.v*100/tot.v) : 0;
        body += `<tr>
            <td>${i+1}</td>
            <td class="clickable" onclick="showClienteDetail('${escAttr(c.name)}', ${c.cliId||'null'})">${c.name}</td>
            <td class="num">${fmtMoney(c.v)}</td>
            <td class="num pos">${fmtMoney(c.p)}</td>
            <td class="num">${pct.toFixed(1)}%</td>
            <td class="num">${fmtNum(c.q)}</td>
            <td class="num">${fmtNum(c.t)}</td>
        </tr>`;
    });
    body += '</tbody></table></div>';'''

new_sub_modal = '''    // sort top100 by qty
    cliArr.sort((a,b)=>b.q-a.q);
    const top100q = cliArr.slice(0,100);
    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">SubCategoría</div><div class="value" style="font-size:14px">${name}</div></div>
            <div class="kpi"><div class="label">Unidades</div><div class="value">${fmtNum(tot.q)}</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">${tot.t?(tot.q/tot.t).toFixed(2):'0'} uds/trans.</div></div>
            <div class="kpi"><div class="label">Clientes únicos</div><div class="value">${fmtNum(cliArr.length)}</div></div>
        </div>
        <h3 style="margin:14px 0 8px">👥 ${cliArr.length<=top100q.length?(cliArr.length===1?'Cliente que compró':cliArr.length+' clientes que compraron'):'Top '+top100q.length+' de '+cliArr.length+' clientes'} (por unidades)</h3>
        <div class="table-wrap" style="max-height:500px"><table><thead><tr>
            <th>#</th><th>Cliente</th><th class="num">Unidades</th><th class="num">% uds subcat</th><th class="num">Transacciones</th><th>Vendedor reciente</th>
        </tr></thead><tbody>`;
    top100q.forEach((c,i) => {
        const pct = tot.q ? (c.q*100/tot.q) : 0;
        const vend = vendedorReciente(c.nameIdx != null ? c.nameIdx : NAME_TO_IDX.get(c.name), null);
        body += `<tr>
            <td>${i+1}</td>
            <td class="clickable" onclick="showClienteDetail('${escAttr(c.name)}', ${c.cliId||'null'})">${c.name}</td>
            <td class="num">${fmtNum(c.q)}</td>
            <td class="num">${pct.toFixed(1)}%</td>
            <td class="num">${fmtNum(c.t)}</td>
            <td style="color:var(--accent-2)">${vend||'-'}</td>
        </tr>`;
    });
    body += '</tbody></table></div>';'''
assert old_sub_modal in html, "sub modal anchor not found"
html = html.replace(old_sub_modal, new_sub_modal)

# ============================================================
# showArticuloDetail — articulo modal with $
# ============================================================
old_art_kpis = '''    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Código</div><div class="value" style="font-size:14px">${codigo}${sr&&ag?' <span class="sr-badge" style="background:'+colors[ag.old]+'">'+labels[ag.old]+'</span>':sr?' <span class="sr-badge">AGING</span>':''}</div></div>
            <div class="kpi"><div class="label">Artículo</div><div class="value" style="font-size:12px; line-height:1.3">${meta.articulo||''}</div><div class="sub">${meta.marca||''} · ${meta.subcat||''}</div></div>
            ${stockKPI}
            <div class="kpi"><div class="label">Ventas históricas</div><div class="value">${fmtMoney(tot.v)}</div></div>
            <div class="kpi"><div class="label">Profit</div><div class="value pos">${fmtMoney(tot.p)}</div><div class="sub">${tot.v?(tot.p*100/tot.v).toFixed(1):'0'}% margen</div></div>
            <div class="kpi"><div class="label">Cantidad / Trans.</div><div class="value">${fmtNum(tot.q)} / ${fmtNum(tot.t)}</div><div class="sub">Ticket: ${tot.t?fmtMoney(tot.v/tot.t):'$0'}</div></div>
        </div>`;'''
new_art_kpis = '''    let body = `
        <div class="kpis">
            <div class="kpi"><div class="label">Código</div><div class="value" style="font-size:14px">${codigo}${sr&&ag?' <span class="sr-badge" style="background:'+colors[ag.old]+'">'+labels[ag.old]+'</span>':sr?' <span class="sr-badge">AGING</span>':''}</div></div>
            <div class="kpi"><div class="label">Artículo</div><div class="value" style="font-size:12px; line-height:1.3">${meta.articulo||''}</div><div class="sub">${meta.marca||''} · ${meta.subcat||''}</div></div>
            ${stockKPI}
            <div class="kpi"><div class="label">Unidades vendidas</div><div class="value">${fmtNum(tot.q)}</div></div>
            <div class="kpi"><div class="label">Transacciones</div><div class="value">${fmtNum(tot.t)}</div><div class="sub">${tot.t?(tot.q/tot.t).toFixed(2):'0'} uds/trans.</div></div>
            <div class="kpi"><div class="label">Clientes únicos</div><div class="value">${fmtNum(cliArr.length)}</div></div>
        </div>`;'''
assert old_art_kpis in html, "art kpis anchor not found"
html = html.replace(old_art_kpis, new_art_kpis)

# Articulo detail — "Últimos 10 que compraron" — remove Ventas col
html = html.replace(
    '''        body += `<h3 style="margin:14px 0 8px">📞 Últimos 10 clientes que compraron — para ofrecer</h3>
        <div class="table-wrap" style="max-height:340px"><table><thead><tr>
            <th>#</th><th>Cliente</th><th>Vendedor reciente</th><th>Última compra</th><th class="num">Días atrás</th>
            <th class="num">Cant. total</th><th class="num">Ventas</th><th class="num">Veces que compró</th>
            <th>Última plataforma</th><th>Provincia</th>
        </tr></thead><tbody>`;
        const today = Math.floor((Date.now() - EPOCH_MS) / 86400000);
        last10.forEach((c,i) => {
            const dias = today - c.days;
            const vend = vendedorReciente(c.nameIdx != null ? c.nameIdx : (NAME_TO_IDX ? NAME_TO_IDX.get(c.cliente) : null), null);
            body += `<tr>
                <td>${i+1}</td>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c.cliente)}', ${c.cliId||'null'})">${c.cliente}</td>
                <td style="color:var(--accent-2)">${vend||'-'}</td>
                <td>${c.ultima}</td>
                <td class="num">${fmtNum(dias)}</td>
                <td class="num">${fmtNum(c.cantTotal)}</td>
                <td class="num">${fmtMoney(c.vTotal)}</td>
                <td class="num">${fmtNum(c.vecesCompro)}</td>
                <td>${c.plat}</td>
                <td>${c.prov}</td>
            </tr>`;
        });''',
    '''        body += `<h3 style="margin:14px 0 8px">📞 ${last10.length===lastBuyArr.length?last10.length+' clientes':'Últimos '+last10.length+' de '+lastBuyArr.length} que compraron — para ofrecer</h3>
        <div class="table-wrap" style="max-height:340px"><table><thead><tr>
            <th>#</th><th>Cliente</th><th>Vendedor reciente</th><th>Última compra</th><th class="num">Días atrás</th>
            <th class="num">Cant. total</th><th class="num">Veces que compró</th>
            <th>Última plataforma</th><th>Provincia</th>
        </tr></thead><tbody>`;
        const today = Math.floor((Date.now() - EPOCH_MS) / 86400000);
        last10.forEach((c,i) => {
            const dias = today - c.days;
            const nIdx = NAME_TO_IDX.get(c.cliente);
            const vend = vendedorReciente(nIdx, null);
            body += `<tr>
                <td>${i+1}</td>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c.cliente)}', ${c.cliId||'null'})">${c.cliente}</td>
                <td style="color:var(--accent-2)">${vend||'-'}</td>
                <td>${c.ultima}</td>
                <td class="num">${fmtNum(dias)}</td>
                <td class="num">${fmtNum(c.cantTotal)}</td>
                <td class="num">${fmtNum(c.vecesCompro)}</td>
                <td>${c.plat}</td>
                <td>${c.prov}</td>
            </tr>`;
        });'''
)

# Articulo yearly (same pattern)
old_art_yr = '''    if (yrArr.length) {
        body += `<h3 style="margin:14px 0 8px">📅 Evolución por Año</h3>
            <div class="chart-grid" style="grid-template-columns: 2fr 1fr; gap:12px; margin-bottom:10px">
                <div class="chart-card"><div class="chart-container" style="height:220px"><canvas id="modalArtYearChart"></canvas></div></div>
                <div class="chart-card"><div class="chart-container" style="height:220px"><canvas id="modalArtYearQty"></canvas></div></div>
            </div>
            <div class="table-wrap" style="max-height:220px; margin-bottom:10px"><table><thead><tr>
                <th>Año</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">Margen</th><th class="num">Cantidad</th><th class="num">Trans.</th>
            </tr></thead><tbody>`;
        yrArr.forEach(([y,e]) => {
            const m = e.v ? (e.p*100/e.v) : 0;
            body += `<tr><td>${y}</td><td class="num">${fmtMoney(e.v)}</td><td class="num pos">${fmtMoney(e.p)}</td><td class="num">${m.toFixed(1)}%</td><td class="num">${fmtNum(e.q)}</td><td class="num">${fmtNum(e.t)}</td></tr>`;
        });
        body += '</tbody></table></div>';
    }'''
new_art_yr = '''    if (yrArr.length) {
        body += `<h3 style="margin:14px 0 8px">📅 Evolución por Año</h3>
            <div class="chart-grid" style="grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:10px">
                <div class="chart-card"><div class="chart-container" style="height:220px"><canvas id="modalArtYearQty"></canvas></div></div>
                <div class="chart-card"><div class="chart-container" style="height:220px"><canvas id="modalArtYearTrans"></canvas></div></div>
            </div>
            <div class="table-wrap" style="max-height:220px; margin-bottom:10px"><table><thead><tr>
                <th>Año</th><th class="num">Unidades</th><th class="num">Transacciones</th><th class="num">Uds / trans.</th>
            </tr></thead><tbody>`;
        yrArr.forEach(([y,e]) => {
            const udsT = e.t ? (e.q/e.t) : 0;
            body += `<tr><td>${y}</td><td class="num">${fmtNum(e.q)}</td><td class="num">${fmtNum(e.t)}</td><td class="num">${udsT.toFixed(2)}</td></tr>`;
        });
        body += '</tbody></table></div>';
    }'''
assert old_art_yr in html, "art yr anchor not found"
html = html.replace(old_art_yr, new_art_yr)

# Articulo top clients
old_art_cli = '''    // Map cliKey -> lastDays para poder mostrar "Última compra" en la tabla de Top clientes
    const lastDaysByKey = new Map();
    lastBuy.forEach((e, key) => { lastDaysByKey.set(key, e.lastDays); });
    if (topCli.length) {
        body += `<h3 style="margin:14px 0 8px">👥 Top 20 Clientes que más compraron</h3>
            <div class="table-wrap" style="max-height:420px"><table><thead><tr>
                <th>#</th><th>Cliente</th><th>Vendedor reciente</th><th>Última compra</th><th class="num">Días atrás</th><th class="num">Ventas</th><th class="num">Profit</th><th class="num">% del artículo</th><th class="num">Cantidad</th><th class="num">Trans.</th>
            </tr></thead><tbody>`;
        const todayDays = Math.floor((Date.now() - EPOCH_MS) / 86400000);
        topCli.forEach((c,i) => {
            const pct = tot.v ? (c[1]*100/tot.v) : 0;
            const vend = vendedorReciente(c[5], null);
            const key = c[6] > 0 ? c[6] : (-c[5] - 1000000);
            const lastDays = lastDaysByKey.get(key);
            const ultima = (lastDays != null && lastDays >= 0) ? fmtDate(lastDays) : '-';
            const dias = (lastDays != null && lastDays >= 0) ? (todayDays - lastDays) : null;
            const diasColor = dias == null ? 'var(--text-dim)' : (dias <= 180 ? 'var(--good)' : (dias <= 730 ? 'var(--warn)' : 'var(--bad)'));
            body += `<tr>
                <td>${i+1}</td>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c[0])}', ${c[6]||'null'})">${c[0]||'(sin dato)'}</td>
                <td style="color:var(--accent-2)">${vend||'-'}</td>
                <td>${ultima}</td>
                <td class="num" style="color:${diasColor}; font-weight:600">${dias != null ? fmtNum(dias) : '-'}</td>
                <td class="num">${fmtMoney(c[1])}</td>
                <td class="num pos">${fmtMoney(c[2])}</td>
                <td class="num">${pct.toFixed(1)}%</td>
                <td class="num">${fmtNum(c[3])}</td>
                <td class="num">${fmtNum(c[4])}</td>
            </tr>`;
        });
        body += '</tbody></table></div>';
    }'''
new_art_cli = '''    // sort top clients by qty
    cliArr.sort((a,b)=>b[3]-a[3]);
    const topCliQ = cliArr.slice(0,20);
    // Map cliKey -> lastDays para "Última compra"
    const lastDaysByKey = new Map();
    lastBuy.forEach((e, key) => { lastDaysByKey.set(key, e.lastDays); });
    if (topCliQ.length) {
        const titleTop = cliArr.length <= topCliQ.length
            ? `👥 ${cliArr.length===1?'Cliente que':cliArr.length+' clientes que'} compraron (por unidades)`
            : `👥 Top ${topCliQ.length} de ${cliArr.length} clientes (por unidades)`;
        body += `<h3 style="margin:14px 0 8px">${titleTop}</h3>
            <div class="table-wrap" style="max-height:420px"><table><thead><tr>
                <th>#</th><th>Cliente</th><th class="num">Unidades</th><th class="num">% uds artículo</th><th class="num">Transacciones</th><th>Vendedor reciente</th><th>Última compra</th><th class="num">Días atrás</th>
            </tr></thead><tbody>`;
        const todayDays = Math.floor((Date.now() - EPOCH_MS) / 86400000);
        topCliQ.forEach((c,i) => {
            const pct = tot.q ? (c[3]*100/tot.q) : 0;
            const vend = vendedorReciente(c[5], null);
            const key = c[6] > 0 ? c[6] : (-c[5] - 1000000);
            const lastDays = lastDaysByKey.get(key);
            const ultima = (lastDays != null && lastDays >= 0) ? fmtDate(lastDays) : '-';
            const dias = (lastDays != null && lastDays >= 0) ? (todayDays - lastDays) : null;
            const diasColor = dias == null ? 'var(--text-dim)' : (dias <= 180 ? 'var(--good)' : (dias <= 730 ? 'var(--warn)' : 'var(--bad)'));
            body += `<tr>
                <td>${i+1}</td>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c[0])}', ${c[6]||'null'})">${c[0]||'(sin dato)'}</td>
                <td class="num">${fmtNum(c[3])}</td>
                <td class="num">${pct.toFixed(1)}%</td>
                <td class="num">${fmtNum(c[4])}</td>
                <td style="color:var(--accent-2)">${vend||'-'}</td>
                <td>${ultima}</td>
                <td class="num" style="color:${diasColor}; font-weight:600">${dias != null ? fmtNum(dias) : '-'}</td>
            </tr>`;
        });
        body += '</tbody></table></div>';
    }'''
assert old_art_cli in html, "art cli anchor not found"
html = html.replace(old_art_cli, new_art_cli)

# Articulo year charts (no $)
old_art_ycharts = '''    const afterRender = () => {
        if (yrArr.length && document.getElementById('modalArtYearChart')) {
            destroyChart('modalArtYearChart');
            charts['modalArtYearChart'] = new Chart(document.getElementById('modalArtYearChart'), {
                type:'bar',
                data:{ labels:yrArr.map(y=>y[0]), datasets:[
                    {label:'Ventas', data:yrArr.map(y=>y[1].v), backgroundColor:'#3b82f6'},
                    {label:'Profit', data:yrArr.map(y=>y[1].p), backgroundColor:'#10b981'}]},
                options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmtMoney(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtMoney(v)}, grid:{color:'#334155'}}}}
            });
            destroyChart('modalArtYearQty');
            charts['modalArtYearQty'] = new Chart(document.getElementById('modalArtYearQty'), {
                type:'bar',
                data:{ labels:yrArr.map(y=>y[0]), datasets:[{label:'Cantidad', data:yrArr.map(y=>y[1].q), backgroundColor:'#f59e0b'}]},
                options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>'Cantidad: '+fmtNum(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtNum(v)}, grid:{color:'#334155'}}}}
            });
        }
    };'''
new_art_ycharts = '''    const afterRender = () => {
        if (yrArr.length) {
            if (document.getElementById('modalArtYearQty')) {
                destroyChart('modalArtYearQty');
                charts['modalArtYearQty'] = new Chart(document.getElementById('modalArtYearQty'), {
                    type:'bar',
                    data:{ labels:yrArr.map(y=>y[0]), datasets:[{label:'Unidades', data:yrArr.map(y=>y[1].q), backgroundColor:'#06b6d4'}]},
                    options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>'Unidades: '+fmtNum(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtNum(v)}, grid:{color:'#334155'}}}}
                });
            }
            if (document.getElementById('modalArtYearTrans')) {
                destroyChart('modalArtYearTrans');
                charts['modalArtYearTrans'] = new Chart(document.getElementById('modalArtYearTrans'), {
                    type:'bar',
                    data:{ labels:yrArr.map(y=>y[0]), datasets:[{label:'Transacciones', data:yrArr.map(y=>y[1].t), backgroundColor:'#8b5cf6'}]},
                    options:{maintainAspectRatio:false, plugins:{legend:{labels:{color:'#cbd5e1'}}, tooltip:{callbacks:{label:c=>'Transacciones: '+fmtNum(c.raw)}}}, scales:{x:{ticks:{color:'#94a3b8'}, grid:{color:'#334155'}}, y:{ticks:{color:'#94a3b8', callback:v=>fmtNum(v)}, grid:{color:'#334155'}}}}
                });
            }
        }
    };'''
assert old_art_ycharts in html, "art ycharts anchor not found"
html = html.replace(old_art_ycharts, new_art_ycharts)

# ============================================================
# Cruce Cliente x Sub — remove $ columns
# ============================================================
old_cruce_cli = '''        let html = '<div class="table-wrap"><table><thead><tr><th>Cliente</th><th class="num">Ventas</th><th class="num">Profit</th><th>Top 1</th><th>Top 2</th><th>Top 3</th></tr></thead><tbody>';
        top.forEach(c => {
            const idxs = rowsForCliente(c.nIdx, c.id);
            const sm = aggOnIndexes(idxs, C.sub);
            const sa = [...sm.entries()].map(([k,e])=>[LK.subcat[k]||'(sin dato)', e.v]).sort((a,b)=>b[1]-a[1]);
            html += `<tr>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c.name)}', ${c.id})">${c.name}</td>
                <td class="num">${fmtMoney(c.v)}</td><td class="num pos">${fmtMoney(c.p)}</td>
                <td>${sa[0]?sa[0][0]:'-'}</td><td>${sa[1]?sa[1][0]:'-'}</td><td>${sa[2]?sa[2][0]:'-'}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';'''
new_cruce_cli = '''        let html = '<div class="table-wrap"><table><thead><tr><th>Cliente</th><th class="num">Unidades</th><th class="num">Trans.</th><th>Vendedor reciente</th><th>Top 1 SubCat</th><th>Top 2</th><th>Top 3</th></tr></thead><tbody>';
        // Re-sort by qty
        rows.sort((a,b)=>b.q-a.q);
        const topQ = rows.slice(0,30);
        topQ.forEach(c => {
            const idxs = rowsForCliente(c.nIdx, c.id);
            const sm = aggOnIndexes(idxs, C.sub);
            const sa = [...sm.entries()].map(([k,e])=>[LK.subcat[k]||'(sin dato)', e.q]).sort((a,b)=>b[1]-a[1]);
            const vend = vendedorReciente(c.nIdx, null);
            html += `<tr>
                <td class="clickable" onclick="showClienteDetail('${escAttr(c.name)}', ${c.id})">${c.name}</td>
                <td class="num">${fmtNum(c.q)}</td><td class="num">${fmtNum(c.t)}</td>
                <td style="color:var(--accent-2)">${vend||'-'}</td>
                <td>${sa[0]?sa[0][0]:'-'}</td><td>${sa[1]?sa[1][0]:'-'}</td><td>${sa[2]?sa[2][0]:'-'}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';'''
assert old_cruce_cli in html, "cruce cli anchor not found"
html = html.replace(old_cruce_cli, new_cruce_cli)

# Need to expose q,t on rows in cruce - find renderCruce and fix rows push
html = html.replace(
    '''        cliMap.forEach((e,id) => {
            const name = LK.clienteName[e.nIdx] || '';
            if (!name.toLowerCase().includes(q)) return;
            rows.push({ id, name, v:e.v, p:e.p, nIdx:e.nIdx });
        });''',
    '''        cliMap.forEach((e,id) => {
            const name = LK.clienteName[e.nIdx] || '';
            if (!name.toLowerCase().includes(q)) return;
            rows.push({ id, name, v:e.v, p:e.p, q:e.q, t:e.t, nIdx:e.nIdx });
        });'''
)

old_cruce_sub = '''        top.forEach(s => {
            const idxs = rowsForSubcat(s.kIdx);
            const cm = aggByClienteEffective(idxs);
            const ca = [...cm.values()].map(e => [LK.clienteName[e.nameIdx]||'(sin dato)', e.v]).sort((a,b)=>b[1]-a[1]);
            html += `<tr>
                <td class="clickable" onclick="showSubcatDetail('${escAttr(s.name)}')">${s.name}</td>
                <td class="num">${fmtMoney(s.v)}</td><td class="num pos">${fmtMoney(s.p)}</td>
                <td>${ca[0]?ca[0][0]:'-'}</td><td>${ca[1]?ca[1][0]:'-'}</td><td>${ca[2]?ca[2][0]:'-'}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';'''
new_cruce_sub = '''        rows.sort((a,b)=>b.q-a.q);
        const topQ = rows.slice(0,30);
        topQ.forEach(s => {
            const idxs = rowsForSubcat(s.kIdx);
            const cm = aggByClienteEffective(idxs);
            const ca = [...cm.values()].map(e => [LK.clienteName[e.nameIdx]||'(sin dato)', e.q]).sort((a,b)=>b[1]-a[1]);
            html += `<tr>
                <td class="clickable" onclick="showSubcatDetail('${escAttr(s.name)}')">${s.name}</td>
                <td class="num">${fmtNum(s.q)}</td><td class="num">${fmtNum(s.t)}</td>
                <td>${ca[0]?ca[0][0]:'-'}</td><td>${ca[1]?ca[1][0]:'-'}</td><td>${ca[2]?ca[2][0]:'-'}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';'''
assert old_cruce_sub in html, "cruce sub anchor not found"
html = html.replace(old_cruce_sub, new_cruce_sub)

# Expose q,t on sub rows
html = html.replace(
    '''        subMap.forEach((e,k) => {
            const name = LK.subcat[k] || '';
            if (!name.toLowerCase().includes(q)) return;
            rows.push({ name, v:e.v, p:e.p, kIdx:k });
        });''',
    '''        subMap.forEach((e,k) => {
            const name = LK.subcat[k] || '';
            if (!name.toLowerCase().includes(q)) return;
            rows.push({ name, v:e.v, p:e.p, q:e.q, t:e.t, kIdx:k });
        });'''
)

# ============================================================
# Sin Rotación - Clientes Oportunidad: change cols ventas → trans/cant
# ============================================================
old_oport_rows_push = '''        rows.push({
            cliente: name, nIdx,
            vendedor: idx.nameToVendedor.get(nIdx) || '(sin asignar)',
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units, ventas: e.ventas, profit: e.profit,
            ultima: fmtDate(e.lastDays), dias, ventasTotales: idx.nameToTotal.get(nIdx)||0,
            count: e.count
        });'''
new_oport_rows_push = '''        rows.push({
            cliente: name, nIdx,
            vendedor: vendedorReciente(nIdx, idx.nameToVendedor.get(nIdx)) || '(sin asignar)',
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units,
            ultima: fmtDate(e.lastDays), dias,
            count: e.count,
            transTotales: idx.nameToTransTotales.get(nIdx) || 0
        });'''
assert old_oport_rows_push in html, "oport rows push anchor not found"
html = html.replace(old_oport_rows_push, new_oport_rows_push)

# Replace oport table headers/rows
old_oport_tbl = '''    let html = `<table><thead><tr>
        <th onclick="sortSR('sropor','cliente')">Cliente</th>
        <th onclick="sortSR('sropor','vendedor')">Vendedor</th>
        <th onclick="sortSR('sropor','provincia')">Provincia</th>
        <th class="num" onclick="sortSR('sropor','srArticulos')">Art. en aging</th>
        <th class="num" onclick="sortSR('sropor','units')">Cant. histórica</th>
        <th class="num" onclick="sortSR('sropor','ventas')">Ventas (de art. en aging)</th>
        <th class="num" onclick="sortSR('sropor','ventasTotales')">Ventas totales</th>
        <th onclick="sortSR('sropor','ultima')">Última compra (aging)</th>
        <th class="num" onclick="sortSR('sropor','dias')">Días</th>
        <th></th>
    </tr></thead><tbody>`;
    rows.slice(0, 500).forEach(r => {
        // Status badge
        let badgeColor = '#94a3b8';
        if (r.dias <= 90) badgeColor = '#10b981';
        else if (r.dias <= 365) badgeColor = '#f59e0b';
        else badgeColor = '#94a3b8';
        const vendStyle = r.vendedor === '(sin asignar)' || r.vendedor === '-- SIN ASIGNAR --' ? 'color:var(--text-dim); font-style:italic' : '';
        html += `<tr>
            <td class="clickable" onclick="showClienteDetail('${escAttr(r.cliente)}', null)">${r.cliente}</td>
            <td style="${vendStyle}">${r.vendedor}</td>
            <td>${r.provincia}</td>
            <td class="num" style="font-weight:600">${fmtNum(r.srArticulos)}</td>
            <td class="num">${fmtNum(r.units)}</td>
            <td class="num">${fmtMoney(r.ventas)}</td>
            <td class="num">${fmtMoney(r.ventasTotales)}</td>
            <td>${r.ultima}</td>
            <td class="num" style="color:${badgeColor}; font-weight:600">${fmtNum(r.dias)}</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteSinRot('${escAttr(r.cliente)}')">Ver para ofrecer →</button></td>
        </tr>`;
    });'''

new_oport_tbl = '''    let html = `<table><thead><tr>
        <th onclick="sortSR('sropor','cliente')">Cliente</th>
        <th onclick="sortSR('sropor','vendedor')">Vendedor reciente</th>
        <th onclick="sortSR('sropor','provincia')">Provincia</th>
        <th class="num" onclick="sortSR('sropor','srArticulos')">Art. en aging</th>
        <th class="num" onclick="sortSR('sropor','units')">Uds. histórica</th>
        <th class="num" onclick="sortSR('sropor','count')">Compras de aging</th>
        <th class="num" onclick="sortSR('sropor','transTotales')">Compras totales</th>
        <th onclick="sortSR('sropor','ultima')">Última compra (aging)</th>
        <th class="num" onclick="sortSR('sropor','dias')">Días</th>
        <th></th>
    </tr></thead><tbody>`;
    rows.slice(0, 500).forEach(r => {
        let badgeColor = '#94a3b8';
        if (r.dias <= 90) badgeColor = '#10b981';
        else if (r.dias <= 365) badgeColor = '#f59e0b';
        const vendStyle = r.vendedor === '(sin asignar)' || r.vendedor === '-- SIN ASIGNAR --' ? 'color:var(--text-dim); font-style:italic' : 'color:var(--accent-2)';
        html += `<tr>
            <td class="clickable" onclick="showClienteDetail('${escAttr(r.cliente)}', null)">${r.cliente}</td>
            <td style="${vendStyle}">${r.vendedor}</td>
            <td>${r.provincia}</td>
            <td class="num" style="font-weight:600">${fmtNum(r.srArticulos)}</td>
            <td class="num">${fmtNum(r.units)}</td>
            <td class="num">${fmtNum(r.count)}</td>
            <td class="num">${fmtNum(r.transTotales)}</td>
            <td>${r.ultima}</td>
            <td class="num" style="color:${badgeColor}; font-weight:600">${fmtNum(r.dias)}</td>
            <td><button class="btn" style="padding:3px 8px;font-size:10px" onclick="showClienteSinRot('${escAttr(r.cliente)}')">Ver para ofrecer →</button></td>
        </tr>`;
    });'''
assert old_oport_tbl in html, "oport tbl anchor not found"
html = html.replace(old_oport_tbl, new_oport_tbl)

# Top ranking for oportunidad: change the "top N clientes" filter to be by transactions instead of ventas
html = html.replace(
    '''        <option value="100">Top 100 clientes (por ventas históricas)</option>
          <option value="500" selected>Top 500</option>
          <option value="1000">Top 1.000</option>
          <option value="0">Todos los clientes</option>''',
    '''        <option value="100">Top 100 clientes (por transacciones históricas)</option>
          <option value="500" selected>Top 500</option>
          <option value="1000">Top 1.000</option>
          <option value="0">Todos los clientes</option>'''
)

# Add a "Vendedor" filter dropdown right after oportRecency
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

# Filter rows by the vendedor reciente in the forEach
html = html.replace(
    '''        rows.push({
            cliente: name, nIdx,
            vendedor: vendedorReciente(nIdx, idx.nameToVendedor.get(nIdx)) || '(sin asignar)',
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units,
            ultima: fmtDate(e.lastDays), dias,
            count: e.count,
            transTotales: idx.nameToTransTotales.get(nIdx) || 0
        });''',
    '''        const vendRec = vendedorReciente(nIdx, idx.nameToVendedor.get(nIdx)) || '(sin asignar)';
        if (vendFiltro && vendRec !== vendFiltro) return;
        rows.push({
            cliente: name, nIdx,
            vendedor: vendRec,
            provincia: idx.nameToProvincia.get(nIdx) || '',
            srArticulos: e.codigos.size, units: e.units,
            ultima: fmtDate(e.lastDays), dias,
            count: e.count,
            transTotales: idx.nameToTransTotales.get(nIdx) || 0
        });'''
)

# Populate the vendor dropdown from the universe of possible "Vendedor reciente" values
# Also hook up a 'change' listener
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
                const v = vendedorReciente(nIdx, idx.nameToVendedor.get(nIdx));
                vends.add(v || '(sin asignar)');
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

# Update buildSRIndexes to also compute nameToTransTotales (total transactions per client)
html = html.replace(
    '''    // Build cliente totales históricos (todas sus ventas) para ranking de "top cliente"
    const cliTotal = aggregateCli();  // map cliId -> {v,p,q,t,nIdx}
    // Map cliNameIdx -> total ventas
    const nameToTotal = new Map();
    cliTotal.forEach((e, id) => {
        const cur = nameToTotal.get(e.nIdx) || 0;
        nameToTotal.set(e.nIdx, cur + e.v);
    });''',
    '''    // Build cliente totales históricos para ranking de "top cliente" (ahora por transacciones, sin $)
    const cliTotal = aggregateCli();
    const nameToTotal = new Map();
    const nameToTransTotales = new Map();
    cliTotal.forEach((e, id) => {
        nameToTotal.set(e.nIdx, (nameToTotal.get(e.nIdx)||0) + e.t);
        nameToTransTotales.set(e.nIdx, (nameToTransTotales.get(e.nIdx)||0) + e.t);
    });'''
)
# Expose nameToTransTotales in STATE.srIdx
html = html.replace(
    '''    STATE.srIdx = {
        pmMap, subcatMap, marcaMap, cliMap, nameToTotal, srCodIdxSet,
        nameToVendedor, nameToProvincia, nameToClase
    };''',
    '''    STATE.srIdx = {
        pmMap, subcatMap, marcaMap, cliMap, nameToTotal, nameToTransTotales, srCodIdxSet,
        nameToVendedor, nameToProvincia, nameToClase
    };'''
)

# ============================================================
# showClienteSinRot — remove $ KPIs
# ============================================================
old_cli_sr_kpi = '''    // Vendedor/provincia/clase: tomar el primero que se encuentre entre las variantes
    let vendedor = '(sin asignar)', provincia = '', clase = '';
    for (const ni of allNameIdxs) {
        if (vendedor === '(sin asignar)' && idx.nameToVendedor.get(ni)) vendedor = idx.nameToVendedor.get(ni);
        if (!provincia && idx.nameToProvincia.get(ni)) provincia = idx.nameToProvincia.get(ni);
        if (!clase && idx.nameToClase.get(ni)) clase = idx.nameToClase.get(ni);
    }

    // Estado para los botones de exportar (Excel/PDF)
    window._cliSROptCtx = { cliente, vendedor, provincia, clase,
        totalVentas, totalSR, totalV, totalCompras: arts.reduce((a,x)=>a+x.count,0),
        arts, hasPrices: true };

    let body = `
        <div style="background:linear-gradient(90deg, rgba(239,68,68,.15), rgba(245,158,11,.10)); border:1px solid var(--warn); border-radius:10px; padding:14px; margin-bottom:14px">
            <div style="font-size:13px; font-weight:600; color:var(--warn); margin-bottom:6px">🎯 OPORTUNIDAD DE RE-VENTA</div>
            <div style="font-size:13px">Este cliente compró históricamente <strong>${arts.length}</strong> productos diferentes que hoy tienen stock en aging. Hablale para ofrecerle el Aging.</div>
            <div style="font-size:12px; margin-top:8px; padding-top:8px; border-top:1px solid rgba(245,158,11,.3)"><strong>📞 Vendedor asignado:</strong> <span style="color:${vendedor==='(sin asignar)'||vendedor==='-- SIN ASIGNAR --'?'var(--bad)':'var(--accent-2)'}; font-weight:600">${vendedor}</span> · ${provincia} · ${clase}</div>
        </div>
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:13px; line-height:1.3">${cliente}</div><div class="sub">${provincia}</div></div>
            <div class="kpi"><div class="label">Vendedor</div><div class="value" style="font-size:13px">${vendedor}</div><div class="sub">${clase}</div></div>
            <div class="kpi"><div class="label">Ventas totales</div><div class="value">${fmtMoney(totalVentas)}</div></div>
            <div class="kpi" style="border-color:var(--warn)"><div class="label" style="color:var(--warn)">Art. en aging que compró</div><div class="value">${fmtNum(arts.length)}</div></div>
            <div class="kpi"><div class="label">Uds. en aging comprada</div><div class="value">${fmtNum(totalSR)}</div></div>
            <div class="kpi"><div class="label">Facturado en aging</div><div class="value">${fmtMoney(totalV)}</div></div>
        </div>'''

new_cli_sr_kpi = '''    const totalCompras = arts.reduce((a,x)=>a+x.count, 0);

    // Vendedor reciente: probar todas las variantes de nombre del cliente
    let vendAsig = '(sin asignar)', provincia = '', clase = '';
    for (const ni of allNameIdxs) {
        if (vendAsig === '(sin asignar)' && idx.nameToVendedor.get(ni)) vendAsig = idx.nameToVendedor.get(ni);
        if (!provincia && idx.nameToProvincia.get(ni)) provincia = idx.nameToProvincia.get(ni);
        if (!clase && idx.nameToClase.get(ni)) clase = idx.nameToClase.get(ni);
    }
    let vendedor = null;
    for (const ni of allNameIdxs) {
        const v = vendedorReciente(ni, null);
        if (v) { vendedor = v; break; }
    }
    if (!vendedor) vendedor = vendAsig;

    // Estado para los botones de exportar (Excel/PDF) — versión Vendedores: sin precios
    window._cliSROptCtx = { cliente, vendedor, provincia, clase,
        totalSR, totalCompras, arts, hasPrices: false };

    let body = `
        <div style="background:linear-gradient(90deg, rgba(239,68,68,.15), rgba(245,158,11,.10)); border:1px solid var(--warn); border-radius:10px; padding:14px; margin-bottom:14px">
            <div style="font-size:13px; font-weight:600; color:var(--warn); margin-bottom:6px">🎯 OPORTUNIDAD DE RE-VENTA</div>
            <div style="font-size:13px">Este cliente compró históricamente <strong>${arts.length}</strong> productos diferentes que hoy tienen stock en aging. Hablale para ofrecerle el Aging.</div>
            <div style="font-size:12px; margin-top:8px; padding-top:8px; border-top:1px solid rgba(245,158,11,.3)"><strong>📞 Vendedor reciente (últimos 3 meses):</strong> <span style="color:${vendedor==='(sin asignar)'||vendedor==='-- SIN ASIGNAR --'||!vendedor?'var(--bad)':'var(--accent-2)'}; font-weight:600">${vendedor||'(sin actividad reciente)'}</span> · ${provincia} · ${clase}</div>
        </div>
        <div class="kpis">
            <div class="kpi"><div class="label">Cliente</div><div class="value" style="font-size:13px; line-height:1.3">${cliente}</div><div class="sub">${provincia}</div></div>
            <div class="kpi"><div class="label">Vendedor reciente</div><div class="value" style="font-size:13px; color:var(--accent-2)">${vendedor||'-'}</div><div class="sub">${clase}</div></div>
            <div class="kpi" style="border-color:var(--warn)"><div class="label" style="color:var(--warn)">Art. en aging que compró</div><div class="value">${fmtNum(arts.length)}</div></div>
            <div class="kpi"><div class="label">Uds. SR compradas</div><div class="value">${fmtNum(totalSR)}</div></div>
            <div class="kpi"><div class="label">Compras en aging</div><div class="value">${fmtNum(totalCompras)}</div></div>
        </div>'''
assert old_cli_sr_kpi in html, "cli sr kpi anchor not found"
html = html.replace(old_cli_sr_kpi, new_cli_sr_kpi)

# Drop v,p from perCod aggregate (not needed) — keeping as is, just not displayed
# Remove the $ column in showClienteSinRot's table (it didn't have one actually, let me re-check)
# Looking at original, it was: Código, Artículo, Marca, SubCat, Stock SR, Última compra, Días atrás, Cant histórica, Veces compró
# No $ cols. Good.

# ============================================================
# Remove cliente min filter — "ventas" in the clientes table's "cliMin"
# Already handled above ✓
# ============================================================

# ============================================================
# Remove CSV export oport $ fields
# ============================================================
html = html.replace(
    '''        data = (STATE.lastSROport||[]).map(r => ({cliente:r.cliente, vendedor:r.vendedor, provincia:r.provincia, articulos_SR_comprados:r.srArticulos, cantidad_historica:r.units, ventas_de_SR:Math.round(r.ventas), ventas_totales:Math.round(r.ventasTotales), ultima_compra_SR:r.ultima, dias_atras:r.dias}));''',
    '''        data = (STATE.lastSROport||[]).map(r => ({cliente:r.cliente, vendedor_reciente:r.vendedor, provincia:r.provincia, articulos_SR_comprados:r.srArticulos, unidades_historicas:r.units, compras_de_SR:r.count, compras_totales:r.transTotales, ultima_compra_SR:r.ultima, dias_atras:r.dias}));'''
)

# ============================================================
# Universal DOM sort — auto-attach a sort handler to every <table>
# in the document (including modals). Skips tables that already have
# onclick on their th (those use the existing data-array sort).
# ============================================================
universal_sort = '''
// ==== Universal table sort (DOM-based) ===================================
// Aplica sort clickeable a CUALQUIER tabla del documento, incluyendo
// las que aparecen dentro de modales. No interfiere con las tablas que
// ya tienen handlers (Clientes, Artículos, dim tables, Sin Rotación)
// porque ésas mantienen su sort basado en datos para soportar paginación.
function _stripFormatAR(s) {
    // Quita letras (USD, ARS), $, %, espacios; convierte separador de miles
    // "." → vacío y decimal "," → "."
    // "$1.234.567" → "1234567" ; "USD 419" → "419" ; "75,3%" → "75.3"
    return s.replace(/[A-Za-z\\$%\\s]/g, '').replace(/\\./g, '').replace(',', '.');
}
function _parseCellValue(cell, isNum, isDate) {
    const text = (cell.textContent || '').trim();
    if (isDate || /^\\d{4}-\\d{2}-\\d{2}$/.test(text)) return text;  // ISO sortable as string
    if (isNum) {
        const n = parseFloat(_stripFormatAR(text));
        return isNaN(n) ? -Infinity : n;
    }
    // Try numeric anyway if looks like a number
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
    // Separar fila TOTAL del final si existe
    let totalRow = null;
    if (allRows.length > 0 && _isTotalRow(allRows[allRows.length - 1])) {
        totalRow = allRows.pop();
    }
    const cur = th.dataset.uSortDir;
    const newDir = cur === 'desc' ? 'asc' : 'desc';
    // Resetear flechas en otros headers de la MISMA tabla
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
    // Re-anexar al DOM
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
        // Si el th ya tiene su propio onclick (sortBy/sortSR), no lo tocamos
        if (th.hasAttribute('onclick')) return;
        // Si el header está vacío (columna acción), no lo hacemos sortable
        if ((th.textContent || '').trim() === '' && !th.querySelector('span,a,b')) return;
        th.style.cursor = 'pointer';
        th.style.userSelect = 'none';
        th.title = 'Click para ordenar';
        // Insertar flecha indicadora
        if (!th.querySelector('.u-sort-arrow')) {
            const arrow = document.createElement('span');
            arrow.className = 'u-sort-arrow';
            arrow.textContent = '↕';
            arrow.style.cssText = 'margin-left:4px; opacity:.35; font-size:9px; vertical-align:middle;';
            th.appendChild(arrow);
        }
        th.addEventListener('click', (ev) => {
            // Ignorar clicks en botones/links dentro del header
            if (ev.target.closest('button,a,input,select')) return;
            sortTableByColumn(table, idx, th);
        });
        // Hover effect (si no lo tiene ya por CSS)
        th.addEventListener('mouseenter', () => { th.style.background = '#475569'; });
        th.addEventListener('mouseleave', () => { th.style.background = ''; });
    });
}
// MutationObserver: detecta tablas nuevas que se insertan en el DOM (modales)
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
    // Pasar por las tablas iniciales
    document.querySelectorAll('table').forEach(makeTableUniversallySortable);
});
'''

# universal_sort será concatenado a vendedor_fn más abajo (después de su definición)

# ============================================================
# Quitar precios/costos del Aging en la versión Vendedores
# ============================================================
# Stock KPI banner del modal de artículo: sacar "· ARS ${...}"
html = html.replace(
    "<div class=\"sub\">Físico: ${fmtNum(sr.fis)} · ARS ${ag?fmtMoney(ag.ars):'-'}</div>",
    "<div class=\"sub\">Físico: ${fmtNum(sr.fis)}</div>"
)
# Banner de aging: sacar "· Costo total: ... (USD ...)"
html = html.replace(
    "<div><strong>${fmtNum(sr.sr)}</strong> unidades en aging de un total físico de <strong>${fmtNum(sr.fis)}</strong>${agInfo ? ` · Costo total: <strong>${fmtMoney(agInfo.ars)}</strong> (USD ${fmtNum(agInfo.usd)})` : ''}.</div>",
    "<div><strong>${fmtNum(sr.sr)}</strong> unidades en aging de un total físico de <strong>${fmtNum(sr.fis)}</strong>.</div>"
)
# Tabla de breakdown de buckets en banner: quitar columnas de costo
html = html.replace(
    "bucketRows += `<tr><td style=\"color:${colors[i]}; font-weight:600\">${labels[i]}</td><td class=\"num\">${fmtNum(agInfo.b[i])}</td><td class=\"num\">${fmtMoney(agInfo.ba[i])}</td><td class=\"num\">USD ${fmtNum(agInfo.bu[i])}</td></tr>`;",
    "bucketRows += `<tr><td style=\"color:${colors[i]}; font-weight:600\">${labels[i]}</td><td class=\"num\">${fmtNum(agInfo.b[i])}</td></tr>`;"
)
html = html.replace(
    '${bucketRows ? `<table style="margin-top:8px; width:100%"><thead><tr style="background:rgba(239,68,68,.15)"><th style="text-align:left; padding:4px 8px">Bucket</th><th class="num" style="padding:4px 8px">Unidades</th><th class="num" style="padding:4px 8px">Costo ARS</th><th class="num" style="padding:4px 8px">Costo USD</th></tr></thead><tbody>${bucketRows}</tbody></table>` : \'\'}',
    '${bucketRows ? `<table style="margin-top:8px; width:100%"><thead><tr style="background:rgba(239,68,68,.15)"><th style="text-align:left; padding:4px 8px">Bucket</th><th class="num" style="padding:4px 8px">Unidades</th></tr></thead><tbody>${bucketRows}</tbody></table>` : \'\'}'
)
# Sub-vista "Por Bucket": KPIs sin costo
html = html.replace(
    "kpiHtml += `<div class=\"kpi\" style=\"border-color:${colors[i]}\"><div class=\"label\" style=\"color:${colors[i]}\">${labels[i]}</div><div class=\"value\">${fmtNum(totals[i])}</div><div class=\"sub\">${codigosCount[i]} cod · ${fmtMoney(ars[i])} · USD ${fmtNum(usd[i])} · ${pctU.toFixed(1)}%</div></div>`;",
    "kpiHtml += `<div class=\"kpi\" style=\"border-color:${colors[i]}\"><div class=\"label\" style=\"color:${colors[i]}\">${labels[i]}</div><div class=\"value\">${fmtNum(totals[i])}</div><div class=\"sub\">${codigosCount[i]} cod · ${pctU.toFixed(1)}%</div></div>`;"
)
html = html.replace(
    "kpiHtml += `<div class=\"kpi\" style=\"border-color:var(--bad)\"><div class=\"label\" style=\"color:var(--bad)\">TOTAL aging</div><div class=\"value\">${fmtNum(totalU)}</div><div class=\"sub\">${totalCodes} códigos · ${fmtMoney(totalArs)} · USD ${fmtNum(totalUsd)}</div></div>`;",
    "kpiHtml += `<div class=\"kpi\" style=\"border-color:var(--bad)\"><div class=\"label\" style=\"color:var(--bad)\">TOTAL aging</div><div class=\"value\">${fmtNum(totalU)}</div><div class=\"sub\">${totalCodes} códigos</div></div>`;"
)
# Tabla del bucket: quitar cabeceras y celdas de costo
html = html.replace(
    '<th class="num">Costo ARS</th><th class="num">USD</th><th>PM</th>',
    '<th>PM</th>'
)
html = html.replace(
    "html += `<td class=\"num\">${fmtMoney(r.ars)}</td><td class=\"num\">${fmtNum(r.usd)}</td><td>${r.pm}</td>",
    "html += `<td>${r.pm}</td>"
)
# Total row of bucket table
html = html.replace(
    'html += `<tr style="background:var(--bg-3); font-weight:bold"><td colspan="4">TOTAL ${rows.length} códigos</td><td class="num">${fmtNum(rows.reduce((a,r)=>a+r.ag,0))}</td><td colspan="6"></td><td class="num">${fmtMoney(rows.reduce((a,r)=>a+r.ars,0))}</td><td class="num">${fmtNum(rows.reduce((a,r)=>a+r.usd,0))}</td><td></td></tr>`;',
    'html += `<tr style="background:var(--bg-3); font-weight:bold"><td colspan="4">TOTAL ${rows.length} códigos</td><td class="num">${fmtNum(rows.reduce((a,r)=>a+r.ag,0))}</td><td colspan="6"></td><td></td></tr>`;'
)
# CSV export del bucket: quitar costos
html = html.replace(
    """data = (STATE.lastSRBucket||[]).map(r => ({
            codigo:r.codigo, articulo:r.articulo, marca:r.marca, subcat:r.subcat,
            total_aging:r.ag, fisico:r.fis, costo_ars:r.ars, costo_usd:r.usd,
            bucket_mas_viejo: r.old>=0 ? buckets[r.old] : '-',
            uds_0a30:r.b[0]||0, uds_30a60:r.b[1]||0, uds_60a90:r.b[2]||0,
            uds_90a150:r.b[3]||0, uds_150a365:r.b[4]||0, uds_mas365:r.b[5]||0,
            pm:r.pm
        }));""",
    """data = (STATE.lastSRBucket||[]).map(r => ({
            codigo:r.codigo, articulo:r.articulo, marca:r.marca, subcat:r.subcat,
            total_aging:r.ag, fisico:r.fis,
            bucket_mas_viejo: r.old>=0 ? buckets[r.old] : '-',
            uds_0a30:r.b[0]||0, uds_30a60:r.b[1]||0, uds_60a90:r.b[2]||0,
            uds_90a150:r.b[3]||0, uds_150a365:r.b[4]||0, uds_mas365:r.b[5]||0,
            pm:r.pm
        }));"""
)

# Versión Vendedores: el export del listado de Clientes no muestra plata
html = html.replace(
    'function _hasPricesDashboard() {\n    // Detecta si el dashboard maneja plata. La versión Vendedores reemplaza\n    // este flag a true via build_vendedores.py.\n    return true;\n}',
    'function _hasPricesDashboard() {\n    // Versión Vendedores — sin plata\n    return false;\n}'
)

# Fix SRSubcat chart calls to use makeBarChartQty (they show cantidades, not $)
html = html.replace(
    "makeBarChart('chartSRSub', topSub.map(x=>x.nombre), topSub.map(x=>x.units), '#ef4444', true);",
    "makeBarChartQty('chartSRSub', topSub.map(x=>x.nombre), topSub.map(x=>x.units), '#ef4444', true);"
)
html = html.replace(
    "makeBarChart('chartSRMarca', topMarca.map(x=>x.nombre), topMarca.map(x=>x.units), '#f59e0b', true);",
    "makeBarChartQty('chartSRMarca', topMarca.map(x=>x.nombre), topMarca.map(x=>x.units), '#f59e0b', true);"
)

# ============================================================
# Modal de PM (Aging > Ranking de PMs > click): quitar costos ARS/USD
# El template los incluye para el dashboard con precios — acá los borramos.
# ============================================================
# 0) Cambiar window._pmCtx.hasPrices a false (versión Vendedores no exporta plata)
html = html.replace(
    '''    // Estado para los botones de export del modal de PM
    window._pmCtx = {
        pm: pm,
        totalCodes: arts.length,
        totalUnits: Math.round(e.units),
        totalFis: Math.round(e.fis),
        totalARS: totalARS,
        totalUSD: totalUSD,
        arts: arts,
        hasPrices: true
    };''',
    '''    // Estado para los botones de export del modal de PM (sin precios)
    window._pmCtx = {
        pm: pm,
        totalCodes: arts.length,
        totalUnits: Math.round(e.units),
        totalFis: Math.round(e.fis),
        arts: arts,
        hasPrices: false
    };'''
)
# 1) Quitar las 2 KPIs de costo
html = html.replace(
    '''            <div class="kpi" style="border-color:var(--warn)"><div class="label" style="color:var(--warn)">Costo total ARS</div><div class="value" style="font-size:16px">${fmtMoney(totalARS)}</div></div>
            <div class="kpi" style="border-color:var(--warn)"><div class="label" style="color:var(--warn)">Costo total USD</div><div class="value" style="font-size:16px">USD ${fmtNum(totalUSD)}</div></div>
        </div>''',
    '''        </div>'''
)
# 2) Quitar columnas de costo del header de la tabla y reajustar anchos
html = html.replace(
    '''            <th class="num" style="width:8%">Stock aging</th>
            <th class="num" style="width:10%">Costo ARS</th>
            <th class="num" style="width:10%">Costo USD</th>
            <th class="num" style="width:8%">Físico</th>''',
    '''            <th class="num" style="width:14%">Stock aging</th>
            <th class="num" style="width:14%">Físico</th>'''
)
# 3) Quitar celdas de costo del tbody
html = html.replace(
    '''            <td class="num" style="color:${agColor}; font-weight:600">${fmtNum(a.sr)}</td>
            <td class="num">${fmtMoney(a.ars)}</td>
            <td class="num">USD ${fmtNum(a.usd)}</td>
            <td class="num">${fmtNum(a.fis)}</td>''',
    '''            <td class="num" style="color:${agColor}; font-weight:600">${fmtNum(a.sr)}</td>
            <td class="num">${fmtNum(a.fis)}</td>'''
)

# ============================================================
# INJECT vendedorReciente + precomputed indexes — add after EPOCH_MS
# ============================================================
vendedor_fn = '''
// ==== Optimizaciones: índices precalculados para evitar indexOf O(N) =====
const NAME_TO_IDX = new Map();
LK.clienteName.forEach((n, i) => { if (n != null) NAME_TO_IDX.set(n, i); });
const CODIGO_TO_IDX = new Map();
LK.codigo.forEach((c, i) => { if (c != null) CODIGO_TO_IDX.set(c, i); });
const SUBCAT_TO_IDX = new Map();
LK.subcat.forEach((s, i) => { if (s != null) SUBCAT_TO_IDX.set(s, i); });

// ==== Vendedor reciente (últimos 3 meses) — PRE-CALCULADO ==============
// Una sola pasada O(N) sobre ROWS al cargar; después es lookup O(1).
const VEND_WINDOW_DAYS = 90;
const TODAY_DAYS = Math.floor((Date.now() - EPOCH_MS) / 86400000);
const VEND_CUTOFF = TODAY_DAYS - VEND_WINDOW_DAYS;
const VEND_RECIENTE = new Map();   // cliNameIdx -> vendName (o null si no hay actividad)
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
'''
vendedor_fn = vendedor_fn + universal_sort
html = html.replace(
    '''const EPOCH_MS = Date.parse(D.meta.epoch + 'T00:00:00Z');''',
    '''const EPOCH_MS = Date.parse(D.meta.epoch + 'T00:00:00Z');\n''' + vendedor_fn
)

# ============================================================
# Also change the sort default for clientes in sortClientes
# ============================================================

# ============================================================
# Replace indexOf calls with precomputed maps
# ============================================================
html = html.replace('LK.clienteName.indexOf(', 'NAME_TO_IDX.get(')
html = html.replace('LK.codigo.indexOf(', 'CODIGO_TO_IDX.get(')
html = html.replace('LK.subcat.indexOf(', 'SUBCAT_TO_IDX.get(')

# Some indexOf calls return -1 when not found, but Map.get returns undefined.
# Patch the checks: cliIdx<0 => cliIdx==null, codIdx<0 => codIdx==null, etc.
html = html.replace(
    'if (cliIdx < 0) { alert(\'Cliente no encontrado\'); return; }',
    'if (cliIdx == null) { alert(\'Cliente no encontrado\'); return; }'
)
html = html.replace(
    'if (cliIdx<0 || codIdx<0)',
    'if (cliIdx==null || codIdx==null)'
)
html = html.replace(
    'if (subIdx<0) { alert(\'Subcat no encontrada\'); return; }',
    'if (subIdx==null) { alert(\'Subcat no encontrada\'); return; }'
)
html = html.replace(
    'if (codIdx<0) { alert(\'Código no encontrado\'); return; }',
    'if (codIdx==null) { alert(\'Código no encontrado\'); return; }'
)
# In showArticuloDetail there's a special case: hasSales = codIdx >= 0
html = html.replace(
    'const hasSales = codIdx >= 0;',
    'const hasSales = codIdx != null;'
)
# In showSubcatDetail there's: const subIdx = LK.subcat.indexOf(name);
# Already handled. Also for vendedorReciente: nIdx might be undefined now (was -1)
html = html.replace(
    "if (cliNameIdx == null || cliNameIdx < 0) return fallback || null;",
    "if (cliNameIdx == null || cliNameIdx < 0) return fallback || null;"
)
# Fix subcat sort default for clientes table to use trans
html = html.replace(
    "const s = STATE.sort.clientes || {key:'trans', dir:'desc'};",
    "const s = STATE.sort.clientes || {key:'trans', dir:'desc'};"
)

# ============================================================
# CSS optimizations: tabla con scroll solo vertical, anchos ajustables, wrap en nombres
# ============================================================
css_extra = '''
  /* === Mejoras de tabla v2 === */
  .table-wrap { overflow-x: hidden; }                 /* sólo scroll vertical */
  table { table-layout: fixed; }
  td { white-space: normal; word-wrap: break-word; overflow-wrap: anywhere; }
  th { white-space: normal; }
  td.nowrap, th.nowrap { white-space: nowrap; }
  td.num { white-space: nowrap; }                     /* números no rompen */
  /* Hover indica clickable en headers */
  th[onclick] { cursor: pointer; }
  th[onclick]:hover { background: #475569; }
  /* Sort arrows always visible (light) */
  th.sortable::after { content: " ↕"; opacity: 0.3; font-size: 9px; }
  th.sortable.sorted-asc::after { content: " ▲"; opacity: 1; color: var(--accent); }
  th.sortable.sorted-desc::after { content: " ▼"; opacity: 1; color: var(--accent); }
'''
html = html.replace(
    '  /* Sin rotación */',
    css_extra + '  /* Sin rotación */'
)

# ============================================================
# Add visible sort arrows to Sin Rotación tables (sortSR)
# ============================================================
arrow_helper = '''
function arrowSR(view, key) {
    const s = STATE.sort[view] || {key:null, dir:'desc'};
    if (s.key === key) return s.dir==='desc' ? 'sortable sorted-desc' : 'sortable sorted-asc';
    return 'sortable';
}
'''
html = html.replace(
    'function sortSR(view, key) {',
    arrow_helper + '\nfunction sortSR(view, key) {'
)

# Patch the sort tables in Sin Rotación to use the css class
# PMs ranking
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

# Oport
html = html.replace(
    '''<th onclick="sortSR('sropor','cliente')">Cliente</th>
        <th onclick="sortSR('sropor','vendedor')">Vendedor reciente</th>
        <th onclick="sortSR('sropor','provincia')">Provincia</th>
        <th class="num" onclick="sortSR('sropor','srArticulos')">Art. en aging</th>
        <th class="num" onclick="sortSR('sropor','units')">Uds. histórica</th>
        <th class="num" onclick="sortSR('sropor','count')">Compras de aging</th>
        <th class="num" onclick="sortSR('sropor','transTotales')">Compras totales</th>
        <th onclick="sortSR('sropor','ultima')">Última compra (aging)</th>
        <th class="num" onclick="sortSR('sropor','dias')">Días</th>
        <th></th>''',
    '''<th class="${arrowSR('sropor','cliente')}" onclick="sortSR('sropor','cliente')" style="width:18%">Cliente</th>
        <th class="${arrowSR('sropor','vendedor')}" onclick="sortSR('sropor','vendedor')" style="width:11%">Vendedor reciente</th>
        <th class="${arrowSR('sropor','provincia')}" onclick="sortSR('sropor','provincia')" style="width:9%">Provincia</th>
        <th class="num ${arrowSR('sropor','srArticulos')}" onclick="sortSR('sropor','srArticulos')" style="width:8%">Art. aging</th>
        <th class="num ${arrowSR('sropor','units')}" onclick="sortSR('sropor','units')" style="width:8%">Uds hist.</th>
        <th class="num ${arrowSR('sropor','count')}" onclick="sortSR('sropor','count')" style="width:8%">Compras aging</th>
        <th class="num ${arrowSR('sropor','transTotales')}" onclick="sortSR('sropor','transTotales')" style="width:8%">Compras tot.</th>
        <th class="${arrowSR('sropor','ultima')}" onclick="sortSR('sropor','ultima')" style="width:9%">Última compra aging</th>
        <th class="num ${arrowSR('sropor','dias')}" onclick="sortSR('sropor','dias')" style="width:6%">Días</th>
        <th style="width:13%"></th>'''
)

# Subcat / Marca tab
html = html.replace(
    '''<table><thead><tr><th>Tipo</th><th>Nombre</th><th class="num">Códigos sin rot</th><th class="num">Unidades muertas</th><th class="num">Stock físico</th><th class="num">% muerto</th></tr></thead><tbody>''',
    '''<table><thead><tr><th style="width:8%">Tipo</th><th style="width:30%">Nombre</th><th class="num" style="width:14%">Códigos</th><th class="num" style="width:18%">Uds muertas</th><th class="num" style="width:15%">Stock físico</th><th class="num" style="width:15%">% muerto</th></tr></thead><tbody>'''
)

# Add sort arrows to main dim tables and clientes/articulos
# We need to update arrowOf to return the class string with sortable + sorted-*
old_arrowOf = '''function arrowOf(tab, key) {
    const s = STATE.sort[tab]; return (s && s.key===key) ? `<span class="arrow">${s.dir==='desc'?'▼':'▲'}</span>` : '';
}'''
new_arrowOf = '''function arrowOf(tab, key) {
    const s = STATE.sort[tab]; return (s && s.key===key) ? `<span class="arrow">${s.dir==='desc'?'▼':'▲'}</span>` : '';
}
function arrowClass(tab, key) {
    const s = STATE.sort[tab];
    if (!s || s.key !== key) return 'sortable';
    return s.dir==='desc' ? 'sortable sorted-desc' : 'sortable sorted-asc';
}'''
html = html.replace(old_arrowOf, new_arrowOf)

# Update Clientes table with width hints + arrowClass
html = html.replace(
    '''<th onclick="sortBy('clientes','id')">ID${arr('id')}</th>
        <th onclick="sortBy('clientes','nombre')">Cliente${arr('nombre')}</th>
        <th class="num" onclick="sortBy('clientes','cantidad')">Unidades${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('clientes','trans')">Transacciones${arr('trans')}</th>
        <th class="num">Uds / trans.</th>
        <th onclick="sortBy('clientes','provincia')">Provincia${arr('provincia')}</th>
        <th onclick="sortBy('clientes','clase')">Clase${arr('clase')}</th>
        <th onclick="sortBy('clientes','vendedor')">Vendedor reciente${arr('vendedor')}</th>''',
    '''<th class="${arrowClass('clientes','id')}" onclick="sortBy('clientes','id')" style="width:7%">ID</th>
        <th class="${arrowClass('clientes','nombre')}" onclick="sortBy('clientes','nombre')" style="width:22%">Cliente</th>
        <th class="num ${arrowClass('clientes','cantidad')}" onclick="sortBy('clientes','cantidad')" style="width:9%">Unidades</th>
        <th class="num ${arrowClass('clientes','trans')}" onclick="sortBy('clientes','trans')" style="width:10%">Trans.</th>
        <th class="num" style="width:9%">Uds/trans.</th>
        <th class="${arrowClass('clientes','provincia')}" onclick="sortBy('clientes','provincia')" style="width:11%">Provincia</th>
        <th class="${arrowClass('clientes','clase')}" onclick="sortBy('clientes','clase')" style="width:10%">Clase</th>
        <th class="${arrowClass('clientes','vendedor')}" onclick="sortBy('clientes','vendedor')" style="width:22%">Vendedor reciente</th>'''
)

# Update Articulos table headers with arrow class
html = html.replace(
    '''<th onclick="sortBy('articulos','codigo')">Código${arr('codigo')}</th>
        <th onclick="sortBy('articulos','articulo')">Artículo${arr('articulo')}</th>
        <th onclick="sortBy('articulos','marca')">Marca${arr('marca')}</th>
        <th onclick="sortBy('articulos','subcat')">SubCategoría${arr('subcat')}</th>
        <th class="num" onclick="sortBy('articulos','sr')">Stock aging${arr('sr')}</th>
        <th class="num" onclick="sortBy('articulos','fis')">Stock${arr('fis')}</th>
        <th class="num" onclick="sortBy('articulos','cantidad')">Unidades${arr('cantidad')}</th>
        <th class="num" onclick="sortBy('articulos','trans')">Transacciones${arr('trans')}</th>
        <th class="num">Uds / trans.</th>''',
    '''<th class="${arrowClass('articulos','codigo')}" onclick="sortBy('articulos','codigo')" style="width:7%">Código</th>
        <th class="${arrowClass('articulos','articulo')}" onclick="sortBy('articulos','articulo')" style="width:32%">Artículo</th>
        <th class="${arrowClass('articulos','marca')}" onclick="sortBy('articulos','marca')" style="width:11%">Marca</th>
        <th class="${arrowClass('articulos','subcat')}" onclick="sortBy('articulos','subcat')" style="width:14%">SubCategoría</th>
        <th class="num ${arrowClass('articulos','sr')}" onclick="sortBy('articulos','sr')" style="width:7%">Sin Rot</th>
        <th class="num ${arrowClass('articulos','fis')}" onclick="sortBy('articulos','fis')" style="width:7%">Stock</th>
        <th class="num ${arrowClass('articulos','cantidad')}" onclick="sortBy('articulos','cantidad')" style="width:8%">Unidades</th>
        <th class="num ${arrowClass('articulos','trans')}" onclick="sortBy('articulos','trans')" style="width:8%">Trans.</th>
        <th class="num" style="width:6%">Uds/T</th>'''
)

# Generic dim tables
html = html.replace(
    '''<th onclick="sortBy('${tab}','nombre')">${label}${arr('nombre')}</th>
        <th class="num" onclick="sortBy('${tab}','cantidad')">Unidades${arr('cantidad')}</th>
        <th class="num">% uds</th>
        <th class="num" onclick="sortBy('${tab}','trans')">Transacciones${arr('trans')}</th>
        <th class="num">% trans.</th>
        <th class="num">Uds / trans.</th>''',
    '''<th class="${arrowClass(tab,'nombre')}" onclick="sortBy('${tab}','nombre')" style="width:35%">${label}</th>
        <th class="num ${arrowClass(tab,'cantidad')}" onclick="sortBy('${tab}','cantidad')" style="width:14%">Unidades</th>
        <th class="num" style="width:10%">% uds</th>
        <th class="num ${arrowClass(tab,'trans')}" onclick="sortBy('${tab}','trans')" style="width:14%">Trans.</th>
        <th class="num" style="width:10%">% trans.</th>
        <th class="num" style="width:12%">Uds/trans.</th>'''
)

# ============================================================
# Force re-render of Sin Rotación views to inject the arrow classes
# (the renderSRPMs etc. used template literals directly — they need to be re-rendered)
# We did the substitutions on those literals already — should auto-apply.
# ============================================================

# ============================================================
# Data is loaded via external <script src> tags (no inline)
# ============================================================
final = html
Path(OUT_FILE).parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write(final)

import os
sz = os.path.getsize(OUT_FILE)
print(f"Saved: {OUT_FILE}")
print(f"Size: {sz:,} bytes ({sz/1024/1024:.2f} MB)")
