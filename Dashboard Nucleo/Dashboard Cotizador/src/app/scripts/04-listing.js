// ============ LISTADO ============
function filterForListado() {
  const s = state.listado;
  if (s.soloSel) return DATA.articulos.filter(a => s.selected.has(a.codigo));
  return DATA.articulos.filter(a => {
    if (s.categorias.size && !s.categorias.has(a.categoria)) return false;
    if (s.subCategorias.size && !s.subCategorias.has(a.subCategoria)) return false;
    if (s.marca && a.marca !== s.marca) return false;
    if (s.conStock && a.fisico <= 0) return false;
    if (s.conPrecio) {
      const hasAny = (s.lista === 'ambas') ? (a.lista5 || a.lista8) : a[s.lista];
      if (!hasAny) return false;
    }
    if (!matchSearch(s.text, searchableText(a))) return false;
    return true;
  });
}

// Cómo extraer un valor sortable de un artículo según la columna del listado.
function sortValueListado(a, key) {
  const s = state.listado;
  switch (key) {
    case 'price': {
      const l = a[s.lista];
      if (!l) return 0;
      return s.moneda === 'dolares' ? l.dolares : l.pesos;
    }
    case 'iva': return ivaOf(a);
    case 'stock': return a.fisico || 0;
    case 'codigo': {
      // Si el código es numérico lo ordeno como número, si no como string.
      const n = parseFloat(a.codigo);
      return isNaN(n) ? a.codigo : n;
    }
    default: return a[key] || '';
  }
}
function sortRowsListado(rows, key, dir) {
  const mul = dir === 'asc' ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const va = sortValueListado(a, key), vb = sortValueListado(b, key);
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * mul;
    return String(va || '').localeCompare(String(vb || '')) * mul;
  });
}

const LIST_COL_DEFS = [
  { key: 'codigo',    label: 'Código' },
  { key: 'articulo',  label: 'Artículo' },
  { key: 'marca',     label: 'Marca' },
  { key: 'categoria', label: 'Categoría' },
  { key: 'price',     label: 'Precio',  num: true },
  { key: 'iva',       label: 'IVA %',   num: true },
  { key: 'stock',     label: 'Stock',   num: true },
];

function renderListado() {
  const s = state.listado;
  let rows = filterForListado();
  rows = sortRowsListado(rows, s.sort.key, s.sort.dir);
  document.getElementById('list-count').textContent = rows.length + ' artículos';
  document.getElementById('list-sel-count').textContent = s.selected.size ? '(' + s.selected.size + ' seleccionados)' : '';
  document.getElementById('list-empty').style.display = rows.length ? 'none' : 'block';

  const ths = LIST_COL_DEFS.map(c => {
    const cls = [];
    if (c.num) cls.push('num');
    if (s.sort.key === c.key) cls.push('sorted-' + s.sort.dir);
    return `<th class="${cls.join(' ')}" data-sort="${c.key}">${c.label}</th>`;
  }).join('');
  document.getElementById('list-head').innerHTML = `<tr><th><input type="checkbox" id="list-sel-all"></th>${ths}</tr>`;

  const body = rows.slice(0, 3000).map(a => {
    const l = a[s.lista];
    const price = l ? (s.moneda==='dolares'?l.dolares:l.pesos) : null;
    const checked = s.selected.has(a.codigo) ? 'checked' : '';
    const depsStr = s.showPot
      ? a.depositos.map(d => escapeHtml(d.deposito) + ': F=' + d.fisico + ' / P=' + d.potencial).join(' · ')
      : a.depositos.map(d => escapeHtml(d.deposito) + ': ' + d.fisico).join(' · ');
    const deps = a.depositos.length ? '<div class="small">' + depsStr + '</div>' : '';
    const stockCell = s.showPot
      ? `${a.fisico}<div class="small" style="color:var(--muted);">Pot: ${a.potencial}</div>`
      : a.fisico;
    const badge = agingBadge(a.aging);
    const codeCell = badge ? escapeHtml(a.codigo) + '<div class="aging-row">' + badge + '</div>' : escapeHtml(a.codigo);
    return `<tr>
      <td><input type="checkbox" class="list-row-sel" data-code="${escapeHtml(a.codigo)}" ${checked}></td>
      <td>${codeCell}</td>
      <td><div>${escapeHtml(a.articulo)}</div>${deps}</td>
      <td>${escapeHtml(a.marca)}</td>
      <td class="small">${escapeHtml(a.categoria)}</td>
      <td class="num">${price!==null?fmtMoney(price,s.moneda):'–'}</td>
      <td class="num">${fmtPct(ivaOf(a))}</td>
      <td class="num">${stockCell}</td>
    </tr>`;
  }).join('');
  document.getElementById('list-body').innerHTML = body;

  // Bind selection
  document.querySelectorAll('.list-row-sel').forEach(cb => cb.addEventListener('change', e => {
    const code = e.target.dataset.code;
    if (e.target.checked) s.selected.add(code); else s.selected.delete(code);
    document.getElementById('list-sel-count').textContent = s.selected.size ? '(' + s.selected.size + ' seleccionados)' : '';
  }));
  const sa = document.getElementById('list-sel-all');
  if (sa) sa.addEventListener('change', e => {
    document.querySelectorAll('.list-row-sel').forEach(cb => {
      cb.checked = e.target.checked;
      const code = cb.dataset.code;
      if (e.target.checked) s.selected.add(code); else s.selected.delete(code);
    });
    document.getElementById('list-sel-count').textContent = s.selected.size ? '(' + s.selected.size + ' seleccionados)' : '';
  });

  // Click en los headers para ordenar (toggle asc/desc en la misma columna)
  document.querySelectorAll('#list-head th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (s.sort.key === key) s.sort.dir = s.sort.dir === 'asc' ? 'desc' : 'asc';
      else { s.sort.key = key; s.sort.dir = 'asc'; }
      renderListado();
    });
  });
}
