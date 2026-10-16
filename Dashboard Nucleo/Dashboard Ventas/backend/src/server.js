const express = require('express');
const fs = require('node:fs');
const path = require('node:path');

const app = express();
const port = Number(process.env.PORT || 4321);
const host = process.env.HOST || '0.0.0.0';
const dataDir = path.resolve(__dirname, '../data/processed');
const dataFile = path.join(dataDir, 'data_raw_v2.json');
const agingFile = path.join(dataDir, 'aging.json');

app.get('/api/health', (_req, res) => res.json({ service: 'dashboard-ventas-api', status: 'ok' }));
app.get('/api/info', (_req, res) => {
  if (!fs.existsSync(dataFile)) return res.status(503).json({ error: 'Datos de ventas no generados' });
  res.json({ generatedAt: fs.statSync(dataFile).mtime.toISOString() });
});
app.get('/api/data', (_req, res) => {
  if (!fs.existsSync(dataFile)) return res.status(503).json({ error: 'Datos de ventas no generados' });
  res.setHeader('Cache-Control', 'public, max-age=300');
  res.sendFile(dataFile);
});
app.get('/api/aging', (_req, res) => {
  if (!fs.existsSync(agingFile)) return res.json({});
  res.setHeader('Cache-Control', 'public, max-age=300');
  res.sendFile(agingFile);
});
app.listen(port, host, () => console.log(`Dashboard Ventas API escuchando en ${host}:${port}`));
