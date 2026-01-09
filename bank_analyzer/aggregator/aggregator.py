"""Transaction aggregation by categories and time periods."""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Any

from bank_analyzer.models.transaction import Transaction
from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class Aggregator:
    """Aggregate transactions by categories and time periods."""

    def aggregate(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Aggregate transactions by year, month, and category.

        Args:
            transactions: List of transactions to aggregate

        Returns:
            Dictionary with aggregated data structure
        """
        logger.info(f"Aggregating {len(transactions)} transactions")

        # Group by years and months
        data = defaultdict(lambda: defaultdict(lambda: {
            'categories': defaultdict(lambda: defaultdict(lambda: {
                'total': Decimal('0'),
                'count': 0,
                'transactions': []
            })),
            'total': Decimal('0'),
            'total_income': Decimal('0'),
            'total_expense': Decimal('0'),
        }))

        uncategorized = []

        for trans in transactions:
            year = trans.date.year
            month = trans.date.month

            # Add to month totals
            if trans.transaction_type == 'expense':
                data[year][month]['total_expense'] += trans.amount
            else:
                data[year][month]['total_income'] += trans.amount

            data[year][month]['total'] += trans.amount

            # Track uncategorized
            if trans.category_sub == "Nieprzypisane":
                uncategorized.append(trans)

            cat_main = trans.category_main or "Inne wydatki"
            cat_sub = trans.category_sub or "Nieprzypisane"

            # Add to category
            cat_data = data[year][month]['categories'][cat_main][cat_sub]
            cat_data['total'] += trans.amount
            cat_data['count'] += 1
            cat_data['transactions'].append(trans)

        # Convert to regular dictionaries and calculate yearly totals
        result = {
            'years': {},
            'uncategorized': uncategorized,
            'all_transactions': transactions,
            'summary': {
                'total_transactions': len(transactions),
                'total_categorized': len(transactions) - len(uncategorized),
                'total_uncategorized': len(uncategorized),
            }
        }

        for year in sorted(data.keys()):
            year_data = {
                'months': {},
                'total_year': Decimal('0'),
                'total_year_income': Decimal('0'),
                'total_year_expense': Decimal('0'),
                'categories_year': defaultdict(lambda: defaultdict(lambda: {
                    'total': Decimal('0'),
                    'count': 0,
                })),
            }

            for month in sorted(data[year].keys()):
                month_data = data[year][month]

                # Convert categories to regular dict
                categories_dict = {}
                for cat_main, subcats in month_data['categories'].items():
                    categories_dict[cat_main] = {}
                    for cat_sub, values in subcats.items():
                        categories_dict[cat_main][cat_sub] = {
                            'total': values['total'],
                            'count': values['count'],
                            'transactions': values['transactions'],
                        }
                        # Aggregate to yearly
                        year_data['categories_year'][cat_main][cat_sub]['total'] += values['total']
                        year_data['categories_year'][cat_main][cat_sub]['count'] += values['count']

                year_data['months'][month] = {
                    'categories': categories_dict,
                    'total': month_data['total'],
                    'total_income': month_data['total_income'],
                    'total_expense': month_data['total_expense'],
                }

                year_data['total_year'] += month_data['total']
                year_data['total_year_income'] += month_data['total_income']
                year_data['total_year_expense'] += month_data['total_expense']

            # Convert yearly categories to regular dict
            year_data['categories_year'] = {
                cat_main: dict(subcats)
                for cat_main, subcats in year_data['categories_year'].items()
            }

            result['years'][year] = year_data

        logger.info(
            f"Aggregated {len(result['years'])} years, "
            f"{len(uncategorized)} uncategorized transactions"
        )

        return result

    def get_monthly_summary(
        self,
        aggregated_data: Dict[str, Any],
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Get summary for a specific month.

        Args:
            aggregated_data: Output from aggregate()
            year: Year
            month: Month (1-12)

        Returns:
            Monthly summary or empty dict if not found
        """
        years = aggregated_data.get('years', {})
        if year not in years:
            return {}

        months = years[year].get('months', {})
        return months.get(month, {})

    def get_category_summary(
        self,
        aggregated_data: Dict[str, Any],
        year: int,
        category_main: str = None
    ) -> Dict[str, Any]:
        """
        Get category summary for a year.

        Args:
            aggregated_data: Output from aggregate()
            year: Year
            category_main: Optional main category filter

        Returns:
            Category summary
        """
        years = aggregated_data.get('years', {})
        if year not in years:
            return {}

        categories = years[year].get('categories_year', {})

        if category_main:
            return categories.get(category_main, {})

        return categories

    def get_top_expenses(
        self,
        aggregated_data: Dict[str, Any],
        year: int = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top expense categories.

        Args:
            aggregated_data: Output from aggregate()
            year: Optional year filter (None for all years)
            limit: Number of top categories to return

        Returns:
            List of top expense categories with totals
        """
        category_totals = defaultdict(lambda: {'total': Decimal('0'), 'count': 0})

        years = aggregated_data.get('years', {})
        target_years = [year] if year else list(years.keys())

        for yr in target_years:
            if yr not in years:
                continue

            categories = years[yr].get('categories_year', {})
            for cat_main, subcats in categories.items():
                for cat_sub, values in subcats.items():
                    key = f"{cat_main} > {cat_sub}"
                    category_totals[key]['total'] += values['total']
                    category_totals[key]['count'] += values['count']
                    category_totals[key]['category_main'] = cat_main
                    category_totals[key]['category_sub'] = cat_sub

        # Sort by total (descending)
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )

        return [
            {
                'category': key,
                'category_main': values['category_main'],
                'category_sub': values['category_sub'],
                'total': float(values['total']),
                'count': values['count'],
            }
            for key, values in sorted_categories[:limit]
        ]
