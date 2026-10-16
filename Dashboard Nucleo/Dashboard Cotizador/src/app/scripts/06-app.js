// ============ EVENTS ============
function bindEvents() {
  // Tabs
  document.querySelectorAll('nav.tabs button').forEach(b => b.addEventListener('click', () => {
    const t = b.dataset.tab;
    state.tab = t;
    document.querySelectorAll('nav.tabs button').forEach(x => x.classList.toggle('active', x.dataset.tab === t));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + t));
    if (t === 'cotizacion') renderCotizacion();
    if (t === 'listado') renderListado();
  }));

  // Filters catálogo
  document.getElementById('f-text').addEventListener('input', e => { state.filters.text = e.target.value; renderCatalogo(); });
  document.getElementById('f-categoria').addEventListener('change', e => { state.filters.categoria = e.target.value; renderCatalogo(); });
  document.getElementById('f-subcategoria').addEventListener('change', e => { state.filters.subCategoria = e.target.value; renderCatalogo(); });
  document.getElementById('f-marca').addEventListener('change', e => { state.filters.marca = e.target.value; renderCatalogo(); });
  document.getElementById('f-deposito').addEventListener('change', e => { state.filters.deposito = e.target.value; renderCatalogo(); });
  document.getElementById('f-stock').addEventListener('change', e => { state.filters.stock = e.target.checked; renderCatalogo(); });
  document.getElementById('f-con-precio').addEventListener('change', e => { state.filters.conPrecio = e.target.checked; renderCatalogo(); });
  document.getElementById('f-show-pot').addEventListener('change', e => { state.filters.showPot = e.target.checked; renderCatalogo(); });
  document.getElementById('f-moneda').addEventListener('change', e => { state.moneda = e.target.value; renderCatalogo(); });

  document.getElementById('reset-filters').addEventListener('click', () => {
    state.filters = { text: '', categoria: '', subCategoria: '', marca: '', deposito: '', stock: false, conPrecio: false, showPot: false };
    ['f-text','f-categoria','f-subcategoria','f-marca','f-deposito'].forEach(id => document.getElementById(id).value = '');
    ['f-stock','f-con-precio','f-show-pot'].forEach(id => document.getElementById(id).checked = false);
    renderCatalogo();
  });

  // Columns
  document.querySelectorAll('.col-toggle').forEach(cb => cb.addEventListener('change', e => {
    state.cols[e.target.dataset.col] = e.target.checked;
    renderCatalogo();
  }));

  // Add selected
  document.getElementById('add-selected').addEventListener('click', () => {
    const checks = document.querySelectorAll('.row-sel:checked');
    if (!checks.length) { alert('Seleccioná al menos un artículo'); return; }
    chooseListIfNeeded((chosen) => {
      if (chosen === null && state.cols.lista5 && state.cols.lista8) return; // canceled
      if (chosen) document.getElementById('q-lista').value = chosen;
      checks.forEach(cb => addToCart(cb.dataset.code, 1));
      checks.forEach(cb => cb.checked = false);
      const sa = document.getElementById('sel-all'); if (sa) sa.checked = false;
      const listName = chosen === 'lista5' ? 'Lista 5' : chosen === 'lista8' ? 'Lista 8' : '';
      alert(`${checks.length} artículo(s) agregados a la cotización${listName ? ' (' + listName + ')' : ''}.`);
      renderCotizacion();
    });
  });

  // Cotización
  ['q-lista','q-moneda','q-descuento'].forEach(id => document.getElementById(id).addEventListener('input', renderCotizacion));
  document.getElementById('q-moneda').addEventListener('change', e => applyAutoObs(e.target.value));
  document.getElementById('tipo-cambio').addEventListener('input', () => { renderCotizacion(); });
  document.getElementById('q-clear').addEventListener('click', () => {
    if (!state.cart.size) return;
    if (confirm('¿Vaciar la cotización?')) { state.cart.clear(); refreshCartBadge(); renderCotizacion(); }
  });
  document.getElementById('q-add-from-cat').addEventListener('click', () => {
    state.tab = 'catalogo';
    document.querySelectorAll('nav.tabs button').forEach(x => x.classList.toggle('active', x.dataset.tab === 'catalogo'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-catalogo'));
  });
  document.getElementById('q-preview').addEventListener('click', () => {
    if (!state.cart.size) { alert('Agregá al menos un artículo'); return; }
    const w = window.open('', '_blank');
    w.document.write('<html><head><title>Vista previa</title><style>body{font-family:Arial;padding:20px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:4px 6px;}th{background:#eee;text-align:left;}td.num{text-align:right;}.muted{color:#666;}.brand{display:flex;justify-content:space-between;border-bottom:2px solid #333;padding-bottom:6px;}.totals{text-align:right;margin-top:10px;}</style></head><body>' + buildQuoteHTML() + '</body></html>');
    w.document.close();
  });
  document.getElementById('q-pdf').addEventListener('click', () => {
    if (!state.cart.size) { alert('Agregá al menos un artículo'); return; }
    printSection(buildQuoteHTML());
  });
  document.getElementById('q-email').addEventListener('click', () => {
    if (!state.cart.size) { alert('Agregá al menos un artículo'); return; }
    emailQuote();
  });

  // Listado
  const bindList = (id, prop, type='value') => document.getElementById(id).addEventListener(type==='checked'?'change':'input', e => { state.listado[prop] = type==='checked'?e.target.checked:e.target.value; renderListado(); });
  bindList('l-lista','lista','value');
  bindList('l-moneda','moneda','value');
  bindList('l-titulo','titulo','value');
  bindList('l-empresa','empresa','value');
  bindList('lf-text','text','value');
  bindList('lf-marca','marca','value');
  bindList('lf-con-stock','conStock','checked');
  bindList('lf-con-precio','conPrecio','checked');
  bindList('lf-solo-sel','soloSel','checked');
  bindList('lf-show-pot','showPot','checked');
  // lista/moneda selects fire 'change' also
  ['l-lista','l-moneda','lf-marca'].forEach(id => document.getElementById(id).addEventListener('change', () => renderListado()));

  document.getElementById('l-pdf').addEventListener('click', () => {
    const rows = filterForListado();
    const count = state.listado.selected.size || rows.length;
    if (!count) { alert('No hay artículos para exportar.'); return; }
    printSection(buildListHTML());
  });
  document.getElementById('l-email').addEventListener('click', emailList);
  document.getElementById('l-preview').addEventListener('click', () => {
    const rows = filterForListado();
    const count = state.listado.selected.size || rows.length;
    if (!count) { alert('No hay artículos para mostrar.'); return; }
    const w = window.open('', '_blank');
    w.document.write('<html><head><title>Vista previa</title><style>body{font-family:Arial;padding:20px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:4px 6px;}th{background:#eee;text-align:left;}td.num,th.num{text-align:right;}.muted{color:#666;}.brand{display:flex;justify-content:space-between;border-bottom:2px solid #333;padding-bottom:6px;}</style></head><body>' + buildListHTML() + '</body></html>');
    w.document.close();
  });
  document.getElementById('l-clear-sel').addEventListener('click', () => {
    state.listado.selected.clear();
    renderListado();
  });

  document.getElementById('help-btn').addEventListener('click', () => document.getElementById('help-dlg').showModal());
}

// ============ BOOT ============
function boot() {
  const f = DATA.fechas || {};
  const c = DATA.conteo || { total: DATA.articulos.length, lista5: 0, lista8: 0, aging: 0 };
  const fL = f.lista ? new Date(f.lista).toLocaleDateString('es-AR') : '?';
  const fA = f.aging ? new Date(f.aging).toLocaleDateString('es-AR') : '?';
  const tc = DATA.tipoCambio ? Number(DATA.tipoCambio).toLocaleString('es-AR', { maximumFractionDigits: 2 }) : '?';
  document.getElementById('meta-info').innerHTML =
    `${c.total} artículos · Stock+Precios ${fL} (L5: ${c.lista5} · L8: ${c.lista8}) · Aging ${fA} (${c.aging} items) · TC implícito: $${tc}`;
  // leyenda de aging arriba del catálogo
  const host = document.getElementById('aging-legend-host');
  if (host) host.innerHTML = agingLegendHTML();
  populateSelects();
  bindEvents();
  applyAutoObs(document.getElementById('q-moneda').value);
  renderCatalogo();
  renderCotizacion();
  renderListado();
}
boot();
