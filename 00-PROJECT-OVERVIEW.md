# kma-bank-analyzer - Project Overview

## Cel projektu

Automatyzacja analizowania wyciągów bankowych z kategoryzacją transakcji, agregacją wydatków i eksportem do Excel/Google Sheets.

## Architektura finalna

```
┌─────────────────────────────────────────────────────────┐
│                         n8n                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐            │
│  │  Cron    │→ │  Check   │→ │   HTTP    │            │
│  │ Trigger  │  │  Files   │  │  Request  │            │
│  └──────────┘  └──────────┘  └─────┬─────┘            │
│                                      │                   │
└──────────────────────────────────────┼───────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────┐
│              Python Microservice (FastAPI)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │           bank_analyzer (core library)           │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────┐     │  │
│  │  │ Parsers │→ │Categorize│→ │ Aggregator │     │  │
│  │  └─────────┘  └──────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Endpoints:                                             │
│  POST /analyze     - analyze CSV files                 │
│  GET  /categories  - list categories                   │
│  POST /reprocess   - reprocess with new rules          │
└─────────────────────────────────────────────────────────┘
                                       │
                                       ↓
                        ┌──────────────────────────┐
                        │     Google Sheets        │
                        │  (via n8n native node)   │
                        └──────────────────────────┘
```

## Wymagania funkcjonalne

1. **Parsowanie CSV** - obsługa różnych formatów banków (PKO, Alior, możliwość rozbudowy)
2. **Kategoryzacja transakcji** - system reguł + manual overrides
3. **Agregacja** - sumy według kategorii, miesięcy, lat
4. **Eksport** - Excel z formatowaniem, Google Sheets
5. **Automatyzacja** - scheduled processing przez n8n
6. **Reprocessing** - możliwość ponownego przetworzenia z nowymi regułami
7. **Analiza** - narzędzie do analizy historycznych transakcji

## Wymagania niefunkcjonalne

1. **Prywatność** - self-hosted, dane nie wychodzą na zewnątrz
2. **Open source** - kod publiczny (bez wrażliwych danych)
3. **Hosting** - Raspberry Pi
4. **Częstotliwość** - 2 wyciągi miesięcznie (low frequency)
5. **Elastyczność** - łatwe dodawanie nowych banków
6. **Testowanie** - >80% coverage
7. **CI/CD** - automatyczny build i push do GHCR

## Technologie

- **Core**: Python 3.11+
- **Biblioteki**: pandas, openpyxl, pyyaml, chardet, click
- **API**: FastAPI, uvicorn
- **Orchestration**: n8n
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Registry**: GitHub Container Registry (GHCR)
- **Integration**: Google Sheets API

## Fazy implementacji

### Faza 1: Python CLI Library (2 tygodnie)
Podstawowa biblioteka + CLI do ręcznego użycia
- Parsery (PKO, Alior)
- Kategoryzator (reguły)
- Agregator
- Excel exporter
- CLI interface
- Testy unit + integration

### Faza 2: FastAPI Microservice + Docker (1 tydzień)
Wrap biblioteki w API, dockeryzacja
- FastAPI endpoints
- Dockerfile + docker-compose
- CI/CD (GitHub Actions)
- API testing
- Push do GHCR

### Faza 3: n8n Orchestration (3 dni)
Automatyzacja workflow
- n8n workflow design
- Google Sheets integration
- State management
- Error handling
- Monitoring

### Faza 4: Deployment na RPI (2 dni)
Production deployment
- RPI setup
- Production docker-compose
- Health monitoring
- Backup automation
- Security hardening

## Harmonogram

**Tydzień 1-2:** Faza 1 (Python CLI)
**Tydzień 3:** Faza 2 (FastAPI + Docker)
**Tydzień 4:** Faza 3 + 4 (n8n + Deployment)

**Total:** 3-4 tygodnie

## Struktura repozytorium

```
kma-bank-analyzer/
├── bank_analyzer/              # Core library
│   ├── models/
│   ├── parsers/
│   ├── categorizer/
│   ├── aggregator/
│   ├── exporters/
│   └── utils/
├── api/                        # FastAPI microservice
│   ├── main.py
│   ├── models.py
│   └── routers/
├── cli/                        # CLI interface
│   └── main.py
├── config/                     # Configuration files
│   ├── categories.example.yaml
│   ├── rules.example.yaml
│   └── banks_formats.yaml
├── docker/                     # Docker files
│   ├── Dockerfile.api
│   └── docker-compose.yml
├── n8n/                        # n8n workflows
│   └── workflows/
├── tests/                      # Tests
│   ├── fixtures/
│   └── test_*.py
├── .github/                    # CI/CD
│   └── workflows/
├── docs/                       # Documentation
└── data/                       # Data (gitignored)
    ├── input/
    ├── processed/
    └── output/
```

## Kluczowe decyzje projektowe

1. **Hybrydowe podejście** - Python dla logiki, n8n dla orchestracji
2. **Library-first** - core jako importowalna biblioteka, nie monolith
3. **Stateless** - API bezstanowe, state w n8n lub plikach
4. **Staged implementation** - działający CLI → API → orchestracja
5. **Docker-native** - wszystko w kontenerach
6. **GHCR** - public registry dla obrazów
7. **Google Sheets** - główny target (Excel jako backup/local)

## Success Criteria

### Minimum Viable Product (MVP - Faza 1)
- [ ] CLI parsuje PKO i Alior CSV
- [ ] Kategoryzacja według reguł działa
- [ ] Generuje Excel z podsumowaniem rocznym
- [ ] Możliwość ręcznego uruchomienia
- [ ] Testy >80% coverage

### Production Ready (Fazy 2-4)
- [ ] API działa, obrazy w GHCR
- [ ] n8n workflow automatycznie przetwarza pliki
- [ ] Google Sheets wypełnia się danymi
- [ ] Deployment na RPI
- [ ] Monitoring i backup działają

### Future Enhancements (poza scope)
- Web UI dla zarządzania kategoriami
- ML dla automatycznej kategoryzacji
- Więcej banków
- Predykcja wydatków
- Budżetowanie

## Linki do szczegółowych planów

- [Faza 1: Python CLI Library](./01-PHASE1-PYTHON-CLI.md)
- [Faza 2: FastAPI Microservice](./02-PHASE2-FASTAPI-DOCKER.md)
- [Faza 3: n8n Orchestration](./03-PHASE3-N8N-ORCHESTRATION.md)
- [Faza 4: Deployment](./04-PHASE4-DEPLOYMENT.md)
- [Struktury danych](./05-DATA-STRUCTURES.md)
- [Konfiguracja](./06-CONFIGURATION.md)
- [CI/CD](./07-CICD.md)

## Kontakt i kontrybutowanie

- Repository: https://github.com/[username]/kma-bank-analyzer
- Issues: GitHub Issues
- Contributions: Zobacz CONTRIBUTING.md
- License: MIT (lub inna OSS)

---

**Status:** Plan ostateczny, gotowy do implementacji
**Data:** 2026-01-09
**Wersja:** 1.0
