"""
FinanceDigest SEC EDGAR Client
Fetch filings from SEC EDGAR system.
"""

import logging
import httpx
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from .models import SECFiling, SECSearchResult

logger = logging.getLogger(__name__)


# SEC EDGAR API base URL
SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_API_BASE = "https://data.sec.gov"
SEC_FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"

# Common CIK to ticker mapping (partial, for demo)
TICKER_TO_CIK = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    "JPM": "0000019617",
    "JNJ": "0000200406",
    "V": "0001403161",
}


class SECEdgarClient:
    """
    Client for fetching SEC EDGAR filings.

    Note: The SEC requires a User-Agent header with contact info.
    """

    def __init__(
        self,
        user_agent: str = "FinanceDigest/1.0 (contact@example.com)"
    ):
        """
        Initialize SEC client.

        Args:
            user_agent: User-Agent string (SEC requires identification)
        """
        self.user_agent = user_agent
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.user_agent},
                timeout=30.0
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK number for a ticker."""
        ticker = ticker.upper()
        return TICKER_TO_CIK.get(ticker)

    async def get_company_filings(
        self,
        cik: Optional[str] = None,
        ticker: Optional[str] = None,
        filing_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SECFiling]:
        """
        Get company filings from SEC EDGAR.

        Args:
            cik: Company CIK number
            ticker: Company stock ticker
            filing_type: Filter by type (10-K, 10-Q, 8-K)
            limit: Maximum results

        Returns:
            List of SECFiling objects
        """
        # Get CIK from ticker if not provided
        if not cik and ticker:
            cik = self.get_cik_for_ticker(ticker)
            if not cik:
                logger.warning(f"CIK not found for ticker: {ticker}")
                return []

        if not cik:
            raise ValueError("Either cik or ticker must be provided")

        # Normalize CIK (remove leading zeros for API)
        cik_normalized = cik.lstrip("0")
        cik_padded = cik.zfill(10)

        try:
            # Use SEC submissions API
            url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            filings = []

            # Parse filings from response
            recent = data.get("filings", {}).get("recent", {})

            forms = recent.get("form", [])
            filing_dates = recent.get("filingDate", [])
            accession_numbers = recent.get("accessionNumber", [])
            primary_documents = recent.get("primaryDocument", [])

            for i in range(min(len(forms), limit * 2)):  # Get more, filter later
                form = forms[i] if i < len(forms) else ""

                # Filter by filing type if specified
                if filing_type and form != filing_type:
                    continue

                accession = accession_numbers[i] if i < len(accession_numbers) else ""
                filing_date = filing_dates[i] if i < len(filing_dates) else ""
                primary_doc = primary_documents[i] if i < len(primary_documents) else ""

                # Build URLs
                accession_no_dash = accession.replace("-", "")
                filing_url = f"{SEC_EDGAR_BASE}/Archives/edgar/data/{cik_normalized}/{accession_no_dash}/{accession}-index.htm"
                doc_url = f"{SEC_EDGAR_BASE}/Archives/edgar/data/{cik_normalized}/{accession_no_dash}/{primary_doc}"

                filing = SECFiling(
                    accession_number=accession,
                    filing_type=form,
                    company_name=data.get("name", ""),
                    cik=cik_padded,
                    ticker=ticker.upper() if ticker else None,
                    filing_date=filing_date,
                    accepted_date=filing_date,  # API doesn't provide accepted time
                    document_url=doc_url,
                    filing_url=filing_url
                )

                filings.append(filing)

                if len(filings) >= limit:
                    break

            return filings

        except httpx.HTTPError as e:
            logger.error(f"SEC API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching filings: {e}")
            return []

    async def get_recent_filings(
        self,
        ticker: str,
        filing_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[SECFiling]:
        """
        Get recent filings for a company.

        Args:
            ticker: Company stock ticker
            filing_types: Filter by types (default: 10-K, 10-Q, 8-K)
            limit: Maximum results

        Returns:
            List of recent filings
        """
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K"]

        all_filings = await self.get_company_filings(
            ticker=ticker,
            limit=limit * len(filing_types)
        )

        # Filter by types
        filtered = [f for f in all_filings if f.filing_type in filing_types]

        return filtered[:limit]

    async def get_10k_filings(
        self,
        ticker: str,
        limit: int = 5
    ) -> List[SECFiling]:
        """Get 10-K annual reports."""
        return await self.get_company_filings(
            ticker=ticker,
            filing_type="10-K",
            limit=limit
        )

    async def get_10q_filings(
        self,
        ticker: str,
        limit: int = 4
    ) -> List[SECFiling]:
        """Get 10-Q quarterly reports."""
        return await self.get_company_filings(
            ticker=ticker,
            filing_type="10-Q",
            limit=limit
        )

    async def get_8k_filings(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[SECFiling]:
        """Get 8-K current reports."""
        return await self.get_company_filings(
            ticker=ticker,
            filing_type="8-K",
            limit=limit
        )

    async def download_filing(
        self,
        filing: SECFiling
    ) -> Optional[str]:
        """
        Download filing document text.

        Args:
            filing: SECFiling object

        Returns:
            Filing text content
        """
        try:
            response = await self.client.get(filing.document_url)
            response.raise_for_status()

            content = response.text

            # Basic HTML cleanup for text filings
            if filing.document_url.endswith(".htm") or filing.document_url.endswith(".html"):
                # Remove HTML tags (basic cleanup)
                import re
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()

            return content

        except Exception as e:
            logger.error(f"Error downloading filing: {e}")
            return None

    async def search_filings(
        self,
        query: str,
        filing_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> SECSearchResult:
        """
        Search SEC filings by text query.

        Note: This is a simplified search. Full-text search requires
        the SEC EDGAR full-text search API.

        Args:
            query: Search query
            filing_types: Filter by types
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum results

        Returns:
            SECSearchResult with matching filings
        """
        # For demo, we'll search by ticker
        # Full implementation would use SEC's full-text search API

        filings = []

        # If query looks like a ticker, search for that company
        if query.isalpha() and len(query) <= 5:
            filings = await self.get_company_filings(
                ticker=query.upper(),
                limit=limit
            )

        # Filter by filing types
        if filing_types:
            filings = [f for f in filings if f.filing_type in filing_types]

        # Filter by date range
        if start_date:
            filings = [f for f in filings if f.filing_date >= start_date]
        if end_date:
            filings = [f for f in filings if f.filing_date <= end_date]

        return SECSearchResult(
            query=query,
            total_results=len(filings),
            filings=filings[:limit]
        )

    async def get_company_info(self, ticker: str) -> Optional[Dict]:
        """
        Get basic company information from SEC.

        Args:
            ticker: Company stock ticker

        Returns:
            Company info dict
        """
        cik = self.get_cik_for_ticker(ticker)
        if not cik:
            return None

        try:
            cik_padded = cik.zfill(10)
            url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            return {
                "cik": cik_padded,
                "name": data.get("name"),
                "ticker": ticker.upper(),
                "sic": data.get("sic"),
                "sic_description": data.get("sicDescription"),
                "fiscal_year_end": data.get("fiscalYearEnd"),
                "state": data.get("stateOfIncorporation"),
                "exchange": data.get("exchanges", [None])[0] if data.get("exchanges") else None
            }

        except Exception as e:
            logger.error(f"Error getting company info: {e}")
            return None

