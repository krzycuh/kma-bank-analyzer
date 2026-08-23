# Faza 3: n8n Orchestration

**Czas trwania:** 3 dni  
**Cel:** Automatyczna orkiestracja przez n8n + Google Sheets integration

## Przegląd

W tej fazie dodajemy n8n jako layer orkiestracyjny, który automatycznie wykrywa nowe pliki, wywołuje API i zapisuje wyniki do Google Sheets.

## Architektura

```
┌────────────── n8n Workflow ──────────────┐
│                                           │
│  1. Cron Trigger (co 6h)                 │
│           ↓                               │
│  2. List Files (/data/input/*.csv)       │
│           ↓                               │
│  3. Filter (tylko nowe pliki)            │
│           ↓                               │
│  4. Read File                             │
│           ↓                               │
│  5. HTTP Request                          │
│      POST http://api:8000/api/v1/analyze │
│           ↓                               │
│  6. Switch (success/error)                │
│           ↓                               │
│  7. Transform Data                        │
│           ↓                               │
│  8. Google Sheets Append                  │
│           ↓                               │
│  9. Move File (input → processed)         │
│           ↓                               │
│ 10. Update State                          │
│           ↓                               │
│ 11. Email Notification (optional)        │
│                                           │
└───────────────────────────────────────────┘
```

## Setup n8n

### docker-compose.yml - rozszerzenie

```yaml
version: '3.8'

services:
  api:
    # ... (bez zmian z Fazy 2)
  
  n8n:
    image: n8nio/n8n:latest
    container_name: bank-analyzer-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ../data:/data  # Ten sam folder co API
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD:-changeme}
      - GENERIC_TIMEZONE=Europe/Warsaw
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - N8N_LOG_LEVEL=info
    depends_on:
      - api
    networks:
      - bank-analyzer

networks:
  bank-analyzer:
    driver: bridge

volumes:
  n8n_data:
```

### .env rozszerzenie

```bash
# n8n credentials
N8N_USER=admin
N8N_PASSWORD=strong_password_here_change_me

# Google Sheets (opcjonalne na tym etapie)
GOOGLE_SHEETS_ID=your_sheet_id_here
```

## n8n Workflow Design

### Workflow JSON Export

Plik: `n8n/workflows/bank-statement-processor.json`

Główne nodes:

1. **Cron Trigger**
2. **List Files (Execute Command)**
3. **Filter New Files (Code)**
4. **Read File (Read Binary File)**
5. **HTTP Request (Call API)**
6. **Switch (Check Response)**
7. **Transform Data (Code)**
8. **Google Sheets (Append)**
9. **Move File (Execute Command)**
10. **Update State (Write File)**
11. **Email/Webhook (Notification)**

### Node Configurations

#### 1. Cron Trigger
```json
{
  "name": "Schedule",
  "type": "n8n-nodes-base.cron",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "hours",
          "hoursInterval": 6
        }
      ]
    },
    "triggerTimes": {
      "item": [
        {
          "mode": "everyX",
          "value": 6
        }
      ]
    }
  }
}
```

#### 2. List Files
```json
{
  "name": "List CSV Files",
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "ls /data/input/*.csv 2>/dev/null || echo 'no files'"
  }
}
```

#### 3. Filter New Files (Code Node)
```javascript
// Wczytaj state (lista już przetworzonych plików)
const stateFile = '/data/state.json';
let processedFiles = [];

try {
  const fs = require('fs');
  if (fs.existsSync(stateFile)) {
    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    processedFiles = state.processed_files || [];
  }
} catch (error) {
  console.log('No state file, starting fresh');
}

// Lista plików z poprzedniego node'a
const fileList = $input.first().json.stdout.split('\n').filter(f => f.trim());

// Filtruj tylko nowe
const newFiles = fileList.filter(file => !processedFiles.includes(file));

if (newFiles.length === 0) {
  return []; // Brak nowych plików - zakończ workflow
}

// Zwróć nowe pliki jako osobne items
return newFiles.map(file => ({ json: { filepath: file } }));
```

#### 4. Read File
```json
{
  "name": "Read CSV",
  "type": "n8n-nodes-base.readBinaryFile",
  "parameters": {
    "filePath": "={{ $json.filepath }}"
  }
}
```

