# Email Sending Issues - Troubleshooting Guide

**Date:** November 1, 2025  
**Issue:** Email sending functionality not working

## Common Issues & Solutions

### 🔴 Issue #1: SMTP Credentials Not Configured

**Symptoms:**
- Emails fail silently
- Console shows: "SMTP credentials not configured"
- No errors but no emails received

**Root Cause:**
The `.env` file is missing or `SMTP_USER` and `SMTP_PASSWORD` are not set.

**Solution:**

1. **Check if .env file exists:**
   ```powershell
   Test-Path .env
   ```

2. **If it doesn't exist, create it:**
   ```powershell
   Copy-Item .env.example .env
   ```

3. **Edit `.env` file and add your SMTP credentials:**
   ```env
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

---

### 🔴 Issue #2: Using Gmail Without App Password

**Symptoms:**
- Error: "Username and Password not accepted"
- Error: "Authentication failed"
- Error: "(535, b'5.7.8 Username and Password not accepted')"

**Root Cause:**
Gmail requires **App Passwords** when using 2-Factor Authentication, and has deprecated "less secure apps" access.

**Solution:**

#### For Gmail Users (Recommended):

1. **Enable 2-Factor Authentication:**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other" as the device and name it "Scribes Backend"
   - Click "Generate"
   - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

3. **Update .env file:**
   ```env
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # Use the app password
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   ```

4. **Remove spaces from app password (optional):**
   ```env
   SMTP_PASSWORD=abcdefghijklmnop
   ```

---

### 🔴 Issue #3: Wrong SMTP Host/Port Configuration

**Symptoms:**
- Connection timeout
- Error: "Connection refused"
- Error: "Cannot connect to SMTP server"

**Root Cause:**
Incorrect SMTP server settings for your email provider.

**Solution:**

Choose your email provider and update `.env`:

#### Gmail:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

#### Outlook/Hotmail:
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
```

#### Yahoo:
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
```

#### Office 365:
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

#### SendGrid (Recommended for production):
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### Mailgun:
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
```

---

### 🔴 Issue #4: Firewall or Network Blocking Port 587

**Symptoms:**
- Connection timeout after 30+ seconds
- Works on home network but not at work/school

**Root Cause:**
Corporate firewalls or ISPs may block SMTP port 587.

**Solution:**

1. **Try alternate port 465 (SSL):**
   ```env
   SMTP_PORT=465
   ```
   
   **Note:** This requires code change to use SSL instead of TLS.

2. **Use port 25 (if allowed):**
   ```env
   SMTP_PORT=25
   ```

3. **Test port connectivity:**
   ```powershell
   Test-NetConnection -ComputerName smtp.gmail.com -Port 587
   ```

---

### 🔴 Issue #5: Code Issue - Missing `use_tls` Parameter

**Symptoms:**
- Error: "STARTTLS extension not supported by server"
- Connection established but authentication fails

**Root Cause:**
The current code uses `start_tls=True` but some SMTP servers need different configuration.

**Solution:**

**Current code in `app/utils/email.py`:**
```python
await aiosmtplib.send(
    message,
    hostname=settings.smtp_host,
    port=settings.smtp_port,
    username=settings.smtp_user,
    password=settings.smtp_password,
    start_tls=True,  # For port 587
)
```

**For port 465 (SSL), change to:**
```python
await aiosmtplib.send(
    message,
    hostname=settings.smtp_host,
    port=settings.smtp_port,
    username=settings.smtp_user,
    password=settings.smtp_password,
    use_tls=True,  # For port 465
)
```

---

## 🧪 Testing & Diagnostics

### Step 1: Run the Email Test Script

```powershell
cd "c:\flutter proj\Scribes\backend2"
python test_email.py
```

This will:
- ✅ Check your SMTP configuration
- ✅ Verify credentials are set
- ✅ Send a test email
- ✅ Provide detailed error messages

### Step 2: Check Configuration

