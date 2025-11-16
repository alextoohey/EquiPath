# 🔐 Environment Setup Guide

## Safely Managing Your OpenAI API Key

This guide shows you how to use a `.env` file to keep your API key secure and prevent accidentally committing it to GitHub.

---

## 📋 Quick Setup (3 Steps)

### Step 1: Create your `.env` file

```bash
# Copy the example file
cp .env.example .env
```

### Step 2: Add your API key

Open `.env` in a text editor and replace `your-api-key-here` with your actual key:

```bash
# Before (from .env.example)
OPENAI_API_KEY=your-api-key-here

# After (your actual key)
OPENAI_API_KEY=sk-proj-abc123xyz789...
```

### Step 3: Verify it works

```bash
# Test that the key is loaded correctly
.conda/bin/python src/config.py
```

You should see:
```
✅ OpenAI API Key found: sk-proj...xyz9
```

---

## 🔒 Security Features

### What's Protected?

1. **`.gitignore`** - Prevents `.env` from being committed
2. **`.env.example`** - Template file (safe to commit, has no real keys)
3. **`python-dotenv`** - Loads environment variables automatically

### File Structure

```
your-project/
├── .env.example        ← Safe to commit (template)
├── .env                ← NEVER commit (your actual key)
├── .gitignore          ← Blocks .env from git
└── src/
    └── config.py       ← Loads .env automatically
```

---

## 📝 How to Get an OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...` or `sk-...`)
5. Paste into your `.env` file

**Important:** Copy immediately - you can't see it again!

---

## 🧪 Testing Your Setup

### Test 1: Check Config

```bash
.conda/bin/python src/config.py
```

**Expected output:**
```
Configuration Test
============================================================
✅ OpenAI API Key found: sk-proj...xyz9
Model: gpt-4
============================================================
```

### Test 2: Test AI Features

```bash
.conda/bin/python test_ai_features.py
```

**Expected output:**
```
✅ API key found
[... generates AI summary ...]
✅ TEST COMPLETE
```

### Test 3: Run Streamlit App

```bash
.conda/bin/streamlit run src/app_streamlit_chat.py
```

The app should load without API key errors.

---

## 🛡️ Best Practices

### ✅ DO:

- ✅ Use `.env` files for all secrets
- ✅ Add `.env` to `.gitignore`
- ✅ Commit `.env.example` as a template
- ✅ Use `python-dotenv` to load variables
- ✅ Keep different keys for dev/prod

### ❌ DON'T:

- ❌ Commit `.env` to git
- ❌ Share your API key publicly
- ❌ Hardcode keys in source files
- ❌ Use the same key everywhere
- ❌ Commit API keys in comments

---

## 🔄 Using the .env File in Code

### Method 1: Using `src/config.py` (Recommended)

```python
from src.config import OPENAI_API_KEY

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("No API key found!")
```

### Method 2: Direct with python-dotenv

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file
api_key = os.getenv('OPENAI_API_KEY')
```

### Method 3: Environment Variable (Production)

```bash
# Set temporarily (current session only)
export OPENAI_API_KEY="sk-proj-..."

# Or add to your shell profile (~/.zshrc or ~/.bashrc)
echo 'export OPENAI_API_KEY="sk-proj-..."' >> ~/.zshrc
source ~/.zshrc
```

---

## 🚨 What If You Accidentally Commit Your Key?

### If you committed `.env` to git:

1. **Rotate your key immediately:**
   - Go to https://platform.openai.com/api-keys
   - Revoke the exposed key
   - Create a new one
   - Update your `.env` file

2. **Remove from git history:**

```bash
# Remove the file from git (but keep locally)
git rm --cached .env

# Commit the removal
git commit -m "Remove .env from tracking"

# Push
git push
```

3. **For better security (removes from history):**

```bash
# Use BFG Repo Cleaner or git filter-branch
# See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
```

---

## 🔍 Checking If .env Is Ignored

### Verify .gitignore is working:

```bash
# Check git status
git status

# .env should NOT appear in the list
# If it does, make sure .gitignore contains:
# .env
```

### Test it:

```bash
# Try to add .env
git add .env

# Should see:
# The following paths are ignored by one of your .gitignore files:
# .env
```

---

## 🌐 Deployment (Production)

### Don't use .env files in production!

Instead, use environment variables:

**Streamlit Cloud:**
1. Go to app settings
2. Add secrets in "Secrets" section
3. Format: `OPENAI_API_KEY = "sk-proj-..."`

**Heroku:**
```bash
heroku config:set OPENAI_API_KEY="sk-proj-..."
```

**Docker:**
```bash
docker run -e OPENAI_API_KEY="sk-proj-..." myapp
```

**AWS/GCP/Azure:**
- Use their secrets management services
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault

---

## 📊 Cost Management

### Monitor usage:

1. Check usage: https://platform.openai.com/usage
2. Set spending limits in OpenAI dashboard
3. Enable email alerts for usage

### Estimate costs:

**EquiPath AI features:**
- Chat interface: ~$0.01/session
- Overall summary: ~$0.02-0.05
- Per-college summaries: ~$0.01 each
- **Total: ~$0.13-0.26 per student**

**For 100 students:** ~$13-26/month
**For 1,000 students:** ~$130-260/month

---

## 🆘 Troubleshooting

### "No OpenAI API key found"

**Check:**
1. `.env` file exists
2. Contains `OPENAI_API_KEY=sk-...`
3. No extra spaces or quotes
4. File is in project root

**Test:**
```bash
cat .env
# Should show: OPENAI_API_KEY=sk-proj-...
```

### "Invalid API key"

**Possible causes:**
1. Key was revoked
2. Copied incorrectly (missing characters)
3. Wrapped in quotes (remove them)
4. Expired or rate limited

**Fix:**
- Generate a new key
- Copy carefully
- Update `.env`

### ".env file not loading"

**Check:**
1. `python-dotenv` is installed
2. Using correct path to .env
3. Calling `load_dotenv()` before accessing env vars

**Test:**
```bash
.conda/bin/python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

---

## ✅ Security Checklist

Before committing code:

- [ ] `.env` is in `.gitignore`
- [ ] No API keys in source code
- [ ] `.env.example` has placeholder values only
- [ ] Tested that `.env` is ignored by git
- [ ] API key works in test script
- [ ] Different keys for dev/prod

Before deploying:

- [ ] Use environment variables (not .env file)
- [ ] Keys stored in secrets manager
- [ ] Spending limits set on OpenAI account
- [ ] Usage monitoring enabled
- [ ] Rotate keys regularly

---

## 📚 Additional Resources

- **OpenAI API Keys:** https://platform.openai.com/api-keys
- **OpenAI Best Practices:** https://platform.openai.com/docs/guides/safety-best-practices
- **python-dotenv docs:** https://pypi.org/project/python-dotenv/
- **GitHub secrets guide:** https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

## 🎓 Summary

1. **Never commit API keys to git**
2. **Use `.env` files for local development**
3. **Add `.env` to `.gitignore`**
4. **Use environment variables in production**
5. **Rotate keys if exposed**

**Your `.env` file is now safe and secure!** 🔐
