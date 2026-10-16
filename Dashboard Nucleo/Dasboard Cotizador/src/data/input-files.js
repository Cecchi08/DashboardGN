const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

const PATTERN_LISTA = /^Articulos lista 5 y 8.*\.xlsx$/i;
const PATTERN_AGING = /^Detalle Aging.*\.xlsx$/i;

function findLatestMatching(dir, regex) {
  const files = fs.readdirSync(dir).filter(file => !file.startsWith('~$') && regex.test(file));
  if (files.length === 0) return null;

  return files
    .map(name => ({ name, modifiedAt: fs.statSync(path.join(dir, name)).mtimeMs }))
    .sort((a, b) => b.modifiedAt - a.modifiedAt)[0].name;
}

function archiveOldFiles(dir, regex, keepFile, oldDir) {
  if (!fs.existsSync(oldDir)) fs.mkdirSync(oldDir, { recursive: true });
  const files = fs.readdirSync(dir).filter(file =>
    !file.startsWith('~$') && regex.test(file) && file !== keepFile
  );
  let moved = 0;

  for (const file of files) {
    const source = path.join(dir, file);
    const destination = path.join(oldDir, file);
    try {
      if (fs.existsSync(destination)) fs.rmSync(destination);
      fs.renameSync(source, destination);
      console.log('  archivado:', file);
      moved++;
    } catch (error) {
      console.warn('  no se pudo mover', file, ':', error.message);
    }
  }

  return moved;
}

function readSheet(rootDir, filename) {
  const workbook = XLSX.readFile(path.join(rootDir, filename));
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  return XLSX.utils.sheet_to_json(sheet, { defval: null, raw: true });
}

module.exports = {
  PATTERN_LISTA,
  PATTERN_AGING,
  findLatestMatching,
  archiveOldFiles,
  readSheet,
};
