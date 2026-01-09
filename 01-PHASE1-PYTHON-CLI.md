# Faza 1: Python CLI Library

**Czas trwania:** 2 tygodnie  
**Cel:** Działająca biblioteka Python + CLI do ręcznego użycia

## Przegląd

W tej fazie budujemy solidny fundament projektu - bibliotekę `bank_analyzer` która będzie:
- Importowalna w innych projektach
- Używana przez CLI
- Używana przez API (Faza 2)
- W pełni przetestowana
- Dobrze udokumentowana

## Struktura projektu

```
kma-bank-analyzer/
├── bank_analyzer/              # Core library (importowalna)
│   ├── __init__.py            # Public API exports
│   ├── models/
│   │   ├── __init__.py
│   │   └── transaction.py     # Transaction dataclass
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py     # Abstract base
│   │   ├── pko_parser.py      # PKO BP parser
│   │   ├── alior_parser.py    # Alior Bank parser
│   │   └── detector.py        # Format detection
│   ├── categorizer/
│   │   ├── __init__.py
│   │   ├── rule_engine.py     # Rule-based categorization
│   │   ├── overrides.py       # Manual overrides
│   │   └── analyzer.py        # Historical analysis tool
│   ├── aggregator/
│   │   ├── __init__.py
│   │   └── aggregator.py      # Data aggregation
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── base_exporter.py   # Abstract base
│   │   ├── excel_exporter.py  # Excel export
│   │   └── json_exporter.py   # JSON export (dla API)
│   └── utils/
│       ├── __init__.py
│       └── logger.py          # Logging utilities
├── cli/
│   ├── __init__.py
│   └── main.py                # CLI entry point (click)
├── config/
│   ├── categories.example.yaml
│   ├── rules.example.yaml
│   └── banks_formats.yaml
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── pko_sample.csv
│   │   └── alior_sample.csv
│   ├── test_parsers.py
│   ├── test_categorizer.py
│   ├── test_aggregator.py
│   ├── test_exporters.py
│   └── test_integration.py
├── data/                      # .gitignore
│   ├── input/
│   ├── processed/
│   ├── output/
│   └── manual_overrides.yaml
├── .gitignore
├── requirements.txt
├── requirements-dev.txt       # Dev dependencies (pytest, etc)
├── setup.py                   # Dla pip install
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Szczegółowy plan implementacji

### Krok 1: Setup projektu (Dzień 1, rano)

#### 1.1 Inicjalizacja repo
```bash
mkdir kma-bank-analyzer
cd kma-bank-analyzer
git init
```

#### 1.2 requirements.txt
```
pandas>=2.0.0
openpyxl>=3.1.0
pyyaml>=6.0
chardet>=5.2.0
click>=8.1.0
python-dateutil>=2.8.0
```

#### 1.3 requirements-dev.txt
```
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
```

#### 1.4 setup.py
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bank-analyzer",
    version="0.1.0",
    author="kma",
    description="Bank statement analyzer with categorization and reporting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/[username]/kma-bank-analyzer",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0",
        "chardet>=5.2.0",
        "click>=8.1.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        'console_scripts': [
            'bank-analyzer=cli.main:cli',
        ],
    },
)
```

#### 1.5 .gitignore
```
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

# Virtual environments
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Data files (sensitive!)
data/
*.csv
*.xlsx
!tests/fixtures/*.csv

# Config files (sensitive!)
config/categories.yaml
config/rules.yaml
.bank-analyzer.yaml

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
```

#### 1.6 Katalogi
```bash
mkdir -p bank_analyzer/{models,parsers,categorizer,aggregator,exporters,utils}
mkdir -p cli
mkdir -p config
mkdir -p tests/fixtures
mkdir -p data/{input,processed,output}
touch bank_analyzer/__init__.py
touch bank_analyzer/{models,parsers,categorizer,aggregator,exporters,utils}/__init__.py
touch cli/__init__.py
touch tests/__init__.py
```

### Krok 2: Model danych (Dzień 1, popołudnie)

#### bank_analyzer/models/transaction.py
```python
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
import hashlib


@dataclass
class Transaction:
    """Znormalizowana transakcja bankowa"""
    
    # Podstawowe dane
    date: datetime
    description: str
    amount: Decimal
    
    # Metadata
    transaction_type: str  # 'expense' lub 'income'
    currency: str = "PLN"
    counterparty: str = ""
    
    # Pochodzenie
    source_bank: str = ""
    source_file: str = ""
    processed_at: datetime = field(default_factory=datetime.now)
    
    # Kategoryzacja
    category_main: Optional[str] = None
    category_sub: Optional[str] = None
    manual_override: bool = False
    
    # Identyfikator (generowany automatycznie)
    id: str = field(init=False)
    
    def __post_init__(self):
        """Generuj ID na podstawie danych transakcji"""
        if not hasattr(self, 'id') or not self.id:
            hash_input = f"{self.date.isoformat()}{self.description}{self.amount}"
            self.id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        """Konwersja do słownika"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'counterparty': self.counterparty,
            'amount': float(self.amount),
            'transaction_type': self.transaction_type,
            'currency': self.currency,
            'category_main': self.category_main,
            'category_sub': self.category_sub,
            'source_bank': self.source_bank,
            'source_file': self.source_file,
            'manual_override': self.manual_override,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Utworzenie z słownika"""
        data = data.copy()
        data['date'] = datetime.fromisoformat(data['date'])
        data['amount'] = Decimal(str(data['amount']))
        if 'processed_at' in data:
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        return cls(**data)
```

