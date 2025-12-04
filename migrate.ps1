# Automatyczna migracja bazy danych
# Automatic Database Migration Script

Write-Host "=== Django Database Migration ===" -ForegroundColor Cyan
Write-Host "Uruchamianie migracji bazy danych..." -ForegroundColor Yellow

cd "C:\Users\kondz\work"

# Check if virtual environment exists, if not create it
if (-not (Test-Path ".venv")) {
    Write-Host "Tworzenie środowiska wirtualnego..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Aktywowanie środowiska wirtualnego..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Instalowanie zależności..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Create migrations
Write-Host "Tworzenie migracji..." -ForegroundColor Yellow
python manage.py makemigrations

# Apply migrations
Write-Host "Aplikowanie migracji..." -ForegroundColor Yellow
python manage.py migrate

# Collect static files
Write-Host "Zbieranie plików statycznych..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

Write-Host "=== Migracja ukończona pomyślnie ===" -ForegroundColor Green
Write-Host "Baza danych jest gotowa do użycia!" -ForegroundColor Green

# Display migration info
Write-Host "`nInformacje o migracji:" -ForegroundColor Cyan
python manage.py showmigrations
