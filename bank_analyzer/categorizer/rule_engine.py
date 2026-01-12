"""Rule-based transaction categorization engine."""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from bank_analyzer.models.transaction import Transaction
from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class RuleEngine:
    """Rule-based transaction categorization engine."""

    def __init__(self, rules_file: Optional[Path] = None):
        """
        Initialize the rule engine.

        Args:
            rules_file: Path to YAML file with categorization rules.
                       If None, no rules will be loaded.
        """
        self.rules_file = Path(rules_file) if rules_file else None
        self.rules: List[Dict] = []
        self.exclude_rules: List[Dict] = []  # Exclusion rules
        self.compiled_patterns: Dict[int, re.Pattern] = {}
        self.compiled_exclude_patterns: Dict[int, re.Pattern] = {}
        self.stats: Dict[str, int] = {}  # Rule usage statistics
        self.exclude_stats: Dict[str, int] = {}  # Exclusion statistics
        self._cache: Dict[str, Tuple[str, str]] = {}  # Results cache

        if self.rules_file:
            self._load_rules()

    def _load_rules(self):
        """Load and compile rules from YAML file."""
        if not self.rules_file or not self.rules_file.exists():
            logger.warning(f"Rules file not found: {self.rules_file}")
            self.rules = []
            return

        try:
            import yaml
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            self.rules = data.get('rules', [])
            self.exclude_rules = data.get('exclude', [])

            # Sort by priority (descending)
            self.rules.sort(key=lambda r: r.get('priority', 0), reverse=True)

            # Pre-compile regex patterns for categorization rules
            for idx, rule in enumerate(self.rules):
                if rule.get('match_type') == 'regex':
                    flags = 0 if rule.get('case_sensitive', False) else re.IGNORECASE
                    try:
                        self.compiled_patterns[idx] = re.compile(
                            rule['pattern'], flags
                        )
                    except re.error as e:
                        logger.warning(
                            f"Invalid regex in rule '{rule.get('name', idx)}': {e}"
                        )

            # Pre-compile regex patterns for exclusion rules
            for idx, rule in enumerate(self.exclude_rules):
                if rule.get('match_type') == 'regex':
                    flags = 0 if rule.get('case_sensitive', False) else re.IGNORECASE
                    try:
                        self.compiled_exclude_patterns[idx] = re.compile(
                            rule['pattern'], flags
                        )
                    except re.error as e:
                        logger.warning(
                            f"Invalid regex in exclude rule '{rule.get('name', idx)}': {e}"
                        )

            logger.info(f"Loaded {len(self.rules)} categorization rules, "
                       f"{len(self.exclude_rules)} exclusion rules")

        except ImportError:
            logger.error("PyYAML not installed. Cannot load rules.")
            self.rules = []
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            self.rules = []

    def should_exclude(self, transaction: Transaction) -> Tuple[bool, Optional[str]]:
        """
        Check if transaction should be excluded from analysis.

        Args:
            transaction: Transaction to check

        Returns:
            Tuple of (should_exclude, reason)
        """
        for idx, rule in enumerate(self.exclude_rules):
            if self._match_exclude_rule(rule, transaction, idx):
                rule_name = rule.get('name', f"exclude_{idx}")
                reason = rule.get('reason', rule_name)

                # Update statistics
                self.exclude_stats[rule_name] = self.exclude_stats.get(rule_name, 0) + 1

                return True, reason

        return False, None

    def _match_exclude_rule(
        self, rule: Dict, transaction: Transaction, rule_idx: int
    ) -> bool:
        """Check if exclusion rule matches transaction."""
        pattern = rule.get('pattern', '')
        field_name = rule.get('field', 'description')
        match_type = rule.get('match_type', 'contains')
        case_sensitive = rule.get('case_sensitive', False)

        # Get field value
        if field_name == 'counterparty':
            field_value = transaction.counterparty
        elif field_name == 'description':
            field_value = transaction.description
        else:
            field_value = ""

        if not case_sensitive:
            field_value = field_value.lower()
            if isinstance(pattern, str) and match_type != 'regex':
                pattern = pattern.lower()

        # Match by type
        if match_type == 'contains':
            return pattern in field_value
        elif match_type == 'exact':
            return pattern == field_value
        elif match_type == 'startswith':
            return field_value.startswith(pattern)
        elif match_type == 'endswith':
            return field_value.endswith(pattern)
        elif match_type == 'regex':
            compiled = self.compiled_exclude_patterns.get(rule_idx)
            if compiled:
                return bool(compiled.search(field_value))
            return False

        return False

    def get_exclude_stats(self) -> Dict[str, int]:
        """Get exclusion rule usage statistics."""
        return self.exclude_stats.copy()

    def categorize(self, transaction: Transaction) -> Tuple[str, str]:
        """
        Categorize a transaction using rules.

        Args:
            transaction: Transaction to categorize

        Returns:
            Tuple of (category_main, category_sub)
        """
        # Check cache
        cache_key = f"{transaction.counterparty.lower()}|{transaction.description.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Iterate through rules
        for idx, rule in enumerate(self.rules):
            if self._match_rule(rule, transaction, idx):
                category_main = rule['category_main']
                category_sub = rule['category_sub']

                # Update statistics
                rule_name = rule.get('name', f"rule_{idx}")
                self.stats[rule_name] = self.stats.get(rule_name, 0) + 1

                # Save to cache
                self._cache[cache_key] = (category_main, category_sub)

                return category_main, category_sub

        # No match
        return "Inne wydatki", "Nieprzypisane"

    def _match_rule(
        self, rule: Dict, transaction: Transaction, rule_idx: int
    ) -> bool:
        """Check if rule matches transaction."""
        pattern = rule.get('pattern', '')
        field_name = rule.get('field', 'counterparty')
        match_type = rule.get('match_type', 'contains')
        case_sensitive = rule.get('case_sensitive', False)

        # Get field value
        if field_name == 'counterparty':
            field_value = transaction.counterparty
        elif field_name == 'description':
            field_value = transaction.description
        else:
            field_value = ""

        if not case_sensitive:
            field_value = field_value.lower()
            if isinstance(pattern, str) and match_type != 'regex':
                pattern = pattern.lower()

        # Match by type
        if match_type == 'contains':
            return pattern in field_value

        elif match_type == 'exact':
            return pattern == field_value

        elif match_type == 'startswith':
            return field_value.startswith(pattern)

        elif match_type == 'endswith':
            return field_value.endswith(pattern)

        elif match_type == 'regex':
            compiled = self.compiled_patterns.get(rule_idx)
            if compiled:
                return bool(compiled.search(field_value))
            return False

        return False

    def get_stats(self) -> Dict[str, int]:
        """Get rule usage statistics."""
        return self.stats.copy()

    def clear_cache(self):
        """Clear the results cache."""
        self._cache.clear()

    def add_rule(
        self,
        name: str,
        pattern: str,
        category_main: str,
        category_sub: str,
        field: str = 'counterparty',
        match_type: str = 'contains',
        priority: int = 10,
        case_sensitive: bool = False,
    ):
        """
        Add a rule programmatically.

        Args:
            name: Rule name
            pattern: Pattern to match
            category_main: Main category
            category_sub: Subcategory
            field: Field to match against ('counterparty' or 'description')
            match_type: Match type ('contains', 'exact', 'regex', etc.)
            priority: Rule priority (higher = checked first)
            case_sensitive: Whether match is case-sensitive
        """
        rule = {
            'name': name,
            'pattern': pattern,
            'category_main': category_main,
            'category_sub': category_sub,
            'field': field,
            'match_type': match_type,
            'priority': priority,
            'case_sensitive': case_sensitive,
        }

        self.rules.append(rule)
        # Re-sort by priority
        self.rules.sort(key=lambda r: r.get('priority', 0), reverse=True)

        # Compile regex if needed
        if match_type == 'regex':
            idx = len(self.rules) - 1
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                self.compiled_patterns[idx] = re.compile(pattern, flags)
            except re.error as e:
                logger.warning(f"Invalid regex in rule '{name}': {e}")

        # Clear cache as rules changed
        self.clear_cache()
