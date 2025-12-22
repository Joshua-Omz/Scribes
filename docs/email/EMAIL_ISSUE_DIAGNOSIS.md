# Email Issue Diagnosis - November 1, 2025

## 🔍 Issue Found

Your email sending is failing due to **Gmail authentication error**.

### Error Details:
```
AUTHENTICATION ERROR: (535, '5.7.8 Username and Password not accepted')
```

## 🎯 Root Cause

Your `.env` file has placeholder values that haven't been updated with real credentials:

```env
SMTP_USER=your-email@gmail.com     # ← Still placeholder
SMTP_PASSWORD=your-app-password    # ← Still placeholder
```

## ✅ Solution

You need to update your `.env` file with **real Gmail credentials**.

### Step 1: Generate a Gmail App Password

Since Gmail requires 2-Factor Authentication for app access, you need to generate an **App Password**:

1. **Go to Google Account Security:**
   - Visit: https://myaccount.google.com/security

2. **Enable 2-Step Verification:**
   - If not already enabled, click "2-Step Verification" and follow the setup

3. **Generate App Password:**
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app type
   - Select "Other (Custom name)" and enter "Scribes Backend"
   - Click "Generate"
   - You'll get a 16-character password like: `abcd efgh ijkl mnop`

4. **Copy the App Password** (remove spaces)

### Step 2: Update Your .env File

Open `c:\flutter proj\Scribes\backend2\.env` and update:

```env
# Replace these with your actual credentials
SMTP_USER=your-actual-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop    # The 16-char app password (no spaces)
```

### Step 3: Test Again

```powershell
cd "c:\flutter proj\Scribes\backend2"
python test_email.py
```

## 📝 Alternative: Use a Different Email Provider

If you don't want to use Gmail or can't set up App Passwords, you can use other providers:

### Option 1: SendGrid (Recommended for Production)
- Free tier: 100 emails/day
- Sign up: https://sendgrid.com
- No 2FA required

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=verified@yourdomain.com
```

### Option 2: Mailgun
- Free tier: 5,000 emails/month
- Sign up: https://mailgun.com

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgunapp.com
SMTP_PASSWORD=your-mailgun-password
```

### Option 3: Outlook/Hotmail
- Use your Microsoft account password directly (no app password needed)

```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
```

## 🧪 Testing Steps

After updating your credentials:

1. **Run the diagnostic script:**
   ```powershell
   python test_email.py
   ```

2. **If successful, test through the API:**
   - Start your backend server
   - Go to http://localhost:8000/docs
   - Test the `/auth/register` endpoint
   - Check if verification email is sent

3. **Check for emails:**
   - Check your inbox
   - Check spam/junk folder
   - Allow 1-2 minutes for delivery

## 🔒 Security Notes

**IMPORTANT:** Never commit your `.env` file to Git!

The `.env` file is already in `.gitignore`, but double-check:

```powershell
git status
```

If you see `.env` listed, add it to `.gitignore`:

```powershell
echo ".env" >> .gitignore
```

## 📋 Checklist

Before you can send emails:

- [ ] Create or update `.env` file
- [ ] Set real email in `SMTP_USER`
- [ ] Generate Gmail App Password (if using Gmail)
- [ ] Set App Password in `SMTP_PASSWORD`
- [ ] Run `python test_email.py` to verify
- [ ] Check spam folder if email not received
- [ ] Confirm `.env` is in `.gitignore`

## 🎯 Quick Fix Commands

```powershell
# 1. Check if .env exists
Test-Path .env

# 2. If not, create from example
Copy-Item .env.example .env

# 3. Edit the file
notepad .env

# 4. Test email configuration
python test_email.py

# 5. Restart your server if it's running
# Press Ctrl+C in the uvicorn terminal, then restart
```

## ❓ Still Not Working?

If you've updated the credentials and emails still won't send:

1. **Check your Gmail settings:**
   - Make sure you copied the app password correctly (no spaces)
   - Verify 2FA is enabled

2. **Test your credentials manually:**
   - Try logging into Gmail webmail with the same email
   - The app password won't work for webmail (that's normal)

3. **Try a different email provider:**
   - Sometimes corporate networks block Gmail SMTP
   - Try Outlook or SendGrid instead

4. **Check firewall/antivirus:**
   - Temporarily disable to test if it's blocking port 587

5. **Run verbose test:**
   ```powershell
   python -c "import asyncio; from app.utils.email import send_email; asyncio.run(send_email('test@example.com', 'Test', 'Body'))"
   ```

---

**Next Action:** Update your `.env` file with real Gmail credentials and run `python test_email.py`
