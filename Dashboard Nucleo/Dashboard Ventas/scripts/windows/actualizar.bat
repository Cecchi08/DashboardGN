@echo off
setlocal enabledelayedexpansion
REM Actualizador de Dashboards Ventas Nucleo — Windows
REM Doble-click este archivo para actualizar los HTMLs con los Excel nuevos.

cd /d "%~dp0..\.."
echo.
echo ================================================================
echo   ACTUALIZADOR DASHBOARD VENTAS NUCLEO
echo ================================================================
echo.

REM ================================================================
REM Detectar Python REAL (no el stub de Microsoft Store de Windows 11)
REM El stub imprime "no se encontro Python; ejecutar sin argumentos..."
REM cuando corres "python". Un Python real responde a "python --version".
REM ================================================================

set PYTHON=
set PYTHON_OK=0

REM Probar "py" primero (launcher oficial, no tiene stub)
where py >nul 2>nul
if not errorlevel 1 (
    py --version >nul 2>nul
    if not errorlevel 1 (
        set PYTHON=py
        set PYTHON_OK=1
    )
)

REM Si "py" no anduvo, probar "python" pero verificando que sea real
if "!PYTHON_OK!"=="0" (
    where python >nul 2>nul
    if not errorlevel 1 (
        REM Capturar la salida para detectar el stub
        for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
        echo !PYVER! | findstr /C:"Python" >nul
        if not errorlevel 1 (
            set PYTHON=python
            set PYTHON_OK=1
        )
    )
)

if "!PYTHON_OK!"=="0" (
    echo ERROR: Python no esta instalado en esta PC.
    echo.
    echo  NO INSTALES DESDE MICROSOFT STORE — usa el instalador oficial:
    echo.
    echo   1^) Abri este link en tu navegador:
    echo      https://www.python.org/downloads/
    echo.
    echo   2^) Descarga "Windows installer (64-bit)" de la ultima version
    echo      estable (ej: Python 3.12^).
    echo.
    echo   3^) CRITICO: cuando corras el instalador, marca
    echo      la casilla "Add python.exe to PATH" al principio.
    echo      Despues tocas "Install Now".
    echo.
    echo   4^) Cuando termine la instalacion, volve a ejecutar
    echo      este actualizar.bat.
    echo.
    echo  Si queres, presiona cualquier tecla y te abro la pagina de descarga...
    pause >nul
    start https://www.python.org/downloads/
    exit /b 1
)

echo Python detectado: !PYTHON!
!PYTHON! --version
echo.

REM ================================================================
REM Verificar openpyxl (dependencia para leer Excel)
REM ================================================================
!PYTHON! -c "import openpyxl" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependencia openpyxl ^(solo la primera vez^)...
    !PYTHON! -m pip install openpyxl
    if errorlevel 1 (
        echo.
        echo ERROR al instalar openpyxl. Probablemente falta pip o no hay conexion a internet.
        echo.
        echo Intenta manualmente desde el CMD:
        echo   !PYTHON! -m pip install openpyxl
        echo.
        pause
        exit /b 1
    )
    echo openpyxl instalado OK.
    echo.
)

REM ================================================================
REM Correr el actualizador
REM ================================================================
!PYTHON! scripts\update\actualizar.py
if errorlevel 1 (
    echo.
    echo ERROR durante la actualizacion. Revisa el mensaje arriba.
    pause
    exit /b 1
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
endlocal
