"""Tests for bank statement parsers."""

import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from bank_analyzer.parsers import detect_and_parse, detect_format, PKOParser, AliorParser
from bank_analyzer.models.transaction import Transaction

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


class TestPKOParser:
    """Tests for PKO BP parser."""

    def test_can_parse_pko_file(self):
        """Test that PKO parser detects PKO format."""
        parser = PKOParser()
        assert parser.can_parse(FIXTURES_DIR / 'pko_sample.csv')

    def test_cannot_parse_alior_file(self):
        """Test that PKO parser rejects Alior format."""
        parser = PKOParser()
        assert not parser.can_parse(FIXTURES_DIR / 'alior_sample.csv')

    def test_parse_pko_file(self):
        """Test parsing PKO CSV file."""
        transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')

        assert len(transactions) == 8
        assert all(isinstance(t, Transaction) for t in transactions)
        assert all(t.source_bank == 'PKO' for t in transactions)

    def test_pko_transaction_data(self):
        """Test that PKO transactions have correct data."""
        transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')

        # First transaction (expense)
        biedronka = transactions[0]
        assert biedronka.date == datetime(2026, 1, 8)
        assert biedronka.amount == Decimal('143.00')
        assert biedronka.transaction_type == 'expense'
        assert biedronka.currency == 'PLN'

        # Income transaction
        income = [t for t in transactions if t.transaction_type == 'income'][0]
        assert income.amount == Decimal('5000.00')


class TestAliorParser:
    """Tests for Alior Bank parser."""

    def test_can_parse_alior_file(self):
        """Test that Alior parser detects Alior format."""
        parser = AliorParser()
        assert parser.can_parse(FIXTURES_DIR / 'alior_sample.csv')

    def test_cannot_parse_pko_file(self):
        """Test that Alior parser rejects PKO format."""
        parser = AliorParser()
        assert not parser.can_parse(FIXTURES_DIR / 'pko_sample.csv')

    def test_parse_alior_file(self):
        """Test parsing Alior CSV file."""
        transactions = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')

        assert len(transactions) == 8
        assert all(isinstance(t, Transaction) for t in transactions)
        assert all(t.source_bank == 'ALIOR' for t in transactions)

    def test_alior_transaction_data(self):
        """Test that Alior transactions have correct data."""
        transactions = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')

        # Find Carrefour transaction
        carrefour = [t for t in transactions if 'carrefour' in t.counterparty.lower()][0]
        assert carrefour.amount == Decimal('862.87')
        assert carrefour.transaction_type == 'expense'

        # Income transaction
        income = [t for t in transactions if t.transaction_type == 'income'][0]
        assert income.amount == Decimal('7500.00')


class TestDetector:
    """Tests for format detection."""

    def test_detect_pko_format(self):
        """Test detecting PKO format."""
        bank = detect_format(FIXTURES_DIR / 'pko_sample.csv')
        assert bank == 'PKO'

    def test_detect_alior_format(self):
        """Test detecting Alior format."""
        bank = detect_format(FIXTURES_DIR / 'alior_sample.csv')
        assert bank == 'ALIOR'

    def test_detect_unknown_format(self, tmp_path):
        """Test detecting unknown format."""
        # Create a random CSV file
        unknown_file = tmp_path / 'unknown.csv'
        unknown_file.write_text('col1,col2,col3\n1,2,3\n')

        bank = detect_format(unknown_file)
        assert bank == 'UNKNOWN'

    def test_detect_and_parse_nonexistent(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            detect_and_parse(Path('/nonexistent/file.csv'))

    def test_detect_and_parse_wrong_extension(self, tmp_path):
        """Test error handling for wrong file extension."""
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('test')

        with pytest.raises(ValueError, match='Unsupported file format'):
            detect_and_parse(txt_file)
