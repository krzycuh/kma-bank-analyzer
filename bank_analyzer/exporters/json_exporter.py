"""JSON export for API and data interchange."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List

from bank_analyzer.models.transaction import Transaction
from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Transaction):
            return obj.to_dict()
        return super().default(obj)


class JSONExporter:
    """Export data to JSON format."""

    def export(
        self,
        aggregated_data: Dict[str, Any],
        output_path: Path,
        include_transactions: bool = False,
        pretty: bool = True,
    ):
        """
        Export aggregated data to JSON file.

        Args:
            aggregated_data: Aggregated data from Aggregator
            output_path: Path to output file
            include_transactions: Whether to include individual transactions
            pretty: Whether to format JSON with indentation
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data for export
        export_data = self._prepare_data(aggregated_data, include_transactions)

        # Write to file
        indent = 2 if pretty else None
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, cls=DecimalEncoder, indent=indent, ensure_ascii=False)

        logger.info(f"Exported JSON to: {output_path}")

    def export_string(
        self,
        aggregated_data: Dict[str, Any],
        include_transactions: bool = False,
        pretty: bool = True,
    ) -> str:
        """
        Export aggregated data to JSON string.

        Args:
            aggregated_data: Aggregated data from Aggregator
            include_transactions: Whether to include individual transactions
            pretty: Whether to format JSON with indentation

        Returns:
            JSON string
        """
        export_data = self._prepare_data(aggregated_data, include_transactions)
        indent = 2 if pretty else None
        return json.dumps(export_data, cls=DecimalEncoder, indent=indent, ensure_ascii=False)

    def _prepare_data(
        self,
        aggregated_data: Dict[str, Any],
        include_transactions: bool
    ) -> Dict[str, Any]:
        """Prepare data for JSON export."""
        result = {
            'generated_at': datetime.now().isoformat(),
            'summary': aggregated_data.get('summary', {}),
            'years': {},
        }

        # Process years
        for year, year_data in aggregated_data.get('years', {}).items():
            year_export = {
                'total_year': float(year_data.get('total_year', 0)),
                'total_year_income': float(year_data.get('total_year_income', 0)),
                'total_year_expense': float(year_data.get('total_year_expense', 0)),
                'months': {},
                'categories': {},
            }

            # Process months
            for month, month_data in year_data.get('months', {}).items():
                month_export = {
                    'total': float(month_data.get('total', 0)),
                    'total_income': float(month_data.get('total_income', 0)),
                    'total_expense': float(month_data.get('total_expense', 0)),
                    'categories': {},
                }

                # Process categories
                for cat_main, subcats in month_data.get('categories', {}).items():
                    month_export['categories'][cat_main] = {}
                    for cat_sub, values in subcats.items():
                        cat_export = {
                            'total': float(values.get('total', 0)),
                            'count': values.get('count', 0),
                        }
                        if include_transactions:
                            cat_export['transactions'] = [
                                t.to_dict() for t in values.get('transactions', [])
                            ]
                        month_export['categories'][cat_main][cat_sub] = cat_export

                year_export['months'][month] = month_export

            # Process yearly categories
            for cat_main, subcats in year_data.get('categories_year', {}).items():
                year_export['categories'][cat_main] = {}
                for cat_sub, values in subcats.items():
                    year_export['categories'][cat_main][cat_sub] = {
                        'total': float(values.get('total', 0)),
                        'count': values.get('count', 0),
                    }

            result['years'][year] = year_export

        # Add uncategorized
        uncategorized = aggregated_data.get('uncategorized', [])
        result['uncategorized'] = [t.to_dict() for t in uncategorized]
        result['uncategorized_count'] = len(uncategorized)

        return result

    def export_transactions(
        self,
        transactions: List[Transaction],
        output_path: Path,
        pretty: bool = True,
    ):
        """
        Export raw transactions to JSON.

        Args:
            transactions: List of transactions
            output_path: Path to output file
            pretty: Whether to format JSON with indentation
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            'generated_at': datetime.now().isoformat(),
            'count': len(transactions),
            'transactions': [t.to_dict() for t in transactions],
        }

        indent = 2 if pretty else None
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, cls=DecimalEncoder, indent=indent, ensure_ascii=False)

        logger.info(f"Exported {len(transactions)} transactions to: {output_path}")