### Krok 3: Parsery (Dzień 2-3)

#### bank_analyzer/parsers/base_parser.py
```python
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
import chardet

from ..models.transaction import Transaction


class BaseParser(ABC):
    """Abstrakcyjna klasa bazowa dla parserów bankowych"""
    
    def __init__(self):
        self.bank_name = self.__class__.__name__.replace('Parser', '').upper()
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Sprawdź czy ten parser obsługuje dany format
        
        Args:
            file_path: Ścieżka do pliku CSV
            
        Returns:
            True jeśli parser może obsłużyć ten plik
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: Path) -> List[Transaction]:
        """
        Parsuj plik CSV do listy transakcji
        
        Args:
            file_path: Ścieżka do pliku CSV
            
        Returns:
            Lista znormalizowanych transakcji
            
        Raises:
            ValueError: Jeśli plik nie może być sparsowany
        """
        pass
    
    def _detect_encoding(self, file_path: Path) -> str:
        """
        Wykryj kodowanie pliku
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            Nazwa kodowania (np. 'utf-8', 'windows-1250')
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Pierwsze 10KB
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    def _clean_text(self, text: str) -> str:
        """
        Oczyść tekst z nadmiarowych spacji i znaków
        
        Args:
            text: Tekst do oczyszczenia
            
        Returns:
            Oczyszczony tekst
        """
        if not text:
            return ""
        # Usuń wielokrotne spacje
        text = ' '.join(text.split())
        return text.strip()
```

#### bank_analyzer/parsers/pko_parser.py
```python
import csv
from pathlib import Path
from typing import List
from datetime import datetime
from decimal import Decimal
import re

from .base_parser import BaseParser
from ..models.transaction import Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PKOParser(BaseParser):
    """Parser dla wyciągów PKO BP"""
    
    def can_parse(self, file_path: Path) -> bool:
        """Wykryj format PKO po nagłówku"""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                first_line = f.readline()
                # PKO ma "Data operacji" jako pierwszą kolumnę
                return "Data operacji" in first_line
        except Exception as e:
            logger.warning(f"Błąd podczas sprawdzania formatu PKO: {e}")
            return False
    
    def parse(self, file_path: Path) -> List[Transaction]:
        """Parsuj plik PKO"""
        encoding = self._detect_encoding(file_path)
        logger.info(f"Parsowanie PKO: {file_path.name} (kodowanie: {encoding})")
        
        transactions = []
        errors = []
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        transaction = self._parse_row(row, file_path.name)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        errors.append((row_num, str(e)))
                        logger.warning(f"Błąd w wierszu {row_num}: {e}")
        
        except Exception as e:
            logger.error(f"Błąd czytania pliku {file_path}: {e}")
            raise ValueError(f"Nie udało się sparsować pliku PKO: {e}")
        
        logger.info(f"PKO: Przetworzono {len(transactions)} transakcji, "
                   f"pominięto {len(errors)} wierszy")
        
        return transactions
    
    def _parse_row(self, row: List[str], source_file: str) -> Transaction:
        """Parsuj pojedynczy wiersz PKO"""
        if len(row) < 7:
            raise ValueError(f"Za mało kolumn: {len(row)}")
        
        # Ekstrakcja danych
        date_str = row[0].strip()
        transaction_type = row[2].strip()
        amount_str = row[3].strip()
        currency = row[4].strip()
        
        # Parsowanie daty
        date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Parsowanie kwoty
        amount_str = amount_str.replace('+', '').replace('-', '')
        amount = Decimal(amount_str)
        
        # Typ transakcji (na podstawie znaku w oryginalnej kwocie)
        is_expense = '-' in row[3]
        trans_type = 'expense' if is_expense else 'income'
        
        # Budowanie opisu z kolumn 7-12
        description_parts = []
        for col in row[6:12]:
            col = col.strip()
            if col:
                # Usuń prefiksy typu "Tytuł:", "Lokalizacja:"
                col = re.sub(r'^(Tytu\xb3|Lokalizacja|Nazwa odbiorcy|Adres):\s*', '', col)
                description_parts.append(col)
        
        description = self._clean_text(' '.join(description_parts))
        
        # Ekstrakcja kontrahenta
        counterparty = self._extract_counterparty(row[6:12])
        
        return Transaction(
            date=date,
            description=description,
            counterparty=counterparty,
            amount=amount,
            transaction_type=trans_type,
            currency=currency,
            source_bank="PKO",
            source_file=source_file,
        )
    
    def _extract_counterparty(self, desc_columns: List[str]) -> str:
        """Inteligentna ekstrakcja kontrahenta"""
        # Próba 1: Szukaj w "Nazwa odbiorcy:"
        for col in desc_columns:
            match = re.search(r'Nazwa odbiorcy:\s*(.+)', col)
            if match:
                return self._clean_text(match.group(1))
        
        # Próba 2: Szukaj w "Adres:" (nazwa sklepu)
        for col in desc_columns:
            match = re.search(r'Adres:\s*([^M]+?)(?=\s*Miasto:|$)', col)
            if match:
                name = self._clean_text(match.group(1))
                # Usuń "K.1" i podobne
                name = re.sub(r'\s+K\.\d+', '', name)
                return name
        
        # Próba 3: Pierwsze słowo z tytułu
        for col in desc_columns:
            if col.strip() and not col.startswith(('Data', 'Oryginalna', 'Numer')):
                words = col.strip().split()
                if words:
                    return self._clean_text(words[0])
        
        return "Nieznany"
```

