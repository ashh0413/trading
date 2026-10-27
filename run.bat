@echo off
REM run_all.bat — double-click or run from terminal
title Nifty 213 Scanner
cd /d "%~dp0"
call activate py311
python scanner_v2.py
python scorer.py
python report.py
echo.
echo === Pipeline done. Open dashboard.html in your browser. ===
pause