#### 5. HTTP Request (Call API)
```json
{
  "name": "Analyze via API",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://api:8000/api/v1/analyze",
    "method": "POST",
    "sendBody": true,
    "contentType": "multipart-form-data",
    "bodyParameters": {
      "parameters": [
        {
          "name": "files",
          "value": "={{ $binary.data }}"
        }
      ]
    },
    "options": {
      "timeout": 300000
    }
  }
}
```

#### 6. Switch Node
```json
{
  "name": "Check Status",
  "type": "n8n-nodes-base.switch",
  "parameters": {
    "conditions": {
      "boolean": [
        {
          "value1": "={{ $json.status }}",
          "value2": "success"
        }
      ]
    }
  }
}
```

#### 7. Transform Data (Code Node)
```javascript
// Przygotuj dane do zapisu w Google Sheets
const data = $input.first().json;
const aggregated = data.aggregated_data;

const rows = [];

// Dla każdego roku i miesiąca
for (const [year, yearData] of Object.entries(aggregated.years)) {
  for (const [month, monthData] of Object.entries(yearData.months)) {
    // Dla każdej kategorii
    for (const [catMain, subcats] of Object.entries(monthData.categories)) {
      for (const [catSub, amounts] of Object.entries(subcats)) {
        rows.push({
          year: parseInt(year),
          month: parseInt(month),
          category_main: catMain,
          category_sub: catSub,
          amount: amounts.total,
          transaction_count: amounts.count,
          updated_at: new Date().toISOString()
        });
      }
    }
  }
}

return rows.map(row => ({ json: row }));
```

#### 8. Google Sheets Node
```json
{
  "name": "Append to Sheet",
  "type": "n8n-nodes-base.googleSheets",
  "parameters": {
    "operation": "append",
    "sheetId": "={{ $env.GOOGLE_SHEETS_ID }}",
    "range": "Podsumowanie!A:G",
    "options": {
      "valueInputMode": "USER_ENTERED"
    }
  },
  "credentials": {
    "googleSheetsOAuth2Api": {
      "name": "Google Sheets Account"
    }
  }
}
```

#### 9. Move File
```json
{
  "name": "Move to Processed",
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "mv {{ $node['Read CSV'].json.filepath }} /data/processed/$(basename {{ $node['Read CSV'].json.filepath }}).$(date +%Y%m%d_%H%M%S)"
  }
}
```

#### 10. Update State (Write File)
```javascript
// Code node do aktualizacji state.json
const fs = require('fs');
const stateFile = '/data/state.json';

let state = {
  last_run: new Date().toISOString(),
  processed_files: [],
  total_transactions: 0
};

// Wczytaj istniejący state
try {
  if (fs.existsSync(stateFile)) {
    state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  }
} catch (error) {
  console.log('Creating new state file');
}

// Dodaj nowy plik do listy przetworzonych
const newFile = $node['Read CSV'].json.filepath;
if (!state.processed_files.includes(newFile)) {
  state.processed_files.push(newFile);
}

// Aktualizuj statystyki
state.last_run = new Date().toISOString();
state.total_transactions += $node['Analyze via API'].json.transactions_count;

// Zapisz
fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));

return [{ json: { status: 'state updated', state } }];
```

## Google Sheets Setup

### Krok 1: Utwórz Service Account

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com)
2. Utwórz nowy projekt (lub użyj istniejącego)
3. Włącz API:
   - Google Sheets API
   - Google Drive API
4. IAM & Admin → Service Accounts → Create Service Account
5. Nazwa: `bank-analyzer-n8n`
6. Role: brak (nie potrzebne dla Sheets)
7. Create Key → JSON
8. Zapisz plik JSON

### Krok 2: Przygotuj Google Sheet

1. Utwórz nowy Google Sheet
2. Nazwa: `Bank Analyzer - Wydatki`
3. Utwórz arkusze:
   - **Podsumowanie** - główne dane
   - **Nieprzypisane** - transakcje bez kategorii
   - **Dashboard** - wykresy (ręcznie)

#### Struktura arkusza "Podsumowanie"

Nagłówki (wiersz 1):
```
| Rok | Miesiąc | Kategoria główna | Podkategoria | Kwota | Liczba transakcji | Data aktualizacji |
```

### Krok 3: Udostępnij arkusz Service Account

1. Otwórz Service Account JSON
2. Znajdź pole `client_email` (np. `bank-analyzer-n8n@project.iam.gserviceaccount.com`)
3. W Google Sheets → Share
4. Dodaj ten email z uprawnieniami **Editor**
5. Wyślij

