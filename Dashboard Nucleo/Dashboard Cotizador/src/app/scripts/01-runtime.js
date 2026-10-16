const DATA = __DATA_JSON__;

// ============ UTIL ============
const fmtNum = (n) => {
  if (n === null || n === undefined || isNaN(n)) return '';
  return Number(n).toLocaleString('es-AR', { maximumFractionDigits: 2 });
};
const fmtMoney = (n, moneda) => {
  if (n === null || n === undefined || isNaN(n) || n === 0) return '–';
  const prefix = moneda === 'dolares' ? 'U$S' : '$';
  return prefix + ' ' + Number(n).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const priceOf = (art, listKey, moneda) => {
  const l = art[listKey];
  if (!l) return 0;
  return moneda === 'dolares' ? l.dolares : l.pesos;
};
const ivaOf = (art) => {
  if (art.lista5 && art.lista5.impuestos != null) return art.lista5.impuestos;
  if (art.lista8 && art.lista8.impuestos != null) return art.lista8.impuestos;
  return 0;
};
const fmtPct = (n) => (n == null || isNaN(n)) ? '–' : Number(n).toLocaleString('es-AR', { maximumFractionDigits: 2 }) + '%';
const getTipoCambio = () => {
  const v = parseFloat(document.getElementById('tipo-cambio').value);
  return isNaN(v) || v <= 0 ? null : v;
};

const OBS_AUTO = {
  pesos: 'Valores expresados en pesos incluyen iva',
  dolares: 'Valores expresados en pesos incluyen iva',
};
// Variantes anteriores que también deben considerarse "auto" (para no pisar texto que el usuario tipeó)
const OBS_AUTO_LEGACY = [
  'Valores expresados en pesos no incluyen iva',
  'Valores expresados en dolares no incluyen iva',
  'Valores expresados en dolares incluyen iva',
];
function applyAutoObs(moneda) {
  const el = document.getElementById('q-obs');
  if (!el) return;
  const current = el.value.trim();
  const isAuto = current === '' || current === OBS_AUTO.pesos || current === OBS_AUTO.dolares || OBS_AUTO_LEGACY.includes(current);
  if (isAuto) el.value = OBS_AUTO[moneda] || OBS_AUTO.pesos;
}

// ============ STATE ============
const state = {
  tab: 'catalogo',
  filters: { text: '', categoria: '', subCategoria: '', marca: '', deposito: '', stock: false, conPrecio: false, showPot: false },
  cols: { categoria: true, subCategoria: false, marca: true, codigo: true, articulo: true, fisico: true, potencial: false, lista5: true, lista8: true, iva: true, pm: false },
  moneda: 'pesos',
  sort: { key: 'articulo', dir: 'asc' },
  cart: new Map(), // codigo -> { art, cantidad }
  // listado
  listado: { lista: 'lista5', moneda: 'pesos', text: '', categorias: new Set(), subCategorias: new Set(), marca: '', conStock: false, conPrecio: true, soloSel: false, showPot: false, titulo: 'Listado de precios', empresa: '', selected: new Set(), sort: { key: 'articulo', dir: 'asc' } },
};

function chooseListIfNeeded(callback) {
  const show5 = state.cols.lista5;
  const show8 = state.cols.lista8;
  if (show5 && show8) {
    const dlg = document.getElementById('list-choice-dlg');
    const handler = (e) => {
      const choice = e.target.dataset.choice;
      if (!choice) return;
      dlg.querySelectorAll('[data-choice]').forEach(b => b.removeEventListener('click', handler));
      dlg.close();
      callback(choice === 'cancel' ? null : choice);
    };
    dlg.querySelectorAll('[data-choice]').forEach(b => b.addEventListener('click', handler));
    dlg.showModal();
  } else if (show5) {
    callback('lista5');
  } else if (show8) {
    callback('lista8');
  } else {
    callback(null);
  }
}

// ============ INIT ============
function uniqueSorted(arr) { return Array.from(new Set(arr.filter(Boolean))).sort((a,b)=>a.localeCompare(b)); }

// Multiselect reutilizable: une un <div class="multiselect"> con un Set del state.
function setupMultiselect(rootId, options, selectedSet, onChange) {
  const root = document.getElementById(rootId);
  if (!root) return;
  const toggle = root.querySelector('.multiselect-toggle');
  const summary = root.querySelector('.ms-summary');
  const panel = root.querySelector('.multiselect-panel');
  const optionsEl = root.querySelector('.ms-options');
  const search = root.querySelector('.ms-search');
  const allBtn = root.querySelector('.ms-all');
  const noneBtn = root.querySelector('.ms-none');

  function updateSummary() {
    if (selectedSet.size === 0) summary.textContent = 'Todas';
    else if (selectedSet.size === 1) summary.textContent = Array.from(selectedSet)[0];
    else summary.textContent = selectedSet.size + ' seleccionadas';
  }
  function renderOptions() {
    const filter = (search.value || '').toLowerCase().trim();
    const visible = options.filter(o => !filter || o.toLowerCase().includes(filter));
    if (visible.length === 0) {
      optionsEl.innerHTML = '<div class="ms-empty">Sin resultados</div>';
      return;
    }
    optionsEl.innerHTML = visible.map(o =>
      `<label><input type="checkbox" value="${escapeHtml(o)}"${selectedSet.has(o) ? ' checked' : ''}> <span>${escapeHtml(o)}</span></label>`
    ).join('');
    optionsEl.querySelectorAll('input[type=checkbox]').forEach(cb => {
      cb.addEventListener('change', e => {
        const v = e.target.value;
        if (e.target.checked) selectedSet.add(v); else selectedSet.delete(v);
        updateSummary();
        if (onChange) onChange();
      });
    });
  }
  toggle.addEventListener('click', e => {
    e.stopPropagation();
    panel.classList.toggle('collapsed');
    root.classList.toggle('open');
    if (!panel.classList.contains('collapsed')) {
      renderOptions();
      setTimeout(() => search.focus(), 0);
    }
  });
  // cerrar al hacer click afuera
  document.addEventListener('click', e => {
    if (!root.contains(e.target) && !panel.classList.contains('collapsed')) {
      panel.classList.add('collapsed');
      root.classList.remove('open');
    }
  });
  search.addEventListener('input', renderOptions);
  allBtn.addEventListener('click', e => {
    e.preventDefault();
    options.forEach(o => selectedSet.add(o));
    renderOptions(); updateSummary(); if (onChange) onChange();
  });
  noneBtn.addEventListener('click', e => {
    e.preventDefault();
    selectedSet.clear();
    renderOptions(); updateSummary(); if (onChange) onChange();
  });
  updateSummary();
  return { refresh: () => { renderOptions(); updateSummary(); } };
}

function populateSelects() {
  const cats = uniqueSorted(DATA.articulos.map(a => a.categoria));
  const subs = uniqueSorted(DATA.articulos.map(a => a.subCategoria));
  const marcas = uniqueSorted(DATA.articulos.map(a => a.marca));
  const deps = uniqueSorted(DATA.articulos.flatMap(a => a.depositos.map(d => d.deposito)));

  const fill = (id, list) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const current = sel.value;
    sel.innerHTML = '<option value="">Todos/as</option>' + list.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('');
    sel.value = current;
  };
  fill('f-categoria', cats);
  fill('f-subcategoria', subs);
  fill('f-marca', marcas);
  fill('f-deposito', deps);
  fill('lf-marca', marcas);

  // Multiselects del listado
  setupMultiselect('lf-categoria-ms', cats, state.listado.categorias, renderListado);
  setupMultiselect('lf-subcategoria-ms', subs, state.listado.subCategorias, renderListado);
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Búsqueda multi-palabra: separa por espacios, "+", ",", ";", "|"; todas tienen que aparecer (AND, case-insensitive)
