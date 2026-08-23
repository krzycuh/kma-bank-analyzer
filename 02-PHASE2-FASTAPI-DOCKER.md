# Faza 2: FastAPI Microservice + Docker

**Czas trwania:** 1 tydzień  
**Cel:** Wrap biblioteki w API, dockeryzacja, CI/CD

## Przegląd

W tej fazie opakowujemy bibliotekę `bank_analyzer` w REST API używając FastAPI, tworzymy obrazy Docker i konfigurujemy CI/CD do automatycznego builda.

## Struktura rozszerzona

```
kma-bank-analyzer/
├── bank_analyzer/              # Bez zmian (z Fazy 1)
├── cli/                        # Bez zmian
├── api/                        # NOWE
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── models.py               # Pydantic models
│   ├── dependencies.py         # DI
│   └── routers/
│       ├── __init__.py
│       ├── analyze.py          # POST /analyze
│       ├── categories.py       # GET /categories
│       └── health.py           # GET /health
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.cli          # Opcjonalny
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── build-api.yml
│       └── lint.yml
└── ...
```

## Szczegółowy plan implementacji

### Krok 1: FastAPI Application (Dzień 1)

#### requirements.txt - rozszerzenie
Dodaj do istniejącego pliku:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
```

#### api/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, categories, health

app = FastAPI(
    title="Bank Analyzer API",
    version="0.2.0",
    description="Microservice for analyzing bank statements",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (jeśli będzie frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji: konkretne domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])


@app.on_event("startup")
async def startup_event():
    """Inicjalizacja przy starcie"""
    from bank_analyzer.utils.logger import setup_logging
    setup_logging("INFO")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### api/models.py
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    """Request do analizy plików"""
    output_format: str = Field(default="json", description="Format wyjściowy: json lub excel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "output_format": "json"
            }
        }


class AnalyzeResponse(BaseModel):
    """Response z wynikami analizy"""
    status: str
    transactions_count: int
    categorized_count: int
    uncategorized_count: int
    aggregated_data: dict
    download_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "transactions_count": 156,
                "categorized_count": 154,
                "uncategorized_count": 2,
                "aggregated_data": {},
                "download_url": "/api/v1/download/abc123"
            }
        }


class CategoryInfo(BaseModel):
    """Informacja o kategorii"""
    name: str
    subcategories: List[str]


class CategoriesResponse(BaseModel):
    """Response z listą kategorii"""
    categories: List[CategoryInfo]


class HealthResponse(BaseModel):
    """Response health check"""
    status: str
    version: str
    uptime: float
```

#### api/routers/health.py
```python
from fastapi import APIRouter
import time

router = APIRouter()

START_TIME = time.time()


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "uptime": time.time() - START_TIME
    }
```

#### api/routers/analyze.py
```python
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from pathlib import Path
import tempfile
import uuid

from bank_analyzer import detect_and_parse, RuleEngine, ManualOverrides, Aggregator
from bank_analyzer.utils.logger import get_logger
from ..models import AnalyzeResponse

router = APIRouter()
logger = get_logger(__name__)

# Katalog na pliki tymczasowe
TEMP_DIR = Path("/tmp/bank-analyzer")
TEMP_DIR.mkdir(exist_ok=True)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    output_format: str = "json"
):
    """
    Analizuj przesłane pliki CSV
    
    - **files**: Lista plików CSV do analizy
    - **output_format**: Format wyniku (json lub excel)
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="Brak plików do przetworzenia")
    
    job_id = str(uuid.uuid4())
    logger.info(f"[{job_id}] Rozpoczynam analizę {len(files)} plików")
    
    # Zapisz pliki tymczasowo
    temp_files = []
    for file in files:
        temp_path = TEMP_DIR / f"{job_id}_{file.filename}"
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        temp_files.append(temp_path)
    
    try:
        # Parse wszystkie pliki
        all_transactions = []
        for temp_file in temp_files:
            try:
                transactions = detect_and_parse(temp_file)
                all_transactions.extend(transactions)
                logger.info(f"[{job_id}] Sparsowano {temp_file.name}: {len(transactions)} transakcji")
            except Exception as e:
                logger.error(f"[{job_id}] Błąd parsowania {temp_file.name}: {e}")
                continue
        
        if not all_transactions:
            raise HTTPException(status_code=400, detail="Nie udało się sparsować żadnych transakcji")
        
        # Kategoryzacja
        rule_engine = RuleEngine(Path("config/rules.yaml"))
        manual_overrides = ManualOverrides(Path("data/manual_overrides.yaml"))
        
        categorized_count = 0
        for trans in all_transactions:
            override = manual_overrides.get(trans.id)
            if override:
                trans.category_main, trans.category_sub = override
                trans.manual_override = True
                categorized_count += 1
            else:
                trans.category_main, trans.category_sub = rule_engine.categorize(trans)
                if trans.category_sub != "Nieprzypisane":
                    categorized_count += 1
        
        # Agregacja
        aggregator = Aggregator()
        aggregated = aggregator.aggregate(all_transactions)
        
        # Konwersja do JSON-friendly format
        aggregated_json = _convert_to_json(aggregated)
        
        response = AnalyzeResponse(
            status="success",
            transactions_count=len(all_transactions),
            categorized_count=categorized_count,
            uncategorized_count=len(all_transactions) - categorized_count,
            aggregated_data=aggregated_json,
            download_url=None
        )
        
        # Cleanup w tle
        background_tasks.add_task(_cleanup_files, temp_files)
        
        return response
    
    except Exception as e:
        logger.error(f"[{job_id}] Błąd podczas analizy: {e}")
        # Cleanup
        background_tasks.add_task(_cleanup_files, temp_files)
        raise HTTPException(status_code=500, detail=str(e))


def _convert_to_json(aggregated: dict) -> dict:
    """Konwertuj Decimal i inne typy do JSON-friendly"""
    import json
    from decimal import Decimal
    
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    # Serialize i deserialize żeby przekonwertować Decimals
    json_str = json.dumps(aggregated, default=decimal_default)
    return json.loads(json_str)


async def _cleanup_files(files: List[Path]):
    """Usuń pliki tymczasowe"""
    for file in files:
        try:
            file.unlink()
        except:
            pass
```

