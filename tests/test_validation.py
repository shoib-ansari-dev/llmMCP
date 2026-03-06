"""
Tests for validation utilities.
"""

import pytest


class TestFileValidation:
    """Tests for file validation."""

    def test_valid_pdf_extension(self):
        from src.utils.validation import validate_file_extension

        result = validate_file_extension("document.pdf")
        assert result.is_valid is True

    def test_valid_xlsx_extension(self):
        from src.utils.validation import validate_file_extension

        result = validate_file_extension("spreadsheet.xlsx")
        assert result.is_valid is True

    def test_invalid_extension(self):
        from src.utils.validation import validate_file_extension

        result = validate_file_extension("script.exe")
        assert result.is_valid is False
        assert "Invalid file type" in result.errors[0]

    def test_no_extension(self):
        from src.utils.validation import validate_file_extension

        result = validate_file_extension("noextension")
        assert result.is_valid is False

    def test_valid_file_size(self):
        from src.utils.validation import validate_file_size

        result = validate_file_size(1024 * 1024)  # 1MB
        assert result.is_valid is True

    def test_empty_file(self):
        from src.utils.validation import validate_file_size

        result = validate_file_size(0)
        assert result.is_valid is False
        assert "empty" in result.errors[0].lower()

    def test_file_too_large(self):
        from src.utils.validation import validate_file_size, MAX_FILE_SIZE

        result = validate_file_size(MAX_FILE_SIZE + 1)
        assert result.is_valid is False
        assert "exceeds" in result.errors[0].lower()

    def test_valid_mime_type_pdf(self):
        from src.utils.validation import validate_mime_type

        result = validate_mime_type("application/pdf")
        assert result.is_valid is True

    def test_invalid_mime_type(self):
        from src.utils.validation import validate_mime_type

        result = validate_mime_type("application/javascript")
        assert result.is_valid is False

    def test_comprehensive_file_validation(self):
        from src.utils.validation import validate_file

        result = validate_file(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024
        )
        assert result.is_valid is True


class TestUrlValidation:
    """Tests for URL validation."""

    def test_valid_https_url(self):
        from src.utils.validation import validate_url

        result = validate_url("https://example.com")
        assert result.is_valid is True

    def test_valid_http_url(self):
        from src.utils.validation import validate_url

        result = validate_url("http://example.com/page")
        assert result.is_valid is True

    def test_valid_url_with_port(self):
        from src.utils.validation import validate_url

        result = validate_url("https://api.example.com:8080/v1")
        assert result.is_valid is True

    def test_missing_protocol(self):
        from src.utils.validation import validate_url

        result = validate_url("example.com")
        assert result.is_valid is False
        assert "http" in result.errors[0].lower()

    def test_invalid_protocol(self):
        from src.utils.validation import validate_url

        result = validate_url("ftp://example.com")
        assert result.is_valid is False

    def test_localhost_blocked(self):
        from src.utils.validation import validate_url

        result = validate_url("http://localhost:3000")
        assert result.is_valid is False
        assert "local" in result.errors[0].lower()

    def test_127_0_0_1_blocked(self):
        from src.utils.validation import validate_url

        result = validate_url("http://127.0.0.1:8000")
        assert result.is_valid is False

    def test_empty_url(self):
        from src.utils.validation import validate_url

        result = validate_url("")
        assert result.is_valid is False
        assert "required" in result.errors[0].lower()

    def test_localhost_allowed_when_enabled(self):
        from src.utils.validation import validate_url

        result = validate_url("http://localhost:3000", allow_localhost=True)
        assert result.is_valid is True


class TestQuestionValidation:
    """Tests for question validation."""

    def test_valid_question(self):
        from src.utils.validation import validate_question

        result = validate_question("What is the main topic of this document?")
        assert result.is_valid is True

    def test_question_too_short(self):
        from src.utils.validation import validate_question

        result = validate_question("Hi")
        assert result.is_valid is False
        assert "at least" in result.errors[0].lower()

    def test_empty_question(self):
        from src.utils.validation import validate_question

        result = validate_question("")
        assert result.is_valid is False

    def test_whitespace_only(self):
        from src.utils.validation import validate_question

        result = validate_question("   ")
        assert result.is_valid is False

    def test_question_too_long(self):
        from src.utils.validation import validate_question

        long_question = "a" * 1001
        result = validate_question(long_question)
        assert result.is_valid is False
        assert "exceeds" in result.errors[0].lower()


class TestDocumentIdValidation:
    """Tests for document ID validation."""

    def test_valid_uuid(self):
        from src.utils.validation import validate_document_id

        result = validate_document_id("550e8400-e29b-41d4-a716-446655440000")
        assert result.is_valid is True

    def test_valid_uuid_uppercase(self):
        from src.utils.validation import validate_document_id

        result = validate_document_id("550E8400-E29B-41D4-A716-446655440000")
        assert result.is_valid is True

    def test_invalid_uuid_format(self):
        from src.utils.validation import validate_document_id

        result = validate_document_id("not-a-uuid")
        assert result.is_valid is False

    def test_empty_document_id(self):
        from src.utils.validation import validate_document_id

        result = validate_document_id("")
        assert result.is_valid is False


class TestSanitization:
    """Tests for sanitization functions."""

    def test_sanitize_filename_path_traversal(self):
        from src.utils.validation import sanitize_filename

        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_filename_null_bytes(self):
        from src.utils.validation import sanitize_filename

        result = sanitize_filename("file\x00name.pdf")
        assert "\x00" not in result

    def test_sanitize_string_length_limit(self):
        from src.utils.validation import sanitize_string

        result = sanitize_string("a" * 2000, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_strips_whitespace(self):
        from src.utils.validation import sanitize_string

        result = sanitize_string("  hello world  ")
        assert result == "hello world"

