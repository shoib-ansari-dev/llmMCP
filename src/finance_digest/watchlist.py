"""
FinanceDigest Watchlist Manager
Track companies and manage alerts.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .models import (
    WatchlistItem,
    CompanyWatchlist,
    FinancialAlert,
    AlertType
)

logger = logging.getLogger(__name__)


class WatchlistManager:
    """
    Manages user watchlists and alerts.
    In production, this would be backed by a database.
    """

    def __init__(self):
        """Initialize watchlist manager."""
        # In-memory storage (use database in production)
        self._watchlists: Dict[str, CompanyWatchlist] = {}
        self._alerts: Dict[str, List[FinancialAlert]] = {}

    # =========================================================================
    # WATCHLIST METHODS
    # =========================================================================

    def get_watchlist(self, user_id: str) -> CompanyWatchlist:
        """Get user's watchlist."""
        if user_id not in self._watchlists:
            self._watchlists[user_id] = CompanyWatchlist(
                user_id=user_id,
                items=[],
                created_at=datetime.utcnow().isoformat()
            )
        return self._watchlists[user_id]

    def add_to_watchlist(
        self,
        user_id: str,
        ticker: str,
        company_name: Optional[str] = None,
        notes: Optional[str] = None,
        alert_on_filings: bool = True,
        alert_on_price_change: bool = False,
        price_alert_threshold: Optional[float] = None
    ) -> WatchlistItem:
        """Add a company to watchlist."""
        watchlist = self.get_watchlist(user_id)

        # Check if already in watchlist
        existing = next((i for i in watchlist.items if i.ticker == ticker), None)
        if existing:
            # Update existing
            existing.notes = notes or existing.notes
            existing.alert_on_filings = alert_on_filings
            existing.alert_on_price_change = alert_on_price_change
            existing.price_alert_threshold = price_alert_threshold
            return existing

        # Add new
        item = WatchlistItem(
            ticker=ticker.upper(),
            company_name=company_name or ticker,
            added_at=datetime.utcnow().isoformat(),
            notes=notes,
            alert_on_filings=alert_on_filings,
            alert_on_price_change=alert_on_price_change,
            price_alert_threshold=price_alert_threshold
        )

        watchlist.items.append(item)
        watchlist.updated_at = datetime.utcnow().isoformat()

        logger.info(f"Added {ticker} to watchlist for user {user_id}")
        return item

    def remove_from_watchlist(self, user_id: str, ticker: str) -> bool:
        """Remove a company from watchlist."""
        watchlist = self.get_watchlist(user_id)

        initial_count = len(watchlist.items)
        watchlist.items = [i for i in watchlist.items if i.ticker != ticker.upper()]

        if len(watchlist.items) < initial_count:
            watchlist.updated_at = datetime.utcnow().isoformat()
            logger.info(f"Removed {ticker} from watchlist for user {user_id}")
            return True

        return False

    def get_watchlist_item(
        self,
        user_id: str,
        ticker: str
    ) -> Optional[WatchlistItem]:
        """Get a specific watchlist item."""
        watchlist = self.get_watchlist(user_id)
        return next((i for i in watchlist.items if i.ticker == ticker.upper()), None)

    def update_watchlist_item(
        self,
        user_id: str,
        ticker: str,
        **updates
    ) -> Optional[WatchlistItem]:
        """Update a watchlist item."""
        item = self.get_watchlist_item(user_id, ticker)
        if not item:
            return None

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        watchlist = self.get_watchlist(user_id)
        watchlist.updated_at = datetime.utcnow().isoformat()

        return item

    # =========================================================================
    # ALERT METHODS
    # =========================================================================

    def create_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        ticker: str,
        company_name: str,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ) -> FinancialAlert:
        """Create an alert for a user."""
        alert = FinancialAlert(
            id=str(uuid.uuid4()),
            user_id=user_id,
            alert_type=alert_type,
            ticker=ticker,
            company_name=company_name,
            title=title,
            message=message,
            data=data or {},
            created_at=datetime.utcnow().isoformat()
        )

        if user_id not in self._alerts:
            self._alerts[user_id] = []

        self._alerts[user_id].append(alert)

        logger.info(f"Created alert for user {user_id}: {title}")
        return alert

    def get_alerts(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[FinancialAlert]:
        """Get alerts for a user."""
        alerts = self._alerts.get(user_id, [])

        if unread_only:
            alerts = [a for a in alerts if not a.read]

        # Sort by created_at descending
        alerts = sorted(alerts, key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    def mark_alert_read(self, user_id: str, alert_id: str) -> bool:
        """Mark an alert as read."""
        alerts = self._alerts.get(user_id, [])

        for alert in alerts:
            if alert.id == alert_id:
                alert.read = True
                return True

        return False

    def mark_all_read(self, user_id: str) -> int:
        """Mark all alerts as read. Returns count marked."""
        alerts = self._alerts.get(user_id, [])
        count = 0

        for alert in alerts:
            if not alert.read:
                alert.read = True
                count += 1

        return count

    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Delete an alert."""
        if user_id not in self._alerts:
            return False

        initial_count = len(self._alerts[user_id])
        self._alerts[user_id] = [
            a for a in self._alerts[user_id] if a.id != alert_id
        ]

        return len(self._alerts[user_id]) < initial_count

    def clear_alerts(self, user_id: str) -> int:
        """Clear all alerts for a user. Returns count cleared."""
        count = len(self._alerts.get(user_id, []))
        self._alerts[user_id] = []
        return count

    # =========================================================================
    # NOTIFICATION METHODS
    # =========================================================================

    async def check_for_new_filings(
        self,
        sec_client,
        user_id: str
    ) -> List[FinancialAlert]:
        """Check for new filings for watchlist items."""
        alerts = []
        watchlist = self.get_watchlist(user_id)

        for item in watchlist.items:
            if not item.alert_on_filings:
                continue

            try:
                # Search for recent filings
                filings = await sec_client.get_recent_filings(
                    ticker=item.ticker,
                    limit=1
                )

                if filings:
                    latest = filings[0]

                    # Check if this is new
                    if item.last_filing_date != latest.filing_date:
                        # Create alert
                        alert = self.create_alert(
                            user_id=user_id,
                            alert_type=AlertType.NEW_FILING,
                            ticker=item.ticker,
                            company_name=item.company_name,
                            title=f"New {latest.filing_type} Filing",
                            message=f"{item.company_name} filed {latest.filing_type} on {latest.filing_date}",
                            data={
                                "filing_type": latest.filing_type,
                                "filing_date": latest.filing_date,
                                "url": latest.document_url
                            }
                        )
                        alerts.append(alert)

                        # Update last filing date
                        item.last_filing_date = latest.filing_date

            except Exception as e:
                logger.error(f"Error checking filings for {item.ticker}: {e}")

        return alerts

    def get_pending_email_alerts(self, user_id: str) -> List[FinancialAlert]:
        """Get alerts that need to be emailed."""
        alerts = self._alerts.get(user_id, [])
        return [a for a in alerts if not a.sent]

    def mark_alert_sent(self, alert_id: str, user_id: str) -> bool:
        """Mark an alert as sent."""
        alerts = self._alerts.get(user_id, [])

        for alert in alerts:
            if alert.id == alert_id:
                alert.sent = True
                return True

        return False

