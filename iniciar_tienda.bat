@echo off
title Iniciador de la Tienda
color 0A

echo ==========================================
echo    INICIANDO TIENDA ESCOLAR VIRTUAL
echo ==========================================
echo.
echo Asegurate de tener XAMPP (Apache y MySQL) encendidos.
echo Iniciando servidor...
ping 127.0.0.1 -n 4 > nul

:: Abre una nueva ventana que queda ejecutando el servidor y le pone un título específico
start "Servidor Tienda Escolar" cmd /k ".\venv\Scripts\activate && python main.py"

echo.
echo Abriendo tu navegador web en localhost:5000...
:: Esperar 2 segundos para dar tiempo a que Flask inicie
ping 127.0.0.1 -n 3 > nul
start http://localhost:5000

echo.
echo Todo listo. Puedes cerrar esta ventana.
ping 127.0.0.1 -n 4 > nul
exit
