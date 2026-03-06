"""
Tests for document parsers.
"""

import pytest
from pathlib import Path


class TestPDFParser:
    """Tests for PDF parser."""

    def test_parser_import(self):
        """Test that PDF parser can be imported."""
        from src.parsers import PDFParser
        parser = PDFParser()
        assert parser is not None

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        from src.parsers import PDFParser
        parser = PDFParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.pdf")


class TestSpreadsheetParser:
    """Tests for spreadsheet parser."""

    def test_parser_import(self):
        """Test that spreadsheet parser can be imported."""
        from src.parsers import SpreadsheetParser
        parser = SpreadsheetParser()
        assert parser is not None

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        from src.parsers import SpreadsheetParser
        parser = SpreadsheetParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.xlsx")

    def test_unsupported_file_type(self):
        """Test parsing an unsupported file type."""
        from src.parsers import SpreadsheetParser
        import tempfile

        parser = SpreadsheetParser()

        # Create a temp file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        with pytest.raises(ValueError):
            parser.parse(temp_path)

        # Cleanup
        Path(temp_path).unlink()


class TestWebPageParser:
    """Tests for web page parser."""

    def test_parser_import(self):
        """Test that web parser can be imported."""
        from src.parsers import WebPageParser
        parser = WebPageParser()
        assert parser is not None

