@echo off
echo ==========================================
echo   🚀 FitApp Premium - Starting Server...
echo ==========================================
echo.

:: Kontrola, ci je Python nainstalovany
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python nebol najdeny! Prosim nainstaluj Python.
    pause
    exit /b
)

:: Spustenie aplikacie
echo Aplikacia pobezi na: http://127.0.0.1:8080
echo Pre ukoncenie zavri toto okno alebo stlac Ctrl+C.
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Aplikacia skoncila s chybou.
    pause
)
