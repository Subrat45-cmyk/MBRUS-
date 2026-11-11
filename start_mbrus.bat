@echo off
title MBRUS AI Assistant - TALK THINK ACT
echo ========================================================
echo   Starting MBRUS Personal AI Assistant on Localhost
echo   Motto: TALK * THINK * ACT
echo   URL: http://127.0.0.1:8000
echo ========================================================
cd /d "%~dp0"
python server.py
pause
