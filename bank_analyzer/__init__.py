"""
Bank Analyzer - Library for parsing and analyzing bank statements.

This library provides tools for:
- Parsing CSV statements from various Polish banks (PKO BP, Alior)
- Categorizing transactions using rule-based system
- Aggregating expenses by categories and time periods
- Exporting results to Excel format
"""

from bank_analyzer.models.transaction import Transaction
from bank_analyzer.parsers import detect_and_parse, detect_format, AVAILABLE_PARSERS
from bank_analyzer.categorizer import RuleEngine, ManualOverrides
from bank_analyzer.aggregator import Aggregator
from bank_analyzer.exporters import ExcelExporter, JSONExporter

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "detect_and_parse",
    "detect_format",
    "AVAILABLE_PARSERS",
    "RuleEngine",
    "ManualOverrides",
    "Aggregator",
    "ExcelExporter",
    "JSONExporter",
]
