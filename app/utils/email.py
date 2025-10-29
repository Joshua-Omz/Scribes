"""
Email utility functions for sending notifications and verification emails.
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from app.core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not settings.smtp_user or not settings.smtp_password:
        print("SMTP credentials not configured")
        return False
    
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    # Attach plain text body
    message.attach(MIMEText(body, "plain"))
    
    # Attach HTML body if provided
    if html_body:
        message.attach(MIMEText(html_body, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


async def send_verification_email(email: str, token: str) -> bool:
    """
    Send email verification email.
    
    Args:
        email: User email address
        token: Verification token
        
    Returns:
        bool: True if email sent successfully
    """
    subject = f"Verify your {settings.app_name} account"
    
    # In production, use your frontend URL
    verification_url = f"http://localhost:3000/verify?token={token}"
    
    body = f"""
    Welcome to {settings.app_name}!
    
    Please verify your email address by clicking the link below:
    {verification_url}
    
    This link will expire in {settings.verification_token_expire_hours} hours.
    
    If you didn't create an account, please ignore this email.
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to {settings.app_name}!</h2>
            <p>Please verify your email address by clicking the button below:</p>
            <a href="{verification_url}" style="
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
            ">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in {settings.verification_token_expire_hours} hours.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                If you didn't create an account, please ignore this email.
            </p>
        </body>
    </html>
    """
    
    return await send_email(email, subject, body, html_body)


async def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send password reset email.
    
    Args:
        email: User email address
        token: Reset token
        
    Returns:
        bool: True if email sent successfully
    """
    subject = f"Reset your {settings.app_name} password"
    
    reset_url = f"http://localhost:3000/reset-password?token={token}"
    
    body = f"""
    You requested to reset your password for {settings.app_name}.
    
    Click the link below to reset your password:
    {reset_url}
    
    This link will expire in {settings.reset_token_expire_hours} hour(s).
    
    If you didn't request a password reset, please ignore this email.
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password for {settings.app_name}.</p>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_url}" style="
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
            ">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in {settings.reset_token_expire_hours} hour(s).</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                If you didn't request a password reset, please ignore this email.
            </p>
        </body>
    </html>
    """
    
    return await send_email(email, subject, body, html_body)


from typing import Optional
