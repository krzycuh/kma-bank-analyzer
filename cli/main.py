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


def _load_categories(categories_file: Path) -> List[dict]:
    """Load category definitions from YAML. Returns list of {name, subcategories}."""
    import yaml

    if not categories_file.exists():
        return []

    with open(categories_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    return data.get('categories', [])


# Sentinel values for menu navigation
_BACK = '__back__'
_MANUAL = '__manual__'


def _use_arrow_menus() -> bool:
    """Arrow-key menus need a real terminal and the questionary package."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    try:
        import questionary  # noqa: F401
        return True
    except ImportError:
        return False


# Menu label colors (special entries)
_COLOR_MANUAL = '#ff8c00'   # orange
_COLOR_BACK = '#00afff'     # blue


def _select(
    message: str, choices: List[tuple], esc_back: bool = False
) -> Optional[str]:
    """Single-choice menu. `choices` is a list of (label, value) tuples.

    Uses arrow-key navigation in a terminal (questionary), falls back to
    a numbered prompt otherwise. Returns the chosen value, or None when
    cancelled with Ctrl+C.

    esc_back: when True, Esc and the left-arrow key return _BACK.
    """
    if _use_arrow_menus():
        import questionary

        q_choices = []
        for label, value in choices:
            if value == _MANUAL:
                title = [(f'fg:{_COLOR_MANUAL}', label)]
            elif value == _BACK:
                title = [(f'fg:{_COLOR_BACK}', label)]
            else:
                title = label
            q_choices.append(questionary.Choice(title=title, value=value))

        question = questionary.select(message, choices=q_choices)

        if esc_back:
            kb = question.application.key_bindings

            @kb.add('escape', eager=True)
            @kb.add('left')
            def _go_back(event):
                event.app.exit(result=_BACK)

        return question.ask()

    click.echo(message)
    for i, (label, value) in enumerate(choices, 1):
        if value == _MANUAL:
            label = click.style(label, fg='yellow')
        elif value == _BACK:
            label = click.style(label, fg='blue')
        click.echo(f"  {i:>2}. {label}")
    while True:
        number = click.prompt("Choice", type=int)
        if 1 <= number <= len(choices):
            return choices[number - 1][1]
        click.echo(f"  Invalid choice: {number}")


def _prompt_category(categories: List[dict]) -> Optional[tuple]:
    """Pick (category_main, category_sub). Returns None if user backs out."""
    if not categories:
        category_main = click.prompt("Category").strip()
        category_sub = click.prompt("Subcategory").strip()
        return category_main, category_sub

    while True:
        choices = [(c['name'], c['name']) for c in categories]
        choices += [('(enter manually)', _MANUAL), ('← back', _BACK)]
        category_main = _select("Main category:", choices, esc_back=True)
        if category_main in (None, _BACK):
            return None
        if category_main == _MANUAL:
            category_main = click.prompt("Category").strip()

        subcategories = next(
            (c.get('subcategories', []) for c in categories
             if c['name'] == category_main),
            [],
        )
        if not subcategories:
            category_sub = click.prompt("Subcategory").strip()
            return category_main, category_sub

        sub_choices = [(s, s) for s in subcategories]
        sub_choices += [('(enter manually)', _MANUAL),
                        ('← back (change category)', _BACK)]
        category_sub = _select(f"Subcategory of '{category_main}':", sub_choices,
                               esc_back=True)
        if category_sub in (None, _BACK):
            continue  # back to main category selection
        if category_sub == _MANUAL:
            category_sub = click.prompt("Subcategory").strip()
        return category_main, category_sub


def _remove_rule_from_file(rules_path: Path, name: str):
    """Remove a rule (by name) from the rules YAML file."""
    import yaml

    if not rules_path.exists():
        return
    with open(rules_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    data['rules'] = [r for r in data.get('rules', []) if r.get('name') != name]
    with open(rules_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)


def _save_rule_to_file(
    rules_path: Path,
    pattern: str,
    category_main: str,
    category_sub: str,
    name: Optional[str] = None,
    field: str = 'counterparty',
    match_type: str = 'contains',
    priority: int = 10,
    transaction_type: Optional[str] = None,
) -> str:
    """Append a categorization rule to the rules YAML file.

    Returns the final rule name (auto-generated or de-duplicated if taken).
    """
    import yaml

    rules_path.parent.mkdir(parents=True, exist_ok=True)

    if not name:
        name = pattern.lower()
        name = ''.join(c if c.isalnum() else '_' for c in name)
        name = name.strip('_')[:30]

    if rules_path.exists():
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    if 'rules' not in data:
        data['rules'] = []

    existing_names = {r.get('name') for r in data['rules']}
    if name in existing_names:
        i = 2
        while f"{name}_{i}" in existing_names:
            i += 1
        name = f"{name}_{i}"

    new_rule = {
        'name': name,
        'pattern': pattern,
        'field': field,
        'match_type': match_type,
        'priority': priority,
        'category_main': category_main,
        'category_sub': category_sub,
    }
    if transaction_type:
        new_rule['transaction_type'] = transaction_type
    data['rules'].append(new_rule)

    with open(rules_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return name


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

    # Filter out excluded transactions (kept for reporting, not for totals)
    click.echo("\nFiltering excluded transactions...")
    filtered_transactions = []
    excluded_transactions = []

    for trans in all_transactions:
        should_exclude, reason = rule_engine.should_exclude(trans)
        if should_exclude:
            trans.category_main = "Wykluczone"
            trans.category_sub = reason
            excluded_transactions.append(trans)
            logger.debug(f"Excluded: {trans.counterparty} - {reason}")
        else:
            filtered_transactions.append(trans)

    if excluded_transactions:
        click.echo(f"  Excluded: {len(excluded_transactions)} transactions")
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
        for trans in uncategorized_trans[:100]:  # Show max 100
            # Build description - use full description if different from counterparty
            desc = trans.description if trans.description != trans.counterparty else ""
            click.echo(
                f"  [{trans.id}] {trans.date.strftime('%Y-%m-%d')} | "
                f"{trans.amount:>8.2f} | {trans.counterparty} | {desc}"
            )
        if len(uncategorized_trans) > 100:
            click.echo(f"  ... and {len(uncategorized_trans) - 100} more")
        click.echo("-" * 100)
        click.echo("Tip: Categorize them interactively (rules + overrides) with:")
        click.echo("  bank-analyzer categorize <files>")
        click.echo("Or add a single rule/override manually:")
        click.echo("  bank-analyzer add-rule \"pattern\" \"Category\" \"Subcategory\"")
        click.echo("  bank-analyzer override <ID> \"Category\" \"Subcategory\"")
        click.echo("-" * 100)

    # Aggregation (excluded transactions reported separately, not in totals)
    click.echo("\nAggregating data...")
    aggregator = Aggregator()
    aggregated = aggregator.aggregate(
        filtered_transactions, excluded=excluded_transactions
    )

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
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
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
    '--categories-file',
    type=click.Path(),
    help='Categories YAML file (default: config/categories.yaml)'
)
@click.pass_context
def categorize(ctx, files, rules, overrides, categories_file):
    """
    Interactively categorize uncategorized transactions.

    Parses FILES, finds transactions no rule matches, groups them by
    counterparty and walks through each group. For every group you can
    create a permanent rule, add one-time overrides, or skip.

    \b
    For every group an arrow-key menu offers:
      - Add rule (permanent, all current and future matching transactions)
      - Add override (only these specific transactions)
      - Skip this group
      - Undo previous decision (removes the saved rule/override)
      - Quit (already saved changes are kept)

    Menus support going back a step, and Undo reverts the last decision
    if you mis-clicked. Without a terminal (piped input) menus fall back
    to numbered prompts.

    \b
    Example:
      bank-analyzer categorize data/input/*.csv
    """
    config_dir = ctx.obj.get('config_dir', Path('config'))
    rules_file = Path(rules) if rules else config_dir / 'rules.yaml'
    categories_path = (
        Path(categories_file) if categories_file else config_dir / 'categories.yaml'
    )
    overrides_path = Path(overrides)

    # Parse all files
    all_transactions = []
    for file_path in files:
        try:
            transactions = detect_and_parse(Path(file_path))
            all_transactions.extend(transactions)
        except Exception as e:
            click.echo(f"Error parsing {file_path}: {e}", err=True)

    if not all_transactions:
        click.echo("No transactions found!", err=True)
        sys.exit(1)

    rule_engine = RuleEngine(rules_file if rules_file.exists() else None)
    manual_overrides = ManualOverrides(overrides_path)

    # Collect uncategorized: not excluded, no override, no rule match
    uncategorized = []
    for trans in all_transactions:
        should_exclude, _ = rule_engine.should_exclude(trans)
        if should_exclude:
            continue
        if manual_overrides.get(trans.id):
            continue
        _, category_sub = rule_engine.categorize(trans)
        if category_sub == "Nieprzypisane":
            uncategorized.append(trans)

    if not uncategorized:
        click.echo("All transactions are categorized. Nothing to do!")
        return

    # Group by counterparty (fall back to description when empty or unknown,
    # so unrelated transactions don't end up in one bucket)
    groups = {}
    for trans in uncategorized:
        key = trans.counterparty.strip()
        if not key or key == "Nieznany":
            key = trans.description.strip() or "Nieznany"
        groups.setdefault(key, []).append(trans)

    # Largest groups first - biggest win per decision
    pending = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)

    categories = _load_categories(categories_path)
    if not categories:
        click.echo(f"Note: categories file not found ({categories_path}), "
                   "categories must be typed manually.")

    click.echo(f"\n{len(uncategorized)} uncategorized transaction(s) "
               f"in {len(pending)} group(s)")

    rules_added = 0
    overrides_added = 0
    skipped = 0
    journal = []  # decision log, so 'Undo' can revert saved changes

    i = 0
    while i < len(pending):
        key, group = pending[i]

        total = sum(t.amount for t in group)
        click.echo("-" * 100)
        click.echo(f"[{i + 1}/{len(pending)}] {key}  "
                   f"({len(group)} transaction(s), {total:,.2f} PLN)")
        for trans in group:
            desc = trans.description if trans.description != trans.counterparty else ""
            amount_str = (
                f"+{trans.amount:.2f}" if trans.transaction_type == 'income'
                else f"{trans.amount:.2f}"
            )
            click.echo(f"    {trans.date.strftime('%Y-%m-%d')} | "
                       f"{amount_str:>10} | {desc[:190]}")

        action_choices = [
            ('Add rule (permanent, all matching transactions)', 'r'),
            ('Add override (these transactions only)', 'o'),
            ('Skip this group', 's'),
        ]
        if journal:
            action_choices.append(('← undo previous decision', 'u'))
        action_choices.append(('Quit (keep saved changes)', 'q'))

        action = _select("Action:", action_choices)
        if action in (None, 'q'):
            break

        if action == 'u':
            entry = journal.pop()
            i -= 1  # go back to the previous group
            if entry['action'] == 'rule':
                _remove_rule_from_file(rules_file, entry['rule_name'])
                rules_added -= 1
                # put back groups that the undone rule had covered
                pending[i + 1:i + 1] = entry['covered']
                click.echo(f"  Removed rule '{entry['rule_name']}'")
            elif entry['action'] == 'override':
                for trans_id in entry['ids']:
                    manual_overrides.remove(trans_id)
                overrides_added -= len(entry['ids'])
                click.echo(f"  Removed {len(entry['ids'])} override(s)")
            else:
                skipped -= 1
            continue

        if action == 's':
            journal.append({'action': 'skip'})
            skipped += 1
            i += 1
            continue

        picked = _prompt_category(categories)
        if picked is None:
            continue  # back to the action menu for the same group
        category_main, category_sub = picked

        if action == 'r':
            pattern = click.prompt("Pattern to match", default=key).strip()
            suspicious = (
                len(pattern) < 3
                or pattern.replace(' ', '').isdigit()
                or pattern.endswith(':')
            )
            if suspicious:
                click.echo("  Warning: this pattern looks like a reference "
                           "number or label - it may match wrong transactions.")
                if not click.confirm("  Add this rule anyway?", default=False):
                    continue  # back to the action menu for the same group
            # Match against description when the group key came from it
            field = 'counterparty' if group[0].counterparty.strip() else 'description'
            # Income-only group -> scope the rule to income, so it won't
            # accidentally catch expenses to the same counterparty
            rule_type = (
                'income'
                if all(t.transaction_type == 'income' for t in group)
                else None
            )
            rule_name = _save_rule_to_file(
                rules_file, pattern, category_main, category_sub, field=field,
                transaction_type=rule_type,
            )
            rules_added += 1
            scope = " (income only)" if rule_type else ""
            click.echo(f"  Rule '{rule_name}' added: '{pattern}' "
                       f"-> {category_main} > {category_sub}{scope}")

            # Drop remaining groups already covered by the new rule
            pattern_lower = pattern.lower()
            remaining = pending[i + 1:]
            still_pending = []
            covered = []
            for other_key, other_group in remaining:
                field_value = (
                    other_group[0].counterparty
                    if field == 'counterparty'
                    else other_group[0].description
                )
                type_ok = rule_type is None or all(
                    t.transaction_type == rule_type for t in other_group
                )
                if type_ok and pattern_lower in field_value.lower():
                    covered.append((other_key, other_group))
                else:
                    still_pending.append((other_key, other_group))
            if covered:
                pending[i + 1:] = still_pending
                covered_count = sum(len(g) for _, g in covered)
                click.echo(f"  Also covers {covered_count} more transaction(s) "
                           f"in {len(covered)} other group(s)")
            journal.append({'action': 'rule', 'rule_name': rule_name,
                            'covered': covered})
            i += 1
        else:  # override
            for trans in group:
                manual_overrides.add(trans.id, category_main, category_sub)
            overrides_added += len(group)
            journal.append({'action': 'override',
                            'ids': [t.id for t in group]})
            click.echo(f"  Override saved for {len(group)} transaction(s): "
                       f"{category_main} > {category_sub}")
            i += 1

    click.echo("\n" + "=" * 50)
    click.echo("SUMMARY")
    click.echo("=" * 50)
    click.echo(f"  Rules added:      {rules_added}")
    click.echo(f"  Overrides added:  {overrides_added}")
    click.echo(f"  Groups skipped:   {skipped}")
    remaining_groups = len(pending) - i
    if remaining_groups > 0:
        click.echo(f"  Groups not seen:  {remaining_groups}")
    if rules_added or overrides_added:
        click.echo("\nRun 'bank-analyzer analyze' to apply the changes.")


@cli.command()
@click.argument('pattern')
@click.argument('category_main')
@click.argument('category_sub')
@click.option(
    '--name', '-n',
    default=None,
    help='Rule name (default: auto-generated from pattern)'
)
@click.option(
    '--field', '-f',
    type=click.Choice(['counterparty', 'description']),
    default='counterparty',
    help='Field to match against (default: counterparty)'
)
@click.option(
    '--match-type', '-m',
    type=click.Choice(['contains', 'exact', 'regex', 'startswith', 'endswith']),
    default='contains',
    help='Match type (default: contains)'
)
@click.option(
    '--priority', '-p',
    type=int,
    default=10,
    help='Rule priority - higher = checked first (default: 10)'
)
@click.option(
    '--transaction-type', '-t',
    type=click.Choice(['expense', 'income']),
    default=None,
    help='Limit rule to one transaction type (default: matches both)'
)
@click.option(
    '--rules-file',
    type=click.Path(),
    default='config/rules.yaml',
    help='Rules YAML file'
)
def add_rule(pattern, category_main, category_sub, name, field, match_type,
             priority, transaction_type, rules_file):
    """
    Add a new categorization rule.

    Creates a permanent rule that will categorize all matching transactions.

    \b
    PATTERN: Text or regex to match
    CATEGORY_MAIN: Main category (e.g., "Jedzenie")
    CATEGORY_SUB: Subcategory (e.g., "Zakupy spożywcze")

    \b
    Examples:
      bank-analyzer add-rule "biedronka" "Jedzenie" "Zakupy spożywcze"
      bank-analyzer add-rule "netflix" "Subskrypcje" "Streaming" -f description
      bank-analyzer add-rule "uber.*eats" "Jedzenie" "Na wynos" -m regex
      bank-analyzer add-rule "Pracodawca" "Przychody" "Wynagrodzenie" -t income
    """
    name = _save_rule_to_file(
        Path(rules_file), pattern, category_main, category_sub,
        name=name, field=field, match_type=match_type, priority=priority,
        transaction_type=transaction_type,
    )

    click.echo(f"Rule '{name}' added:")
    click.echo(f"  Pattern: {pattern} ({match_type} in {field})")
    if transaction_type:
        click.echo(f"  Applies to: {transaction_type} only")
    click.echo(f"  Category: {category_main} > {category_sub}")
    click.echo(f"  Priority: {priority}")
    click.echo(f"\nSaved to: {rules_file}")
    click.echo("Run 'bank-analyzer analyze' again to apply.")


@cli.command()
@click.option(
    '--rules-file',
    type=click.Path(exists=True),
    default='config/rules.yaml',
    help='Rules YAML file'
)
def list_rules(rules_file):
    """List all categorization rules."""
    from pathlib import Path
    import yaml

    rules_path = Path(rules_file)
    if not rules_path.exists():
        click.echo("No rules file found.")
        return

    with open(rules_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    rules = data.get('rules', [])
    if not rules:
        click.echo("No rules defined.")
        return

    click.echo(f"Categorization rules ({len(rules)}):")
    click.echo("-" * 80)
    for rule in rules:
        name = rule.get('name', '?')
        pattern = rule.get('pattern', '')
        field = rule.get('field', 'counterparty')
        match_type = rule.get('match_type', 'contains')
        cat_main = rule.get('category_main', '?')
        cat_sub = rule.get('category_sub', '?')
        type_scope = rule.get('transaction_type')
        scope = f", {type_scope} only" if type_scope else ""
        click.echo(f"  {name}: '{pattern}' ({match_type} in {field}{scope}) "
                   f"-> {cat_main} > {cat_sub}")
    click.echo("-" * 80)


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
