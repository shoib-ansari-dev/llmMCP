"""
Email Service
Handles sending password reset emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from .config import get_auth_config

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails."""

    def __init__(self):
        self.config = get_auth_config()

    def _create_password_reset_email(self, to_email: str, reset_link: str) -> MIMEMultipart:
        """Create password reset email content."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset Your Password - DocuBrief"
        msg["From"] = self.config.smtp_from_email
        msg["To"] = to_email

        # Plain text version
        text = f"""
Hello,

You requested to reset your password. Click the link below to set a new password:

{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
DocuBrief Team
        """

        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #3b82f6; 
            color: white !important; 
            text-decoration: none; 
            border-radius: 6px; 
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your Password</h2>
        <p>Hello,</p>
        <p>You requested to reset your password. Click the button below to set a new password:</p>
        
        <a href="{reset_link}" class="button">Reset Password</a>
        
        <p>Or copy and paste this link in your browser:</p>
        <p style="word-break: break-all; color: #3b82f6;">{reset_link}</p>
        
        <p><strong>This link will expire in 1 hour.</strong></p>
        
        <p>If you didn't request this password reset, please ignore this email.</p>
        
        <div class="footer">
            <p>Best regards,<br>DocuBrief Team</p>
        </div>
    </div>
</body>
</html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        return msg

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if sent successfully, False otherwise
        """
        # Check if SMTP is configured
        if not self.config.smtp_host or not self.config.smtp_user:
            logger.warning("SMTP not configured. Password reset email not sent.")
            logger.info(f"Password reset link would be: {self.config.frontend_url}/reset-password?token={reset_token}")
            return True  # Return True in dev mode

        reset_link = f"{self.config.frontend_url}/reset-password?token={reset_token}"

        try:
            msg = self._create_password_reset_email(to_email, reset_link)

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(
                    self.config.smtp_from_email,
                    to_email,
                    msg.as_string()
                )

            logger.info(f"Password reset email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