```powershell
python -c "from app.core.config import settings; print(f'SMTP User: {settings.smtp_user}'); print(f'SMTP Host: {settings.smtp_host}'); print(f'SMTP Port: {settings.smtp_port}')"
```

### Step 3: Manual SMTP Test (Python Shell)

```python
import asyncio
from app.utils.email import send_email

async def test():
    success = await send_email(
        to_email="your-test-email@example.com",
        subject="Test Email",
        body="This is a test"
    )
    print(f"Success: {success}")

asyncio.run(test())
```

---

## 🔧 Code Fixes

### Fix #1: Add Better Error Logging

Update `app/utils/email.py`:

```python
async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send an email using SMTP."""
    
    if not settings.smtp_user or not settings.smtp_password:
        print("❌ ERROR: SMTP credentials not configured in .env file")
        return False
    
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))
    
    if html_body:
        message.attach(MIMEText(html_body, "html"))
    
    try:
        print(f"📧 Attempting to send email to {to_email}...")
        print(f"   Using SMTP: {settings.smtp_host}:{settings.smtp_port}")
        
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
            timeout=30,  # Add timeout
        )
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION ERROR: {str(e)}")
        print("   Check your SMTP_USER and SMTP_PASSWORD")
        print("   For Gmail, you need an App Password")
        return False
        
    except aiosmtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        print("   Cannot connect to SMTP server")
        print("   Check SMTP_HOST and SMTP_PORT")
        return False
        
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT ERROR: Connection timed out")
        print("   SMTP server not responding")
        print("   Check firewall or network settings")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
```

### Fix #2: Add Support for Port 465 (SSL)

Update `app/core/config.py` to add SSL option:

```python
smtp_use_ssl: bool = Field(default=False, description="Use SSL instead of TLS")
```

Update `app/utils/email.py`:

```python
try:
    if settings.smtp_port == 465 or settings.smtp_use_ssl:
        # Use SSL for port 465
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
            timeout=30,
        )
    else:
        # Use STARTTLS for port 587
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
            timeout=30,
        )
```

---

## 📋 Quick Checklist

Before testing email functionality:

- [ ] `.env` file exists in project root
- [ ] `SMTP_USER` is set to a valid email address
- [ ] `SMTP_PASSWORD` is set (App Password for Gmail)
- [ ] `SMTP_HOST` matches your email provider
- [ ] `SMTP_PORT` is correct (587 for TLS, 465 for SSL)
- [ ] For Gmail: 2FA is enabled and App Password generated
- [ ] Firewall allows outbound connections on SMTP port
- [ ] Test email script runs without errors
- [ ] Check spam/junk folder for test emails

---

## 🚀 Production Recommendations

### Don't Use Personal Gmail in Production!

For production environments, use a dedicated email service:

1. **SendGrid** (12,000 free emails/month)
   - Sign up at https://sendgrid.com
   - Generate API key
   - Update .env:
     ```env
     SMTP_HOST=smtp.sendgrid.net
     SMTP_PORT=587
     SMTP_USER=apikey
     SMTP_PASSWORD=your-sendgrid-api-key
     SMTP_FROM_EMAIL=verified@yourdomain.com
     ```

2. **Mailgun** (5,000 free emails/month)
3. **AWS SES** (62,000 free emails/month)
4. **Postmark** (100 free emails/month, then paid)

---

## 📞 Still Having Issues?

If emails still won't send after following this guide:

1. **Run the diagnostic script:**
   ```powershell
   python test_email.py
   ```

2. **Check the exact error message** in the console output

3. **Verify your credentials** are correct:
   - Try logging in to your email provider's webmail
   - Make sure the password works there first

4. **Test SMTP connection manually:**
   ```powershell
   telnet smtp.gmail.com 587
   ```
   (Press Ctrl+C to exit)

5. **Check server logs** for detailed error messages

---

**Last Updated:** November 1, 2025  
**Status:** Active troubleshooting guide