#### bank_analyzer/parsers/alior_parser.py
```python
import csv
from pathlib import Path
from typing import List
from datetime import datetime
from decimal import Decimal
import re

from .base_parser import BaseParser
from ..models.transaction import Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AliorParser(BaseParser):
    """Parser dla wyciągów Alior Bank"""
    
    def can_parse(self, file_path: Path) -> bool:
        """Wykryj format Alior po drugiej linii"""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                f.readline()  # Skip first line (metadata)
                second_line = f.readline()
                return "Data transakcji;Data księgowania" in second_line
        except Exception as e:
            logger.warning(f"Błąd podczas sprawdzania formatu Alior: {e}")
            return False
    
    def parse(self, file_path: Path) -> List[Transaction]:
        """Parsuj plik Alior"""
        encoding = self._detect_encoding(file_path)
        logger.info(f"Parsowanie Alior: {file_path.name} (kodowanie: {encoding})")
        
        transactions = []
        errors = []
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=';')
                next(reader)  # Skip metadata line
                next(reader)  # Skip header line
                
                for row_num, row in enumerate(reader, start=3):
                    try:
                        transaction = self._parse_row(row, file_path.name)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        errors.append((row_num, str(e)))
                        logger.warning(f"Błąd w wierszu {row_num}: {e}")
        
        except Exception as e:
            logger.error(f"Błąd czytania pliku {file_path}: {e}")
            raise ValueError(f"Nie udało się sparsować pliku Alior: {e}")
        
        logger.info(f"Alior: Przetworzono {len(transactions)} transakcji, "
                   f"pominięto {len(errors)} wierszy")
        
        return transactions
    
    def _parse_row(self, row: List[str], source_file: str) -> Transaction:
        """Parsuj pojedynczy wiersz Alior"""
        if len(row) < 9:
            raise ValueError(f"Za mało kolumn: {len(row)}")
        
        # Ekstrakcja danych
        date_str = row[0].strip()
        sender = row[2].strip()
        recipient = row[3].strip()
        description = row[4].strip()
        amount_str = row[5].strip()
        currency = row[6].strip()
        
        # Parsowanie daty (DD-MM-YYYY)
        date = datetime.strptime(date_str, "%d-%m-%Y")
        
        # Parsowanie kwoty (przecinek jako separator dziesiętny)
        amount_str = amount_str.replace(',', '.').replace('-', '')
        amount = Decimal(amount_str)
        
        # Typ transakcji
        is_expense = '-' in row[5]
        trans_type = 'expense' if is_expense else 'income'
        
        # Kontrahent
        counterparty = self._extract_counterparty(sender, recipient, description)
        
        # Opis
        full_description = self._clean_text(description)
        
        return Transaction(
            date=date,
            description=full_description,
            counterparty=counterparty,
            amount=amount,
            transaction_type=trans_type,
            currency=currency,
            source_bank="ALIOR",
            source_file=source_file,
        )
    
    def _extract_counterparty(self, sender: str, recipient: str, 
                            description: str) -> str:
        """Ekstrakcja kontrahenta z dostępnych pól"""
        # Priorytet: sender > recipient > extract from description
        if sender:
            return self._clean_text(sender)
        
        if recipient:
            return self._clean_text(recipient)
        
        # Spróbuj wyciągnąć z opisu (nazwa przed " PL")
        match = re.search(r'^(.+?)\s+PL\s*$', description)
        if match:
            return self._clean_text(match.group(1))
        
        # Pierwsze słowo z opisu
        words = description.split()
        if words:
            return self._clean_text(words[0])
        
        return "Nieznany"
```

#### bank_analyzer/parsers/detector.py
```python
from pathlib import Path
from typing import List, Type

from .base_parser import BaseParser
from .pko_parser import PKOParser
from .alior_parser import AliorParser
from ..models.transaction import Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Lista wszystkich dostępnych parserów
AVAILABLE_PARSERS: List[Type[BaseParser]] = [
    PKOParser,
    AliorParser,
]


def detect_and_parse(file_path: Path) -> List[Transaction]:
    """
    Automatyczne wykrywanie formatu i parsowanie pliku
    
    Args:
        file_path: Ścieżka do pliku CSV
        
    Returns:
        Lista transakcji
        
    Raises:
        ValueError: Jeśli nie znaleziono odpowiedniego parsera
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
    
    if not file_path.suffix.lower() == '.csv':
        raise ValueError(f"Nieobsługiwany format pliku: {file_path.suffix}")
    
    logger.info(f"Wykrywanie formatu: {file_path.name}")
    
    # Próbuj każdego parsera
    for parser_class in AVAILABLE_PARSERS:
        parser = parser_class()
        if parser.can_parse(file_path):
            logger.info(f"Wykryto format: {parser.bank_name}")
            return parser.parse(file_path)
    
    # Żaden parser nie pasuje
    raise ValueError(
        f"Nie rozpoznano formatu pliku: {file_path.name}\n"
        f"Obsługiwane banki: {', '.join(p.__name__.replace('Parser', '') for p in AVAILABLE_PARSERS)}\n"
        f"Jeśli to nowy bank, dodaj odpowiedni parser."
    )


def detect_format(file_path: Path) -> str:
    """
    Wykryj tylko format bez parsowania
    
    Args:
        file_path: Ścieżka do pliku
        
    Returns:
        Nazwa banku lub "UNKNOWN"
    """
    file_path = Path(file_path)
    
    for parser_class in AVAILABLE_PARSERS:
        parser = parser_class()
        if parser.can_parse(file_path):
            return parser.bank_name
    
    return "UNKNOWN"
```

