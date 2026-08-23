"""Tests for transaction categorization."""

import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from tempfile import NamedTemporaryFile

from bank_analyzer.categorizer import RuleEngine, ManualOverrides
from bank_analyzer.models.transaction import Transaction


class TestRuleEngine:
    """Tests for rule-based categorization."""

    @pytest.fixture
    def sample_rules_file(self, tmp_path):
        """Create a temporary rules file."""
        rules_content = """
rules:
  - name: "biedronka"
    pattern: "biedronka"
    field: "counterparty"
    match_type: "contains"
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "netflix"
    pattern: "netflix"
    field: "description"
    match_type: "contains"
    priority: 15
    category_main: "Subskrypcje"
    category_sub: "Streaming"

  - name: "zabka_regex"
    pattern: "zabka|żabka"
    field: "counterparty"
    match_type: "regex"
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"
"""
        rules_file = tmp_path / 'rules.yaml'
        rules_file.write_text(rules_content)
        return rules_file

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction."""
        return Transaction(
            date=datetime.now(),
            description="Zakupy w sklepie",
            amount=Decimal('100.00'),
            transaction_type='expense',
            counterparty='Biedronka Warszawa',
        )

    def test_load_rules(self, sample_rules_file):
        """Test loading rules from file."""
        engine = RuleEngine(sample_rules_file)
        assert len(engine.rules) == 3

    def test_categorize_by_counterparty(self, sample_rules_file, sample_transaction):
        """Test categorization by counterparty."""
        engine = RuleEngine(sample_rules_file)
        cat_main, cat_sub = engine.categorize(sample_transaction)

        assert cat_main == "Jedzenie"
        assert cat_sub == "Zakupy spożywcze"

    def test_categorize_by_description(self, sample_rules_file):
        """Test categorization by description."""
        engine = RuleEngine(sample_rules_file)

        trans = Transaction(
            date=datetime.now(),
            description="Netflix subscription",
            amount=Decimal('49.00'),
            transaction_type='expense',
            counterparty='Unknown',
        )

        cat_main, cat_sub = engine.categorize(trans)
        assert cat_main == "Subskrypcje"
        assert cat_sub == "Streaming"

    def test_categorize_regex(self, sample_rules_file):
        """Test regex pattern matching."""
        engine = RuleEngine(sample_rules_file)

        trans = Transaction(
            date=datetime.now(),
            description="Zakupy",
            amount=Decimal('20.00'),
            transaction_type='expense',
            counterparty='Zabka Z1234',
        )

        cat_main, cat_sub = engine.categorize(trans)
        assert cat_main == "Jedzenie"
        assert cat_sub == "Zakupy spożywcze"

    def test_uncategorized_transaction(self, sample_rules_file):
        """Test uncategorized transaction returns default."""
        engine = RuleEngine(sample_rules_file)

        trans = Transaction(
            date=datetime.now(),
            description="Random purchase",
            amount=Decimal('50.00'),
            transaction_type='expense',
            counterparty='Unknown Shop',
        )

        cat_main, cat_sub = engine.categorize(trans)
        assert cat_main == "Inne wydatki"
        assert cat_sub == "Nieprzypisane"

    def test_rule_stats(self, sample_rules_file, sample_transaction):
        """Test rule usage statistics."""
        engine = RuleEngine(sample_rules_file)
        engine.categorize(sample_transaction)
        engine.categorize(sample_transaction)

        stats = engine.get_stats()
        assert 'biedronka' in stats
        assert stats['biedronka'] == 2

    def test_empty_rules(self):
        """Test with no rules file."""
        engine = RuleEngine(None)
        assert len(engine.rules) == 0

    def test_add_rule_programmatically(self):
        """Test adding rules programmatically."""
        engine = RuleEngine(None)
        engine.add_rule(
            name='test_rule',
            pattern='test',
            category_main='Test',
            category_sub='TestSub',
        )

        trans = Transaction(
            date=datetime.now(),
            description="test transaction",
            amount=Decimal('10.00'),
            transaction_type='expense',
            counterparty='test shop',
        )

        cat_main, cat_sub = engine.categorize(trans)
        assert cat_main == "Test"
        assert cat_sub == "TestSub"


class TestManualOverrides:
    """Tests for manual overrides."""

    @pytest.fixture
    def sample_overrides_file(self, tmp_path):
        """Create a temporary overrides file."""
        content = """
overrides:
  - transaction_id: "abc123"
    category_main: "Transport"
    category_sub: "Taxi"
    note: "Manual override test"
"""
        overrides_file = tmp_path / 'overrides.yaml'
        overrides_file.write_text(content)
        return overrides_file

    def test_load_overrides(self, sample_overrides_file):
        """Test loading overrides."""
        overrides = ManualOverrides(sample_overrides_file)
        assert len(overrides.overrides) == 1

    def test_get_override(self, sample_overrides_file):
        """Test getting an override."""
        overrides = ManualOverrides(sample_overrides_file)
        result = overrides.get('abc123')

        assert result is not None
        assert result == ('Transport', 'Taxi')

    def test_get_nonexistent_override(self, sample_overrides_file):
        """Test getting non-existent override."""
        overrides = ManualOverrides(sample_overrides_file)
        result = overrides.get('nonexistent')

        assert result is None

    def test_add_override(self, tmp_path):
        """Test adding an override."""
        overrides_file = tmp_path / 'new_overrides.yaml'
        overrides = ManualOverrides(overrides_file)

        overrides.add('xyz789', 'NewCategory', 'NewSub', 'Test note')

        result = overrides.get('xyz789')
        assert result == ('NewCategory', 'NewSub')

    def test_empty_overrides(self):
        """Test with no overrides file."""
        overrides = ManualOverrides(None)
        assert len(overrides.overrides) == 0
