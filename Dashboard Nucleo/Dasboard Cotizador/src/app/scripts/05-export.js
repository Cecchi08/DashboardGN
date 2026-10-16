// ============ PDF / EMAIL ============
function buildQuoteHTML() {
  const cliente = document.getElementById('q-cliente').value || '—';
  const email = document.getElementById('q-email').value || '';
  const tel = document.getElementById('q-telefono').value || '';
  const cuit = document.getElementById('q-cuit').value || '';
  const lista = document.getElementById('q-lista').value;
  const moneda = document.getElementById('q-moneda').value;
  const desc = parseFloat(document.getElementById('q-descuento').value) || 0;
  const validez = parseInt(document.getElementById('q-validez').value) || 7;
  const obs = document.getElementById('q-obs').value || '';
  const vendedor = document.getElementById('q-vendedor').value || '';
  const remitente = document.getElementById('q-remitente').value || '';

  const fecha = new Date().toLocaleDateString('es-AR');
  const nro = 'COT-' + Date.now().toString().slice(-8);
  const tc = getTipoCambio();

  let subtotal = 0, ivaTotal = 0;
  const rows = [];
  for (const [code, item] of state.cart.entries()) {
    const p = priceOf(item.art, lista, moneda);
    const iva = ivaOf(item.art);
    const sub = p * item.cantidad;
    subtotal += sub;
    const subConDesc = sub * (1 - desc / 100);
    ivaTotal += subConDesc * (iva / 100);
    rows.push(`<tr>
      <td>${escapeHtml(code)}</td>
      <td>${escapeHtml(item.art.articulo)}<br><small class="muted">${escapeHtml(item.art.marca)} · ${escapeHtml(item.art.categoria)}</small></td>
      <td class="num">${item.cantidad}</td>
      <td class="num">${fmtMoney(p, moneda)}</td>
      <td class="num">${fmtPct(iva)}</td>
      <td class="num">${fmtMoney(sub, moneda)}</td>
    </tr>`);
  }
  const descImp = subtotal * desc / 100;
  const total = subtotal - descImp + ivaTotal;

  return `
    <div class="brand">
      <div><h1>Cotización</h1><div class="muted">Nº ${nro} · ${fecha}${tc?' · TC USD $' + fmtNum(tc):''}</div></div>
      <div style="text-align:right;">${vendedor ? '<b>' + escapeHtml(vendedor) + '</b><br>' : ''}${escapeHtml(remitente)}</div>
    </div>
    <h3>Cliente</h3>
    <div><b>${escapeHtml(cliente)}</b></div>
    <div class="muted">${escapeHtml(email)} · ${escapeHtml(tel)} ${cuit ? '· CUIT/DNI ' + escapeHtml(cuit):''}</div>
    <h3 style="margin-top:10px;">Artículos (Precios · ${moneda === 'dolares' ? 'Dólares' : 'Pesos'})</h3>
    <table>
      <thead><tr><th>Código</th><th>Artículo</th><th class="num">Cant.</th><th class="num">Precio U.</th><th class="num">IVA %</th><th class="num">Subtotal</th></tr></thead>
      <tbody>${rows.join('')}</tbody>
    </table>
    <div class="totals">
      <div>Subtotal: <b>${fmtMoney(subtotal, moneda)}</b></div>
      ${desc ? '<div>Descuento (' + desc + '%): <b>-' + fmtMoney(descImp, moneda) + '</b></div>' : ''}
      <div>IVA: <b>${fmtMoney(ivaTotal, moneda)}</b></div>
      <div style="font-size:16px; margin-top:6px;">TOTAL c/IVA: <b>${fmtMoney(total, moneda)}</b></div>
    </div>
    ${obs ? '<h3>Observaciones</h3><div>' + escapeHtml(obs).replace(/\\n/g,'<br>') + '</div>' : ''}
    <p class="muted" style="margin-top:14px;">Presupuesto válido por ${validez} días. Precios sujetos a disponibilidad.</p>
  `;
}