#### bank_analyzer/parsers/__init__.py
```python
from .detector import detect_and_parse, detect_format, AVAILABLE_PARSERS
from .pko_parser import PKOParser
from .alior_parser import AliorParser

__all__ = [
    'detect_and_parse',
    'detect_format',
    'AVAILABLE_PARSERS',
    'PKOParser',
    'AliorParser',
]
```

### Krok 4: Kategoryzator (Dzień 4-5)

Zobacz plik `06-CONFIGURATION.md` dla szczegółów config files.

#### bank_analyzer/categorizer/rule_engine.py
```python
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

from ..models.transaction import Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RuleEngine:
    """Silnik kategoryzacji oparty o reguły"""
    
    def __init__(self, rules_file: Path):
        self.rules_file = Path(rules_file)
        self.rules: List[Dict] = []
        self.compiled_patterns: Dict[int, re.Pattern] = {}
        self.stats: Dict[str, int] = {}  # Statystyki użycia reguł
        self._cache: Dict[str, Tuple[str, str]] = {}  # Cache wyników
        
        self._load_rules()
    
    def _load_rules(self):
        """Wczytaj i skompiluj reguły"""
        if not self.rules_file.exists():
            logger.warning(f"Plik reguł nie istnieje: {self.rules_file}")
            self.rules = []
            return
        
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.rules = data.get('rules', [])
        
        # Sortuj według priorytetu (malejąco)
        self.rules.sort(key=lambda r: r.get('priority', 0), reverse=True)
        
        # Prekompiluj regex patterns
        for idx, rule in enumerate(self.rules):
            if rule.get('match_type') == 'regex':
                flags = 0 if rule.get('case_sensitive', False) else re.IGNORECASE
                self.compiled_patterns[idx] = re.compile(rule['pattern'], flags)
        
        logger.info(f"Wczytano {len(self.rules)} reguł")
    
    def categorize(self, transaction: Transaction) -> Tuple[str, str]:
        """
        Kategoryzuj transakcję
        
        Args:
            transaction: Transakcja do kategoryzacji
            
        Returns:
            Tuple (category_main, category_sub)
        """
        # Sprawdź cache
        cache_key = f"{transaction.counterparty}|{transaction.description}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Iteruj przez reguły
        for idx, rule in enumerate(self.rules):
            if self._match_rule(rule, transaction, idx):
                category_main = rule['category_main']
                category_sub = rule['category_sub']
                
                # Aktualizuj statystyki
                rule_name = rule.get('name', f"rule_{idx}")
                self.stats[rule_name] = self.stats.get(rule_name, 0) + 1
                
                # Zapisz w cache
                self._cache[cache_key] = (category_main, category_sub)
                
                return category_main, category_sub
        
        # Brak dopasowania
        return "Inne wydatki", "Nieprzypisane"
    
    def _match_rule(self, rule: Dict, transaction: Transaction, 
                   rule_idx: int) -> bool:
        """Sprawdź czy reguła pasuje do transakcji"""
        pattern = rule['pattern']
        field_name = rule.get('field', 'counterparty')
        match_type = rule.get('match_type', 'contains')
        case_sensitive = rule.get('case_sensitive', False)
        
        # Pobierz wartość pola
        if field_name == 'counterparty':
            field_value = transaction.counterparty
        elif field_name == 'description':
            field_value = transaction.description
        else:
            field_value = ""
        
        if not case_sensitive:
            field_value = field_value.lower()
            if isinstance(pattern, str):
                pattern = pattern.lower()
        
        # Dopasuj według typu
        if match_type == 'contains':
            return pattern in field_value
        
        elif match_type == 'exact':
            return pattern == field_value
        
        elif match_type == 'regex':
            compiled = self.compiled_patterns.get(rule_idx)
            if compiled:
                return bool(compiled.search(field_value))
            else:
                return False
        
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """Pobierz statystyki użycia reguł"""
        return self.stats.copy()
    
    def clear_cache(self):
        """Wyczyść cache"""
        self._cache.clear()
```

#### bank_analyzer/categorizer/overrides.py
```python
from pathlib import Path
from typing import Dict, Tuple, Optional
import yaml

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ManualOverrides:
    """Zarządzanie ręcznymi nadpisaniami kategoryzacji"""
    
    def __init__(self, overrides_file: Path):
        self.overrides_file = Path(overrides_file)
        self.overrides: Dict[str, Tuple[str, str]] = {}
        self._load_overrides()
    
    def _load_overrides(self):
        """Wczytaj overrides z pliku"""
        if not self.overrides_file.exists():
            logger.info(f"Plik overrides nie istnieje, tworzę: {self.overrides_file}")
            self._create_empty_file()
            return
        
        try:
            with open(self.overrides_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            overrides_list = data.get('overrides', [])
            
            for override in overrides_list:
                trans_id = override['transaction_id']
                category_main = override['category_main']
                category_sub = override['category_sub']
                self.overrides[trans_id] = (category_main, category_sub)
            
            logger.info(f"Wczytano {len(self.overrides)} nadpisań")
        
        except Exception as e:
            logger.error(f"Błąd wczytywania overrides: {e}")
            self.overrides = {}
    
    def _create_empty_file(self):
        """Utwórz pusty plik overrides"""
        self.overrides_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.overrides_file, 'w', encoding='utf-8') as f:
            yaml.dump({'overrides': []}, f)
    
    def get(self, transaction_id: str) -> Optional[Tuple[str, str]]:
        """
        Pobierz override dla transakcji
        
        Args:
            transaction_id: ID transakcji
            
        Returns:
            Tuple (category_main, category_sub) lub None
        """
        return self.overrides.get(transaction_id)
    
    def add(self, transaction_id: str, category_main: str, 
            category_sub: str, note: str = ""):
        """
        Dodaj nowy override
        
        Args:
            transaction_id: ID transakcji
            category_main: Kategoria główna
            category_sub: Podkategoria
            note: Opcjonalna notka
        """
        self.overrides[transaction_id] = (category_main, category_sub)
        self._save(transaction_id, category_main, category_sub, note)
    
    def _save(self, transaction_id: str, category_main: str,
              category_sub: str, note: str):
        """Zapisz override do pliku"""
        # Wczytaj istniejące
        try:
            with open(self.overrides_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {'overrides': []}
        except:
            data = {'overrides': []}
        
        # Dodaj nowy
        data['overrides'].append({
            'transaction_id': transaction_id,
            'category_main': category_main,
            'category_sub': category_sub,
            'note': note,
        })
        
        # Zapisz
        with open(self.overrides_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
        
        logger.info(f"Dodano override dla transakcji {transaction_id}")
```

