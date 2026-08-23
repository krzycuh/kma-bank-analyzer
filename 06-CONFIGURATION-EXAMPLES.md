# Przykłady plików konfiguracyjnych

## config/categories.yaml

**Pełna struktura kategorii:**

```yaml
categories:
  - name: "Dom i mieszkanie"
    subcategories:
      - "Czynsz/hipoteka"
      - "Media (prąd, gaz, woda)"
      - "Wyposażenie domu"
      - "Naprawy i konserwacja"
      - "Środki czystości"

  - name: "Transport"
    subcategories:
      - "Paliwo"
      - "Komunikacja miejska"
      - "Taxi/Uber"
      - "Serwis pojazdu"
      - "Ubezpieczenie pojazdu"
      - "Parkingi i opłaty drogowe"
      - "Wypożyczalnie"

  - name: "Jedzenie"
    subcategories:
      - "Zakupy spożywcze"
      - "Restauracje"
      - "Kawiarnie"
      - "Jedzenie na wynos"
      - "Kantyna/stołówka"

  - name: "Zdrowie"
    subcategories:
      - "Lekarze i specjaliści"
      - "Apteka"
      - "Suplementy i witaminy"
      - "Ubezpieczenie zdrowotne"
      - "Badania i diagnostyka"
      - "Fizjoterapia"

  - name: "Rozrywka"
    subcategories:
      - "Kino/teatr/koncerty"
      - "Hobby i zainteresowania"
      - "Wyjścia towarzyskie"
      - "Gry i aplikacje"
      - "Sport i fitness"
      - "Wakacje i wyjazdy"

  - name: "Edukacja i rozwój"
    subcategories:
      - "Kursy i szkolenia"
      - "Książki"
      - "Konferencje i eventy"
      - "Oprogramowanie edukacyjne"
      - "Korepetycje"

  - name: "Ubrania i akcesoria"
    subcategories:
      - "Odzież"
      - "Obuwie"
      - "Akcesoria modowe"
      - "Biżuteria i zegarki"

  - name: "Subskrypcje i abonamenty"
    subcategories:
      - "Streaming (Netflix, Spotify, HBO)"
      - "Telefon i internet"
      - "Oprogramowanie i cloud"
      - "Czasopisma i prasa"
      - "Członkostwa i składki"

  - name: "Dzieci"
    subcategories:
      - "Przedszkole/szkoła"
      - "Zajęcia dodatkowe"
      - "Odzież i obuwie"
      - "Zabawki i gry"
      - "Artykuły higieniczne"

  - name: "Zwierzęta"
    subcategories:
      - "Karma i przysmaki"
      - "Weterynarz"
      - "Akcesoria dla zwierząt"
      - "Pielęgnacja"

  - name: "Oszczędności i inwestycje"
    subcategories:
      - "Lokaty"
      - "Fundusze inwestycyjne"
      - "Akcje i obligacje"
      - "Kryptowaluty"
      - "Emerytura/PPE/IKE"

  - name: "Prezenty i okazje"
    subcategories:
      - "Prezenty urodzinowe"
      - "Prezenty świąteczne"
      - "Kwiaty i upominki"
      - "Darowizny i zbiórki"

  - name: "Inne wydatki"
    subcategories:
      - "Opłaty bankowe"
      - "Opłaty pocztowe"
      - "Ubezpieczenia inne"
      - "Kary i mandaty"
      - "Nieprzypisane"
```

## config/rules.yaml

**Przykładowy zestaw ~50 reguł dla polskich sklepów/usług:**

