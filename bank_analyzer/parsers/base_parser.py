"""Abstract base class for bank statement parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from bank_analyzer.models.transaction import Transaction


class BaseParser(ABC):
    """
    Abstract base class for bank statement parsers.

    Each bank parser should inherit from this class and implement
    the can_parse() and parse() methods.
    """

    def __init__(self):
        self.bank_name = self.__class__.__name__.replace('Parser', '').upper()

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file format.

        Args:
            file_path: Path to the CSV file

        Returns:
            True if this parser can handle the file format
        """
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> List[Transaction]:
        """
        Parse CSV file to list of transactions.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of normalized transactions

        Raises:
            ValueError: If the file cannot be parsed
        """
        pass

    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding.

        Args:
            file_path: Path to the file

        Returns:
            Encoding name (e.g., 'utf-8', 'windows-1250')
        """
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                # Handle common encoding aliases
                if encoding:
                    encoding = encoding.lower()
                    if encoding in ('iso-8859-2', 'iso8859-2'):
                        return 'windows-1250'
                    return encoding
                return 'utf-8'
        except ImportError:
            # chardet not available, try common encodings
            return self._try_encodings(file_path)

    def _try_encodings(self, file_path: Path) -> str:
        """Try common encodings and return the first that works."""
        encodings = ['utf-8', 'windows-1250', 'iso-8859-2', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        return 'utf-8'  # Default fallback

    def _clean_text(self, text: str) -> str:
        """
        Clean text from excessive spaces and characters.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""
        # Remove multiple spaces
        text = ' '.join(text.split())
        return text.strip()
