@echo off
:: Ollama LLM Server Startup Script
:: This file is placed in the Windows Startup folder:
::   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
:: It auto-starts the Ollama backend server at logon.

echo Starting Ollama LLM server...
start "" /B "C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe" serve
timeout /t 3 /nobreak >nul
echo Ollama is running on http://localhost:11434
