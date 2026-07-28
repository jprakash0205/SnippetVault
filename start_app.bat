@echo off
:: Navigate to your project directory
cd /d "C:\CODE\PasteBin"

:: Activate virtual environment (if using one)
call venv\Scripts\activate

:: Start your Flask application
python run.py >> background_terminal.log 2>&1