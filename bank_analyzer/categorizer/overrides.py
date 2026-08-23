"""Manual category overrides management."""

from pathlib import Path
from typing import Dict, Tuple, Optional

from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class ManualOverrides:
    """Manage manual category overrides for transactions."""

    def __init__(self, overrides_file: Optional[Path] = None):
        """
        Initialize manual overrides manager.

        Args:
            overrides_file: Path to YAML file with manual overrides.
                           If None or file doesn't exist, starts empty.
        """
        self.overrides_file = Path(overrides_file) if overrides_file else None
        self.overrides: Dict[str, Tuple[str, str]] = {}
        self._load_overrides()

    def _load_overrides(self):
        """Load overrides from YAML file."""
        if not self.overrides_file or not self.overrides_file.exists():
            if self.overrides_file:
                logger.info(
                    f"Overrides file not found, will be created: {self.overrides_file}"
                )
            return

        try:
            import yaml
            with open(self.overrides_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            overrides_list = data.get('overrides', [])

            for override in overrides_list:
                trans_id = override.get('transaction_id')
                category_main = override.get('category_main')
                category_sub = override.get('category_sub')

                if trans_id and category_main and category_sub:
                    self.overrides[trans_id] = (category_main, category_sub)

            logger.info(f"Loaded {len(self.overrides)} manual overrides")

        except ImportError:
            logger.warning("PyYAML not installed. Cannot load overrides.")
        except Exception as e:
            logger.error(f"Error loading overrides: {e}")
            self.overrides = {}

    def _create_empty_file(self):
        """Create empty overrides file."""
        if not self.overrides_file:
            return

        try:
            import yaml
            self.overrides_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.overrides_file, 'w', encoding='utf-8') as f:
                yaml.dump({'overrides': []}, f, allow_unicode=True)
            logger.info(f"Created empty overrides file: {self.overrides_file}")
        except ImportError:
            logger.warning("PyYAML not installed. Cannot create overrides file.")
        except Exception as e:
            logger.error(f"Error creating overrides file: {e}")

    def get(self, transaction_id: str) -> Optional[Tuple[str, str]]:
        """
        Get override for a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Tuple of (category_main, category_sub) or None
        """
        return self.overrides.get(transaction_id)

    def add(
        self,
        transaction_id: str,
        category_main: str,
        category_sub: str,
        note: str = "",
    ):
        """
        Add a new override.

        Args:
            transaction_id: Transaction ID
            category_main: Main category
            category_sub: Subcategory
            note: Optional note
        """
        self.overrides[transaction_id] = (category_main, category_sub)

        if self.overrides_file:
            self._save(transaction_id, category_main, category_sub, note)

    def _save(
        self,
        transaction_id: str,
        category_main: str,
        category_sub: str,
        note: str,
    ):
        """Save override to file."""
        if not self.overrides_file:
            return

        try:
            import yaml
            from datetime import datetime

            # Load existing data
            if self.overrides_file.exists():
                with open(self.overrides_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {'overrides': []}
            else:
                self.overrides_file.parent.mkdir(parents=True, exist_ok=True)
                data = {'overrides': []}

            # Check if override already exists
            existing_ids = {o.get('transaction_id') for o in data['overrides']}
            if transaction_id in existing_ids:
                # Update existing
                for override in data['overrides']:
                    if override.get('transaction_id') == transaction_id:
                        override['category_main'] = category_main
                        override['category_sub'] = category_sub
                        override['note'] = note
                        override['date_updated'] = datetime.now().strftime('%Y-%m-%d')
                        break
            else:
                # Add new
                data['overrides'].append({
                    'transaction_id': transaction_id,
                    'category_main': category_main,
                    'category_sub': category_sub,
                    'note': note,
                    'date_added': datetime.now().strftime('%Y-%m-%d'),
                })

            # Save
            with open(self.overrides_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"Saved override for transaction {transaction_id}")

        except ImportError:
            logger.warning("PyYAML not installed. Cannot save override.")
        except Exception as e:
            logger.error(f"Error saving override: {e}")

    def remove(self, transaction_id: str) -> bool:
        """
        Remove an override.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if removed, False if not found
        """
        if transaction_id not in self.overrides:
            return False

        del self.overrides[transaction_id]

        if self.overrides_file and self.overrides_file.exists():
            self._remove_from_file(transaction_id)

        return True

    def _remove_from_file(self, transaction_id: str):
        """Remove override from file."""
        try:
            import yaml

            with open(self.overrides_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {'overrides': []}

            data['overrides'] = [
                o for o in data['overrides']
                if o.get('transaction_id') != transaction_id
            ]

            with open(self.overrides_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        except Exception as e:
            logger.error(f"Error removing override from file: {e}")

    def list_all(self) -> Dict[str, Tuple[str, str]]:
        """Get all overrides."""
        return self.overrides.copy()
