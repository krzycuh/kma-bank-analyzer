#!/usr/bin/env python3
"""CLI interface for Bank Analyzer."""

import sys
from pathlib import Path
from typing import List, Optional

try:
    import click
except ImportError:
    print("Error: click is required. Run: pip install click")
    sys.exit(1)

from bank_analyzer import (
    detect_and_parse,
    detect_format,
    RuleEngine,
    ManualOverrides,
    Aggregator,
    ExcelExporter,
    JSONExporter,
)
from bank_analyzer.utils.logger import setup_logging, get_logger


@click.group()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True),
    help='Path to config directory'
)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', is_flag=True, help='Enable debug output')
@click.pass_context
def cli(ctx, config, verbose, debug):
    """
    Bank Analyzer - Parse and analyze bank statements.

    Supports PKO BP and Alior Bank CSV formats.
    """
    ctx.ensure_object(dict)
    ctx.obj['config_dir'] = Path(config) if config else Path('config')

    # Setup logging
    if debug:
        log_level = 'DEBUG'
    elif verbose:
        log_level = 'INFO'
    else:
        log_level = 'WARNING'

    setup_logging(log_level)


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='data/output/wydatki.xlsx',
    help='Output Excel file path'
)
@click.option(
    '--rules', '-r',
    type=click.Path(exists=True),
    help='Rules YAML file (default: config/rules.yaml)'
)
@click.option(
    '--overrides',
    type=click.Path(),
    default='data/manual_overrides.yaml',
    help='Manual overrides YAML file'
)
@click.option(
    '--json-output',
    type=click.Path(),
    help='Also export to JSON file'
)
@click.pass_context
def analyze(ctx, files, output, rules, overrides, json_output):
    """
    Analyze CSV files and generate expense report.

    FILES: One or more CSV files to analyze
    """
    logger = get_logger(__name__)
    config_dir = ctx.obj.get('config_dir', Path('config'))

    click.echo(f"Analyzing {len(files)} file(s)...")

    # Parse all files
    all_transactions = []
    for file_path in files:
        try:
            file_path = Path(file_path)
            click.echo(f"  Processing: {file_path.name}")
            transactions = detect_and_parse(file_path)
            all_transactions.extend(transactions)
            click.echo(f"    Found {len(transactions)} transactions")
        except Exception as e:
            click.echo(f"    Error: {e}", err=True)
            continue

    if not all_transactions:
        click.echo("No transactions found!", err=True)
        sys.exit(1)

    click.echo(f"\nTotal: {len(all_transactions)} transactions")

    # Load rules
    rules_file = Path(rules) if rules else config_dir / 'rules.yaml'

    if rules_file.exists():
        rule_engine = RuleEngine(rules_file)
    else:
        click.echo(f"  Warning: Rules file not found: {rules_file}")
        click.echo("  Using empty rules (all will be uncategorized)")
        rule_engine = RuleEngine(None)

    # Filter out excluded transactions
    click.echo("\nFiltering excluded transactions...")
    filtered_transactions = []
    excluded_count = 0

    for trans in all_transactions:
        should_exclude, reason = rule_engine.should_exclude(trans)
        if should_exclude:
            excluded_count += 1
            logger.debug(f"Excluded: {trans.counterparty} - {reason}")
        else:
            filtered_transactions.append(trans)

    if excluded_count > 0:
        click.echo(f"  Excluded: {excluded_count} transactions")
        # Show exclusion stats
        exclude_stats = rule_engine.get_exclude_stats()
        if exclude_stats:
            for rule_name, count in sorted(exclude_stats.items(), key=lambda x: x[1], reverse=True):
                click.echo(f"    - {rule_name}: {count}")

    click.echo(f"  Remaining: {len(filtered_transactions)} transactions")

    # Categorization
    click.echo("\nCategorizing transactions...")
    overrides_file = Path(overrides)
    manual_overrides = ManualOverrides(overrides_file if overrides_file.exists() else None)

    categorized_count = 0
    for trans in filtered_transactions:
        # Check manual override first
        override = manual_overrides.get(trans.id)
        if override:
            trans.category_main, trans.category_sub = override
            trans.manual_override = True
            categorized_count += 1
        else:
            # Categorize with rules
            trans.category_main, trans.category_sub = rule_engine.categorize(trans)
            if trans.category_sub != "Nieprzypisane":
                categorized_count += 1

    uncategorized = len(filtered_transactions) - categorized_count
    click.echo(f"  Categorized: {categorized_count}")
    click.echo(f"  Uncategorized: {uncategorized}")

    # Show uncategorized transactions for easier rule improvement
    uncategorized_trans = [t for t in filtered_transactions if t.category_sub == "Nieprzypisane"]
    if uncategorized_trans:
        click.echo("\n" + "-" * 100)
        click.echo("UNCATEGORIZED TRANSACTIONS:")
        click.echo("-" * 100)
        for trans in uncategorized_trans[:20]:  # Show max 20
            # Build description - use full description if different from counterparty
            desc = trans.description if trans.description != trans.counterparty else ""
            click.echo(
                f"  [{trans.id}] {trans.date.strftime('%Y-%m-%d')} | "
                f"{trans.amount:>8.2f} | {trans.counterparty[:25]:<25} | {desc[:50]}"
            )
        if len(uncategorized_trans) > 20:
            click.echo(f"  ... and {len(uncategorized_trans) - 20} more")
        click.echo("-" * 100)
        click.echo("Tip: Add a rule to config/rules.yaml, or for one-time override run:")
        click.echo("  bank-analyzer override <ID> \"Category\" \"Subcategory\"")
        click.echo("-" * 100)

    # Use filtered transactions for aggregation
    all_transactions = filtered_transactions

    # Aggregation
    click.echo("\nAggregating data...")
    aggregator = Aggregator()
    aggregated = aggregator.aggregate(all_transactions)

    # Export to Excel
    click.echo(f"\nExporting to Excel: {output}")
    exporter = ExcelExporter()
    exporter.export(aggregated, Path(output))

    # Export to JSON if requested
    if json_output:
        click.echo(f"Exporting to JSON: {json_output}")
        json_exporter = JSONExporter()
        json_exporter.export(aggregated, Path(json_output))

    # Show statistics
    click.echo("\n" + "=" * 50)
    click.echo("SUMMARY")
    click.echo("=" * 50)

    years = aggregated.get('years', {})
    for year in sorted(years.keys()):
        year_data = years[year]
        total_expense = float(year_data.get('total_year_expense', 0))
        total_income = float(year_data.get('total_year_income', 0))
        click.echo(f"\nYear {year}:")
        click.echo(f"  Total expenses: {total_expense:,.2f} PLN")
        click.echo(f"  Total income:   {total_income:,.2f} PLN")

    # Top rules used
    stats = rule_engine.get_stats()
    if stats:
        click.echo("\nTop 5 rules used:")
        for rule_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  {rule_name}: {count}")

    click.echo(f"\nDone! Output saved to: {output}")


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def parse(file):
    """
    Parse a CSV file and show info (without categorization).

    FILE: CSV file to parse
    """
    try:
        file_path = Path(file)
        bank = detect_format(file_path)

        click.echo(f"\nFile: {file_path.name}")
        click.echo(f"Detected bank: {bank}")

        if bank == "UNKNOWN":
            click.echo("Cannot determine bank format!", err=True)
            sys.exit(1)

        transactions = detect_and_parse(file_path)

        click.echo(f"\nStatistics:")
        click.echo(f"  Total transactions: {len(transactions)}")

        expenses = [t for t in transactions if t.transaction_type == 'expense']
        incomes = [t for t in transactions if t.transaction_type == 'income']

        total_expense = sum(t.amount for t in expenses)
        total_income = sum(t.amount for t in incomes)

        click.echo(f"  Expenses: {len(expenses)} ({total_expense:,.2f} PLN)")
        click.echo(f"  Incomes: {len(incomes)} ({total_income:,.2f} PLN)")

        if transactions:
            dates = [t.date for t in transactions]
            click.echo(f"  Date range: {min(dates).date()} to {max(dates).date()}")

        click.echo(f"\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5], 1):
            click.echo(f"  {i}. {trans}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def detect(file):
    """
    Detect the bank format of a CSV file.

    FILE: CSV file to check
    """
    file_path = Path(file)
    bank = detect_format(file_path)

    click.echo(f"File: {file_path.name}")
    click.echo(f"Detected bank: {bank}")

    if bank == "UNKNOWN":
        click.echo("\nSupported formats:", err=True)
        click.echo("  - PKO BP (Data operacji header)")
        click.echo("  - Alior Bank (semicolon-separated)")


@cli.command()
@click.option(
    '--source', '-s',
    type=click.Path(exists=True),
    default='data/processed',
    help='Folder with processed files'
)
@click.option('--top', '-n', type=int, default=50, help='Number of top results')
def analyze_history(source, top):
    """
    Analyze historical transactions and show counterparty statistics.
    """
    source_path = Path(source)

    # Find all CSV files
    csv_files = list(source_path.glob('*.csv'))

    if not csv_files:
        click.echo(f"No CSV files found in {source}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(csv_files)} files")

    # Parse all
    all_transactions = []
    for file_path in csv_files:
        try:
            transactions = detect_and_parse(file_path)
            all_transactions.extend(transactions)
        except Exception:
            continue

    if not all_transactions:
        click.echo("No transactions found!", err=True)
        sys.exit(1)

    click.echo(f"Total transactions: {len(all_transactions)}")

    # Analyze counterparties
    from collections import Counter
    counterparties = Counter(t.counterparty for t in all_transactions)

    click.echo(f"\nTop {top} counterparties:")
    for counterparty, count in counterparties.most_common(top):
        click.echo(f"  {counterparty}: {count}")


@cli.command()
@click.option(
    '--source', '-s',
    type=click.Path(exists=True),
    default='data/processed',
    help='Folder with archived files'
)
@click.option(
    '--rules', '-r',
    type=click.Path(exists=True),
    help='Rules file'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='data/output/wydatki.xlsx',
    help='Output file'
)
@click.pass_context
def reprocess(ctx, source, rules, output):
    """
    Reprocess archive with new rules.
    """
    source_path = Path(source)
    csv_files = list(source_path.glob('*.csv'))

    if not csv_files:
        click.echo(f"No files in archive: {source}", err=True)
        sys.exit(1)

    click.echo(f"Reprocessing {len(csv_files)} files...")

    # Call analyze with the files
    ctx.invoke(
        analyze,
        files=[str(f) for f in csv_files],
        output=output,
        rules=rules,
    )


@cli.command()
@click.argument('transaction_id')
@click.argument('category_main')
@click.argument('category_sub')
@click.option(
    '--note', '-n',
    default='',
    help='Optional note explaining the override'
)
@click.option(
    '--overrides-file',
    type=click.Path(),
    default='data/manual_overrides.yaml',
    help='Manual overrides YAML file'
)
def override(transaction_id, category_main, category_sub, note, overrides_file):
    """
    Add manual category override for a specific transaction.

    This is useful when a transaction doesn't fit the general rule
    for that merchant (e.g., buying a gift at a sports store).

    \b
    TRANSACTION_ID: The transaction ID (shown in brackets in uncategorized list)
    CATEGORY_MAIN: Main category (e.g., "Prezenty i okazje")
    CATEGORY_SUB: Subcategory (e.g., "Prezenty urodzinowe")

    \b
    Example:
      bank-analyzer override abc123def456 "Prezenty i okazje" "Prezenty urodzinowe"
      bank-analyzer override abc123def456 "Rozrywka" "Sport" -n "Własny trening"
    """
    from pathlib import Path

    overrides_path = Path(overrides_file)
    overrides_path.parent.mkdir(parents=True, exist_ok=True)

    manual_overrides = ManualOverrides(overrides_path)
    manual_overrides.add(transaction_id, category_main, category_sub, note)

    click.echo(f"Override added for transaction {transaction_id}:")
    click.echo(f"  Category: {category_main} > {category_sub}")
    if note:
        click.echo(f"  Note: {note}")
    click.echo(f"\nSaved to: {overrides_file}")
    click.echo("Run 'bank-analyzer analyze' again to apply.")


@cli.command()
@click.option(
    '--overrides-file',
    type=click.Path(exists=True),
    default='data/manual_overrides.yaml',
    help='Manual overrides YAML file'
)
def list_overrides(overrides_file):
    """List all manual category overrides."""
    from pathlib import Path

    overrides_path = Path(overrides_file)
    if not overrides_path.exists():
        click.echo("No overrides file found.")
        return

    manual_overrides = ManualOverrides(overrides_path)
    all_overrides = manual_overrides.list_all()

    if not all_overrides:
        click.echo("No overrides defined.")
        return

    click.echo(f"Manual overrides ({len(all_overrides)}):")
    click.echo("-" * 60)
    for trans_id, (cat_main, cat_sub) in all_overrides.items():
        click.echo(f"  [{trans_id}] {cat_main} > {cat_sub}")
    click.echo("-" * 60)


@cli.command()
def version():
    """Show version information."""
    from bank_analyzer import __version__
    click.echo(f"Bank Analyzer v{__version__}")
    click.echo("Supported banks: PKO BP, Alior Bank")


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
