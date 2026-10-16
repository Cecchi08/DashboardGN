function matchSearch(query, haystack) {
  if (!query) return true;
  const tokens = String(query).toLowerCase().split(/[\s+,;|]+/).filter(Boolean);
  if (!tokens.length) return true;
  const hay = String(haystack || '').toLowerCase();
  return tokens.every(t => hay.includes(t));
}
function searchableText(a) {
  return [a.articulo, a.codigo, a.marca, a.categoria, a.subCategoria, a.pn, a.pm].filter(Boolean).join(' ');
}

// ============ FILTERING ============
function filterArticles(f) {
  return DATA.articulos.filter(a => {
    if (f.categoria && a.categoria !== f.categoria) return false;
    if (f.subCategoria && a.subCategoria !== f.subCategoria) return false;
    if (f.marca && a.marca !== f.marca) return false;
    if (f.deposito && !a.depositos.some(d => d.deposito === f.deposito)) return false;
    if (f.stock && a.fisico <= 0) return false;
    if (f.conPrecio && !a.lista5 && !a.lista8) return false;
    if (!matchSearch(f.text, searchableText(a))) return false;
    return true;
  });
}

function sortRows(rows, key, dir) {
  const mul = dir === 'asc' ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const va = sortValue(a, key), vb = sortValue(b, key);
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * mul;
    return String(va || '').localeCompare(String(vb || '')) * mul;
  });
}
function sortValue(a, key) {
  switch (key) {
    case 'lista5': return (a.lista5 ? (state.moneda === 'dolares' ? a.lista5.dolares : a.lista5.pesos) : 0);
    case 'lista8': return (a.lista8 ? (state.moneda === 'dolares' ? a.lista8.dolares : a.lista8.pesos) : 0);
    case 'iva': return ivaOf(a);
    case 'fisico':
    case 'potencial': return a[key] || 0;
    default: return a[key] || '';
  }
}

// ============ CATÁLOGO RENDER ============
const COL_DEFS = [
  { key: '_sel', label: '', sortable: false },
  { key: 'categoria', label: 'Categoría' },
  { key: 'subCategoria', label: 'Subcat.' },
  { key: 'marca', label: 'Marca' },
  { key: 'codigo', label: 'Código' },
  { key: 'articulo', label: 'Artículo' },
  { key: 'fisico', label: 'Físico', num: true },
  { key: 'potencial', label: 'Potencial', num: true },
  { key: 'lista5', label: 'Lista 5', num: true },
  { key: 'lista8', label: 'Lista 8', num: true },
  { key: 'iva', label: 'IVA %', num: true },
  { key: 'pm', label: 'PM' },
];

// ============ AGING ============
// Buckets en orden de antigüedad creciente. label es el texto del badge.
const AGING_BUCKETS = [
  { key: 'ag0a30',    label: '0-30d',    cls: 'aging-0a30' },
  { key: 'ag30a60',   label: '30-60d',   cls: 'aging-30a60' },
  { key: 'ag60a90',   label: '60-90d',   cls: 'aging-60a90' },
  { key: 'ag90a150',  label: '90-150d',  cls: 'aging-90a150' },
  { key: 'ag150a365', label: '150-365d', cls: 'aging-150a365' },
  { key: 'agMas365',  label: '+365',     cls: 'aging-mas365' },
];
// Devuelve el bucket dominante (mayor cantidad). Empate -> el más viejo.
function dominantBucket(aging) {
  if (!aging || !aging.total) return null;
  let best = null;
  for (const b of AGING_BUCKETS) {
    const q = aging[b.key] || 0;
    if (q <= 0) continue;
    if (!best || q > best.qty || (q === best.qty)) best = { ...b, qty: q };
  }
  return best;
}
function agingBadge(aging) {
  const b = dominantBucket(aging);
  if (!b) return '';
  return `<span class="aging-badge ${b.cls}" title="Stock ${b.label} = ${b.qty} u. (de ${aging.total} totales)">${b.label}</span>`;
}
function agingLegendHTML() {
  return '<span class="aging-legend">Aging: ' +
    AGING_BUCKETS.map(b => `<span class="aging-badge ${b.cls}">${b.label}</span>`).join(' ') +
    '</span>';
}

