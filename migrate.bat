@echo off
REM Automatyczna migracja bazy danych
REM Automatic Database Migration Script

echo === Django Database Migration ===
echo Uruchamianie migracji bazy danych...

cd /d "C:\Users\kondz\work"

REM Check if virtual environment exists
if not exist ".venv" (
    echo Tworzenie srodowiska wirtualnego...
    python -m venv .venv
)

REM Activate virtual environment
echo Aktywowanie srodowiska wirtualnego...
call .venv\Scripts\activate.bat

REM Install requirements
echo Instalowanie zaleznosci...
pip install -q -r requirements.txt

REM Create migrations
echo Tworzenie migracji...
python manage.py makemigrations

REM Apply migrations
echo Aplikowanie migracji...
python manage.py migrate

REM Collect static files
echo Zbieranie plikow statycznych...
python manage.py collectstatic --noinput

echo.
echo === Migracja ukonczena pomyslnie ===
echo Baza danych jest gotowa do uzycia!

REM Display migration info
echo.
echo Informacje o migracji:
python manage.py showmigrations

pause
