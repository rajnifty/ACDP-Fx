@echo off
TITLE ACDP FX Leaders - Dashboard
color 0A

:: This sets the execution path to the folder where this .bat file is located
cd /d "%~dp0"

echo =========================================================
echo         ACDP FX LEADERS DASHBOARD
echo         Built for Rajan Yadav
echo =========================================================
echo.
echo Initializing the FX Quant Engine and booting up Streamlit...
echo Please wait...
echo.

:: Replace 'acdp_fx.py' with the actual name of your new FX Python file
python -m streamlit run acdp_fx.py

:: Keeps the command prompt open if an error occurs
pause