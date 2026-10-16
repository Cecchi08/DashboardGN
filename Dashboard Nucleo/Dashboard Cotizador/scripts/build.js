const fs = require('fs');
const path = require('path');
const {
  PATTERN_LISTA,
  PATTERN_AGING,
  findLatestMatching,
  archiveOldFiles,
  readSheet,
} = require('../src/data/input-files');
const { num, clean, cleanCode } = require('../src/data/normalizers');

const ROOT = path.resolve(__dirname, '..');
const APP_DIR = path.join(ROOT, 'src', 'app');
const DOCS_DIR = path.join(ROOT, 'data', 'input');
const DIST_DIR = path.join(ROOT, 'dist');

// Patrones de los archivos de origen. Buscamos la versión más reciente por
// fecha de modificación, ignorando archivos temporales de Excel (~$...).
const FILE_LISTA = findLatestMatching(DOCS_DIR, PATTERN_LISTA);
const FILE_AGING = findLatestMatching(DOCS_DIR, PATTERN_AGING);

if (!FILE_LISTA) { console.error('ERROR: no se encontró ningún archivo "Articulos lista 5 y 8*.xlsx" en la carpeta'); process.exit(1); }
if (!FILE_AGING) { console.error('ERROR: no se encontró ningún archivo "Detalle Aging*.xlsx" en la carpeta'); process.exit(1); }
console.log('Archivo lista 5y8 :', FILE_LISTA);
console.log('Archivo aging     :', FILE_AGING);

console.log('Leyendo Articulos lista 5 y 8...');
const listaRows = readSheet(DOCS_DIR, FILE_LISTA);
console.log('  filas:', listaRows.length);

console.log('Leyendo Detalle Aging...');
const agingRows = readSheet(DOCS_DIR, FILE_AGING);
console.log('  filas:', agingRows.length);

// ============================================================
// 1) Indexar el Detalle Aging por Codigo (los precios de aquí
//    tienen prioridad porque vienen ya en pesos Y dólares)
// ============================================================
const agingMap = new Map();
for (const r of agingRows) {
  const code = cleanCode(r.Codigo);
  if (!code) continue;
  const buckets = {
    ag0a30: num(r.Ag0a30),
    ag30a60: num(r.Ag30a60),
    ag60a90: num(r.Ag60a90),
    ag90a150: num(r.Ag90a150),
    ag150a365: num(r.Ag150a365),
    agMas365: num(r.AgMas365),
  };
  buckets.total = buckets.ag0a30 + buckets.ag30a60 + buckets.ag60a90
    + buckets.ag90a150 + buckets.ag150a365 + buckets.agMas365;
  agingMap.set(code, {
    pm: clean(r.PM),
    tipoArticulo: clean(r.TipoArticulo),
    aging: buckets,
    precio5Pesos: num(r.Unitario5Pesos),
    precio5Dolares: num(r.Unitario5Dolares),
    precio8Pesos: num(r.Unitario8Pesos),
    precio8Dolares: num(r.Unitario8Dolares),
  });
}

// ============================================================
// 2) Estimar tipo de cambio implícito (mediana) usando los
//    artículos del Aging que tienen ambos valores > 0.
// ============================================================
const ratios = [];
for (const a of agingMap.values()) {
  if (a.precio5Pesos > 0 && a.precio5Dolares > 0) ratios.push(a.precio5Pesos / a.precio5Dolares);
  if (a.precio8Pesos > 0 && a.precio8Dolares > 0) ratios.push(a.precio8Pesos / a.precio8Dolares);
}
ratios.sort((a, b) => a - b);
const tc = ratios.length ? ratios[Math.floor(ratios.length / 2)] : 1000;
console.log('Tipo de cambio implícito (mediana):', tc.toFixed(2), 'ARS/USD  (de', ratios.length, 'muestras)');

function toBoth(value, moneda) {
  // Devuelve { pesos, dolares } a partir de un precio neto + moneda
  const n = num(value);
  if (n === 0) return { pesos: 0, dolares: 0 };
  const m = clean(moneda).toUpperCase();
  if (m === 'USD' || m === 'U$S' || m === 'DOLARES' || m === 'DÓLARES') {
    return { pesos: n * tc, dolares: n };
  }
  // por defecto pesos
  return { pesos: n, dolares: tc > 0 ? n / tc : 0 };
}

