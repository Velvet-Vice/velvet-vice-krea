@echo off
echo VELVET VICE - KREA legacy duplicate cleanup
echo Close ComfyUI before continuing.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Cleanup-Legacy-KREA-Installs.ps1"
pause