#### bank_analyzer/categorizer/__init__.py
```python
from .rule_engine import RuleEngine
from .overrides import ManualOverrides

__all__ = ['RuleEngine', 'ManualOverrides']
```

### Krok 5: Agregator i Eksporter (Dzień 6-7)

#### bank_analyzer/aggregator/aggregator.py
```python
from typing import List, Dict
from collections import defaultdict
from decimal import Decimal

from ..models.transaction import Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Aggregator:
    """Agregacja transakcji według kategorii i okresów"""
    
    def aggregate(self, transactions: List[Transaction]) -> Dict:
        """
        Agreguj transakcje
        
        Args:
            transactions: Lista transakcji do agregacji
            
        Returns:
            Słownik z zagregowanymi danymi
        """
        logger.info(f"Agregacja {len(transactions)} transakcji")
        
        # Grupowanie po latach i miesiącach
        data = defaultdict(lambda: defaultdict(lambda: {
            'categories': defaultdict(lambda: defaultdict(lambda: {
                'total': Decimal('0'),
                'count': 0,
                'transactions': []
            })),
            'total': Decimal('0'),
            'total_income': Decimal('0'),
            'total_expense': Decimal('0'),
        }))
        
        uncategorized = []
        
        for trans in transactions:
            year = trans.date.year
            month = trans.date.month
            
            # Dodaj do totalu miesiąca
            if trans.transaction_type == 'expense':
                data[year][month]['total_expense'] += trans.amount
            else:
                data[year][month]['total_income'] += trans.amount
            
            data[year][month]['total'] += trans.amount
            
            # Kategoryzacja
            if trans.category_sub == "Nieprzypisane":
                uncategorized.append(trans)
            
            cat_main = trans.category_main or "Inne wydatki"
            cat_sub = trans.category_sub or "Nieprzypisane"
            
            # Dodaj do kategorii
            cat_data = data[year][month]['categories'][cat_main][cat_sub]
            cat_data['total'] += trans.amount
            cat_data['count'] += 1
            cat_data['transactions'].append(trans)
        
        # Konwersja do zwykłych słowników
        result = {
            'years': {},
            'uncategorized': uncategorized,
            'all_transactions': transactions,
        }
        
        for year in sorted(data.keys()):
            year_data = {
                'months': {},
                'total_year': Decimal('0'),
                'categories_year': defaultdict(lambda: defaultdict(lambda: Decimal('0'))),
            }
            
            for month in sorted(data[year].keys()):
                month_data = data[year][month]
                year_data['months'][month] = {
                    'categories': dict(month_data['categories']),
                    'total': month_data['total'],
                    'total_income': month_data['total_income'],
                    'total_expense': month_data['total_expense'],
                }
                
                year_data['total_year'] += month_data['total']
                
                # Agregacja roczna kategorii
                for cat_main, subcats in month_data['categories'].items():
                    for cat_sub, amounts in subcats.items():
                        year_data['categories_year'][cat_main][cat_sub] += amounts['total']
            
            result['years'][year] = year_data
        
        logger.info(f"Zagregowano {len(result['years'])} lat, "
                   f"{len(uncategorized)} transakcji nieprzypisanych")
        
        return result
```

