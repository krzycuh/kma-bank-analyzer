"""Parser for PKO BP bank statements."""

import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional

from bank_analyzer.parsers.base_parser import BaseParser
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class PKOParser(BaseParser):
    """Parser for PKO BP bank statements in CSV format."""

    def can_parse(self, file_path: Path) -> bool:
        """Detect PKO format by header."""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                first_line = f.readline()
                # PKO has "Data operacji" as first column
                return "Data operacji" in first_line
        except Exception as e:
            logger.warning(f"Error checking PKO format: {e}")
            return False

    def parse(self, file_path: Path) -> List[Transaction]:
        """Parse PKO CSV file."""
        file_path = Path(file_path)
        encoding = self._detect_encoding(file_path)
        logger.info(f"Parsing PKO: {file_path.name} (encoding: {encoding})")

        transactions = []
        errors = []

        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                # Try to detect delimiter
                content = f.read()
                f.seek(0)

                # PKO uses comma as delimiter
                reader = csv.reader(f, delimiter=',')
                header = next(reader)  # Skip header

                for row_num, row in enumerate(reader, start=2):
                    try:
                        transaction = self._parse_row(row, file_path.name)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        errors.append((row_num, str(e)))
                        logger.debug(f"Error in row {row_num}: {e}")

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise ValueError(f"Failed to parse PKO file: {e}")

        logger.info(
            f"PKO: Processed {len(transactions)} transactions, "
            f"skipped {len(errors)} rows"
        )

        return transactions

    def _parse_row(self, row: List[str], source_file: str) -> Optional[Transaction]:
        """Parse single PKO row."""
        if len(row) < 6:
            return None

        # Skip empty rows
        if not any(cell.strip() for cell in row[:6]):
            return None

        # Extract data
        date_str = row[0].strip()
        if not date_str:
            return None

        amount_str = row[3].strip() if len(row) > 3 else ""
        currency = row[4].strip() if len(row) > 4 else "PLN"

        # Parse date (YYYY-MM-DD format)
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")

        # Parse amount
        try:
            # Remove spaces and handle Polish number format
            amount_clean = amount_str.replace(' ', '').replace(',', '.')
            # Determine transaction type from sign
            is_expense = amount_clean.startswith('-')
            amount_clean = amount_clean.lstrip('+-')
            amount = Decimal(amount_clean)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid amount: {amount_str}")

        trans_type = 'expense' if is_expense else 'income'

        # Build description from columns 6-11
        description_parts = []
        for i in range(6, min(12, len(row))):
            col = row[i].strip() if i < len(row) else ""
            if col:
                # Remove prefixes like "Tytuł:", "Lokalizacja:"
                col = re.sub(
                    r'^(Tytu[łl]|Lokalizacja|Nazwa odbiorcy|Adres|'
                    r'Rachunek odbiorcy|Data wykonania|Oryginalna kwota|'
                    r'Numer karty|Numer telefonu|Operacja|Numer referencyjny):\s*',
                    '', col, flags=re.IGNORECASE
                )
                if col:
                    description_parts.append(col)

        description = self._clean_text(' '.join(description_parts))

        # Extract counterparty
        counterparty = self._extract_counterparty(row[6:12] if len(row) > 6 else [])

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
        """Intelligent counterparty extraction from PKO description columns."""
        # Try 1: Look for "Nazwa odbiorcy:"
        for col in desc_columns:
            if not col:
                continue
            match = re.search(r'Nazwa odbiorcy:\s*(.+)', col, re.IGNORECASE)
            if match:
                name = self._clean_text(match.group(1))
                if name:
                    return name

        # Try 2: Look in "Adres:" (store name)
        for col in desc_columns:
            if not col:
                continue
            match = re.search(
                r'Adres:\s*([^M]+?)(?=\s*Miasto:|Kraj:|$)',
                col,
                re.IGNORECASE
            )
            if match:
                name = self._clean_text(match.group(1))
                # Remove "K.1" and similar
                name = re.sub(r'\s+K\.\d+', '', name)
                if name and len(name) > 2:
                    return name

        # Try 3: Look for common patterns in description
        for col in desc_columns:
            if not col:
                continue
            # Skip columns with only technical data
            if col.strip().startswith(('Data', 'Oryginalna', 'Numer', 'Operacja')):
                continue

            # Extract first meaningful part
            text = self._clean_text(col)
            if text:
                # Remove common prefixes
                text = re.sub(r'^(Tytu[łl]:\s*)', '', text, flags=re.IGNORECASE)
                # Take first part before common separators
                parts = re.split(r'\s{2,}|,\s+|\s+(?=\d{2,})', text)
                if parts and parts[0]:
                    name = self._clean_text(parts[0])
                    if name and len(name) > 2:
                        return name

        return "Nieznany"
