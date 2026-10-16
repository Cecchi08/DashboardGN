const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const WATCH_DIR = path.join(ROOT, 'docs');
// Patrones aceptados (matchea cualquier sufijo de fecha que ponga Power BI).
const WATCH_PATTERNS = [
  /^Articulos lista 5 y 8.*\.xlsx$/i,
  /^Detalle Aging.*\.xlsx$/i,
];
function shouldWatch(filename) {
  if (!filename) return false;
  if (filename.startsWith('~$')) return false; // temp de Excel
  return WATCH_PATTERNS.some(p => p.test(filename));
}

const ts = () => new Date().toLocaleTimeString('es-AR');

let timer = null;
let running = false;
let pending = false;

function rebuild() {
  if (running) { pending = true; return; }
  running = true;
  console.log('\n[' + ts() + '] Cambios detectados. Regenerando cotizador.html...');
  const child = spawn(process.execPath, [path.join(__dirname, 'build.js')], { stdio: 'inherit', cwd: ROOT });
  child.on('close', code => {
    running = false;
    if (code === 0) {
      console.log('[' + ts() + '] OK. Actualizá (F5) el navegador para ver los cambios nuevos.');
    } else {
      console.log('[' + ts() + '] *** ERROR (code ' + code + '). Revisá el mensaje de arriba.');
    }
    console.log('  Esperando nuevos cambios... (Ctrl+C para salir)\n');
    if (pending) { pending = false; scheduleRebuild(); }
  });
}

function scheduleRebuild() {
  if (timer) clearTimeout(timer);
  // 2s debounce: Excel/Power BI suelen escribir en varios pasos
  timer = setTimeout(rebuild, 2000);
}

console.log('==========================================');
console.log(' Cotizador - Actualización automática');
console.log('==========================================');
console.log('Carpeta vigilada: ' + WATCH_DIR);
console.log('Archivos vigilados (cualquier fecha):');
console.log('  - Articulos lista 5 y 8*.xlsx');
console.log('  - Detalle Aging*.xlsx');
console.log('');
console.log('Dejá esta ventana abierta. Cuando exportes los Excel desde Power BI');
console.log('encima de estos archivos, el cotizador.html se regenera solo.');
console.log('');
console.log('Ctrl+C para salir.');
console.log('');

try {
  fs.watch(WATCH_DIR, (ev, filename) => {
    if (!shouldWatch(filename)) return;
    console.log('  [' + ts() + '] ' + ev + ' -> ' + filename);
    scheduleRebuild();
  });
} catch (e) {
  console.error('No se pudo vigilar la carpeta:', e.message);
  process.exit(1);
}

// Keep the process alive
setInterval(() => {}, 1 << 30);
