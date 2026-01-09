# Struktury danych i formaty plików

## CSV Formats

### PKO BP

**Przykładowy plik: pko_wyciag_2025_12.csv**

```csv
"Data operacji","Data waluty","Typ transakcji","Kwota","Waluta","Saldo po transakcji","Opis transakcji","","","","",""
"2026-01-08","2026-01-08","Przelew na telefon przychodz. zew.","-143.00","PLN","+8482.92","Rachunek odbiorcy :","","Nazwa odbiorcy: ","Tytuł: ZAMOWIENIE  OD: 48519842852 DO: 485*****024","",""
"2026-01-04","2026-01-02","Płatność kartą","-59.80","PLN","+9337.74","Tytuł:  74810316002180039654093 ","Lokalizacja: Adres: Delikatesy Centrum Miasto: Warszawa Kraj: POLSKA","Data wykonania operacji: 2026-01-02","Oryginalna kwota operacji: 59.80","Numer karty: 425125******3732",""
"2026-01-03","2026-01-02","Płatność web - kod mobilny","-159.80","PLN","+9397.54","Tytuł: 00000092928593669  ","Numer telefonu: 48519842852","Lokalizacja: Adres: https://www.frisco.pl","'Operacja: 00000092928593669","Numer referencyjny: 00000092928593669",""
```

**Charakterystyka:**
- Separator: przecinek
- Kodowanie: Windows-1250
- Format daty: YYYY-MM-DD
- Format kwoty: liczba z kropką, znak +/- przed wartością
- Liczba kolumn: 12 (wiele pustych)
- Nagłówek: wiersz 1

### Alior Bank

**Przykładowy plik: alior_wyciag_2025_12.csv**

```csv
Kryteria transakcji: Okres: 01-12-2025 - 31-12-2025;Typ transakcji: Uznania/Obciążenia;Produkty: 
Data transakcji;Data księgowania;Nazwa nadawcy;Nazwa odbiorcy;Szczegóły transakcji;Kwota operacji;Waluta operacji;Kwota w walucie rachunku;Waluta rachunku;Numer rachunku nadawcy;Numer rachunku odbiorcy
31-12-2025;31-12-2025;;;Opłata podstawowa za kartę: 6.00;-6,00;PLN;-6,00;PLN;;
29-12-2025;31-12-2025;;;ZABKA ZD382 K.1 WARSZAWA PL;-20,50;PLN;-20,50;PLN;;
29-12-2025;31-12-2025;;;Storytel Sp. z.o.o. Warszawa PL;-49,90;PLN;-49,90;PLN;;
20-12-2025;22-12-2025;;;CARREFOUR HIPERMARKET WARSZAWA PL;-862,87;PLN;-862,87;PLN;;
```

**Charakterystyka:**
- Separator: średnik
- Kodowanie: UTF-8
- Format daty: DD-MM-YYYY
- Format kwoty: liczba z przecinkiem, znak - dla wydatków
- Liczba kolumn: 11
- Wiersz 1: metadane (do pominięcia)
- Nagłówek: wiersz 2

## Transaction Model

**Znormalizowana struktura transakcji:**

```python
@dataclass
class Transaction:
    # Identyfikator
    id: str                    # UUID z hash(date+description+amount)
    
    # Podstawowe dane
    date: datetime             # Data transakcji
    description: str           # Pełny opis (sklejone części)
    counterparty: str          # Wyekstrahowany kontrahent
    amount: Decimal            # Kwota (zawsze dodatnia)
    
    # Klasyfikacja
    transaction_type: str      # 'expense' lub 'income'
    currency: str              # Domyślnie 'PLN'
    
    # Kategoryzacja
    category_main: Optional[str] = None      # Kategoria główna
    category_sub: Optional[str] = None       # Podkategoria
    manual_override: bool = False            # Czy ręcznie nadpisana
    
    # Metadata
    source_bank: str           # 'PKO', 'ALIOR', itp.
    source_file: str           # Nazwa pliku źródłowego
    processed_at: datetime     # Kiedy przetworzono
```

