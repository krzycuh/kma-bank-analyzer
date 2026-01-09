"""Automatic bank format detection and parsing."""

from pathlib import Path
from typing import List, Type

from bank_analyzer.parsers.base_parser import BaseParser
from bank_analyzer.parsers.pko_parser import PKOParser
from bank_analyzer.parsers.alior_parser import AliorParser
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


# List of all available parsers (order matters for detection)
AVAILABLE_PARSERS: List[Type[BaseParser]] = [
    PKOParser,
    AliorParser,
]


def detect_and_parse(file_path: Path) -> List[Transaction]:
    """
    Automatically detect format and parse the file.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of transactions

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If no suitable parser is found
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.suffix.lower() != '.csv':
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    logger.info(f"Detecting format: {file_path.name}")

    # Try each parser
    for parser_class in AVAILABLE_PARSERS:
        parser = parser_class()
        try:
            if parser.can_parse(file_path):
                logger.info(f"Detected format: {parser.bank_name}")
                return parser.parse(file_path)
        except Exception as e:
            logger.debug(f"Parser {parser.bank_name} failed detection: {e}")
            continue

    # No parser matched
    supported_banks = ', '.join(
        p.__name__.replace('Parser', '') for p in AVAILABLE_PARSERS
    )
    raise ValueError(
        f"Unrecognized file format: {file_path.name}\n"
        f"Supported banks: {supported_banks}\n"
        f"If this is a new bank format, add an appropriate parser."
    )


def detect_format(file_path: Path) -> str:
    """
    Detect only the format without parsing.

    Args:
        file_path: Path to the file

    Returns:
        Bank name or "UNKNOWN"
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return "UNKNOWN"

    for parser_class in AVAILABLE_PARSERS:
        parser = parser_class()
        try:
            if parser.can_parse(file_path):
                return parser.bank_name
        except Exception:
            continue

    return "UNKNOWN"
