# kma-bank-analyzer - Kompletny Plan Implementacji

**Data utworzenia:** 2026-01-09  
**Wersja:** 1.0 - Final  
**Status:** Gotowy do implementacji

## 📋 Spis treści

1. [00-PROJECT-OVERVIEW.md](00-PROJECT-OVERVIEW.md) - Przegląd projektu i architektura
2. [01-PHASE1-PYTHON-CLI.md](01-PHASE1-PYTHON-CLI.md) - Faza 1: Python CLI Library
3. [02-PHASE2-FASTAPI-DOCKER.md](02-PHASE2-FASTAPI-DOCKER.md) - Faza 2: FastAPI + Docker + CI/CD
4. [03-PHASE3-N8N-ORCHESTRATION.md](03-PHASE3-N8N-ORCHESTRATION.md) - Faza 3: n8n Orchestration
5. [04-PHASE4-DEPLOYMENT.md](04-PHASE4-DEPLOYMENT.md) - Faza 4: Production Deployment na RPI
6. [05-DATA-STRUCTURES.md](05-DATA-STRUCTURES.md) - Struktury danych i formaty
7. [06-CONFIGURATION-EXAMPLES.md](06-CONFIGURATION-EXAMPLES.md) - Przykłady konfiguracji

## 🎯 Cel projektu

Automatyzacja analizowania wyciągów bankowych z:
- Parsowaniem różnych formatów CSV (PKO, Alior, możliwość rozbudowy)
- Kategoryzacją transakcji według reguł
- Agregacją wydatków według kategorii i miesięcy
- Eksportem do Excel i Google Sheets
- Automatycznym przetwarzaniem przez n8n

## 🏗️ Architektura finalna

