@echo off
cd /d "%~dp0.."
title Cotizador - Actualizacion automatica (dejar abierto)
call npm run watch
echo.
echo La vigilancia se detuvo.
pause
