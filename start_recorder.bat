@echo off
REM Automatic Activity Tracker Setup and Start
REM Save this as: setup_and_start.bat in the same folder as recorder.py

echo ============================================
echo   ACTIVITY TRACKER - AUTO SETUP
echo ============================================
echo.

cd "C:\Users\PatrickGroth\OneDrive - Logatik\Recorder_PersonalAccountabilit"

REM Create config file automatically
echo Creating configuration...
(
echo {
echo   "log_folder": "C:\\Users\\PatrickGroth\\OneDrive - Logatik\\Recorder_PersonalAccountabilit",
echo   "keystroke_interval": 15
echo }
) > tracker_config.json

echo Config created successfully!
echo.

REM Start the tracker
echo Starting Activity Tracker...
echo.
python recorder.py

pause