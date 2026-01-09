"""Integration tests for the full pipeline."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from bank_analyzer import (
    detect_and_parse,
    RuleEngine,
    ManualOverrides,
    Aggregator,
    ExcelExporter,
    JSONExporter,
)

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


class TestFullPipeline:
    """Integration tests for the complete analysis pipeline."""

    @pytest.fixture
    def rules_file(self, tmp_path):
        """Create test rules file."""
        content = """
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

  - name: "orlen"
    pattern: "orlen"
    field: "counterparty"
    match_type: "contains"
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"

  - name: "carrefour"
    pattern: "carrefour"
    field: "counterparty"
    match_type: "contains"
    priority: 10
    category_main: "Jedzenie"
    category_sub: "Zakupy spożywcze"

  - name: "shell"
    pattern: "shell"
    field: "counterparty"
    match_type: "contains"
    priority: 10
    category_main: "Transport"
    category_sub: "Paliwo"
"""
        rules_file = tmp_path / 'rules.yaml'
        rules_file.write_text(content)
        return rules_file

    def test_parse_and_categorize_pko(self, rules_file):
        """Test parsing and categorizing PKO file."""
        # Parse
        transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')
        assert len(transactions) > 0

        # Categorize
        engine = RuleEngine(rules_file)
        categorized_count = 0

        for trans in transactions:
            trans.category_main, trans.category_sub = engine.categorize(trans)
            if trans.category_sub != "Nieprzypisane":
                categorized_count += 1

        assert categorized_count > 0

    def test_parse_and_categorize_alior(self, rules_file):
        """Test parsing and categorizing Alior file."""
        # Parse
        transactions = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')
        assert len(transactions) > 0

        # Categorize
        engine = RuleEngine(rules_file)
        categorized_count = 0

        for trans in transactions:
            trans.category_main, trans.category_sub = engine.categorize(trans)
            if trans.category_sub != "Nieprzypisane":
                categorized_count += 1

        assert categorized_count > 0

    def test_full_pipeline_with_aggregation(self, rules_file):
        """Test complete pipeline including aggregation."""
        # Parse both files
        pko_trans = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')
        alior_trans = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')
        all_trans = pko_trans + alior_trans

        # Categorize
        engine = RuleEngine(rules_file)
        for trans in all_trans:
            trans.category_main, trans.category_sub = engine.categorize(trans)

        # Aggregate
        aggregator = Aggregator()
        result = aggregator.aggregate(all_trans)

        assert 'years' in result
        assert 2026 in result['years']
        assert 'uncategorized' in result

    def test_full_pipeline_with_excel_export(self, rules_file, tmp_path):
        """Test complete pipeline with Excel export."""
        # Parse
        transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')

        # Categorize
        engine = RuleEngine(rules_file)
        for trans in transactions:
            trans.category_main, trans.category_sub = engine.categorize(trans)

        # Aggregate
        aggregator = Aggregator()
        result = aggregator.aggregate(transactions)

        # Export
        output_file = tmp_path / 'test_output.xlsx'
        exporter = ExcelExporter()
        exporter.export(result, output_file)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_full_pipeline_with_json_export(self, rules_file, tmp_path):
        """Test complete pipeline with JSON export."""
        # Parse
        transactions = detect_and_parse(FIXTURES_DIR / 'alior_sample.csv')

        # Categorize
        engine = RuleEngine(rules_file)
        for trans in transactions:
            trans.category_main, trans.category_sub = engine.categorize(trans)

        # Aggregate
        aggregator = Aggregator()
        result = aggregator.aggregate(transactions)

        # Export
        output_file = tmp_path / 'test_output.json'
        exporter = JSONExporter()
        exporter.export(result, output_file)

        assert output_file.exists()

        # Verify JSON is valid
        import json
        with open(output_file) as f:
            data = json.load(f)

        assert 'years' in data
        assert 'summary' in data

    def test_manual_overrides_in_pipeline(self, rules_file, tmp_path):
        """Test that manual overrides work in pipeline."""
        # Parse
        transactions = detect_and_parse(FIXTURES_DIR / 'pko_sample.csv')

        # Create override for first transaction
        first_trans = transactions[0]
        overrides_file = tmp_path / 'overrides.yaml'

        overrides = ManualOverrides(overrides_file)
        overrides.add(
            first_trans.id,
            'Manual Category',
            'Manual Sub',
            'Test override'
        )

        # Reload overrides
        overrides = ManualOverrides(overrides_file)

        # Categorize with overrides
        engine = RuleEngine(rules_file)
        for trans in transactions:
            override = overrides.get(trans.id)
            if override:
                trans.category_main, trans.category_sub = override
                trans.manual_override = True
            else:
                trans.category_main, trans.category_sub = engine.categorize(trans)

        # Check override was applied
        assert first_trans.category_main == 'Manual Category'
        assert first_trans.category_sub == 'Manual Sub'
        assert first_trans.manual_override is True
