#!/usr/bin/env python3
"""Sube data.js, aging.js, chart.umd.js a un repo GitHub via `git push`.

Mucho más confiable que la GitHub Blob API para archivos grandes
(data.js suele pesar ~88 MB, cerca del tope práctico de la API que tira 502).

Mantiene un clon local "shallow" en .cache/github-repo/ que se
actualiza en cada corrida. Las credenciales se configuran automáticamente
con `gh auth setup-git` (gh actúa como helper de git).

Requisitos:
- Git instalado (https://git-scm.com/download/win)
- gh CLI logueado (`gh auth login` con scope `repo`)
"""
import json
import subprocess
import shutil
from pathlib import Path
import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
BASE = SCRIPT_DIR.parents[1]
CONFIG_FILE = BASE / "config" / ".cloudflare-config.json"
REPO_DIR = BASE / ".cache" / "github-repo"

FILES_TO_UPLOAD = [
    ('data.js', BASE / 'data' / 'processed' / 'data.js'),
    ('aging.js', BASE / 'data' / 'processed' / 'aging.js'),
    ('chart.umd.js', BASE / 'src' / 'vendor' / 'chart.umd.js'),
]

with open(CONFIG_FILE, encoding='utf-8') as f:
    cfg = json.load(f)
REPO = cfg.get('githubRepo')
BRANCH = cfg.get('githubBranch', 'main')
if not REPO or '/' not in REPO:
    print("ERROR: 'githubRepo' invalido en .cloudflare-config.json. Formato esperado: 'usuario/repo'")
    raise SystemExit(1)


def run(cmd, cwd=None, check=True, capture=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    if check and r.returncode != 0:
        print(f"ERROR ejecutando: {' '.join(cmd)}")
        if capture:
            print(f"  stdout: {(r.stdout or '')[:600]}")
            print(f"  stderr: {(r.stderr or '')[:600]}")
        raise SystemExit(1)
    return r


# 1) Verificar git instalado
r = run(['git', '--version'], check=False)
if r.returncode != 0:
    print("ERROR: Git no esta instalado en este sistema.")
    print("  Instalalo desde https://git-scm.com/download/win")
    print("  Despues de instalar, cerrá y abrí el CMD nuevamente.")
    raise SystemExit(1)
print(f"Git OK: {r.stdout.strip()}")

# 2) Configurar gh como helper de credenciales git
print("Configurando gh como helper de credenciales git...")
run(['gh', 'auth', 'setup-git'], check=False)

# 3) Clonar (primera vez) o actualizar el clon local
HTTPS_URL = f'https://github.com/{REPO}.git'
if not REPO_DIR.exists():
    print(f"Clonando {REPO} (primera vez, shallow)...")
    run(['git', 'clone', '--depth', '1', '--branch', BRANCH, HTTPS_URL, str(REPO_DIR)])
else:
    print("Actualizando clon local existente...")
    r = run(['git', '-C', str(REPO_DIR), 'fetch', '--depth', '1', 'origin', BRANCH], check=False)
    if r.returncode == 0:
        run(['git', '-C', str(REPO_DIR), 'reset', '--hard', f'origin/{BRANCH}'], check=False)
    else:
        print("  Fetch fallo, re-clonando desde cero...")
        shutil.rmtree(REPO_DIR)
        run(['git', 'clone', '--depth', '1', '--branch', BRANCH, HTTPS_URL, str(REPO_DIR)])

# 4) Configurar identidad git local (requerido para commits)
run(['git', '-C', str(REPO_DIR), 'config', 'user.name', 'Dashboard Updater'], check=False)
run(['git', '-C', str(REPO_DIR), 'config', 'user.email', 'dashboard@local'], check=False)

# 5) Copiar archivos al clon
print("Copiando archivos al clon...")
copied = 0
for name, fpath in FILES_TO_UPLOAD:
    if not fpath.exists():
        print(f"  WARNING falta {fpath}, lo salto")
        continue
    shutil.copy2(fpath, REPO_DIR / name)
    sz = (REPO_DIR / name).stat().st_size
    print(f"  OK {name} ({sz / 1024 / 1024:.1f} MB)")
    copied += 1

if copied == 0:
    print("ERROR: no hay archivos para subir")
    raise SystemExit(1)

# 6) Add + commit
run(['git', '-C', str(REPO_DIR), 'add', '-A'])
ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
msg = f'Actualizacion de datos {ts}'
r = run(['git', '-C', str(REPO_DIR), 'commit', '-m', msg], check=False)
combined = (r.stdout or '') + (r.stderr or '')
if 'nothing to commit' in combined.lower():
    print("  Sin cambios para commitear (los archivos ya estan al dia).")
else:
    if r.returncode != 0:
        print(f"ERROR en commit:\n{r.stderr}")
        raise SystemExit(1)
    print(f"  OK Commit creado: {msg}")

# 7) Push (puede tardar varios min con data.js de ~88 MB)
print("Pusheando a GitHub (puede tardar 1-3 min con data.js de ~88 MB)...")
r = subprocess.run(
    ['git', '-C', str(REPO_DIR), 'push', 'origin', BRANCH],
    capture_output=False  # mostrar progreso en vivo
)
if r.returncode != 0:
    print("ERROR en git push.")
    raise SystemExit(1)

print()
print("OK Push a GitHub completado.")
print("  GitHub Pages va a propagar los cambios en 1-2 minutos.")
