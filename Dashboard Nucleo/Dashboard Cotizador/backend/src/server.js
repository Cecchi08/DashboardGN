const express = require('express');
const fs = require('node:fs');
const path = require('node:path');

const app = express();
const root = path.resolve(__dirname, '../..');
const port = Number(process.env.PORT || 1234);
const host = process.env.HOST || '0.0.0.0';
const output = path.join(root, 'dist', 'catalog.json');

app.get('/api/health', (_req, res) => res.json({ service: 'dashboard-cotizador-api', status: 'ok' }));
app.get('/api/info', (_req, res) => {
  if (!fs.existsSync(output)) return res.status(503).json({ error: 'Catálogo no generado' });
  const files = fs.readdirSync(path.join(root, 'data', 'input'));
  res.json({
    generatedAt: fs.statSync(output).mtime.toISOString(),
    inputFiles: files.filter((name) => /^(Articulos lista 5 y 8|Detalle Aging).*\.xlsx$/i.test(name)),
  });
});
app.get('/api/catalog', (_req, res) => {
  if (!fs.existsSync(output)) return res.status(503).json({ error: 'Catálogo no generado' });
  res.setHeader('Cache-Control', 'public, max-age=300');
  res.sendFile(output);
});

app.listen(port, host, () => console.log(`Dashboard Cotizador API escuchando en ${host}:${port}`));
