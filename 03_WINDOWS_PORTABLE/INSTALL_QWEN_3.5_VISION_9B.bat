@echo off
where ollama >nul 2>&1
if errorlevel 1 (
    echo Ollama was not found.
    echo Install Ollama first, then run this file again.
    pause
    exit /b 1
)
ollama pull fredrezones55/Qwen3.5-Uncensored-HauhauCS-Aggressive:9b
ollama list
pause
