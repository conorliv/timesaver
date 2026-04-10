"""Tests for notifier module."""

import smtplib
import socket
from unittest.mock import MagicMock, patch

from timesaver import notifier


def test_send_shame_email_success():
    """Test successful email sending."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.sendmail.assert_called_once()


def test_send_shame_email_multiple_recipients():
    """Test sending to multiple recipients."""
    recipients = ["partner1@example.com", "partner2@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is True
        # Verify sendmail was called with both recipients
        call_args = mock_server.sendmail.call_args
        assert call_args[0][1] == recipients


def test_send_shame_email_no_recipients():
    """Test that empty recipients list returns False."""
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    result = notifier.send_shame_email([], smtp_config)
    assert result is False


def test_send_shame_email_no_server():
    """Test that empty server returns False."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    result = notifier.send_shame_email(recipients, smtp_config)
    assert result is False


def test_send_shame_email_connection_failure():
    """Test handling of SMTP connection failure."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = socket.error("Connection refused")

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is False


def test_send_shame_email_auth_failure():
    """Test handling of SMTP authentication failure."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is False


def test_send_shame_email_send_failure():
    """Test handling of send failure."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.side_effect = smtplib.SMTPException("Send failed")

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is False


def test_send_shame_email_without_auth():
    """Test sending without authentication (no username/password)."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "",
        "password": "",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_not_called()


def test_send_shame_email_os_error():
    """Test handling of OS error."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = OSError("Network unreachable")

        result = notifier.send_shame_email(recipients, smtp_config)

        assert result is False


def test_send_shame_email_content():
    """Test that email contains expected content."""
    recipients = ["partner@example.com"]
    smtp_config = {
        "server": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "password123",
    }

    with patch("smtplib.SMTP") as mock_smtp:
        with patch("getpass.getuser", return_value="testuser"):
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            notifier.send_shame_email(recipients, smtp_config)

            # Get the email content
            call_args = mock_server.sendmail.call_args
            email_content = call_args[0][2]

            assert "TimeSaver Alert" in email_content
            assert "testuser" in email_content
            assert "5:00 AM - 5:00 PM" in email_content
