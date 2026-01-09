"""Parser for Alior Bank statements."""

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


class AliorParser(BaseParser):
    """Parser for Alior Bank statements in CSV format."""

    def can_parse(self, file_path: Path) -> bool:
        """Detect Alior format by second line."""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                f.readline()  # Skip first line (metadata)
                second_line = f.readline()
                return "Data transakcji;Data księgowania" in second_line
        except Exception as e:
            logger.warning(f"Error checking Alior format: {e}")
            return False

    def parse(self, file_path: Path) -> List[Transaction]:
        """Parse Alior CSV file."""
        file_path = Path(file_path)
        encoding = self._detect_encoding(file_path)
        logger.info(f"Parsing Alior: {file_path.name} (encoding: {encoding})")

        transactions = []
        errors = []

        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
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
                        logger.debug(f"Error in row {row_num}: {e}")

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise ValueError(f"Failed to parse Alior file: {e}")

        logger.info(
            f"Alior: Processed {len(transactions)} transactions, "
            f"skipped {len(errors)} rows"
        )

        return transactions

    def _parse_row(self, row: List[str], source_file: str) -> Optional[Transaction]:
        """Parse single Alior row."""
        if len(row) < 7:
            return None

        # Skip empty rows
        if not any(cell.strip() for cell in row[:7]):
            return None

        # Extract data
        date_str = row[0].strip()
        if not date_str:
            return None

        sender = row[2].strip() if len(row) > 2 else ""
        recipient = row[3].strip() if len(row) > 3 else ""
        description = row[4].strip() if len(row) > 4 else ""
        amount_str = row[5].strip() if len(row) > 5 else ""
        currency = row[6].strip() if len(row) > 6 else "PLN"

        # Parse date (DD-MM-YYYY format)
        try:
            date = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")

        # Parse amount (comma as decimal separator)
        try:
            amount_clean = amount_str.replace(' ', '').replace(',', '.')
            is_expense = amount_clean.startswith('-')
            amount_clean = amount_clean.lstrip('+-')
            amount = Decimal(amount_clean)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid amount: {amount_str}")

        trans_type = 'expense' if is_expense else 'income'

        # Extract counterparty - combine all available info
        counterparty = self._extract_counterparty(sender, recipient, description)

        # Build full description from all non-empty fields
        desc_parts = []
        if sender:
            desc_parts.append(f"Od: {sender}")
        if recipient:
            desc_parts.append(f"Do: {recipient}")
        if description:
            desc_parts.append(description)
        full_description = " | ".join(desc_parts) if desc_parts else description

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

    def _extract_counterparty(
        self, sender: str, recipient: str, description: str
    ) -> str:
        """Extract counterparty from available fields."""
        # Priority: sender > recipient > extract from description

        if sender and sender.strip():
            return self._clean_text(sender)

        if recipient and recipient.strip():
            return self._clean_text(recipient)

        if description:
            # Try to extract name before " PL"
            match = re.search(r'^(.+?)\s+PL\s*$', description, re.IGNORECASE)
            if match:
                name = self._clean_text(match.group(1))
                if name:
                    return name

            # Try to extract meaningful part
            # Remove common patterns like card numbers, dates
            cleaned = re.sub(r'\s+K\.\d+', '', description)
            cleaned = re.sub(r'\d{4}-\d{2}-\d{2}', '', cleaned)

            # Take first meaningful word(s)
            parts = cleaned.split()
            if parts:
                # Take up to 3 first words
                name = ' '.join(parts[:3])
                name = self._clean_text(name)
                if name and len(name) > 2:
                    return name

        return "Nieznany"
