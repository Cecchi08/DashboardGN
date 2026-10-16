@echo off
setlocal enabledelayedexpansion
REM ===============================================================
REM Sube los dashboards a Cloudflare Pages + GitHub Pages
REM   - JS pesados (data.js, aging.js, chart.umd.js) -> GitHub Pages
REM   - HTMLs livianos (index.html, vendedores.html)  -> Cloudflare
REM Pre-requisitos (una sola vez): seguir LEEME-CLOUDFLARE.md
REM Uso: doble-click DESPUES de actualizar.bat
REM ===============================================================

cd /d "%~dp0..\.."
echo.
echo ===============================================================
echo   SUBIR DASHBOARDS A CLOUDFLARE PAGES + GITHUB PAGES
echo ===============================================================
echo.

REM ---------------------------------------------------------------
REM Verificar que existe .cloudflare-config.json
REM ---------------------------------------------------------------
if not exist "config\.cloudflare-config.json" (
    echo ERROR: no encuentro el archivo .cloudflare-config.json
    echo.
    echo Ese archivo tiene la config del deploy ^(proyecto Cloudflare,
    echo repo de GitHub, URL de los datos^). Ver LEEME-CLOUDFLARE.md.
    echo.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------
REM Detectar Python real ^(no el stub de Microsoft Store^)
REM ---------------------------------------------------------------
set PYTHON=
where py >nul 2>nul
if not errorlevel 1 (
    py --version >nul 2>nul
    if not errorlevel 1 set PYTHON=py
)
if "!PYTHON!"=="" (
    where python >nul 2>nul
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
        echo !PYVER! | findstr /C:"Python" >nul
        if not errorlevel 1 set PYTHON=python
    )
)
if "!PYTHON!"=="" (
    echo ERROR: Python no esta instalado. Instalalo desde python.org primero.
    pause
    exit /b 1
)
echo Python detectado.

REM ---------------------------------------------------------------
REM Verificar Node.js v22+ ^(Wrangler exige v22 o superior^)
REM ---------------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado.
    echo.
    echo Instalalo desde: https://nodejs.org/  ^(version LTS, la verde^)
    echo Despues de instalar, cerra y abri el CMD y volve a correr este .bat
    echo.
    pause
    start https://nodejs.org/
    exit /b 1
)
for /f "tokens=1 delims=." %%v in ('node --version') do set NODEMAJOR=%%v
set NODEMAJOR=!NODEMAJOR:v=!
if !NODEMAJOR! LSS 22 (
    echo ERROR: Wrangler necesita Node.js v22 o superior.
    node --version
    echo Actualiza Node desde https://nodejs.org/ ^(version LTS^).
    echo.
    pause
    start https://nodejs.org/
    exit /b 1
)
echo Node.js detectado:
node --version
echo.

REM ---------------------------------------------------------------
REM Verificar Git ^(necesario para el push de los JS a GitHub^)
REM ---------------------------------------------------------------
where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: Git no esta instalado.
    echo.
    echo Instalalo desde: https://git-scm.com/download/win
    echo Despues de instalar, cerra y abri el CMD y volve a correr este .bat
    echo.
    pause
    start https://git-scm.com/download/win
    exit /b 1
)
echo Git detectado:
git --version

REM ---------------------------------------------------------------
REM Verificar GitHub CLI ^(gh^) — actua de helper de credenciales git
REM ---------------------------------------------------------------
where gh >nul 2>nul
if errorlevel 1 (
    echo ERROR: GitHub CLI ^(gh^) no esta instalado.
    echo.
    echo Instalalo desde: https://cli.github.com/
    echo Despues corre en el CMD:  gh auth login
    echo ^(elegi HTTPS y logueate con tu cuenta pabrivarola-jpg^)
    echo Luego volve a correr este .bat
    echo.
    pause
    start https://cli.github.com/
    exit /b 1
)
echo GitHub CLI detectado:
gh --version | findstr /I "gh version"
echo.

REM Verificar que gh este logueado
gh auth status >nul 2>nul
if errorlevel 1 (
    echo No estas logueado en GitHub. Abro el login...
    call gh auth login
    if errorlevel 1 (
        echo ERROR: no se completo el login de GitHub.
        pause
        exit /b 1
    )
)

REM ---------------------------------------------------------------
REM Verificar / instalar Wrangler ^(CLI de Cloudflare^) globalmente
REM ---------------------------------------------------------------
where wrangler >nul 2>nul
if errorlevel 1 (
    echo Wrangler no instalado. Lo instalo ahora ^(solo la primera vez^)...
    call npm install -g wrangler
    if errorlevel 1 (
        echo ERROR al instalar wrangler.
        echo Intenta manualmente desde CMD:
        echo   npm install -g wrangler
        pause
        exit /b 1
    )
)
echo Wrangler listo:
call wrangler --version
echo.

REM ---------------------------------------------------------------
REM Leer el nombre del proyecto Cloudflare desde el config
REM ---------------------------------------------------------------
for /f "usebackq delims=" %%p in (`!PYTHON! -c "import json; print(json.load(open('config/.cloudflare-config.json'))['pagesProject'])"`) do set PROJECT=%%p
if "!PROJECT!"=="" (
    echo ERROR: no pude leer 'pagesProject' de .cloudflare-config.json
    pause
    exit /b 1
)
echo Proyecto Cloudflare Pages: !PROJECT!
echo.

REM ===============================================================
REM PASO 1 — Preparar los HTMLs apuntando a las URLs de GitHub Pages
REM ===============================================================
echo --- [1/3] Preparando HTMLs ^(dist/cloudflare^) ---
!PYTHON! scripts\deploy\preparar_para_cloudflare.py
if errorlevel 1 (
    echo ERROR preparando dist/cloudflare
    pause
    exit /b 1
)
echo.

REM ===============================================================
REM PASO 2 — Subir los JS pesados a GitHub ^(git push^)
REM ===============================================================
echo --- [2/3] Subiendo data.js / aging.js / chart.umd.js a GitHub ---
echo     ^(puede tardar 1-3 min por el data.js de ~88 MB^)
!PYTHON! scripts\deploy\subir_a_github.py
if errorlevel 1 (
    echo ERROR subiendo los JS a GitHub
    pause
    exit /b 1
)
echo.

REM ===============================================================
REM PASO 3 — Deploy de los HTMLs livianos a Cloudflare Pages
REM ===============================================================
echo --- [3/3] Subiendo HTMLs a Cloudflare Pages ---
call wrangler pages deploy "dist\cloudflare" --project-name=!PROJECT! --branch=main
if errorlevel 1 (
    echo.
    echo ERROR durante el deploy a Cloudflare. Revisa el mensaje arriba.
    echo ^(Si te pide login, se abre el navegador la primera vez.^)
    pause
    exit /b 1
)

echo.
echo ===============================================================
echo   ^> Subida completa
echo ===============================================================
echo.
echo Tu dashboard esta en:
echo   https://nucleo-ventas.pages.dev              ^(con precios^)
echo   https://nucleo-ventas.pages.dev/vendedores   ^(sin precios^)
echo.
echo GitHub Pages tarda 1-2 min en propagar los datos nuevos.
echo Avisale al equipo que refresque con Ctrl+F5.
echo.
pause
endlocal
