# 🔑 Quick: Set Up Your OpenAI API Key

## 3 Simple Steps

### 1️⃣ Open the `.env` file

```bash
# Open in your text editor
open .env

# OR use nano/vim
nano .env
```

### 2️⃣ Replace `your-api-key-here` with your actual key

**Before:**
```
OPENAI_API_KEY=your-api-key-here
```

**After:**
```
OPENAI_API_KEY=sk-proj-abc123xyz789yourrealkeyhere
```

### 3️⃣ Save and test

```bash
# Test it loaded correctly
.conda/bin/python src/config.py

# Should see:
# ✅ OpenAI API Key found: sk-proj...xyz9
```

---

## 🎯 That's It!

Now run the AI-enhanced app:

```bash
.conda/bin/streamlit run src/app_streamlit_chat.py
```

---

## 🔐 Security Notes

✅ `.env` is already in `.gitignore` - it won't be committed to git
✅ Never share your API key with anyone
✅ If exposed, revoke it immediately at: https://platform.openai.com/api-keys

---

## 📍 Where to Get an API Key

1. Go to: **https://platform.openai.com/api-keys**
2. Sign in (or create account)
3. Click **"Create new secret key"**
4. **Copy it immediately** (you can't see it again!)
5. Paste into `.env` file

---

## ❓ Need More Help?

See detailed guide: **[ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)**