**Przykład JSON:**
```json
{
  "id": "a1b2c3d4e5f67890",
  "date": "2025-12-20T00:00:00",
  "description": "CARREFOUR HIPERMARKET WARSZAWA PL",
  "counterparty": "carrefour",
  "amount": 862.87,
  "transaction_type": "expense",
  "currency": "PLN",
  "category_main": "Jedzenie",
  "category_sub": "Zakupy spożywcze",
  "manual_override": false,
  "source_bank": "ALIOR",
  "source_file": "alior_2025_12.csv",
  "processed_at": "2026-01-09T10:00:00"
}
```

## Aggregated Data Structure

**Struktura zagregowanych danych:**

```json
{
  "years": {
    "2025": {
      "months": {
        "12": {
          "categories": {
            "Jedzenie": {
              "Zakupy spożywcze": {
                "total": 3240.50,
                "count": 28,
                "transactions": [...]
              },
              "Restauracje": {
                "total": 567.80,
                "count": 8,
                "transactions": [...]
              }
            },
            "Transport": {
              "Paliwo": {
                "total": 450.00,
                "count": 3,
                "transactions": [...]
              }
            }
          },
          "total": 5678.90,
          "total_income": 0.00,
          "total_expense": 5678.90
        }
      },
      "total_year": 67890.12,
      "categories_year": {
        "Jedzenie": {
          "Zakupy spożywcze": 38886.00,
          "Restauracje": 6809.60
        },
        "Transport": {
          "Paliwo": 5400.00
        }
      }
    }
  },
  "uncategorized": [
    {
      "id": "xyz123",
      "date": "2025-12-15T00:00:00",
      "description": "Nieznany sklep ABC",
      "amount": 125.50,
      ...
    }
  ],
  "all_transactions": [...]
}
```

## State Management

**state.json - tracking przetworzonych plików:**

```json
{
  "last_run": "2026-01-09T14:30:00Z",
  "processed_files": [
    "/data/input/pko_2025_12.csv",
    "/data/input/alior_2025_12.csv",
    "/data/input/pko_2026_01.csv"
  ],
  "total_transactions": 1234,
  "last_month_stats": {
    "2026-01": {
      "total": 2345.67,
      "categorized": 89,
      "uncategorized": 3
    }
  }
}
```

## Excel Output Structure

### Arkusz "Podsumowanie roczne"

```
Rok 2025

Kategoria              | Sty    | Lut    | Mar    | ... | Gru    | SUMA ROCZNA
--------------------------------------------------------------------------------------
Jedzenie              | 1234.56| 1456.78| ...    | ... | ...    | 14678.90
  Zakupy spożywcze    | 890.00 | 1020.00| ...    | ... | ...    | 10680.00
  Restauracje         | 344.56 | 436.78 | ...    | ... | ...    | 3998.90
Transport             | 567.89 | 678.90 | ...    | ... | ...    | 6790.00
  Paliwo              | 400.00 | 500.00 | ...    | ... | ...    | 4800.00
  Serwis pojazdu      | 167.89 | 178.90 | ...    | ... | ...    | 1990.00
...
--------------------------------------------------------------------------------------
SUMA MIESIĘCZNA      | 5678.90| 6789.01| ...    | ... | ...    | 67890.12
```

### Arkusz "Nieprzypisane"

```
Data       | Kontrahent      | Opis                    | Kwota   | Bank   | ID
-----------------------------------------------------------------------------------
2025-12-15 | Nieznany sklep | ABC Store Warszawa      | 125.50  | ALIOR  | xyz123
2025-12-20 | XYZ            | Płatność kartą XYZ      | 89.00   | PKO    | abc456
```

### Arkusz "Wszystkie transakcje"

```
Data       | Kontrahent | Opis            | Kwota  | Kategoria | Podkategoria      | Bank
-------------------------------------------------------------------------------------------------
2025-12-31 | Biedronka  | Zakupy         | 156.78 | Jedzenie  | Zakupy spożywcze | ALIOR
2025-12-30 | Orlen      | Paliwo         | 250.00 | Transport | Paliwo           | PKO
...
```

## Google Sheets Structure

### Arkusz "Podsumowanie"