#### bank_analyzer/exporters/excel_exporter.py
```python
from pathlib import Path
from typing import Dict
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExcelExporter:
    """Eksport do formatu Excel z formatowaniem"""
    
    MONTHS_PL = {
        1: 'Sty', 2: 'Lut', 3: 'Mar', 4: 'Kwi',
        5: 'Maj', 6: 'Cze', 7: 'Lip', 8: 'Sie',
        9: 'Wrz', 10: 'Paź', 11: 'Lis', 12: 'Gru',
    }
    
    def export(self, aggregated_data: Dict, output_path: Path):
        """
        Eksportuj dane do Excel
        
        Args:
            aggregated_data: Zagregowane dane z Aggregatora
            output_path: Ścieżka do pliku wyjściowego
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup jeśli plik istnieje
        if output_path.exists():
            backup_path = output_path.with_suffix(
                f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            output_path.rename(backup_path)
            logger.info(f"Utworzono backup: {backup_path.name}")
        
        wb = Workbook()
        wb.remove(wb.active)  # Usuń domyślny arkusz
        
        # Utwórz arkusze
        for year in sorted(aggregated_data['years'].keys()):
            self._create_year_summary_sheet(wb, aggregated_data, year)
        
        self._create_uncategorized_sheet(wb, aggregated_data['uncategorized'])
        self._create_all_transactions_sheet(wb, aggregated_data['all_transactions'])
        
        # Zapisz
        wb.save(output_path)
        logger.info(f"Eksportowano do: {output_path}")
    
    def _create_year_summary_sheet(self, wb: Workbook, data: Dict, year: int):
        """Utwórz arkusz podsumowania rocznego"""
        ws = wb.create_sheet(f"Rok {year}")
        year_data = data['years'][year]
        
        # Tytuł
        ws['A1'] = f"Wydatki - Rok {year}"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:N1')
        
        # Nagłówki
        row = 3
        ws.cell(row, 1, "Kategoria")
        for month in range(1, 13):
            ws.cell(row, month + 1, self.MONTHS_PL[month])
        ws.cell(row, 14, "SUMA ROCZNA")
        
        # Formatowanie nagłówków
        for col in range(1, 15):
            cell = ws.cell(row, col)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row += 1
        
        # Dane kategorii
        categories = year_data.get('categories_year', {})
        
        for cat_main in sorted(categories.keys()):
            # Kategoria główna
            start_row = row
            ws.cell(row, 1, cat_main)
            ws.cell(row, 1).font = Font(bold=True)
            
            # Sumy miesięczne dla kategorii głównej
            cat_main_monthly = [0] * 12
            
            # Podkategorie
            subcats = categories[cat_main]
            for cat_sub in sorted(subcats.keys()):
                row += 1
                ws.cell(row, 1, f"  {cat_sub}")  # Wcięcie
                
                # Kwoty dla każdego miesiąca
                for month in range(1, 13):
                    month_data = year_data['months'].get(month, {})
                    amount = month_data.get('categories', {}).get(cat_main, {}).get(cat_sub, {}).get('total', 0)
                    if amount:
                        ws.cell(row, month + 1, float(amount))
                        ws.cell(row, month + 1).number_format = '#,##0.00'
                        cat_main_monthly[month - 1] += float(amount)
                
                # Suma roczna dla podkategorii
                total = float(subcats[cat_sub])
                ws.cell(row, 14, total)
                ws.cell(row, 14).number_format = '#,##0.00'
            
            # Wstaw sumy kategorii głównej
            for month in range(1, 13):
                if cat_main_monthly[month - 1]:
                    ws.cell(start_row, month + 1, cat_main_monthly[month - 1])
                    ws.cell(start_row, month + 1).number_format = '#,##0.00'
            
            # Suma roczna kategorii głównej
            total_main = sum(float(v) for v in subcats.values())
            ws.cell(start_row, 14, total_main)
            ws.cell(start_row, 14).number_format = '#,##0.00'
            
            row += 1
        
        # Suma miesięczna (ostatni wiersz)
        row += 1
        ws.cell(row, 1, "SUMA MIESIĘCZNA")
        ws.cell(row, 1).font = Font(bold=True)
        
        for month in range(1, 13):
            month_data = year_data['months'].get(month, {})
            total = float(month_data.get('total_expense', 0))
            if total:
                ws.cell(row, month + 1, total)
                ws.cell(row, month + 1).number_format = '#,##0.00'
                ws.cell(row, month + 1).font = Font(bold=True)
        
        # Suma roczna
        total_year = float(year_data['total_year'])
        ws.cell(row, 14, total_year)
        ws.cell(row, 14).number_format = '#,##0.00'
        ws.cell(row, 14).font = Font(bold=True)
        
        # Formatowanie kolumn
        ws.column_dimensions['A'].width = 30
        for col in range(2, 15):
            ws.column_dimensions[get_column_letter(col)].width = 12
        
        # Zamrożenie nagłówków
        ws.freeze_panes = 'B4'
    
    def _create_uncategorized_sheet(self, wb: Workbook, uncategorized):
        """Arkusz z nieprzypisanymi transakcjami"""
        ws = wb.create_sheet("Nieprzypisane")
        
        # Nagłówki
        headers = ['Data', 'Kontrahent', 'Opis', 'Kwota', 'Bank', 'ID']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        
        # Dane
        for row, trans in enumerate(uncategorized, 2):
            ws.cell(row, 1, trans.date.strftime('%Y-%m-%d'))
            ws.cell(row, 2, trans.counterparty)
            ws.cell(row, 3, trans.description)
            ws.cell(row, 4, float(trans.amount))
            ws.cell(row, 5, trans.source_bank)
            ws.cell(row, 6, trans.id)
            
            ws.cell(row, 4).number_format = '#,##0.00'
        
        # Szerokości kolumn
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 18
        
        # AutoFilter
        ws.auto_filter.ref = f"A1:F{len(uncategorized) + 1}"
    
    def _create_all_transactions_sheet(self, wb: Workbook, transactions):
        """Arkusz ze wszystkimi transakcjami"""
        ws = wb.create_sheet("Wszystkie transakcje")
        
        # Nagłówki
        headers = ['Data', 'Kontrahent', 'Opis', 'Kwota', 'Kategoria', 'Podkategoria', 'Bank', 'ID']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Dane
        for row, trans in enumerate(sorted(transactions, key=lambda t: t.date, reverse=True), 2):
            ws.cell(row, 1, trans.date.strftime('%Y-%m-%d'))
            ws.cell(row, 2, trans.counterparty)
            ws.cell(row, 3, trans.description)
            ws.cell(row, 4, float(trans.amount))
            ws.cell(row, 5, trans.category_main or '')
            ws.cell(row, 6, trans.category_sub or '')
            ws.cell(row, 7, trans.source_bank)
            ws.cell(row, 8, trans.id)
            
            ws.cell(row, 4).number_format = '#,##0.00'
            
            # Kolorowanie co drugi wiersz
            if row % 2 == 0:
                for col in range(1, 9):
                    ws.cell(row, col).fill = PatternFill(
                        start_color="F0F0F0", end_color="F0F0F0", fill_type="solid"
                    )
        
        # Szerokości
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 25
        ws.column_dimensions['G'].width = 10
        ws.column_dimensions['H'].width = 18
        
        # AutoFilter
        ws.auto_filter.ref = f"A1:H{len(transactions) + 1}"
```

