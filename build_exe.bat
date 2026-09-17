@echo off
SETLOCAL
echo.
echo  ==========================================
echo   picpress  ^|  Build EXE
echo  ==========================================
echo.
python --version >nul 2>&1
IF ERRORLEVEL 1 ( echo [ERROR] Python not found. & pause & exit /b 1 )
echo  [1/3]  Installing build dependencies...
python -m pip install --upgrade Pillow tkinterdnd2 pyinstaller --quiet
echo  [2/3]  Building EXE...
pyinstaller picpress.spec --noconfirm --clean
IF ERRORLEVEL 1 ( echo [ERROR] Build failed. & pause & exit /b 1 )
echo  [3/3]  Done!  EXE ready at: dist\picpress.exe
explorer dist
pause
