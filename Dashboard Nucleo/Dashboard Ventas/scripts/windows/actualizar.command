#!/bin/bash
# Actualizador de Dashboards Ventas Núcleo (Mac / Linux)
# Doble-click este archivo para actualizar los HTMLs con los Excel nuevos

cd "$(dirname "$0")/../.."

echo ""
echo "================================================================"
echo "  ACTUALIZADOR DASHBOARD VENTAS NÚCLEO"
echo "================================================================"
echo ""

# Detectar Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 no está instalado."
    echo ""
    echo "Instalalo desde https://www.python.org/downloads/"
    echo ""
    read -p "Presioná ENTER para cerrar..."
    exit 1
fi

# Verificar openpyxl
$PYTHON -c "import openpyxl" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Instalando dependencia openpyxl..."
    $PYTHON -m pip install openpyxl
    if [ $? -ne 0 ]; then
        echo "ERROR al instalar openpyxl."
        read -p "Presioná ENTER para cerrar..."
        exit 1
    fi
fi

# Correr el actualizador
$PYTHON scripts/update/actualizar.py
RESULT=$?

echo ""
if [ $RESULT -ne 0 ]; then
    echo "ERROR durante la actualización."
fi
read -p "Presioná ENTER para cerrar esta ventana..."
exit $RESULT
