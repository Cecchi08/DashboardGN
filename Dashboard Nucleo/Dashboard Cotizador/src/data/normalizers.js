function num(value) {
  if (value === null || value === undefined || value === '') return 0;
  if (typeof value === 'number') return value;
  const normalized = String(value).trim().replace(/[^\d.,-]/g, '').replace(/\./g, '').replace(',', '.');
  const number = parseFloat(normalized);
  return Number.isNaN(number) ? 0 : number;
}

function clean(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function cleanCode(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

module.exports = { num, clean, cleanCode };
