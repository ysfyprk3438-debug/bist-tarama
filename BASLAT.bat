@echo off
chcp 65001 >nul
title BIST Para Avcisi
echo ================================
echo   BIST Para Avcisi baslatiliyor
echo ================================
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo [HATA] Python bulunamadi.
  echo https://www.python.org/downloads/ adresinden kurun.
  echo Kurulumda "Add Python to PATH" kutusunu MUTLAKA isaretleyin.
  echo.
  pause
  exit /b
)
echo Gerekli paketler kuruluyor ^(ilk acilista birkac dakika surebilir^)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
echo.
echo Uygulama aciliyor... Tarayicida otomatik acilacak.
echo Kapatmak icin bu pencereyi kapatin.
echo.
python -m streamlit run app.py
pause