```
┌─────────────────────────────────────────────────────────┐
│                         n8n                              │
│  (Orchestration, Scheduling, Google Sheets)             │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP
                  ↓
┌─────────────────────────────────────────────────────────┐
│              Python Microservice (FastAPI)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │           bank_analyzer (core library)           │  │
│  │  Parsers → Categorizer → Aggregator → Exporter  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📅 Harmonogram

### **Faza 1: Python CLI** (2 tygodnie)
- Parsery PKO i Alior
- System kategoryzacji (reguły)
- Agregacja i eksport do Excel
- CLI interface
- Testy

### **Faza 2: FastAPI + Docker** (1 tydzień)
- REST API endpoints
- Dockeryzacja
- CI/CD (GitHub Actions)
- Push do GHCR

### **Faza 3: n8n** (3 dni)
- Workflow design
- Google Sheets integration
- State management
- Error handling

### **Faza 4: Deployment** (2 dni)
- Setup na Raspberry Pi
- Monitoring i health checks
- Backup automation
- Security hardening

**Total:** 3-4 tygodnie

## 🎨 Kluczowe funkcje

### ✅ Parsowanie
- PKO BP (Windows-1250, format YYYY-MM-DD)
- Alior Bank (UTF-8, format DD-MM-YYYY)
- Automatyczna detekcja formatu
- Inteligentna ekstrakcja kontrahenta

### ✅ Kategoryzacja
- System reguł (YAML)
- Regex i pattern matching
- Manual overrides
- ~50 przykładowych reguł dla PL

### ✅ Agregacja
- Grupowanie: rok → miesiąc → kategoria → podkategoria
- Sumy i statystyki
- Tracking nieprzypisanych transakcji

### ✅ Eksport
- Excel z bogatym formatowaniem
- Google Sheets (przez n8n)
- JSON (dla API)

### ✅ Automatyzacja
- n8n workflow (cron co 6h)
- Automatyczna detekcja nowych plików
- State management (brak duplikatów)
- Error handling i retry

### ✅ CI/CD
- GitHub Actions (testy, lint)
- Automatyczny build Docker
- Push do GHCR
- Multi-platform (amd64, arm64)

## 📦 Deliverables

Po zakończeniu wszystkich faz otrzymasz:

1. **Działający CLI** - możesz uruchamiać ręcznie
2. **REST API** - możesz integrować z innymi systemami
3. **Docker images** - w GHCR, gotowe do użycia
4. **n8n workflow** - automatyczna orkiestracja
5. **Deployment na RPI** - production-ready
6. **Monitoring** - health checks, logi, backup
7. **Dokumentacja** - kompletna, z przykładami

## 🚀 Quick Start (po implementacji)

```bash
# Faza 1: Użycie CLI
pip install -e .
bank-analyzer analyze data/input/*.csv

# Faza 2: Uruchomienie API
docker-compose up

# Faza 3+4: Production na RPI
cd ~/kma-bank-analyzer
docker-compose -f docker-compose.prod.yml up -d
# n8n dostępne na http://[RPI_IP]:5678
```

## 📊 Struktury danych

### Transaction (po parsowaniu)
```python
{
  "id": "a1b2c3d4",
  "date": "2025-12-20",
  "description": "CARREFOUR WARSZAWA",
  "counterparty": "carrefour",
  "amount": 156.78,
  "category_main": "Jedzenie",
  "category_sub": "Zakupy spożywcze"
}
```

### Aggregated (wyjście)
```python
{
  "years": {
    "2025": {
      "months": {
        "12": {
          "categories": {
            "Jedzenie": {
              "Zakupy spożywcze": {
                "total": 3240.50,
                "count": 28
              }
            }
          },
          "total": 5678.90
        }
      }
    }
  }
}
```

## 🔧 Technologie

- **Core:** Python 3.11+
- **Libraries:** pandas, openpyxl, pyyaml, chardet, click
- **API:** FastAPI, uvicorn
- **Orchestration:** n8n
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Registry:** GitHub Container Registry (GHCR)
- **Integration:** Google Sheets API

## 🛡️ Security & Privacy

- ✅ Self-hosted (RPI)
- ✅ Dane nie wychodzą na zewnątrz
- ✅ Wrażliwe pliki w .gitignore
- ✅ Credentials w .env (nie w repo)
- ✅ Firewall configured
- ✅ Basic auth dla n8n

## 📖 Jak czytać ten plan

1. **Zacznij od:** [00-PROJECT-OVERVIEW.md](00-PROJECT-OVERVIEW.md)
2. **Implementuj kolejno:** Fazy 1 → 2 → 3 → 4
3. **Każda faza ma:**
   - Przegląd i cel
   - Szczegółowy plan krok po kroku
   - Przykłady kodu
   - Checklist deliverables
   - Test końcowy
4. **Pliki pomocnicze:**
   - 05: Struktury danych (CSV, JSON, Excel)
   - 06: Przykłady konfiguracji (YAML, .env)

## ✅ Checklist kompletności planu

- [x] Architektura zdefiniowana
- [x] Wszystkie fazy rozpisane
- [x] Struktury danych określone
- [x] Parsery opisane (PKO, Alior)
- [x] System kategoryzacji zaprojektowany
- [x] Przykładowe reguły (~50) przygotowane
- [x] API endpoints określone
- [x] Docker setup opisany
- [x] CI/CD workflow gotowy
- [x] n8n workflow zaprojektowany
- [x] Google Sheets integration opisana
- [x] Deployment na RPI rozpisany
- [x] Monitoring i backup zaplanowany
- [x] Security considerations uwzględnione
- [x] Wszystkie pliki konfiguracyjne
- [x] Testing strategy określona
- [x] Dokumentacja kompletna

## 📝 Uwagi końcowe

### Co jest included:
✅ Kompletny plan wszystkich 4 faz  
✅ Szczegółowa dokumentacja techniczna  
✅ Przykłady kodu (Python, YAML, Docker)  
✅ CI/CD pipeline (GitHub Actions)  
✅ ~50 przykładowych reguł dla PL  
✅ n8n workflow design  
✅ Deployment guide dla RPI  
✅ Monitoring i backup strategies  

### Co NIE jest included (przyszłe rozszerzenia):
❌ Web UI (może być dodane później)  
❌ Machine Learning (opcjonalnie)  
❌ Więcej banków (można dodać wzorując się na PKO/Alior)  
❌ Mobile app  
❌ Budżetowanie i predykcje  

### Gotowość:
🟢 **Plan jest kompletny i gotowy do implementacji**  
🟢 **Wszystkie szczegóły techniczne określone**  
🟢 **Możesz zaczynać od Fazy 1**

## 📞 Support

- **Issues:** GitHub Issues (po utworzeniu repo)
- **Documentation:** Ten plan + README w repo
- **Contributing:** CONTRIBUTING.md (w repo)

## 📜 License

Projekt będzie open source (MIT lub inna OSS license).

---

**Powodzenia w implementacji! 🚀**

*Ostatnia aktualizacja: 2026-01-09*
