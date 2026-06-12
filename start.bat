@echo off
chcp 65001 >nul
echo.
echo ====================================
echo  puromputan - startup
echo ====================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found!
    echo Please install from https://www.python.org/
        exit /b 1
)
echo Python OK!
echo.
echo Installing libraries...
pip install -r requirements.txt -q
echo.
echo Starting app...
python app.py
if %errorlevel% neq 0 (
    echo.
    echo *** エラーが発生したよ！上のメッセージをくろっぴに貼ってね ***
    pause
)
