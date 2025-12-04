# Automatyczna Migracja Bazy Danych

## Szybki Start

### Opcja 1: Skrypt PowerShell (Rekomendowany)
```powershell
cd "C:\Users\kondz\work"
.\migrate.ps1
```

### Opcja 2: Skrypt Batch
```cmd
cd "C:\Users\kondz\work"
migrate.bat
```

### Opcja 3: Manualne polecenia
```powershell
cd "C:\Users\kondz\work"

# Utwórz środowisko wirtualne (jeśli nie istnieje)
python -m venv .venv

# Aktywuj środowisko wirtualne
.\.venv\Scripts\Activate.ps1

# Zainstaluj zależności
pip install -r requirements.txt

# Utwórz migracje
python manage.py makemigrations

# Aplikuj migracje
python manage.py migrate

# Zbierz pliki statyczne
python manage.py collectstatic --noinput

# Wyświetl status migracji
python manage.py showmigrations
```

## Co robi migracja?

1. **Tworzy środowisko wirtualne** (`.venv`) - izoluje zależności Pythona
2. **Instaluje wymagane pakiety** z `requirements.txt`:
   - Django 4.2.1
   - django-rest-framework
   - dj-database-url
   - psycopg2-binary (PostgreSQL)
   - redis, whitenoise, gunicorn
   - python-dotenv (zmienne środowiskowe)

3. **Tworzy migracje** - analiza zmian w modelach i tworzenie plików migracji
4. **Aplikuje migracje** - wykonuje zmiany schematu bazy danych
5. **Zbiera pliki statyczne** - przygotowuje CSS, JS, obrazy do produkcji
6. **Wyświetla status** - pokazuje którą migracje zostały zastosowane

## Struktura migracji

```
workapp/migrations/
├── __init__.py
├── 0001_initial.py              # Początkowe modele
├── 0002_opinion_transmition...  # Opinion, Transmition, Comment
└── 0003_auto_pending_changes.py # Bieżące zmiany (checkpoint)
```

## Zmienne środowiskowe

Projekt obsługuje konfigurację przez `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_LOCAL_DB=true
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Baza danych

### SQLite (domyślnie)
- Plik: `db.sqlite3`
- Idealna do rozwoju lokalnego
- Wystarczy dla małych projektów

### PostgreSQL (produkcja)
- Ustaw `USE_LOCAL_DB=true` w `.env`
- Lub podaj `DATABASE_URL` w formacie: `postgresql://user:pass@host:5432/dbname`

## Troubleshooting

### Błąd: "ModuleNotFoundError: No module named 'django'"
```powershell
# Upewnij się, że venv jest aktywny
.\.venv\Scripts\Activate.ps1

# Zainstaluj zależności
pip install -r requirements.txt
```

### Błąd: "psycopg2 installation failed"
```powershell
# Użyj pre-built wersji
pip install psycopg2-binary
```

### Błąd: "Database already exists"
```powershell
# Usuń starą bazę (jeśli używasz SQLite)
Remove-Item db.sqlite3 -Force

# Następnie uruchom migracje ponownie
python manage.py migrate
```

### Zweryfikuj status migracji
```powershell
python manage.py showmigrations

# Pokazuje które migracje zostały zastosowane:
# [X] = zastosowana
# [ ] = oczekująca
```

## Bezpieczeństwo

⚠️ **Ważne dla produkcji:**
- Nigdy nie commituj `.env` do repozytorium
- Użyj `.env.example` jako szablonu
- Zmień `SECRET_KEY` na unikatowy, długi ciąg
- Ustaw `DEBUG=False` w produkcji
- Skonfiguruj `ALLOWED_HOSTS` z rzeczywistymi domenami

## Dalsze kroki

Po pomyślnej migracji możesz:

1. **Stworzyć superuser (admin)**
   ```powershell
   python manage.py createsuperuser
   ```

2. **Uruchomić serwer rozwojowy**
   ```powershell
   python manage.py runserver
   ```

3. **Uruchomić testy**
   ```powershell
   python manage.py test --verbosity=2
   ```

4. **Wygenerować certyfikat SSL** (lokalnie)
   ```powershell
   python generate_cert.py
   ```

## Pomoc

Jeśli napotkasz problemy:
1. Sprawdź czy Python 3.8+ jest zainstalowany: `python --version`
2. Sprawdź czy pip jest dostępny: `pip --version`
3. Przeczytaj logi migracji: `python manage.py showmigrations --plan`
4. Sprawdź dokumentację Django: https://docs.djangoproject.com/en/4.2/
