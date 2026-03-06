"""
Validation utilities for the Document Analysis API.
Centralized validation for all inputs.
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class FileType(Enum):
    """Supported file types."""
    PDF = "application/pdf"
    EXCEL_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    EXCEL_XLS = "application/vnd.ms-excel"
    CSV = "text/csv"


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: list[str]

    @staticmethod
    def success() -> "ValidationResult":
        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def failure(errors: list[str]) -> "ValidationResult":
        return ValidationResult(is_valid=False, errors=errors)


# =================================
# File Validation
# =================================

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    FileType.PDF.value,
    FileType.EXCEL_XLSX.value,
    FileType.EXCEL_XLS.value,
    FileType.CSV.value,
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}

# Magic bytes for file type verification
FILE_SIGNATURES = {
    "pdf": b"%PDF",
    "xlsx": b"PK\x03\x04",  # ZIP-based format
    "xls": b"\xd0\xcf\x11\xe0",  # OLE format
}


def validate_file_size(size: int) -> ValidationResult:
    """Validate file size."""
    if size <= 0:
        return ValidationResult.failure(["File is empty"])
    if size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        return ValidationResult.failure([f"File size exceeds {max_mb}MB limit"])
    return ValidationResult.success()


def validate_file_extension(filename: str) -> ValidationResult:
    """Validate file extension."""
    if not filename:
        return ValidationResult.failure(["Filename is required"])

    # Get extension
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return ValidationResult.failure([
            f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        ])
    return ValidationResult.success()


def validate_mime_type(content_type: str) -> ValidationResult:
    """Validate MIME type."""
    if not content_type:
        return ValidationResult.failure(["Content type is required"])

    if content_type not in ALLOWED_MIME_TYPES:
        return ValidationResult.failure([
            f"Invalid content type: {content_type}. Allowed: PDF, Excel, CSV"
        ])
    return ValidationResult.success()


def validate_file_content(content: bytes, filename: str) -> ValidationResult:
    """Validate file content by checking magic bytes."""
    if not content:
        return ValidationResult.failure(["File content is empty"])

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Check magic bytes for known types
    if ext == "pdf":
        if not content.startswith(FILE_SIGNATURES["pdf"]):
            return ValidationResult.failure(["Invalid PDF file format"])
    elif ext == "xlsx":
        if not content.startswith(FILE_SIGNATURES["xlsx"]):
            return ValidationResult.failure(["Invalid XLSX file format"])
    elif ext == "xls":
        if not content.startswith(FILE_SIGNATURES["xls"]):
            return ValidationResult.failure(["Invalid XLS file format"])
    # CSV doesn't have magic bytes, skip

    return ValidationResult.success()


def validate_file(
    filename: str,
    content_type: str,
    size: int,
    content: Optional[bytes] = None
) -> ValidationResult:
    """Comprehensive file validation."""
    errors = []

    # Validate extension
    result = validate_file_extension(filename)
    if not result.is_valid:
        errors.extend(result.errors)

    # Validate MIME type
    result = validate_mime_type(content_type)
    if not result.is_valid:
        errors.extend(result.errors)

    # Validate size
    result = validate_file_size(size)
    if not result.is_valid:
        errors.extend(result.errors)

    # Validate content if provided
    if content:
        result = validate_file_content(content, filename)
        if not result.is_valid:
            errors.extend(result.errors)

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


# =================================
# URL Validation
# =================================

URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

MAX_URL_LENGTH = 2048

BLOCKED_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "internal",
    "local",
}


def validate_url(url: str, allow_localhost: bool = False) -> ValidationResult:
    """Validate URL."""
    errors = []

    if not url:
        return ValidationResult.failure(["URL is required"])

    url = url.strip()

    # Check length
    if len(url) > MAX_URL_LENGTH:
        errors.append(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")

    # Check if starts with http:// or https://
    if not url.lower().startswith(('http://', 'https://')):
        errors.append("URL must start with http:// or https://")
        return ValidationResult.failure(errors)

    # Check URL pattern format
    if not URL_PATTERN.match(url):
        errors.append("Invalid URL format")

    # Check for blocked domains (security)
    if not allow_localhost:
        url_lower = url.lower()
        for blocked in BLOCKED_DOMAINS:
            if blocked in url_lower:
                errors.append(f"URLs containing '{blocked}' are not allowed")
                break

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


# =================================
# Question Validation
# =================================

MIN_QUESTION_LENGTH = 3
MAX_QUESTION_LENGTH = 1000


def validate_question(question: str) -> ValidationResult:
    """Validate question input."""
    errors = []

    if not question:
        return ValidationResult.failure(["Question is required"])

    question = question.strip()

    if len(question) < MIN_QUESTION_LENGTH:
        errors.append(f"Question must be at least {MIN_QUESTION_LENGTH} characters")

    if len(question) > MAX_QUESTION_LENGTH:
        errors.append(f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters")

    # Check for empty/whitespace only
    if not question:
        errors.append("Question cannot be empty")

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


# =================================
# Document ID Validation
# =================================

UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def validate_document_id(document_id: str) -> ValidationResult:
    """Validate document ID format (UUID)."""
    if not document_id:
        return ValidationResult.failure(["Document ID is required"])

    document_id = document_id.strip()

    if not UUID_PATTERN.match(document_id):
        return ValidationResult.failure(["Invalid document ID format"])

    return ValidationResult.success()


# =================================
# Text Content Validation
# =================================

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB of text


def validate_text_content(content: str) -> ValidationResult:
    """Validate text content."""
    if not content:
        return ValidationResult.failure(["Content is required"])

    if len(content) > MAX_CONTENT_LENGTH:
        return ValidationResult.failure([
            f"Content exceeds maximum length of {MAX_CONTENT_LENGTH // (1024*1024)}MB"
        ])

    return ValidationResult.success()


# =================================
# Sanitization
# =================================

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not filename:
        return "unnamed"

    # Remove path separators
    filename = filename.replace("/", "").replace("\\", "")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Remove path traversal patterns
    while ".." in filename:
        filename = filename.replace("..", "")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename or "unnamed"


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize general string input."""
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace("\x00", "")

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    return text