function buildListHTML() {
  const s = state.listado;
  let rows;
  if (s.selected.size) {
    rows = DATA.articulos.filter(a => s.selected.has(a.codigo));
  } else {
    rows = filterForListado();
  }
  rows = sortRowsListado(rows, s.sort.key, s.sort.dir);
  const fecha = new Date().toLocaleDateString('es-AR');
  const tc = getTipoCambio();
  const body = rows.map(a => {
    const l = a[s.lista];
    const price = l ? (s.moneda==='dolares'?l.dolares:l.pesos) : null;
    return `<tr><td>${escapeHtml(a.codigo)}</td><td>${escapeHtml(a.articulo)}</td><td>${escapeHtml(a.marca)}</td><td class="num">${price!==null?fmtMoney(price,s.moneda):'–'}</td><td class="num">${fmtPct(ivaOf(a))}</td></tr>`;
  }).join('');
  return `
    <div class="brand">
      <div><h1>${escapeHtml(s.titulo || 'Listado de precios')}</h1>
      <div class="muted">Precios · ${s.moneda === 'dolares' ? 'Dólares' : 'Pesos'} · ${fecha}${tc?' · TC USD $' + fmtNum(tc):''}</div></div>
      <div style="text-align:right;">${escapeHtml(s.empresa || '')}</div>
    </div>
    <table style="table-layout:auto;">
      <colgroup>
        <col style="width:10%;">
        <col style="width:48%;">
        <col style="width:18%;">
        <col style="width:14%;">
        <col style="width:10%;">
      </colgroup>
      <thead><tr><th>Código</th><th>Artículo</th><th>Marca</th><th class="num">Precio</th><th class="num">IVA %</th></tr></thead>
      <tbody>${body}</tbody>
    </table>
  `;
}

function printSection(html) {
  const pa = document.getElementById('print-area');
  pa.innerHTML = html;
  window.print();
}

function emailQuote() {
  const email = document.getElementById('q-email').value;
  if (!email) { alert('Ingresá el email del cliente'); return; }
  const cliente = document.getElementById('q-cliente').value || 'Cliente';
  const nro = 'COT-' + Date.now().toString().slice(-8);
  const lista = document.getElementById('q-lista').value;
  const moneda = document.getElementById('q-moneda').value;
  const desc = parseFloat(document.getElementById('q-descuento').value) || 0;
  let subtotal = 0;
  const lines = [];
  for (const [code, item] of state.cart.entries()) {
    const p = priceOf(item.art, lista, moneda);
    subtotal += p * item.cantidad;
    lines.push(`• [${code}] ${item.art.articulo} — ${item.cantidad} x ${fmtMoney(p, moneda)}`);
  }
  const total = subtotal * (1 - desc/100);
  const body = [
    `Hola ${cliente},`,
    '',
    `Te envío la cotización ${nro}:`,
    '',
    ...lines,
    '',
    `TOTAL: ${fmtMoney(total, moneda)}${desc ? ' (incluye ' + desc + '% de descuento)' : ''}`,
    '',
    'Adjunto el PDF con el detalle completo.',
    '',
    'Saludos.'
  ].join('\n');
  const subject = `Cotización ${nro} – ${cliente}`;
  window.location.href = `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function emailList() {
  const s = state.listado;
  const subject = `${s.titulo || 'Listado de precios'} — ${s.lista === 'ambas' ? 'Lista 5 + 8' : (s.lista === 'lista5' ? 'Lista 5' : 'Lista 8')}`;
  const body = [
    'Hola,',
    '',
    `Adjunto ${s.titulo || 'el listado de precios'} actualizado.`,
    `Lista: ${s.lista === 'ambas' ? 'Lista 5 + Lista 8' : (s.lista === 'lista5' ? 'Lista 5' : 'Lista 8')}`,
    `Moneda: ${s.moneda === 'dolares' ? 'Dólares' : 'Pesos'}`,
    '',
    'Saludos.'
  ].join('\n');
  window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
