// ============ CART / COTIZACIÓN ============
function addToCart(code, qty = 1) {
  const a = DATA.articulos.find(x => x.codigo === code);
  if (!a) return;
  if (state.cart.has(code)) {
    state.cart.get(code).cantidad += qty;
  } else {
    state.cart.set(code, { art: a, cantidad: qty });
  }
  refreshCartBadge();
}
function refreshCartBadge() {
  document.getElementById('cart-count').textContent = state.cart.size;
  document.getElementById('q-item-count').textContent = state.cart.size;
}

function renderCotizacion() {
  const body = document.getElementById('q-body');
  const lista = document.getElementById('q-lista').value;
  const moneda = document.getElementById('q-moneda').value;
  const desc = parseFloat(document.getElementById('q-descuento').value) || 0;
  document.getElementById('q-empty').style.display = state.cart.size ? 'none' : 'block';

  let subtotal = 0, ivaTotal = 0;
  const rows = [];
  for (const [code, item] of state.cart.entries()) {
    const p = priceOf(item.art, lista, moneda);
    const iva = ivaOf(item.art);
    const st = item.art.fisico;
    const sub = p * item.cantidad;
    subtotal += sub;
    rows.push(`<tr>
      <td>${escapeHtml(code)}</td>
      <td>${escapeHtml(item.art.articulo)}<div class="small">${escapeHtml(item.art.marca)}</div></td>
      <td><span class="badge ${st>0?'ok':'danger'}">${st}</span></td>
      <td class="num">${fmtMoney(p, moneda)}</td>
      <td class="num">${fmtPct(iva)}</td>
      <td class="num"><input type="number" min="1" value="${item.cantidad}" style="width:70px; text-align:right;" data-code="${escapeHtml(code)}" class="q-qty"></td>
      <td class="num">${fmtMoney(sub, moneda)}</td>
      <td><button class="btn danger" data-remove="${escapeHtml(code)}" style="padding:4px 8px;">✕</button></td>
    </tr>`);
  }
  body.innerHTML = rows.join('');
  body.querySelectorAll('.q-qty').forEach(inp => inp.addEventListener('input', e => {
    const c = e.target.dataset.code;
    const v = parseInt(e.target.value) || 1;
    state.cart.get(c).cantidad = v;
    renderCotizacion();
  }));
  body.querySelectorAll('[data-remove]').forEach(btn => btn.addEventListener('click', e => {
    state.cart.delete(e.target.dataset.remove);
    refreshCartBadge();
    renderCotizacion();
  }));

  const descImp = subtotal * desc / 100;
  const baseConDesc = subtotal - descImp;
  // IVA over discounted base, per item proportion
  for (const [, item] of state.cart.entries()) {
    const p = priceOf(item.art, lista, moneda);
    const iva = ivaOf(item.art);
    const subItem = p * item.cantidad;
    const subConDesc = subItem * (1 - desc / 100);
    ivaTotal += subConDesc * (iva / 100);
  }
  const total = baseConDesc + ivaTotal;
  document.getElementById('q-subtotal').textContent = fmtMoney(subtotal, moneda);
  document.getElementById('q-desc-importe').textContent = fmtMoney(descImp, moneda);
  document.getElementById('q-iva-importe').textContent = fmtMoney(ivaTotal, moneda);
  document.getElementById('q-total').textContent = fmtMoney(total, moneda);
}
