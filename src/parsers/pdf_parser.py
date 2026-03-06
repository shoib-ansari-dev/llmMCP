"""
PDF Parser
Extract text, tables, and metadata from PDF documents.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImageInfo:
    """Information about an image in a PDF."""
    page_number: int
    width: int
    height: int
    image_type: str


@dataclass
class TableInfo:
    """Information about a table extracted from PDF."""
    page_number: int
    content: str
    row_count: int
    col_count: int


@dataclass
class PDFContent:
    """Parsed PDF content."""
    text: str
    page_count: int
    metadata: dict
    tables: list[TableInfo] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)


class PDFParser:
    """Parser for PDF documents using PyMuPDF."""

    def _extract_tables(self, page, page_num: int) -> list[TableInfo]:
        """Extract tables from a PDF page."""
        tables = []
        try:
            # PyMuPDF can find tables in pages
            page_tables = page.find_tables()
            for table in page_tables:
                # Extract table data
                table_data = table.extract()
                if table_data:
                    # Convert to string representation
                    rows = []
                    for row in table_data:
                        rows.append(" | ".join(str(cell) if cell else "" for cell in row))
                    content = "\n".join(rows)

                    tables.append(TableInfo(
                        page_number=page_num + 1,
                        content=content,
                        row_count=len(table_data),
                        col_count=len(table_data[0]) if table_data else 0
                    ))
        except Exception:
            # Table extraction not supported in older PyMuPDF versions
            pass
        return tables

    def _extract_images(self, page, page_num: int) -> list[ImageInfo]:
        """Extract image metadata from a PDF page."""
        images = []
        try:
            image_list = page.get_images()
            for img in image_list:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                if base_image:
                    images.append(ImageInfo(
                        page_number=page_num + 1,
                        width=base_image.get("width", 0),
                        height=base_image.get("height", 0),
                        image_type=base_image.get("ext", "unknown")
                    ))
        except Exception:
            pass
        return images

    def parse(self, file_path: str | Path) -> PDFContent:
        """
        Parse a PDF file and extract its content.

        Args:
            file_path: Path to the PDF file

        Returns:
            PDFContent with extracted text, tables, images, and metadata
        """
        import fitz  # PyMuPDF

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        doc = fitz.open(file_path)

        text_content = []
        all_tables = []
        all_images = []

        for page_num, page in enumerate(doc):
            text_content.append(page.get_text())
            all_tables.extend(self._extract_tables(page, page_num))
            all_images.extend(self._extract_images(page, page_num))

        content = PDFContent(
            text="\n".join(text_content),
            page_count=len(doc),
            metadata=dict(doc.metadata),
            tables=all_tables,
            images=all_images
        )

        doc.close()
        return content

    def parse_bytes(self, file_bytes: bytes, filename: str = "document.pdf") -> PDFContent:
        """
        Parse PDF from bytes.

        Args:
            file_bytes: PDF file content as bytes
            filename: Optional filename for reference

        Returns:
            PDFContent with extracted text, tables, images, and metadata
        """
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")

        text_content = []
        all_tables = []
        all_images = []

        for page_num, page in enumerate(doc):
            text_content.append(page.get_text())
            all_tables.extend(self._extract_tables(page, page_num))
            all_images.extend(self._extract_images(page, page_num))

        content = PDFContent(
            text="\n".join(text_content),
            page_count=len(doc),
            metadata=dict(doc.metadata),
            tables=all_tables,
            images=all_images
        )

        doc.close()
        return content