```yaml
rules:
  # ==================== JEDZENIE ====================
  
  # Sieci spożywcze
  - name: "biedronka"
    pattern: "biedronka"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "lidl"
    pattern: "lidl"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "kaufland"
    pattern: "kaufland"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "carrefour"
    pattern: "carrefour"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "auchan"
    pattern: "auchan"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "zabka"
    pattern: "^zabka|zab.*ka"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "delikatesy"
    pattern: "delikatesy"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "frisco"
    pattern: "frisco"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  # Restauracje fast food
  - name: "mcdonalds"
    pattern: "mcdonald|mc donald"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Restauracje"

  - name: "kfc"
    pattern: "^kfc"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Restauracje"

  - name: "subway"
    pattern: "subway"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Restauracje"

  - name: "pizza_hut"
    pattern: "pizza hut"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Restauracje"

  # Dostawy jedzenia
  - name: "uber_eats"
    pattern: "uber.*eats"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Jedzenie"
    category_sub: "Jedzenie na wynos"

  - name: "pyszne_pl"
    pattern: "pyszne\\.pl"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Jedzenie"
    category_sub: "Jedzenie na wynos"

  - name: "wolt"
    pattern: "wolt"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Jedzenie"
    category_sub: "Jedzenie na wynos"

  # ==================== TRANSPORT ====================
  
  # Stacje benzynowe
  - name: "orlen"
    pattern: "^orlen|pko orlen"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  - name: "bp"
    pattern: "^bp-|^bp "
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  - name: "shell"
    pattern: "^shell"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  - name: "circle_k"
    pattern: "circle k"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  - name: "lotos"
    pattern: "lotos"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  # Taxi i transport
  - name: "uber"
    pattern: "uber"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Transport"
    category_sub: "Taxi/Uber"

  - name: "bolt"
    pattern: "bolt"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Transport"
    category_sub: "Taxi/Uber"

  - name: "free_now"
    pattern: "free now|freenow"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Transport"
    category_sub: "Taxi/Uber"

  - name: "jakdojade"
    pattern: "jakdojade"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Transport"
    category_sub: "Komunikacja miejska"

  # ==================== SUBSKRYPCJE ====================
  
  - name: "netflix"
    pattern: "netflix"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Streaming (Netflix, Spotify, HBO)"

  - name: "spotify"
    pattern: "spotify"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Streaming (Netflix, Spotify, HBO)"

  - name: "hbo"
    pattern: "hbo"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Streaming (Netflix, Spotify, HBO)"

  - name: "disney_plus"
    pattern: "disney"
    field: "description"
    match_type: "contains"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Streaming (Netflix, Spotify, HBO)"

  - name: "youtube_premium"
    pattern: "youtube.*premium"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Streaming (Netflix, Spotify, HBO)"

  - name: "apple_services"
    pattern: "apple\\.com/bill"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Oprogramowanie i cloud"

  - name: "google_one"
    pattern: "google.*storage|google one"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 15
    category_main: "Subskrypcje i abonamenty"
    category_sub: "Oprogramowanie i cloud"

  # ==================== ZDROWIE ====================
  
  - name: "apteka"
    pattern: "apteka"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Zdrowie"
    category_sub: "Apteka"

  - name: "gemini_apteka"
    pattern: "gemini"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Zdrowie"
    category_sub: "Apteka"

  - name: "doz"
    pattern: "^doz"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Zdrowie"
    category_sub: "Apteka"

  # ==================== ODZIEŻ ====================
  
  - name: "reserved"
    pattern: "reserved"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Ubrania i akcesoria"
    category_sub: "Odzież"

  - name: "zara"
    pattern: "zara"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Ubrania i akcesoria"
    category_sub: "Odzież"

  - name: "hm"
    pattern: "^h&m|h&m |hennes"
    field: "counterparty"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Ubrania i akcesoria"
    category_sub: "Odzież"

  # ==================== SPORT ====================
  
  - name: "decathlon"
    pattern: "decathlon"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Rozrywka"
    category_sub: "Sport i fitness"

  - name: "silownia"
    pattern: "siłownia|silownia|fitness|gym"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 10
    category_main: "Rozrywka"
    category_sub: "Sport i fitness"

  # ==================== ROZRYWKA ====================
  
  - name: "cinema_city"
    pattern: "cinema city"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Rozrywka"
    category_sub: "Kino/teatr/koncerty"

  - name: "multikino"
    pattern: "multikino"
    field: "counterparty"
    match_type: "contains"
    case_sensitive: false
    priority: 10
    category_main: "Rozrywka"
    category_sub: "Kino/teatr/koncerty"

  # ==================== INNE ====================
  
  - name: "oplata_bankowa"
    pattern: "opłata.*kart|prowadzenie.*rachunk"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 20
    category_main: "Inne wydatki"
    category_sub: "Opłaty bankowe"

  - name: "przelew_wewnetrzny"
    pattern: "przelew.*oszczędnościowy|na lokatę"
    field: "description"
    match_type: "regex"
    case_sensitive: false
    priority: 25
    category_main: "Oszczędności i inwestycje"
    category_sub: "Lokaty"
```

## config/banks_formats.yaml

**Konfiguracja formatów banków (dla parserów):**

