@echo off
cd /d "%~dp0"
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --fp8_e4m3fn-text-enc --fast-disk
pause
