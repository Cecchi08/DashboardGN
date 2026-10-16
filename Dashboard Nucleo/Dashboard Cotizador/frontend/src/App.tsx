import { useEffect, useMemo, useState } from 'react';

type PriceList = { pesos: number; dolares: number; impuestos?: number };
type Article = {
  codigo: string; articulo: string; categoria?: string; subCategoria?: string; marca?: string;
  fisico?: number; potencial?: number; pm?: string; depositos?: { deposito: string; fisico?: number }[];
  lista5?: PriceList; lista8?: PriceList; aging?: { total: number; [key: string]: number };
};
type Catalog = { generadoEn: string; tipoCambio: number; conteo: { total: number }; articulos: Article[] };
type CartLine = { article: Article; qty: number };
type ListKey = 'lista5' | 'lista8';

const money = (value: number, currency: string) => new Intl.NumberFormat('es-AR', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value || 0);
const price = (article: Article, list: ListKey, currency: string) => article[list]?.[currency === 'USD' ? 'dolares' : 'pesos'] || 0;

function TopBar({ online, message }: { online: boolean; message: string }) {
  return <header className="topbar"><a className="brand" href="#"><span className="mark">N</span><span><b>Núcleo</b><small>Cotizador</small></span></a><span className="connection"><i className={online ? 'dot online' : 'dot'} />{message}</span><button className="button quiet" onClick={() => window.location.reload()}>Actualizar</button></header>;
}

function ProductRow({ article, list, currency, onAdd }: { article: Article; list: ListKey; currency: string; onAdd: (article: Article) => void }) {
  return <tr><td className="code">{article.codigo}</td><td><b>{article.articulo}</b><small className="subline">{article.subCategoria || article.pm || ''}</small></td><td>{article.categoria || '—'}</td><td>{article.marca || '—'}</td><td className="numeric"><span className={(article.fisico || 0) > 0 ? 'stock' : 'out'}>{article.fisico || 0}</span></td><td className="numeric">{article.potencial || 0}</td><td className="numeric price-cell">{price(article, list, currency) ? money(price(article, list, currency), currency) : '—'}{article.aging?.total ? <small className="subline">Aging {article.aging.total}</small> : null}</td><td><button className="button add" onClick={() => onAdd(article)}>Agregar</button></td></tr>;
}

function QuoteLine({ row, list, currency, onQty, onRemove }: { row: CartLine; list: ListKey; currency: string; onQty: (code: string, qty: number) => void; onRemove: (code: string) => void }) {
  const unitPrice = price(row.article, list, currency);
  return <tr><td><b>{row.article.articulo}</b><small className="subline">{row.article.codigo}</small></td><td>{money(unitPrice, currency)}</td><td>{row.article[list]?.impuestos || 0}%</td><td><input className="qty" type="number" min="0" value={row.qty} onChange={(event) => onQty(row.article.codigo, Number(event.target.value))} /></td><td><b>{money(unitPrice * row.qty, currency)}</b></td><td><button className="remove" onClick={() => onRemove(row.article.codigo)} aria-label="Quitar artículo">×</button></td></tr>;
}