### Krok 4: Konfiguracja w n8n

1. Otwórz n8n: http://localhost:5678
2. Login (admin / hasło z .env)
3. Settings → Credentials → New
4. Typ: **Google Sheets OAuth2 API**
5. Wybierz: **Service Account**
6. Upload JSON file z Service Account
7. Test connection
8. Save

## State Management

### state.json structure

```json
{
  "last_run": "2026-01-09T14:30:00Z",
  "processed_files": [
    "/data/input/pko_2025_12.csv",
    "/data/input/alior_2025_12.csv"
  ],
  "total_transactions": 1234,
  "last_month_stats": {
    "2025-12": {
      "total": 5678.90,
      "categorized": 154,
      "uncategorized": 2
    }
  }
}
```

## Error Handling

### Error Path w Switch Node

Jeśli API zwróci błąd:

1. **Log Error** (Write File)
   - Zapisz błąd do `/data/logs/errors.log`
   - Format: `[timestamp] [file] [error_message]`

2. **Send Alert** (Email lub Webhook)
   - Treść: "Błąd przetwarzania pliku X: Y"
   - Załącznik: log

3. **Continue** (nie przerywaj całego workflow)
   - Następne pliki są przetwarzane

### Retry Logic

HTTP Request node:
- Retry on fail: **Yes**
- Max retries: **3**
- Retry interval: **10 seconds**

## Testing Workflow

### Manual Trigger

1. n8n → Workflows → Bank Statement Processor
2. Execute Workflow (przycisk play)
3. Obserwuj execution przez UI
4. Sprawdź logi każdego node'a

### Test Cases

1. **Brak nowych plików**
   - Workflow kończy się po Filter node
   - Brak wywołania API

2. **Jeden nowy plik PKO**
   - Parsowanie OK
   - Kategoryzacja OK
   - Zapis do Sheets
   - File moved

3. **Błąd parsowania**
   - Error path aktywowany
   - Alert wysłany
   - Inne pliki dalej przetwarzane

4. **Google Sheets offline**
   - Retry 3x
   - Error logged
   - File nie przeniesiony (zostaje w input)

## Monitoring

### n8n Dashboard

- Workflows → Bank Statement Processor
- Executions (historia uruchomień)
- Kliknij execution → szczegóły każdego node'a

### Logi

```bash
# n8n logs
docker logs -f bank-analyzer-n8n

# API logs
docker logs -f bank-analyzer-api
```

### Metrics w Google Sheets

Dodaj arkusz "Metrics":
- Liczba przetworzonych plików (dzienna/miesięczna)
- Średni czas przetwarzania
- Liczba błędów
- Trend wydatków

## Dokumentacja

### README.md - update

```markdown
## n8n Orchestration

### Setup

1. Uruchom stack:
```bash
docker-compose up -d
```

2. Otwórz n8n: http://localhost:5678
3. Login: admin / hasło_z_.env
4. Import workflow: n8n/workflows/bank-statement-processor.json
5. Skonfiguruj Google Sheets credentials
6. Aktywuj workflow

### Workflow

- Automatycznie uruchamia się co 6h
- Sprawdza `/data/input` dla nowych CSV
- Wywołuje API do analizy
- Zapisuje do Google Sheets
- Archiwizuje pliki do `/data/processed`

### Ręczne uruchomienie

1. n8n → Workflows → Bank Statement Processor
2. Execute Workflow

### Monitoring

- n8n UI: http://localhost:5678
- Executions: historia wszystkich uruchomień
- Google Sheets: live updates
```

## Deliverables Fazy 3

### Checklist

- [ ] n8n dodane do docker-compose
- [ ] Workflow zaprojektowany
- [ ] Wszystkie nodes skonfigurowane
- [ ] Google Sheets setup
- [ ] Service Account działa
- [ ] State management zaimplementowany
- [ ] Error handling
- [ ] Retry logic
- [ ] Testing (manual triggers)
- [ ] Dokumentacja zaktualizowana

### Test End-to-End

1. Wrzuć plik CSV do `data/input/`
2. Zaczekaj na cron lub uruchom ręcznie
3. Sprawdź:
   - API logs (przetwarzanie OK)
   - Google Sheets (nowe dane)
   - `data/processed/` (plik przeniesiony)
   - `data/state.json` (zaktualizowany)

### Next Steps

Po zakończeniu Fazy 3 → **Faza 4: Deployment na RPI**