// ============================================================
// 3) Recorrer Lista 5 y 8 (rows = una fila por depósito) y
//    consolidar por Codigo: stock, depósitos y precios.
// ============================================================
const articles = new Map();
for (const r of listaRows) {
  const code = cleanCode(r.Codigo);
  if (!code) continue;
  let a = articles.get(code);
  if (!a) {
    a = {
      codigo: code,
      articulo: clean(r.Articulo),
      categoria: clean(r.Categoria),
      subCategoria: clean(r.SubCategoria),
      marca: clean(r.Marca),
      pn: clean(r.PN),
      pm: '',
      depositos: [],
      fisico: 0,
      potencial: 0,
      _neto5: null,
      _moneda5: '',
      _neto8: null,
      _moneda8: '',
      _impuestos: 0,
    };
    articles.set(code, a);
  }
  const fisico = num(r.Fisico);
  const pot = num(r.Potencial);
  if (clean(r.Deposito)) {
    a.depositos.push({
      deposito: clean(r.Deposito),
      fisico,
      potencial: pot,
    });
    a.fisico += fisico;
    a.potencial += pot;
  }
  // Tomamos los precios de la primera fila no nula
  if (a._neto5 == null && r.Neto5 != null) { a._neto5 = num(r.Neto5); a._moneda5 = clean(r.Moneda5); }
  if (a._neto8 == null && r.Neto8 != null) { a._neto8 = num(r.Neto8); a._moneda8 = clean(r.Moneda8); }
  if (!a._impuestos && r.Impuestos != null) a._impuestos = num(r.Impuestos);
}

// ============================================================
// 4) Construir lista_5/lista_8 con AMBAS monedas y mergear aging
// ============================================================
for (const a of articles.values()) {
  const ag = agingMap.get(a.codigo);

  // PM y aging del archivo aging
  if (ag) {
    a.pm = ag.pm || '';
    a.tipoArticulo = ag.tipoArticulo || '';
    if (ag.aging.total > 0) a.aging = ag.aging;
  }

  // ---------- LISTA 5 ----------
  let l5Pesos = 0, l5Dolares = 0;
  if (ag && (ag.precio5Pesos > 0 || ag.precio5Dolares > 0)) {
    l5Pesos = ag.precio5Pesos;
    l5Dolares = ag.precio5Dolares;
    if (l5Pesos > 0 && l5Dolares === 0) l5Dolares = l5Pesos / tc;
    if (l5Dolares > 0 && l5Pesos === 0) l5Pesos = l5Dolares * tc;
  } else if (a._neto5 != null && a._neto5 > 0) {
    const r = toBoth(a._neto5, a._moneda5);
    l5Pesos = r.pesos; l5Dolares = r.dolares;
  }
  if (l5Pesos > 0 || l5Dolares > 0) {
    a.lista5 = {
      moneda: a._moneda5 || (ag ? 'ARS' : ''),
      pesos: l5Pesos,
      dolares: l5Dolares,
      impuestos: a._impuestos,
    };
  }

  // ---------- LISTA 8 ----------
  let l8Pesos = 0, l8Dolares = 0;
  if (ag && (ag.precio8Pesos > 0 || ag.precio8Dolares > 0)) {
    l8Pesos = ag.precio8Pesos;
    l8Dolares = ag.precio8Dolares;
    if (l8Pesos > 0 && l8Dolares === 0) l8Dolares = l8Pesos / tc;
    if (l8Dolares > 0 && l8Pesos === 0) l8Pesos = l8Dolares * tc;
  } else if (a._neto8 != null && a._neto8 > 0) {
    const r = toBoth(a._neto8, a._moneda8);
    l8Pesos = r.pesos; l8Dolares = r.dolares;
  }
  if (l8Pesos > 0 || l8Dolares > 0) {
    a.lista8 = {
      moneda: a._moneda8 || (ag ? 'ARS' : ''),
      pesos: l8Pesos,
      dolares: l8Dolares,
      impuestos: a._impuestos,
    };
  }

  // limpiar campos auxiliares
  delete a._neto5; delete a._moneda5; delete a._neto8; delete a._moneda8; delete a._impuestos;
}

