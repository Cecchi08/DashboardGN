@echo off
setlocal enabledelayedexpansion
REM ===============================================================
REM Sube los dashboards a Azure Static Web Apps
REM Pre-requisitos (una sola vez): seguir LEEME-AZURE.md
REM Uso: doble-click despues de actualizar.bat
REM ===============================================================

cd /d "%~dp0..\.."
echo.
echo ===============================================================
echo   SUBIR DASHBOARDS A AZURE STATIC WEB APPS
echo ===============================================================
echo.

REM ---------------------------------------------------------------
REM Verificar que existe .azure-config.json (datos del SWA)
REM ---------------------------------------------------------------
if not exist "config\.azure-config.json" (
    echo ERROR: no encuentro el archivo .azure-config.json
    echo.
    echo Antes de subir por primera vez tenes que:
    echo   1. Crear el Static Web App en Azure ^(ver LEEME-AZURE.md^)
    echo   2. Crear el archivo .azure-config.json con tu tenantId y deploymentToken
    echo.
    echo Ejemplo de .azure-config.json:
    echo {
    echo   "tenantId": "00000000-0000-0000-0000-000000000000",
    echo   "deploymentToken": "PEGAR-AQUI-EL-TOKEN-DEL-PORTAL-AZURE"
    echo }
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

REM ---------------------------------------------------------------
REM Verificar Node.js ^(necesario para Azure SWA CLI^)
REM ---------------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado.
    echo.
    echo Instalalo desde: https://nodejs.org/
    echo Bajate la version "LTS" ^(la grande verde^), instalador para Windows.
    echo Despues de instalar, volve a correr este .bat
    echo.
    pause
    start https://nodejs.org/
    exit /b 1
)
echo Node.js detectado:
node --version
echo.

REM ---------------------------------------------------------------
REM Verificar / instalar Azure SWA CLI globalmente
REM ---------------------------------------------------------------
where swa >nul 2>nul
if errorlevel 1 (
    echo Azure SWA CLI no instalado. Lo instalo ahora ^(solo la primera vez^)...
    call npm install -g @azure/static-web-apps-cli
    if errorlevel 1 (
        echo ERROR al instalar @azure/static-web-apps-cli
        echo Intenta manualmente desde CMD ^(o PowerShell como admin^):
        echo   npm install -g @azure/static-web-apps-cli
        pause
        exit /b 1
    )
)
echo Azure SWA CLI listo.
echo.

REM ---------------------------------------------------------------
REM Preparar carpeta dist con los HTMLs + JS + config
REM ---------------------------------------------------------------
echo --- Preparando paquete a subir ---
!PYTHON! scripts\deploy\preparar_para_azure.py
if errorlevel 1 (
    echo ERROR preparando dist/azure
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------
REM Leer deploymentToken del config y deployar
REM ---------------------------------------------------------------
echo --- Subiendo a Azure Static Web Apps ---
for /f "usebackq delims=" %%t in (`!PYTHON! -c "import json; print(json.load(open('config/.azure-config.json'))['deploymentToken'])"`) do set TOKEN=%%t

if "!TOKEN!"=="" (
    echo ERROR: no pude leer el deploymentToken del archivo .azure-config.json
    pause
    exit /b 1
)

call swa deploy "dist\azure" --env production --deployment-token !TOKEN!
if errorlevel 1 (
    echo.
    echo ERROR durante el deploy. Revisa el mensaje arriba.
    pause
    exit /b 1
)

echo.
echo ===============================================================
echo   ^& Subida completa
echo ===============================================================
echo.
echo Los dashboards ya estan online. Compartile a tu equipo el link
echo de Azure ^(lo encontras en el Portal Azure ^> tu Static Web App ^>
echo Overview ^> URL^).
echo.
echo Solo gente de tu organizacion ^(tenant^) podra entrar — los demas
echo veran un error de login.
echo.
pause
endlocal
