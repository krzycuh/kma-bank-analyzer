"""Excel export with formatting."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

from bank_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelExporter:
    """Export aggregated data to Excel with formatting."""

    MONTHS_PL = {
        1: 'Sty', 2: 'Lut', 3: 'Mar', 4: 'Kwi',
        5: 'Maj', 6: 'Cze', 7: 'Lip', 8: 'Sie',
        9: 'Wrz', 10: 'Paź', 11: 'Lis', 12: 'Gru',
    }

    def export(self, aggregated_data: Dict[str, Any], output_path: Path):
        """
        Export data to Excel file.

        Args:
            aggregated_data: Aggregated data from Aggregator
            output_path: Path to output file
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            logger.error("openpyxl not installed. Run: pip install openpyxl")
            raise ImportError("openpyxl is required for Excel export")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup if file exists
        if output_path.exists():
            backup_path = output_path.with_suffix(
                f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            output_path.rename(backup_path)
            logger.info(f"Created backup: {backup_path.name}")

        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Create sheets
        years = aggregated_data.get('years', {})
        for year in sorted(years.keys()):
            self._create_year_summary_sheet(wb, aggregated_data, year)

        uncategorized = aggregated_data.get('uncategorized', [])
        if uncategorized:
            self._create_uncategorized_sheet(wb, uncategorized)

        all_transactions = aggregated_data.get('all_transactions', [])
        if all_transactions:
            self._create_all_transactions_sheet(wb, all_transactions)

        # Save
        wb.save(output_path)
        logger.info(f"Exported to: {output_path}")

    # Number format with an empty third section: zeros display as blank,
    # so formula cells don't clutter the sheet with 0.00
    NUM_FMT = '#,##0.00;-#,##0.00;'

    # Main category holding real incomes (salary etc.). Incomes assigned to
    # any OTHER category are treated as refunds and net against expenses.
    INCOME_CATEGORY = 'Przychody'

    def _create_year_summary_sheet(
        self,
        wb,
        data: Dict[str, Any],
        year: int
    ):
        """Create yearly summary sheet.

        Expenses (including uncategorized) and incomes are shown in separate
        sections. All totals are Excel SUM formulas, so it is visible which
        cells feed into each sum.
        """
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter

        ws = wb.create_sheet(f"Rok {year}")
        year_data = data['years'][year]

        # Title
        ws['A1'] = f"Rok {year}"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:N1')

        # Headers
        row = 3
        ws.cell(row, 1, "Kategoria")
        for month in range(1, 13):
            ws.cell(row, month + 1, self.MONTHS_PL[month])
        ws.cell(row, 14, "SUMA ROCZNA")

        header_fill = PatternFill(
            start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
        )
        for col in range(1, 15):
            cell = ws.cell(row, col)
            cell.font = Font(bold=True)
            cell.fill = header_fill

        sum_fill = PatternFill(
            start_color="E0E0E0", end_color="E0E0E0", fill_type="solid"
        )

        # Expense section: everything except the income category; refunds
        # (incomes assigned to regular categories) show up as negatives
        ws.cell(row + 1, 1, "WYDATKI").font = Font(bold=True, size=12)
        next_row, expense_mains = self._write_category_section(
            ws, year_data, row + 2, section='expense'
        )
        self._write_sum_row(
            ws, next_row, "SUMA MIESIĘCZNA (wydatki)", expense_mains, sum_fill
        )
        row = next_row + 2

        # Income section: only the 'Przychody' category
        categories = year_data.get('categories_year', {})
        income_subcats = categories.get(self.INCOME_CATEGORY, {})
        has_income = any(
            sub.get('expense') or sub.get('income')
            for sub in income_subcats.values()
        )
        if has_income:
            ws.cell(row, 1, "PRZYCHODY").font = Font(bold=True, size=12)
            next_row, income_mains = self._write_category_section(
                ws, year_data, row + 1, section='income'
            )
            self._write_sum_row(
                ws, next_row, "SUMA MIESIĘCZNA (przychody)", income_mains,
                sum_fill,
            )
            row = next_row + 2

        # Excluded section: shown for reference only, never part of totals.
        # Reuses the category writer via a pseudo year_data keyed by reason.
        excluded_year = (
            data.get('excluded', {}).get('years', {}).get(year)
        )
        if excluded_year:
            ws.cell(row, 1, "WYKLUCZONE (poza sumami)").font = Font(
                bold=True, size=12
            )
            pseudo_year_data = {
                'categories_year': {
                    'Wykluczone': excluded_year.get('reasons_year', {})
                },
                'months': {
                    month: {'categories': {'Wykluczone': reasons}}
                    for month, reasons in excluded_year.get('months', {}).items()
                },
            }
            next_row, excluded_mains = self._write_category_section(
                ws, pseudo_year_data, row + 1, section='expense'
            )
            self._write_sum_row(
                ws, next_row, "SUMA MIESIĘCZNA (wykluczone)", excluded_mains,
                sum_fill,
            )

        # Column widths
        ws.column_dimensions['A'].width = 35
        for col in range(2, 15):
            ws.column_dimensions[get_column_letter(col)].width = 12

        # Freeze panes
        ws.freeze_panes = 'B4'

    def _write_category_section(self, ws, year_data, row, section):
        """Write category rows for one sheet section.

        section='expense': all categories except INCOME_CATEGORY; monthly
        values are expense minus income, so a refund assigned to a regular
        category reduces it (showing as a negative in the refund's month).
        section='income': only INCOME_CATEGORY (income minus expense).

        Subcategory cells hold values; main-category rows and the yearly
        column are SUM formulas over them. Returns (next_free_row,
        list_of_main_category_rows).
        """
        from openpyxl.styles import Font
        from openpyxl.utils import get_column_letter

        categories = year_data.get('categories_year', {})
        months = year_data.get('months', {})
        main_rows = []
        zero = Decimal('0')

        for cat_main in sorted(categories.keys()):
            if (cat_main == self.INCOME_CATEGORY) != (section == 'income'):
                continue

            subcats = categories[cat_main]
            active_subs = [
                s for s in sorted(subcats.keys())
                if subcats[s].get('expense', zero)
                or subcats[s].get('income', zero)
            ]
            if not active_subs:
                continue

            start_row = row
            main_rows.append(start_row)
            ws.cell(row, 1, cat_main)
            ws.cell(row, 1).font = Font(bold=True)

            for cat_sub in active_subs:
                row += 1
                ws.cell(row, 1, f"  {cat_sub}")  # Indented

                for month in range(1, 13):
                    cats = months.get(month, {}).get('categories', {})
                    values = cats.get(cat_main, {}).get(cat_sub, {})
                    expense = values.get('expense', zero)
                    income = values.get('income', zero)
                    amount = (
                        income - expense if section == 'income'
                        else expense - income
                    )
                    if amount:
                        cell = ws.cell(row, month + 1, float(amount))
                        cell.number_format = self.NUM_FMT

                # Yearly total for subcategory: sum of its months
                cell = ws.cell(row, 14, f"=SUM(B{row}:M{row})")
                cell.number_format = self.NUM_FMT

            # Main category row: per-month SUM over its subcategory rows
            first_sub, last_sub = start_row + 1, row
            for month in range(1, 13):
                col = get_column_letter(month + 1)
                cell = ws.cell(
                    start_row, month + 1,
                    f"=SUM({col}{first_sub}:{col}{last_sub})"
                )
                cell.number_format = self.NUM_FMT
                cell.font = Font(bold=True)

            cell = ws.cell(start_row, 14, f"=SUM(B{start_row}:M{start_row})")
            cell.number_format = self.NUM_FMT
            cell.font = Font(bold=True)

            row += 1

        return row + 1, main_rows

    def _write_sum_row(self, ws, row, label, main_rows, fill):
        """Write a bold sum row adding up the given main-category rows."""
        from openpyxl.styles import Font
        from openpyxl.utils import get_column_letter

        ws.cell(row, 1, label)
        ws.cell(row, 1).font = Font(bold=True)
        ws.cell(row, 1).fill = fill

        for month in range(1, 13):
            col = get_column_letter(month + 1)
            refs = ",".join(f"{col}{r}" for r in main_rows)
            cell = ws.cell(row, month + 1, f"=SUM({refs})" if refs else 0)
            cell.number_format = self.NUM_FMT
            cell.font = Font(bold=True)
            cell.fill = fill

        cell = ws.cell(row, 14, f"=SUM(B{row}:M{row})")
        cell.number_format = self.NUM_FMT
        cell.font = Font(bold=True)
        cell.fill = fill

    def _create_uncategorized_sheet(self, wb, uncategorized):
        """Sheet with uncategorized transactions."""
        from openpyxl.styles import Font, PatternFill

        ws = wb.create_sheet("Nieprzypisane")

        # Headers
        headers = ['Data', 'Kontrahent', 'Opis', 'Kwota', 'Bank', 'ID']
        header_fill = PatternFill(
            start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
        )

        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col, header)
            cell.font = Font(bold=True)
            cell.fill = header_fill

        # Data
        for row, trans in enumerate(uncategorized, 2):
            ws.cell(row, 1, trans.date.strftime('%Y-%m-%d'))
            ws.cell(row, 2, trans.counterparty)
            ws.cell(row, 3, trans.description[:100])  # Limit description length
            ws.cell(row, 4, float(trans.amount))
            ws.cell(row, 5, trans.source_bank)
            ws.cell(row, 6, trans.id)

            ws.cell(row, 4).number_format = '#,##0.00'

        # Column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 18

        # AutoFilter
        if uncategorized:
            ws.auto_filter.ref = f"A1:F{len(uncategorized) + 1}"

    def _create_all_transactions_sheet(self, wb, transactions):
        """Sheet with all transactions."""
        from openpyxl.styles import Font, PatternFill

        ws = wb.create_sheet("Wszystkie transakcje")

        # Headers
        headers = [
            'Data', 'Kontrahent', 'Opis', 'Kwota',
            'Kategoria', 'Podkategoria', 'Bank', 'ID'
        ]
        header_fill = PatternFill(
            start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
        )

        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col, header)
            cell.font = Font(bold=True)
            cell.fill = header_fill

        # Data (sorted by date descending)
        sorted_trans = sorted(transactions, key=lambda t: t.date, reverse=True)
        alt_fill = PatternFill(
            start_color="F0F0F0", end_color="F0F0F0", fill_type="solid"
        )

        for row, trans in enumerate(sorted_trans, 2):
            ws.cell(row, 1, trans.date.strftime('%Y-%m-%d'))
            ws.cell(row, 2, trans.counterparty)
            ws.cell(row, 3, trans.description[:100])
            ws.cell(row, 4, float(trans.amount))
            ws.cell(row, 5, trans.category_main or '')
            ws.cell(row, 6, trans.category_sub or '')
            ws.cell(row, 7, trans.source_bank)
            ws.cell(row, 8, trans.id)

            ws.cell(row, 4).number_format = '#,##0.00'

            # Excluded transactions greyed out - visible but out of totals
            if trans.category_main == 'Wykluczone':
                for col in range(1, 9):
                    ws.cell(row, col).font = Font(color="999999")

            # Alternate row coloring
            if row % 2 == 0:
                for col in range(1, 9):
                    ws.cell(row, col).fill = alt_fill

        # Column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 25
        ws.column_dimensions['G'].width = 10
        ws.column_dimensions['H'].width = 18

        # AutoFilter
        if transactions:
            ws.auto_filter.ref = f"A1:H{len(transactions) + 1}"