```yaml
pko:
  bank_name: "PKO BP"
  identifier:
    type: "first_column"
    value: "Data operacji"
  
  encoding: "windows-1250"
  encoding_fallback: "utf-8"
  separator: ","
  skip_rows: 0
  headers_row: 0
  
  date_column: 0
  date_format: "%Y-%m-%d"
  
  amount_column: 4
  decimal_separator: "."
  
  columns_mapping:
    date: 0
    transaction_type: 2
    amount: 4
    currency: 5
    balance: 6
    description_parts: [7, 8, 9, 10, 11]
  
  extraction_rules:
    counterparty:
      - field: 9
        pattern: "Nazwa odbiorcy:\\s*(.+)"
        priority: 1
      - field: 8
        pattern: "Adres:\\s*([^M]+?)(?=\\s*Miasto:|$)"
        priority: 2
      - field: 7
        pattern: "Tytuł:\\s*(.+)"
        priority: 3

alior:
  bank_name: "Alior Bank"
  identifier:
    type: "second_line_pattern"
    value: "Data transakcji;Data księgowania"
  
  encoding: "utf-8"
  separator: ";"
  skip_rows: 1
  headers_row: 1
  
  date_column: 0
  date_format: "%d-%m-%Y"
  
  amount_column: 5
  decimal_separator: ","
  
  columns_mapping:
    date: 0
    booking_date: 1
    sender: 2
    recipient: 3
    description: 4
    amount: 5
    currency: 6
    amount_account_currency: 7
    account_currency: 8
  
  extraction_rules:
    counterparty:
      - field: "sender"
        priority: 1
      - field: "recipient"
        priority: 2
      - field: "description"
        pattern: "^(.+?)\\s+PL\\s*$"
        priority: 3
```

## data/manual_overrides.yaml

**Przykład ręcznych nadpisań:**

```yaml
overrides:
  - transaction_id: "a1b2c3d4e5f67890"
    category_main: "Transport"
    category_sub: "Taxi/Uber"
    note: "Nietypowy opis Ubera bez słowa 'uber'"
    date_added: "2026-01-09"

  - transaction_id: "xyz123abc456def7"
    category_main: "Rozrywka"
    category_sub: "Hobby i zainteresowania"
    note: "Sklep modelarski - niezidentyfikowany automatycznie"
    date_added: "2026-01-08"

  - transaction_id: "qwerty123456"
    category_main: "Prezenty i okazje"
    category_sub: "Prezenty urodzinowe"
    note: "Prezent dla kolegi"
    date_added: "2026-01-07"
```

## .env.example

**Szablon zmiennych środowiskowych:**

```bash
# ==============================================
# kma-bank-analyzer - Environment Configuration
# ==============================================

# n8n Credentials
N8N_USER=admin
N8N_PASSWORD=change_me_to_strong_password

# Google Sheets (opcjonalne)
GOOGLE_SHEETS_ID=

# Timezone
TZ=Europe/Warsaw

# Logging
LOG_LEVEL=INFO
LOG_ROTATION=monthly
LOG_MAX_SIZE_MB=10

# Paths (relative to project root)
DATA_DIR=./data
CONFIG_DIR=./config
LOGS_DIR=./logs

# Scheduler (n8n cron format)
SCHEDULE_CRON=0 */6 * * *

# Email notifications (opcjonalne)
ENABLE_EMAIL=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_TO=

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Feature flags
ENABLE_GOOGLE_SHEETS=false
ENABLE_WEB_UI=false
```

## .gitignore

**Co wykluczyć z repo:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Data files (SENSITIVE!)
data/
*.csv
*.xlsx
*.xls
!tests/fixtures/*.csv
!tests/fixtures/*.xlsx

# Configuration files (SENSITIVE!)
config/categories.yaml
config/rules.yaml
.bank-analyzer.yaml
.env
docker-compose.yml
docker-compose.prod.yml

# Logs
logs/
*.log

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Backups
backups/
*.backup
*.tar.gz
*.zip

# n8n
n8n_data/

# Temporary files
tmp/
temp/
*.tmp
```

## docker-compose.yml.example

**Szablon do skopiowania:**

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    container_name: bank-analyzer-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    restart: unless-stopped

  n8n:
    image: n8nio/n8n:latest
    container_name: bank-analyzer-n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ./data:/data
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
      - GENERIC_TIMEZONE=Europe/Warsaw
    depends_on:
      - api

volumes:
  n8n_data:
```

## pytest.ini

**Konfiguracja testów:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    --verbose
    --strict-markers
    --cov=bank_analyzer
    --cov=api
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## setup.cfg

**Konfiguracja narzędzi:**

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,build,dist
ignore = E203, W503

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
ignore_missing_imports = True

[coverage:run]
source = bank_analyzer,api
omit = tests/*,*/__init__.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```