**Kolumny:**
```
A: Rok (int)
B: Miesiąc (int, 1-12)
C: Kategoria główna (string)
D: Podkategoria (string)
E: Kwota (float)
F: Liczba transakcji (int)
G: Data aktualizacji (timestamp)
```

**Przykładowe dane:**
```
2025 | 12 | Jedzenie  | Zakupy spożywcze | 3240.50 | 28 | 2026-01-09 14:30:00
2025 | 12 | Jedzenie  | Restauracje      | 567.80  | 8  | 2026-01-09 14:30:00
2025 | 12 | Transport | Paliwo           | 450.00  | 3  | 2026-01-09 14:30:00
```

### Formulas dla podsumowań

```
# Suma dla kategorii w danym miesiącu
=SUMIFS(E:E, A:A, 2025, B:B, 12, C:C, "Jedzenie")

# Suma roczna dla kategorii
=SUMIFS(E:E, A:A, 2025, C:C, "Jedzenie")

# Średnia miesięczna
=AVERAGE(SUMIFS(E:E, A:A, 2025, B:B, {1;2;3;4;5;6;7;8;9;10;11;12}, C:C, "Jedzenie"))
```

## API Request/Response Examples

### POST /api/v1/analyze

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "files=@pko_2025_12.csv" \
  -F "files=@alior_2025_12.csv" \
  -F "output_format=json"
```

**Response:**
```json
{
  "status": "success",
  "transactions_count": 156,
  "categorized_count": 154,
  "uncategorized_count": 2,
  "aggregated_data": {
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
    },
    "uncategorized": [...]
  },
  "download_url": null
}
```

### GET /api/v1/categories

**Response:**
```json
{
  "categories": [
    {
      "name": "Jedzenie",
      "subcategories": [
        "Zakupy spożywcze",
        "Restauracje",
        "Kawiarnie"
      ]
    },
    {
      "name": "Transport",
      "subcategories": [
        "Paliwo",
        "Komunikacja miejska",
        "Taxi/Uber"
      ]
    }
  ]
}
```

## n8n Workflow Data Flow

**1. Input (List Files):**
```json
{
  "stdout": "/data/input/pko_2025_12.csv\n/data/input/alior_2025_12.csv"
}
```

**2. After Filter:**
```json
[
  { "filepath": "/data/input/pko_2025_12.csv" },
  { "filepath": "/data/input/alior_2025_12.csv" }
]
```

**3. After API Call:**
```json
{
  "status": "success",
  "transactions_count": 156,
  "aggregated_data": {...}
}
```

**4. Transformed for Sheets:**
```json
[
  {
    "year": 2025,
    "month": 12,
    "category_main": "Jedzenie",
    "category_sub": "Zakupy spożywcze",
    "amount": 3240.50,
    "transaction_count": 28,
    "updated_at": "2026-01-09T14:30:00Z"
  },
  ...
]
```

## Logs Format

**Application logs (app.log):**
```
2026-01-09 14:30:22 | INFO     | main | Pipeline rozpoczęty
2026-01-09 14:30:23 | INFO     | detector | Wykryto format PKO dla pko_wyciag.csv
2026-01-09 14:30:25 | INFO     | pko_parser | Przetworzono 156 transakcji, pominięto 2
2026-01-09 14:30:26 | WARNING  | pko_parser | Niepoprawny wiersz 45: invalid date format
2026-01-09 14:30:30 | INFO     | categorizer | Skategoryzowano 154/156 transakcji
2026-01-09 14:30:35 | INFO     | exporter | Wygenerowano wydatki_2025.xlsx
2026-01-09 14:30:36 | INFO     | main | Pipeline zakończony pomyślnie
```

**Error logs (errors.log):**
```
[2026-01-09 14:30:00] [pko_2025_12.csv] ValueError: Invalid date format in row 45
[2026-01-09 14:35:00] [alior_2025_12.csv] UnicodeDecodeError: Failed to decode with utf-8
```

## Backup Files

**Backup structure:**
```
backups/
├── config_20260109_030000.tar.gz
├── data_20260109_030000.tar.gz
├── n8n_20260109_030000.tar.gz
└── ...
```

**Backup contents:**
- config: categories.yaml, rules.yaml
- data: processed/, output/, state.json
- n8n: workflow data, credentials (encrypted)
