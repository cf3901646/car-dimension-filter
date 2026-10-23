@echo off
title Car Dimension Filter - Autohome Image Proxy Server
cd /d "%~dp0"
echo Starting Car Dimension Filter Server...
python server.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Server stopped with error code %ERRORLEVEL%.
)
pause