function renderCatalogo() {
  const head = document.getElementById('cat-head');
  const body = document.getElementById('cat-body');
  const visibleCols = COL_DEFS.filter(c => c.key === '_sel' || state.cols[c.key]);

  head.innerHTML = visibleCols.map(c => {
    if (c.key === '_sel') return '<th><input type="checkbox" id="sel-all"></th>';
    const cls = state.sort.key === c.key ? ('sorted-' + state.sort.dir) : '';
    return `<th class="${cls}" data-sort="${c.key}">${c.label}</th>`;
  }).join('');

  let rows = filterArticles(state.filters);
  rows = sortRows(rows, state.sort.key, state.sort.dir);
  document.getElementById('cat-count').textContent = rows.length + ' artículos';
  document.getElementById('cat-empty').style.display = rows.length ? 'none' : 'block';

  const moneda = state.moneda;
  const html = rows.slice(0, 1000).map(a => {
    const cells = visibleCols.map(c => {
      if (c.key === '_sel') return `<td><input type="checkbox" class="row-sel" data-code="${escapeHtml(a.codigo)}"></td>`;
      if (c.key === 'lista5') return `<td class="num">${a.lista5 ? '<span class="pill-lista5">' + fmtMoney(moneda==='dolares'?a.lista5.dolares:a.lista5.pesos, moneda) + '</span>' : '<span class="small">–</span>'}</td>`;
      if (c.key === 'lista8') return `<td class="num">${a.lista8 ? '<span class="pill-lista8">' + fmtMoney(moneda==='dolares'?a.lista8.dolares:a.lista8.pesos, moneda) + '</span>' : '<span class="small">–</span>'}</td>`;
      if (c.key === 'iva') return `<td class="num">${fmtPct(ivaOf(a))}</td>`;
      if (c.key === 'fisico') return `<td class="num">${a.fisico}${state.filters.showPot?'<div class="small" style="color:var(--muted);">Pot: '+a.potencial+'</div>':''}</td>`;
      if (c.key === 'potencial') return `<td class="num">${a.potencial}</td>`;
      if (c.key === 'codigo') {
        const badge = agingBadge(a.aging);
        return `<td>${escapeHtml(a.codigo)}${badge ? '<div class="aging-row">' + badge + '</div>' : ''}</td>`;
      }
      if (c.key === 'articulo') {
        const depList = state.filters.showPot
          ? a.depositos.map(d => escapeHtml(d.deposito) + ': F=' + d.fisico + ' / P=' + d.potencial).join(' · ')
          : a.depositos.map(d => escapeHtml(d.deposito) + ': ' + d.fisico).join(' · ');
        return `<td><div>${escapeHtml(a.articulo)}</div>${a.depositos.length?'<div class="small">' + depList + '</div>':''}</td>`;
      }
      return `<td>${escapeHtml(a[c.key] || '')}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');
  body.innerHTML = html;
  if (rows.length > 1000) {
    body.insertAdjacentHTML('beforeend', `<tr><td colspan="${visibleCols.length}" class="small" style="text-align:center;">Mostrando primeros 1000 de ${rows.length}. Refiná los filtros.</td></tr>`);
  }

  // Bind header clicks
  head.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (state.sort.key === key) state.sort.dir = state.sort.dir === 'asc' ? 'desc' : 'asc';
      else { state.sort.key = key; state.sort.dir = 'asc'; }
      renderCatalogo();
    });
  });
  const sa = document.getElementById('sel-all');
  if (sa) sa.addEventListener('change', (e) => {
    body.querySelectorAll('.row-sel').forEach(cb => cb.checked = e.target.checked);
  });
}
