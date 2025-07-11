@echo off
REM Script to run CSV loader and save output for review on Windows

REM Create logs directory if it doesn't exist
if not exist csv_loader_logs mkdir csv_loader_logs

REM Generate timestamp for unique log file
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set LOG_FILE=csv_loader_logs\csv_load_%TIMESTAMP%.log

REM Run the CSV loader with all arguments passed through
echo Starting CSV loader at %date% %time% > "%LOG_FILE%"
echo Command: python load_csv_to_ims.py %* >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

python load_csv_to_ims.py %* >> "%LOG_FILE%" 2>&1

echo ======================================== >> "%LOG_FILE%"
echo Completed at %date% %time% >> "%LOG_FILE%"

REM Copy to latest.log for easy access
copy /Y "%LOG_FILE%" csv_loader_logs\latest.log > nul

echo.
echo Log saved to: %LOG_FILE%
echo View latest log: csv_loader_logs\latest.log
echo.
echo To share this log:
echo   git add csv_loader_logs\latest.log
echo   git commit -m "CSV loader results from %TIMESTAMP%"
echo   git push