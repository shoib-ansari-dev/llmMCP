"""
Web Page Parser
Extract content from web pages.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WebPageContent:
    """Parsed web page content."""
    url: str
    title: str
    text: str
    metadata: dict


class WebPageParser:
    """Parser for web pages using trafilatura."""

    def parse(self, url: str) -> WebPageContent:
        """
        Fetch and parse a web page.

        Args:
            url: URL of the web page

        Returns:
            WebPageContent with extracted text
        """
        import requests
        import trafilatura

        # Fetch the page
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; DocumentAnalysisBot/1.0)"
        })
        response.raise_for_status()

        # Extract main content
        text = trafilatura.extract(response.text)

        # Extract metadata
        metadata = trafilatura.extract_metadata(response.text)

        title = ""
        meta_dict = {}
        if metadata:
            title = metadata.title or ""
            meta_dict = {
                "author": metadata.author,
                "date": metadata.date,
                "description": metadata.description,
                "sitename": metadata.sitename,
            }

        return WebPageContent(
            url=url,
            title=title,
            text=text or "",
            metadata=meta_dict
        )

    def parse_html(self, html: str, url: str = "") -> WebPageContent:
        """
        Parse HTML content directly.

        Args:
            html: HTML content as string
            url: Optional source URL

        Returns:
            WebPageContent with extracted text
        """
        import trafilatura

        text = trafilatura.extract(html)
        metadata = trafilatura.extract_metadata(html)

        title = ""
        meta_dict = {}
        if metadata:
            title = metadata.title or ""
            meta_dict = {
                "author": metadata.author,
                "date": metadata.date,
                "description": metadata.description,
            }

        return WebPageContent(
            url=url,
            title=title,
            text=text or "",
            metadata=meta_dict
        )

