"""Tests for transaction aggregation."""

import pytest
from decimal import Decimal
from datetime import datetime

from bank_analyzer.aggregator import Aggregator
from bank_analyzer.models.transaction import Transaction


class TestAggregator:
    """Tests for the Aggregator class."""

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing."""
        return [
            Transaction(
                date=datetime(2026, 1, 15),
                description="Biedronka zakupy",
                amount=Decimal('100.00'),
                transaction_type='expense',
                counterparty='Biedronka',
                category_main='Jedzenie',
                category_sub='Zakupy spożywcze',
            ),
            Transaction(
                date=datetime(2026, 1, 20),
                description="Lidl zakupy",
                amount=Decimal('150.00'),
                transaction_type='expense',
                counterparty='Lidl',
                category_main='Jedzenie',
                category_sub='Zakupy spożywcze',
            ),
            Transaction(
                date=datetime(2026, 1, 25),
                description="McDonald's",
                amount=Decimal('45.00'),
                transaction_type='expense',
                counterparty='McDonalds',
                category_main='Jedzenie',
                category_sub='Restauracje',
            ),
            Transaction(
                date=datetime(2026, 2, 10),
                description="Orlen paliwo",
                amount=Decimal('250.00'),
                transaction_type='expense',
                counterparty='Orlen',
                category_main='Transport',
                category_sub='Paliwo',
            ),
            Transaction(
                date=datetime(2026, 1, 1),
                description="Wynagrodzenie",
                amount=Decimal('5000.00'),
                transaction_type='income',
                counterparty='Pracodawca',
                category_main='Przychody',
                category_sub='Wynagrodzenie',
            ),
            Transaction(
                date=datetime(2026, 1, 30),
                description="Nieznany sklep",
                amount=Decimal('75.00'),
                transaction_type='expense',
                counterparty='Unknown',
                category_main='Inne wydatki',
                category_sub='Nieprzypisane',
            ),
        ]

    def test_aggregate_basic(self, sample_transactions):
        """Test basic aggregation."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        assert 'years' in result
        assert 2026 in result['years']
        assert 'uncategorized' in result
        assert 'all_transactions' in result

    def test_aggregate_monthly_totals(self, sample_transactions):
        """Test monthly totals are correct."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        jan_data = result['years'][2026]['months'][1]

        # January expenses: 100 + 150 + 45 + 75 = 370
        assert float(jan_data['total_expense']) == 370.00

        # January income: 5000
        assert float(jan_data['total_income']) == 5000.00

    def test_aggregate_categories(self, sample_transactions):
        """Test category aggregation."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        jan_cats = result['years'][2026]['months'][1]['categories']

        # Jedzenie category
        assert 'Jedzenie' in jan_cats
        assert 'Zakupy spożywcze' in jan_cats['Jedzenie']
        assert float(jan_cats['Jedzenie']['Zakupy spożywcze']['total']) == 250.00
        assert jan_cats['Jedzenie']['Zakupy spożywcze']['count'] == 2

    def test_aggregate_uncategorized(self, sample_transactions):
        """Test uncategorized transactions tracking."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        uncategorized = result['uncategorized']
        assert len(uncategorized) == 1
        assert uncategorized[0].counterparty == 'Unknown'

    def test_aggregate_yearly_totals(self, sample_transactions):
        """Test yearly totals."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        year_data = result['years'][2026]

        # Total expenses: 100 + 150 + 45 + 250 + 75 = 620
        assert float(year_data['total_year_expense']) == 620.00

        # Total income: 5000
        assert float(year_data['total_year_income']) == 5000.00

    def test_aggregate_yearly_categories(self, sample_transactions):
        """Test yearly category summary."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        year_cats = result['years'][2026]['categories_year']

        assert 'Jedzenie' in year_cats
        assert 'Zakupy spożywcze' in year_cats['Jedzenie']

    def test_aggregate_empty_list(self):
        """Test aggregation with empty list."""
        aggregator = Aggregator()
        result = aggregator.aggregate([])

        assert result['years'] == {}
        assert result['uncategorized'] == []
        assert result['all_transactions'] == []

    def test_get_monthly_summary(self, sample_transactions):
        """Test getting monthly summary."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        summary = aggregator.get_monthly_summary(result, 2026, 1)

        assert 'total_expense' in summary
        assert 'categories' in summary

    def test_get_top_expenses(self, sample_transactions):
        """Test getting top expense categories."""
        aggregator = Aggregator()
        result = aggregator.aggregate(sample_transactions)

        top = aggregator.get_top_expenses(result, year=2026, limit=5)

        assert len(top) > 0
        # First should be highest expense
        assert top[0]['total'] >= top[-1]['total']
