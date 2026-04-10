"""Email notification module for accountability features."""

import getpass
import smtplib
import socket
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def send_shame_email(recipients: list[str], smtp_config: dict[str, Any]) -> bool:
    """Send notification that user disabled blocking during focus time.

    Args:
        recipients: List of email addresses to notify
        smtp_config: SMTP configuration dict with server, port, username, password

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not recipients:
        return False

    if not smtp_config.get("server"):
        return False

    # Get current time in Pacific
    now_pacific = datetime.now(PACIFIC_TZ)
    timestamp = now_pacific.strftime("%Y-%m-%d %I:%M %p")

    # Get username
    username = getpass.getuser()

    subject = "TimeSaver Alert: Blocking Disabled"
    body = f"""{username} disabled their website blocker.

Time: {timestamp} Pacific
During: Scheduled focus hours (5:00 AM - 5:00 PM)

This is an automated accountability notification from TimeSaver.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_config.get("username", "timesaver@localhost")
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(smtp_config["server"], smtp_config["port"], timeout=10) as server:
            server.starttls()
            if smtp_config.get("username") and smtp_config.get("password"):
                server.login(smtp_config["username"], smtp_config["password"])
            server.sendmail(msg["From"], recipients, msg.as_string())
        return True
    except (smtplib.SMTPException, socket.error, OSError):
        return False
