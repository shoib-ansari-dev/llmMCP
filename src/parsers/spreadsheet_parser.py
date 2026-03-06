"""
Spreadsheet Parser
Extract data from Excel and CSV files.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class SpreadsheetContent:
    """Parsed spreadsheet content."""
    sheets: dict[str, pd.DataFrame]
    sheet_names: list[str]
    summary: str
    row_count: int
    column_count: int


class SpreadsheetParser:
    """Parser for Excel and CSV files."""

    def parse(self, file_path: str | Path) -> SpreadsheetContent:
        """
        Parse a spreadsheet file.

        Args:
            file_path: Path to Excel (.xlsx, .xls) or CSV file

        Returns:
            SpreadsheetContent with data and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return self._parse_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            return self._parse_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _parse_csv(self, file_path: Path) -> SpreadsheetContent:
        """Parse CSV file."""
        df = pd.read_csv(file_path)

        return SpreadsheetContent(
            sheets={"Sheet1": df},
            sheet_names=["Sheet1"],
            summary=self._generate_summary({"Sheet1": df}),
            row_count=len(df),
            column_count=len(df.columns)
        )

    def _parse_excel(self, file_path: Path) -> SpreadsheetContent:
        """Parse Excel file."""
        excel_file = pd.ExcelFile(file_path)
        sheets = {name: pd.read_excel(excel_file, sheet_name=name)
                  for name in excel_file.sheet_names}

        total_rows = sum(len(df) for df in sheets.values())
        max_cols = max(len(df.columns) for df in sheets.values()) if sheets else 0

        return SpreadsheetContent(
            sheets=sheets,
            sheet_names=excel_file.sheet_names,
            summary=self._generate_summary(sheets),
            row_count=total_rows,
            column_count=max_cols
        )

    def _generate_summary(self, sheets: dict[str, pd.DataFrame]) -> str:
        """Generate a text summary of the spreadsheet data."""
        summaries = []

        for name, df in sheets.items():
            summary = f"Sheet: {name}\n"
            summary += f"  Rows: {len(df)}, Columns: {len(df.columns)}\n"
            summary += f"  Columns: {', '.join(df.columns.astype(str))}\n"

            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary += f"  Numeric columns: {', '.join(numeric_cols)}\n"

            summaries.append(summary)

        return "\n".join(summaries)

    def to_text(self, content: SpreadsheetContent, max_rows: int = 100) -> str:
        """Convert spreadsheet content to readable text for LLM processing."""
        text_parts = []

        for name, df in content.sheets.items():
            text_parts.append(f"=== Sheet: {name} ===")
            text_parts.append(df.head(max_rows).to_string())
            if len(df) > max_rows:
                text_parts.append(f"... and {len(df) - max_rows} more rows")

        return "\n\n".join(text_parts)