### Krok 6: CLI Interface (Dzień 8)

#### cli/main.py
```python
import click
from pathlib import Path
import sys

from bank_analyzer import (
    detect_and_parse,
    RuleEngine,
    ManualOverrides,
    Aggregator,
    ExcelExporter,
)
from bank_analyzer.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--config', type=click.Path(), help='Ścieżka do pliku konfiguracyjnego')
@click.option('--verbose', is_flag=True, help='Tryb verbose')
@click.pass_context
def cli(ctx, config, verbose):
    """Bank Analyzer - narzędzie do analizy wyciągów bankowych"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    
    # Setup logging
    log_level = 'DEBUG' if verbose else 'INFO'
    setup_logging(log_level)


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), default='data/output/wydatki.xlsx',
              help='Ścieżka do pliku wyjściowego')
@click.option('--rules', type=click.Path(), default='config/rules.yaml',
              help='Plik z regułami kategoryzacji')
@click.option('--categories', type=click.Path(), default='config/categories.yaml',
              help='Plik z definicją kategorii')
@click.option('--overrides', type=click.Path(), default='data/manual_overrides.yaml',
              help='Plik z ręcznymi nadpisaniami')
def analyze(files, output, rules, categories, overrides):
    """Analizuj pliki CSV i wygeneruj raport"""
    
    logger.info(f"Rozpoczynam analizę {len(files)} plików")
    
    # Parse wszystkie pliki
    all_transactions = []
    for file_path in files:
        try:
            logger.info(f"Przetwarzam: {file_path}")
            transactions = detect_and_parse(Path(file_path))
            all_transactions.extend(transactions)
        except Exception as e:
            logger.error(f"Błąd przetwarzania {file_path}: {e}")
            continue
    
    if not all_transactions:
        logger.error("Brak transakcji do przetworzenia")
        sys.exit(1)
    
    logger.info(f"Sparsowano łącznie {len(all_transactions)} transakcji")
    
    # Kategoryzacja
    logger.info("Kategoryzacja transakcji...")
    rule_engine = RuleEngine(Path(rules))
    manual_overrides = ManualOverrides(Path(overrides))
    
    categorized_count = 0
    for trans in all_transactions:
        # Sprawdź manual override
        override = manual_overrides.get(trans.id)
        if override:
            trans.category_main, trans.category_sub = override
            trans.manual_override = True
            categorized_count += 1
        else:
            # Kategoryzuj regułami
            trans.category_main, trans.category_sub = rule_engine.categorize(trans)
            if trans.category_sub != "Nieprzypisane":
                categorized_count += 1
    
    logger.info(f"Skategoryzowano {categorized_count}/{len(all_transactions)} transakcji")
    
    # Agregacja
    logger.info("Agregacja danych...")
    aggregator = Aggregator()
    aggregated = aggregator.aggregate(all_transactions)
    
    # Eksport
    logger.info(f"Eksport do {output}")
    exporter = ExcelExporter()
    exporter.export(aggregated, Path(output))
    
    # Statystyki
    stats = rule_engine.get_stats()
    logger.info("Top 10 użytych reguł:")
    for rule_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {rule_name}: {count}")
    
    logger.info(f"✓ Gotowe! Plik zapisany: {output}")


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def parse(file):
    """Parsuj plik CSV i wyświetl informacje"""
    
    try:
        transactions = detect_and_parse(Path(file))
        
        click.echo(f"\n📊 Statystyki dla {file}:")
        click.echo(f"  Liczba transakcji: {len(transactions)}")
        click.echo(f"  Suma wydatków: {sum(t.amount for t in transactions if t.transaction_type == 'expense'):.2f} PLN")
        click.echo(f"  Suma przychodów: {sum(t.amount for t in transactions if t.transaction_type == 'income'):.2f} PLN")
        
        click.echo(f"\n🏦 Pierwsze 5 transakcji:")
        for i, trans in enumerate(transactions[:5], 1):
            click.echo(f"  {i}. {trans.date.strftime('%Y-%m-%d')} | {trans.counterparty} | {trans.amount} PLN")
    
    except Exception as e:
        click.echo(f"❌ Błąd: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--top', type=int, default=50, help='Liczba top wyników')
@click.option('--source', type=click.Path(), default='data/processed',
              help='Folder z przetworzonymi plikami')
def analyze_history(top, source):
    """Analizuj historyczne transakcje i generuj raporty"""
    
    source_path = Path(source)
    if not source_path.exists():
        click.echo(f"❌ Folder nie istnieje: {source}", err=True)
        sys.exit(1)
    
    # Znajdź wszystkie CSV
    csv_files = list(source_path.glob('*.csv'))
    
    if not csv_files:
        click.echo("❌ Brak plików CSV do analizy", err=True)
        sys.exit(1)
    
    click.echo(f"📁 Znaleziono {len(csv_files)} plików")
    
    # Parse wszystkie
    all_transactions = []
    for file_path in csv_files:
        try:
            transactions = detect_and_parse(file_path)
            all_transactions.extend(transactions)
        except:
            continue
    
    if not all_transactions:
        click.echo("❌ Brak transakcji", err=True)
        sys.exit(1)
    
    # Analiza kontrahentów
    from collections import Counter
    counterparties = Counter(t.counterparty for t in all_transactions)
    
    click.echo(f"\n🏪 Top {top} kontrahentów:")
    for counterparty, count in counterparties.most_common(top):
        click.echo(f"  {counterparty}: {count} transakcji")
    
    # TODO: Export do CSV dla dalszej analizy


@cli.command()
@click.option('--source', type=click.Path(), default='data/processed',
              help='Folder z archiwum')
@click.option('--rules', type=click.Path(), default='config/rules.yaml',
              help='Plik z regułami')
@click.option('--output', type=click.Path(), default='data/output/wydatki.xlsx',
              help='Plik wyjściowy')
def reprocess(source, rules, output):
    """Przetwórz ponownie archiwum z nowymi regułami"""
    
    click.echo("🔄 Ponowne przetwarzanie archiwum...")
    
    # Użyj funkcji analyze na plikach z archiwum
    source_path = Path(source)
    csv_files = list(source_path.glob('*.csv'))
    
    if not csv_files:
        click.echo("❌ Brak plików w archiwum", err=True)
        sys.exit(1)
    
    ctx = click.get_current_context()
    ctx.invoke(analyze, files=csv_files, output=output, rules=rules)


if __name__ == '__main__':
    cli(obj={})
```