#### api/routers/categories.py
```python
from fastapi import APIRouter
from pathlib import Path
import yaml

from ..models import CategoriesResponse, CategoryInfo

router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories():
    """
    Pobierz listę dostępnych kategorii
    """
    
    categories_file = Path("config/categories.yaml")
    
    if not categories_file.exists():
        return CategoriesResponse(categories=[])
    
    with open(categories_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    categories_list = []
    for cat in data.get('categories', []):
        categories_list.append(CategoryInfo(
            name=cat['name'],
            subcategories=cat.get('subcategories', [])
        ))
    
    return CategoriesResponse(categories=categories_list)
```

### Krok 2: Docker Setup (Dzień 2)

#### docker/Dockerfile.api
```dockerfile
# Multi-stage build dla mniejszego obrazu

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY bank_analyzer/ ./bank_analyzer/
COPY api/ ./api/
COPY config/banks_formats.yaml ./config/
COPY setup.py .

# Install bank_analyzer package
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /app/data/{input,processed,output} /app/logs

# Set PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker/docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    container_name: bank-analyzer-api
    ports:
      - "8000:8000"
    volumes:
      - ../data:/app/data
      - ../config:/app/config:ro
      - ../logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

#### docker/docker-compose.prod.yml
```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/${GITHUB_REPOSITORY}/api:latest
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 1m
      timeout: 10s
      retries: 3
    networks:
      - bank-analyzer

networks:
  bank-analyzer:
    driver: bridge
```

### Krok 3: CI/CD - GitHub Actions (Dzień 3)

#### .github/workflows/test.yml
```yaml
name: Tests

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest --cov=bank_analyzer --cov=api --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: github.event_name == 'pull_request'
        with:
          file: ./coverage.xml
          flags: unittests
  
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install black flake8 mypy
      
      - name: Run black
        run: black --check .
      
      - name: Run flake8
        run: flake8 bank_analyzer/ api/ cli/
      
      - name: Run mypy
        run: mypy bank_analyzer/ api/ cli/ --ignore-missing-imports
```

#### .github/workflows/build-api.yml
```yaml
name: Build and Push Docker Image

on:
  push:
    branches:
      - main
    tags:
      - 'v*'
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/api

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: docker/Dockerfile.api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64
      
      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

### Krok 4: Testing API (Dzień 4)

#### tests/test_api.py
```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime" in data


def test_categories_endpoint():
    """Test pobierania kategorii"""
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_analyze_endpoint_no_files():
    """Test analizy bez plików"""
    response = client.post("/api/v1/analyze")
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_with_file():
    """Test analizy z przykładowym plikiem"""
    fixtures_dir = Path(__file__).parent / 'fixtures'
    
    with open(fixtures_dir / 'pko_sample.csv', 'rb') as f:
        response = client.post(
            "/api/v1/analyze",
            files={"files": ("pko.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "transactions_count" in data
    assert "categorized_count" in data
    assert "aggregated_data" in data


def test_api_docs_available():
    """Test że dokumentacja jest dostępna"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200
```

### Krok 5: Dokumentacja API (Dzień 5)

#### README.md - update

Dodaj sekcję:

```markdown
## API Usage

### Uruchomienie lokalnie

```bash
# Bezpośrednio
uvicorn api.main:app --reload

# Lub Docker
docker-compose -f docker/docker-compose.yml up
```

API dostępne na: http://localhost:8000

### Dokumentacja

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Przykłady użycia

#### Analiza plików
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "files=@pko.csv" \
  -F "files=@alior.csv"
```

#### Pobierz kategorie
```bash
curl "http://localhost:8000/api/v1/categories"
```

#### Health check
```bash
curl "http://localhost:8000/health"
```

### Pull z GHCR

```bash
docker pull ghcr.io/[username]/kma-bank-analyzer/api:latest
docker run -p 8000:8000 ghcr.io/[username]/kma-bank-analyzer/api:latest
```
```

## Deliverables Fazy 2

### Checklist

- [ ] FastAPI app zaimplementowana
- [ ] Wszystkie endpointy działają
- [ ] Dockerfile.api działa
- [ ] docker-compose.yml lokalnie działa
- [ ] GitHub Actions - testy
- [ ] GitHub Actions - build i push
- [ ] Obrazy w GHCR
- [ ] API testy napisane
- [ ] README.md zaktualizowane
- [ ] Swagger docs dostępne

### Przykładowe użycie

```bash
# Lokalnie z Docker
cd docker
docker-compose up

# Test
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Analiza
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "files=@../data/input/pko.csv"
```

### Next Steps

Po zakończeniu Fazy 2 → **Faza 3: n8n Orchestration**
