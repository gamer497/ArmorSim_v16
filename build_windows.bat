@echo off
chcp 65001 > nul
echo ===================================================
echo   Сборка 2D Armor Simulator (v16) под Windows
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден! Установите Python 3.11-3.13 с галочкой 'Add to PATH'.
    pause
    exit /b 1
)

echo [1/3] Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Компиляция ArmorSim.exe...
pyinstaller --clean --noconfirm --onefile --windowed --name "ArmorSim_v16" main.py

echo.
echo [3/3] Перемещение готового файла в папку release/...
if not exist "release" mkdir release
copy /y "dist\ArmorSim_v16.exe" "release\ArmorSim_v16.exe"

echo.
echo ===================================================
echo [УСПЕХ] Готовый файл находится в: release\ArmorSim_v16.exe
echo ===================================================
pause