// ============================================================
// 5) Incluir artículos que están solo en el Aging y no en la
//    Lista 5y8 (sin stock, pero con precios y aging)
// ============================================================
for (const [code, ag] of agingMap.entries()) {
  if (articles.has(code)) continue;
  // Buscar info básica (Articulo, Marca, etc.) en la fila original del aging
  const src = agingRows.find(r => cleanCode(r.Codigo) === code);
  if (!src) continue;
  const a = {
    codigo: code,
    articulo: clean(src.Articulo),
    categoria: clean(src.Categoria),
    subCategoria: clean(src.SubCategoria),
    marca: clean(src.Marca),
    pn: '',
    pm: ag.pm || '',
    tipoArticulo: ag.tipoArticulo || '',
    depositos: [],
    fisico: num(src.StockFisico),
    potencial: num(src.StockPotencial),
  };
  if (ag.aging.total > 0) a.aging = ag.aging;

  if (ag.precio5Pesos > 0 || ag.precio5Dolares > 0) {
    a.lista5 = {
      moneda: 'ARS',
      pesos: ag.precio5Pesos || ag.precio5Dolares * tc,
      dolares: ag.precio5Dolares || ag.precio5Pesos / tc,
      impuestos: 21,
    };
  }
  if (ag.precio8Pesos > 0 || ag.precio8Dolares > 0) {
    a.lista8 = {
      moneda: 'ARS',
      pesos: ag.precio8Pesos || ag.precio8Dolares * tc,
      dolares: ag.precio8Dolares || ag.precio8Pesos / tc,
      impuestos: 21,
    };
  }
  articles.set(code, a);
}

// ============================================================
// 6) Escribir el catálogo que consume la API
// ============================================================
function mtime(f) {
  try { return fs.statSync(path.join(DOCS_DIR, f)).mtime.toISOString(); }
  catch (e) { return null; }
}

const articulosArr = Array.from(articles.values()).sort((a, b) => a.articulo.localeCompare(b.articulo));
const countLista5 = articulosArr.filter(a => a.lista5).length;
const countLista8 = articulosArr.filter(a => a.lista8).length;
const countAging = articulosArr.filter(a => a.aging).length;

const data = {
  generadoEn: new Date().toISOString(),
  fechas: {
    lista: mtime(FILE_LISTA),
    aging: mtime(FILE_AGING),
  },
  fuentes: { lista: FILE_LISTA, aging: FILE_AGING },
  tipoCambio: tc,
  conteo: {
    total: articulosArr.length,
    lista5: countLista5,
    lista8: countLista8,
    aging: countAging,
  },
  articulos: articulosArr,
};

console.log('Artículos consolidados:', data.articulos.length,
  '· con Lista 5:', countLista5,
  '· con Lista 8:', countLista8,
  '· con aging:', countAging);

if (!fs.existsSync(DIST_DIR)) fs.mkdirSync(DIST_DIR, { recursive: true });
const outPath = path.join(DIST_DIR, 'catalog.json');
fs.writeFileSync(outPath, JSON.stringify(data), 'utf8');
console.log('OK ->', outPath, '(', (fs.statSync(outPath).size / 1024).toFixed(1), 'KB )');

// ============================================================
// 7) Archivar versiones anteriores de los archivos de origen
// ============================================================
const ARCHIVE_DIR = path.join(DOCS_DIR, 'archive');
console.log('Archivando versiones anteriores en docs/archive/...');
const movedLista = archiveOldFiles(DOCS_DIR, PATTERN_LISTA, FILE_LISTA, ARCHIVE_DIR);
const movedAging = archiveOldFiles(DOCS_DIR, PATTERN_AGING, FILE_AGING, ARCHIVE_DIR);
console.log('  lista 5y8:', movedLista, '· aging:', movedAging);
