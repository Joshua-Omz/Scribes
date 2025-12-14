"""
Email Utilities Module

Email sending and formatting utilities.

Usage:
    from app.utils.email import send_email, send_verification_email, send_password_reset_email
"""

from app.utils.email.email import (
    send_email,
    send_verification_email,
    send_password_reset_email,
)

__all__ = [
    "send_email",
    "send_verification_email",
    "send_password_reset_email",
]