function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [subcategory, setSubcategory] = useState('');
  const [brand, setBrand] = useState('');
  const [deposit, setDeposit] = useState('');
  const [inStock, setInStock] = useState(false);
  const [hasPrice, setHasPrice] = useState(false);
  const [currency, setCurrency] = useState('USD');
  const [list, setList] = useState<ListKey>('lista5');
  const [cart, setCart] = useState<Record<string, CartLine>>({});
  const [customer, setCustomer] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerTaxId, setCustomerTaxId] = useState('');
  const [seller, setSeller] = useState('');
  const [validDays, setValidDays] = useState(7);
  const [conditions, setConditions] = useState('');
  const [discount, setDiscount] = useState(0);
  const [active, setActive] = useState<'catalog' | 'quote'>('catalog');

  useEffect(() => {
    fetch('/api/catalog')
      .then((response) => { if (!response.ok) throw new Error('No se pudo cargar el catálogo.'); return response.json(); })
      .then(setCatalog)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const categories = useMemo(() => [...new Set(catalog?.articulos.map((article) => article.categoria).filter(Boolean) as string[])].sort(), [catalog]);
  const subcategories = useMemo(() => [...new Set(catalog?.articulos.map((article) => article.subCategoria).filter(Boolean) as string[])].sort(), [catalog]);
  const brands = useMemo(() => [...new Set(catalog?.articulos.map((article) => article.marca).filter(Boolean) as string[])].sort(), [catalog]);
  const deposits = useMemo(() => [...new Set(catalog?.articulos.flatMap((article) => article.depositos?.map((item) => item.deposito) || []).filter(Boolean))].sort(), [catalog]);
  const articles = useMemo(() => (catalog?.articulos || []).filter((article) => {
    const text = `${article.codigo} ${article.articulo} ${article.marca || ''} ${article.categoria || ''} ${article.subCategoria || ''}`.toLocaleLowerCase();
    return (!query || query.toLocaleLowerCase().split(/\s+/).every((part) => text.includes(part)))
      && (!category || article.categoria === category) && (!subcategory || article.subCategoria === subcategory)
      && (!brand || article.marca === brand) && (!deposit || article.depositos?.some((item) => item.deposito === deposit))
      && (!inStock || (article.fisico || 0) > 0) && (!hasPrice || !!article.lista5 || !!article.lista8);
  }), [catalog, query, category, subcategory, brand, deposit, inStock, hasPrice]);
  const cartLines = Object.values(cart);
  const subtotal = cartLines.reduce((sum, row) => sum + price(row.article, list, currency) * row.qty, 0);
  const safeDiscount = Math.min(100, Math.max(0, discount));
  const discountAmount = subtotal * safeDiscount / 100;
  const tax = cartLines.reduce((sum, row) => sum + price(row.article, list, currency) * row.qty * ((row.article[list]?.impuestos || 0) / 100), 0) * (1 - safeDiscount / 100);
  const total = subtotal - discountAmount + tax;

  function add(article: Article) { setCart((old) => ({ ...old, [article.codigo]: { article, qty: (old[article.codigo]?.qty || 0) + 1 } })); }
  function updateQty(code: string, qty: number) {
    setCart((old) => { const next = { ...old }; if (qty <= 0) delete next[code]; else if (next[code]) next[code] = { ...next[code], qty }; return next; });
  }
  function downloadCsv(filename: string, rows: string[][]) {
    const csv = rows.map((row) => row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(';')).join('\n');
    const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })); link.download = filename; link.click(); URL.revokeObjectURL(link.href);
  }
  function exportQuote() {
    const rows = [['Código', 'Artículo', 'Cantidad', 'Precio unitario', 'IVA %', 'Total'], ...cartLines.map((row) => [row.article.codigo, row.article.articulo, String(row.qty), String(price(row.article, list, currency)), String(row.article[list]?.impuestos || 0), String(price(row.article, list, currency) * row.qty)]), ['', '', '', '', 'Subtotal', String(subtotal)], ['', '', '', '', 'Descuento', String(discountAmount)], ['', '', '', '', 'IVA', String(tax)], ['', '', '', '', 'Total', String(total)]];
    downloadCsv('cotizacion.csv', rows);
  }
  function exportPriceList() {
    downloadCsv('lista-de-precios.csv', [['Código', 'Artículo', 'Marca', 'Categoría', 'Stock', 'Precio', 'IVA %'], ...articles.map((article) => [article.codigo, article.articulo, article.marca || '', article.categoria || '', String(article.fisico || 0), String(price(article, list, currency)), String(article[list]?.impuestos || 0)])]);
  }

  return <div className="app-shell">
    <TopBar online={!!catalog} message={catalog ? 'Datos actualizados' : error || 'Cargando catálogo…'} />
    <main className="page">
      <div className="page-heading"><div><p className="eyebrow">VENTAS · CATÁLOGO</p><h1>Cotizador</h1><p>Buscá artículos, consultá disponibilidad y armá una propuesta comercial.</p></div><div className="updated"><span>{catalog ? `${catalog.conteo.total.toLocaleString('es-AR')} artículos` : 'Conectando'}</span><strong>{catalog ? `Actualizado ${new Date(catalog.generadoEn).toLocaleDateString('es-AR')}` : ''}</strong></div></div>
      <nav className="tabs"><button className={active === 'catalog' ? 'tab active' : 'tab'} onClick={() => setActive('catalog')}>Catálogo <span>{articles.length.toLocaleString('es-AR')}</span></button><button className={active === 'quote' ? 'tab active' : 'tab'} onClick={() => setActive('quote')}>Cotización <span>{cartLines.length}</span></button></nav>
      {active === 'catalog' ? <>
        <section className="filters"><label className="search">⌕<input placeholder="Buscar por artículo, código, marca…" value={query} onChange={(event) => setQuery(event.target.value)} /></label><select value={category} onChange={(event) => setCategory(event.target.value)}><option value="">Todas las categorías</option>{categories.map((value) => <option key={value}>{value}</option>)}</select><select value={subcategory} onChange={(event) => setSubcategory(event.target.value)}><option value="">Todas las subcategorías</option>{subcategories.map((value) => <option key={value}>{value}</option>)}</select><select value={brand} onChange={(event) => setBrand(event.target.value)}><option value="">Todas las marcas</option>{brands.map((value) => <option key={value}>{value}</option>)}</select><select value={deposit} onChange={(event) => setDeposit(event.target.value)}><option value="">Todos los depósitos</option>{deposits.map((value) => <option key={value}>{value}</option>)}</select><label className="check"><input type="checkbox" checked={inStock} onChange={(event) => setInStock(event.target.checked)} /> Con stock</label><label className="check"><input type="checkbox" checked={hasPrice} onChange={(event) => setHasPrice(event.target.checked)} /> Con precio</label><select value={list} onChange={(event) => setList(event.target.value as ListKey)}><option value="lista5">Lista 5</option><option value="lista8">Lista 8</option></select><select value={currency} onChange={(event) => setCurrency(event.target.value)}><option value="ARS">Pesos</option><option value="USD">Dólares</option></select><button className="button" onClick={exportPriceList}>Exportar lista</button></section>
        <section className="panel table-panel"><div className="panel-title"><div><h2>Artículos</h2><p>Seleccioná un artículo para agregarlo a la cotización.</p></div><span className="muted">Tipo de cambio {money(catalog?.tipoCambio || 0, 'ARS')}</span></div><div className="table-scroll"><table><thead><tr><th>Código</th><th>Artículo</th><th>Categoría</th><th>Marca</th><th className="numeric">Stock</th><th className="numeric">Potencial</th><th className="numeric">Precio</th><th></th></tr></thead><tbody>{articles.slice(0, 500).map((article) => <ProductRow key={article.codigo} article={article} list={list} currency={currency} onAdd={add} />)}</tbody></table>{articles.length > 500 && <p className="table-note">Mostrando los primeros 500 resultados. Refiná la búsqueda para ver más.</p>}{articles.length === 0 && <p className="empty">No hay artículos para esos filtros.</p>}</div></section>
      </> : <section className="quote-layout">
        <div className="panel quote-items"><div className="panel-title"><div><h2>Detalle de la cotización</h2><p>Revisá las cantidades y condiciones antes de imprimir.</p></div><button className="button quiet" onClick={() => setCart({})}>Vaciar</button></div>
          <div className="quote-meta"><label>Cliente<input value={customer} onChange={(event) => setCustomer(event.target.value)} placeholder="Nombre o razón social" /></label><label>Email del cliente<input type="email" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} placeholder="cliente@empresa.com" /></label><label>Teléfono<input value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} /></label><label>CUIT / DNI<input value={customerTaxId} onChange={(event) => setCustomerTaxId(event.target.value)} /></label><label>Vendedor<input value={seller} onChange={(event) => setSeller(event.target.value)} /></label><label>Validez (días)<input type="number" min="1" value={validDays} onChange={(event) => setValidDays(Math.max(1, Number(event.target.value)))} /></label><label>Lista<select value={list} onChange={(event) => setList(event.target.value as ListKey)}><option value="lista5">Lista 5</option><option value="lista8">Lista 8</option></select></label><label>Moneda<select value={currency} onChange={(event) => setCurrency(event.target.value)}><option value="ARS">Pesos</option><option value="USD">Dólares</option></select></label><label className="conditions">Condiciones<textarea rows={2} value={conditions} onChange={(event) => setConditions(event.target.value)} placeholder="Forma de pago, plazo de entrega…" /></label></div>
          <div className="table-scroll"><table><thead><tr><th>Artículo</th><th>Precio</th><th>IVA</th><th>Cantidad</th><th>Total</th><th></th></tr></thead><tbody>{cartLines.map((row) => <QuoteLine key={row.article.codigo} row={row} list={list} currency={currency} onQty={updateQty} onRemove={(code) => updateQty(code, 0)} />)}</tbody></table>{!cartLines.length && <p className="empty">Todavía no agregaste artículos. Volvé al catálogo para empezar.</p>}</div>
        </div>
        <aside className="panel summary"><h2>Resumen</h2><label>Descuento (%)<input type="number" min="0" max="100" value={discount} onChange={(event) => setDiscount(Number(event.target.value))} /></label><div className="sum-row"><span>Subtotal</span><b>{money(subtotal, currency)}</b></div><div className="sum-row"><span>Descuento</span><b>− {money(discountAmount, currency)}</b></div><div className="sum-row"><span>IVA</span><b>{money(tax, currency)}</b></div><div className="sum-total"><span>Total estimado</span><strong>{money(total, currency)}</strong></div><button className="button primary full" disabled={!cartLines.length} onClick={() => window.print()}>Vista previa / Guardar PDF</button><button className="button full" disabled={!cartLines.length} onClick={exportQuote}>Descargar CSV</button><button className="button full" disabled={!cartLines.length || !customerEmail} onClick={() => { const subject = encodeURIComponent(`Cotización para ${customer || 'cliente'}`); const body = encodeURIComponent(`Hola ${customer || ''},\n\nTotal: ${money(total, currency)}\nValidez: ${validDays} días\nVendedor: ${seller}\n${conditions}`); window.location.href = `mailto:${customerEmail}?subject=${subject}&body=${body}`; }}>Preparar email</button><p className="fineprint">Válida por {validDays} días. Los precios e impuestos corresponden a la lista seleccionada.</p></aside>
      </section>}
    </main>
    {cartLines.length > 0 && active === 'catalog' && <button className="cart-fab" onClick={() => setActive('quote')}>Cotización · {cartLines.length} artículos <b>{money(total, currency)}</b></button>}
  </div>;
}

export default App;