### Krok 7: Testy (Dzień 9-10)

#### tests/test_parsers.py
```python
import pytest
from pathlib import Path
from bank_analyzer.parsers import detect_and_parse, PKOParser, AliorParser

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def test_pko_parser_can_parse():
    """Test detekcji formatu PKO"""
    parser = PKOParser()
    assert parser.can_parse(FIXTURES_DIR / 'pko_sample.csv')
    assert not parser.can_parse(FIXTURES_DIR / 'alior_sample.csv')


def test_alior_parser_can_parse():
    """Test detekcji formatu Alior"""
    parser = AliorParser()
    assert parser.can_parse(FIXTURES_DIR / 'alior_sample.csv')
    assert not parser.can_parse(FIXTURES_DIR / 'pko_sample.csv')


def test_pko_parser_parse():
    """Test parsowania PKO"""
    transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')
    
    assert len(transactions) > 0
    assert all(t.source_bank == 'PKO' for t in transactions)
    assert all(t.date is not None for t in transactions)
    assert all(t.amount > 0 for t in transactions)


def test_alior_parser_parse():
    """Test parsowania Alior"""
    transactions = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')
    
    assert len(transactions) > 0
    assert all(t.source_bank == 'ALIOR' for t in transactions)
    assert all(t.date is not None for t in transactions)
    assert all(t.amount > 0 for t in transactions)
```

### Krok 8: Dokumentacja (Dzień 10)

#### README.md
```markdown
# kma-bank-analyzer

Automatyczne przetwarzanie wyciągów bankowych z kategoryzacją transakcji i generowaniem raportów.

## Instalacja

```bash
# Clone repo
git clone https://github.com/[username]/kma-bank-analyzer.git
cd kma-bank-analyzer

# Utwórz virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows

# Instalacja w trybie dev
pip install -e .
pip install -r requirements-dev.txt
```

## Quick Start

```bash
# 1. Skopiuj przykładowe pliki konfiguracyjne
cp config/categories.example.yaml config/categories.yaml
cp config/rules.example.yaml config/rules.yaml

# 2. Umieść wyciągi CSV w data/input/

# 3. Uruchom analizę
bank-analyzer analyze data/input/*.csv

# 4. Sprawdź wynik w data/output/wydatki.xlsx
```

## Komendy CLI

### Analiza plików
```bash
bank-analyzer analyze plik1.csv plik2.csv --output raport.xlsx
```

### Parsowanie (bez kategoryzacji)
```bash
bank-analyzer parse plik.csv
```

### Analiza historyczna
```bash
bank-analyzer analyze-history --top 50
```

### Reprocessing
```bash
bank-analyzer reprocess
```

## Obsługiwane banki

- PKO BP
- Alior Bank

## Dodawanie nowego banku

Zobacz [docs/adding-banks.md](docs/adding-banks.md)

## License

MIT
```

## Deliverables Fazy 1

### Checklist

- [ ] Struktura projektu utworzona
- [ ] Model Transaction zaimplementowany
- [ ] Parsery PKO i Alior działają
- [ ] Detector formatu działa
- [ ] Rule Engine kategoryzuje
- [ ] Manual Overrides działają
- [ ] Aggregator agreguje dane
- [ ] Excel Exporter generuje pliki
- [ ] CLI wszystkie komendy działają
- [ ] Testy napisane (>80% coverage)
- [ ] README.md kompletne
- [ ] Przykładowe config files
- [ ] .gitignore poprawny

### Przykładowe użycie

```bash
# Instalacja
pip install -e .

# Analiza
bank-analyzer analyze data/input/*.csv

# Wynik w: data/output/wydatki_2025.xlsx
```

### Next Steps

Po zakończeniu Fazy 1 → **Faza 2: FastAPI Microservice**
