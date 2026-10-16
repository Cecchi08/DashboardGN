@echo off
cd /d "%~dp0.."
echo ================================
echo  Actualizando Cotizador...
echo ================================
echo.
call npm run build
echo.
if %ERRORLEVEL% NEQ 0 (
  echo *** ERROR al actualizar. Revisa el mensaje de arriba. ***
  echo.
  pause
  exit /b 1
)
echo.
echo Abriendo cotizador.html en el navegador...
start "" "dist\cotizador.html"
exit /b 0
