# Environment Configuration Files - README

## 📁 Available Configuration Templates

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.env.production` | Production environment template | ✅ Yes |
| `.env.development` | Development environment template | ✅ Yes |
| `.env` | **Active configuration (YOUR COPY)** | ❌ **NO - Contains secrets!** |

## 🚀 Quick Start

### For Development

```bash
# Copy development template
cp .env.development .env

# Add your HuggingFace API key
# Edit .env and set: HUGGINGFACE_API_KEY=hf_your_key_here

# Start developing!
uvicorn app.main:app --reload
```

### For Production

```bash
# Copy production template
cp .env.production .env

# Configure all secrets
# See: docs/DEPLOYMENT_SETUP_GUIDE.md

# Verify no placeholders remain
grep -i "CHANGE_ME" .env  # Should return nothing

# Deploy!
uvicorn app.main:app --workers 4
```

## ⚙️ Configuration Overview

### Development Settings
- **Rate Limits:** Relaxed (100/min, 1000/hour)
- **Cost Limits:** High ($50/day user, $500/day global)
- **Debug:** Enabled
- **Token Expiry:** 24 hours
- **CORS:** All localhost allowed

### Production Settings
- **Rate Limits:** Strict (10/min, 100/hour)
- **Cost Limits:** Low ($5/day user, $100/day global)
- **Debug:** Disabled
- **Token Expiry:** 30 minutes
- **CORS:** Specific domains only

## 🔒 Security Rules

### ✅ Safe to Commit
- `.env.production` (template with placeholders)
- `.env.development` (template with defaults)
- `.env.example` (generic example)

### ❌ NEVER Commit
- `.env` (your active configuration)
- `.env.local` (local overrides)
- Any file with real API keys/passwords

## 📖 Full Documentation

For complete setup instructions, see:
- **[DEPLOYMENT_SETUP_GUIDE.md](./DEPLOYMENT_SETUP_GUIDE.md)** - Complete deployment guide
- **[PRODUCTION_FEATURES_QUICK_START.md](./PRODUCTION_FEATURES_QUICK_START.md)** - 5-minute quick start
- **[RATE_LIMITING_IMPLEMENTATION.md](./RATE_LIMITING_IMPLEMENTATION.md)** - Rate limiting details

## 🔧 Troubleshooting

**Issue:** "CHANGE_ME values still in .env"
```bash
# Check for placeholders
grep -i "CHANGE_ME" .env

# Should return nothing when ready
```

**Issue:** "HuggingFace API key not working"
```bash
# Test your API key
curl https://huggingface.co/api/whoami-v2 \
  -H "Authorization: Bearer $HUGGINGFACE_API_KEY"
```

**Issue:** "Rate limiting not working"
```bash
# Check Redis connection
redis-cli ping  # Should return "PONG"

# Check rate limiting enabled
grep RATE_LIMITING_ENABLED .env  # Should be "true"
```

## 📝 Checklist Before Production

- [ ] Copied `.env.production` to `.env`
- [ ] Replaced all `CHANGE_ME` values
- [ ] Generated secure `JWT_SECRET_KEY` (32+ chars)
- [ ] Set `DEBUG=false`
- [ ] Configured database credentials
- [ ] Configured Redis credentials
- [ ] Added HuggingFace API key
- [ ] Set CORS to specific domains
- [ ] Tested health endpoint
- [ ] Tested rate limiting
- [ ] Verified no secrets in git: `git status .env`

---

**Last Updated:** December 18, 2024
