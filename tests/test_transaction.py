"""Tests for Transaction model."""

import pytest
from decimal import Decimal
from datetime import datetime

from bank_analyzer.models.transaction import Transaction


class TestTransaction:
    """Tests for Transaction dataclass."""

    def test_create_transaction(self):
        """Test creating a basic transaction."""
        trans = Transaction(
            date=datetime(2026, 1, 15),
            description="Test purchase",
            amount=Decimal('100.50'),
            transaction_type='expense',
        )

        assert trans.date == datetime(2026, 1, 15)
        assert trans.description == "Test purchase"
        assert trans.amount == Decimal('100.50')
        assert trans.transaction_type == 'expense'

    def test_auto_generate_id(self):
        """Test that ID is auto-generated."""
        trans = Transaction(
            date=datetime(2026, 1, 15),
            description="Test",
            amount=Decimal('100'),
            transaction_type='expense',
        )

        assert trans.id is not None
        assert len(trans.id) == 16

    def test_same_data_same_id(self):
        """Test that same data produces same ID."""
        trans1 = Transaction(
            date=datetime(2026, 1, 15),
            description="Test",
            amount=Decimal('100'),
            transaction_type='expense',
        )
        trans2 = Transaction(
            date=datetime(2026, 1, 15),
            description="Test",
            amount=Decimal('100'),
            transaction_type='expense',
        )

        assert trans1.id == trans2.id

    def test_different_data_different_id(self):
        """Test that different data produces different ID."""
        trans1 = Transaction(
            date=datetime(2026, 1, 15),
            description="Test1",
            amount=Decimal('100'),
            transaction_type='expense',
        )
        trans2 = Transaction(
            date=datetime(2026, 1, 15),
            description="Test2",
            amount=Decimal('100'),
            transaction_type='expense',
        )

        assert trans1.id != trans2.id

    def test_to_dict(self):
        """Test conversion to dictionary."""
        trans = Transaction(
            date=datetime(2026, 1, 15),
            description="Test",
            amount=Decimal('100'),
            transaction_type='expense',
            counterparty='Shop',
            category_main='Shopping',
            category_sub='General',
        )

        data = trans.to_dict()

        assert data['date'] == '2026-01-15T00:00:00'
        assert data['description'] == 'Test'
        assert data['amount'] == 100.0
        assert data['counterparty'] == 'Shop'
        assert data['category_main'] == 'Shopping'
        assert data['category_sub'] == 'General'

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'date': '2026-01-15T00:00:00',
            'description': 'Test',
            'amount': 100.0,
            'transaction_type': 'expense',
            'counterparty': 'Shop',
            'currency': 'PLN',
            'category_main': 'Shopping',
            'category_sub': 'General',
            'source_bank': 'PKO',
            'source_file': 'test.csv',
            'manual_override': False,
        }

        trans = Transaction.from_dict(data)

        assert trans.date == datetime(2026, 1, 15)
        assert trans.description == 'Test'
        assert trans.amount == Decimal('100.0')
        assert trans.counterparty == 'Shop'

    def test_str_representation(self):
        """Test string representation."""
        trans = Transaction(
            date=datetime(2026, 1, 15),
            description="Test",
            amount=Decimal('100.50'),
            transaction_type='expense',
            counterparty='TestShop',
            category_main='Shopping',
        )

        str_repr = str(trans)
        assert '2026-01-15' in str_repr
        assert 'TestShop' in str_repr
        assert '100.50' in str_repr

    def test_amount_as_float_converted(self):
        """Test that float amount is converted to Decimal."""
        trans = Transaction(
            date=datetime.now(),
            description="Test",
            amount=100.5,  # Float instead of Decimal
            transaction_type='expense',
        )

        assert isinstance(trans.amount, Decimal)
        assert trans.amount == Decimal('100.5')

    def test_default_values(self):
        """Test default values."""
        trans = Transaction(
            date=datetime.now(),
            description="Test",
            amount=Decimal('100'),
            transaction_type='expense',
        )

        assert trans.currency == 'PLN'
        assert trans.counterparty == ''
        assert trans.source_bank == ''
        assert trans.category_main is None
        assert trans.category_sub is None
        assert trans.manual_override is False
