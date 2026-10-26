@echo off
title Apagar Tienda Escolar
color 0C

echo ==========================================
echo    APAGANDO TIENDA ESCOLAR VIRTUAL
echo ==========================================
echo.
echo Deteniendo el servidor web Flask...

:: Cierra la ventana y el proceso que tenga como título "Servidor Tienda Escolar"
taskkill /FI "WINDOWTITLE eq Servidor Tienda Escolar*" /T /F >nul 2>&1

echo.
echo El servidor se ha detenido de forma segura.
echo.
echo IMPORTANTE: Recuerda presionar "Stop" en XAMPP si ya terminaste.
echo.
echo Esta ventana se cerrara en unos segundos...
ping 127.0.0.1 -n 6 > nul
exit
