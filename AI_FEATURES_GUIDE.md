# 🤖 EquiPath AI Features Guide

## Overview

The enhanced EquiPath app (`app_streamlit_chat.py`) includes powerful AI features:

1. **💬 Conversational Profile Builder** - Chat with an AI to build your profile naturally
2. **🤖 Personalized Summary** - AI-generated overview of your matches
3. **💡 College-Specific Insights** - AI explanation for why each college fits you

---

## 🚀 Quick Start

### 1. Set Your OpenAI API Key

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Option B: In the App**
- Enter your API key in the sidebar settings

### 2. Run the Enhanced App

```bash
.conda/bin/streamlit run src/app_streamlit_chat.py
```

---

## 💬 Chat Mode (Conversational Profile Building)

Instead of filling out forms, just chat naturally!

### Example Conversation:

**EquiPath:** Hi! I'm here to help you find colleges. What's your name?
> **You:** Maria Rodriguez

**EquiPath:** Nice to meet you! How would you describe your racial/ethnic background?
> **You:** I'm Hispanic

**EquiPath:** Are you a student-parent (do you have children)?
> **You:** Yes, I have a 2-year-old daughter

**EquiPath:** Are you a first-generation college student?
> **You:** Yes, my parents didn't go to college

**EquiPath:** What's your approximate annual budget for college?
> **You:** About 18000 dollars

**EquiPath:** What's your household income level? (LOW, MEDIUM, or HIGH)
> **You:** LOW

**EquiPath:** What's your current GPA on a 4.0 scale?
> **You:** 3.4

**EquiPath:** Great! Any specific preferences?
> **You:** I'd like to stay in California and prefer public schools

**EquiPath:** ✅ Profile complete! Let me find your matches...

### How It Works:

- **Natural language processing** - No need for exact formats
- **Progressive questions** - One question at a time
- **Smart parsing** - Understands variations ("yes", "I have kids", "I'm a parent")
- **Automatic profile creation** - Converts conversation to structured data

---

## 🤖 AI-Generated Summaries

### Overall Summary (Top of Results)

After finding matches, you'll see a personalized overview like:

```
🤖 Your Personalized College Guide

Based on your profile as a Hispanic first-generation student-parent
with a $18,000 budget and 3.4 GPA, I've identified colleges that
prioritize both affordability and support for students like you.

Your top recommendations focus heavily on affordability (55% weight)
and equity (25% weight) because of your financial situation and
student-parent status.

Here are your best matches:

1. California State University, Los Angeles
   - This is an excellent match because it's well within your budget
     at $6,200 net price, has strong outcomes for Hispanic students
     (62% graduation rate), and offers robust support services for
     student-parents. As a public in-state option, you'll benefit
     from lower costs while accessing quality education.

[... continues for top 3-5 colleges ...]

Next Steps:
- Research each college's specific support services for parents
- Check application deadlines
- Look into campus childcare facilities
```

### Individual College Summaries

Each college card shows:

```
💡 Why this college?

Cal State LA is a perfect fit because it combines exceptional
affordability ($6,200 net price) with strong equity outcomes
for Hispanic students. As a designated Hispanic-Serving Institution
with dedicated resources for student-parents, you'll find both
financial accessibility and comprehensive support systems to
help you succeed while balancing parenting responsibilities.
```

---

## 🎛️ Modes

### Chat Mode (Default)
- **Best for:** First-time users, students who prefer conversation
- **Features:**
  - Step-by-step questions
  - Natural language input
  - AI-powered profile creation
  - Personalized explanations

### Manual Form Mode
- **Best for:** Quick updates, users who know exactly what they want
- **Features:**
  - Traditional form inputs
  - Faster if you have all info ready
  - Still gets AI summaries

**Switch modes** using the radio button in the sidebar.

---

## 💰 Cost Considerations

### OpenAI API Usage

**Per User Session:**
- Profile parsing: ~$0.01
- Overall summary: ~$0.02-0.05
- Per-college summary (×10): ~$0.10-0.20
- **Total per session:** ~$0.13-0.26

**For 100 users:** ~$13-26
**For 1,000 users:** ~$130-260

### Free Alternative

Run without API key:
- Chat mode won't work
- But manual form still works
- No AI summaries
- Still get all matching logic and visualizations

---

## 🔒 Privacy & Security

### API Key Safety
- **Never commit API keys to git**
- Use environment variables in production
- Rotate keys regularly

### User Data
- Chat conversations are stored in session state only
- Not sent to any server except OpenAI for processing
- Cleared when browser tab closes

---

## 🛠️ Troubleshooting

### "OpenAI package not installed"
```bash
.conda/bin/pip install openai
```

### "No OpenAI API key"
- Set environment variable: `export OPENAI_API_KEY="sk-..."`
- Or enter in sidebar settings

### Chat not progressing
- Click "Reset / Start Over" in sidebar
- Refresh the page

### AI summaries not showing
- Check API key is valid
- Check you have API credits
- Try the manual form mode

---

## 📊 Comparison: Standard vs AI-Enhanced

| Feature | Standard App | AI-Enhanced App |
|---------|-------------|-----------------|
| **Profile Creation** | Manual form | Conversational chat |
| **Input Method** | Dropdowns, sliders | Natural language |
| **Results Summary** | None | AI-generated overview |
| **College Explanations** | Raw metrics | Personalized insights |
| **Setup** | No API key needed | Requires OpenAI key |
| **Cost** | Free | ~$0.13-0.26/session |
| **Speed** | Instant | 10-30 seconds for AI |

---

## 🎓 Best Practices

### For Students

1. **Be honest in chat** - The AI can't help if info is inaccurate
2. **Read the summaries** - AI highlights what's important for YOU
3. **Use as a starting point** - Visit colleges, do more research
4. **Compare recommendations** - Look at multiple matches

### For Counselors

1. **Pre-load API key** - Set as environment variable
2. **Guide students through chat** - Help interpret questions
3. **Review AI summaries together** - Discuss recommendations
4. **Use manual mode for speed** - If you're entering data for them

### For Developers

1. **Monitor API costs** - Set up usage alerts in OpenAI dashboard
2. **Cache where possible** - Store common responses
3. **Implement rate limiting** - Prevent abuse
4. **Add error handling** - Graceful degradation if API fails

---

## 🔮 Future Enhancements

Potential additions:
- **Voice input** - Speak instead of type
- **Multi-language support** - Spanish, Mandarin, etc.
- **Follow-up questions** - AI asks clarifying questions
- **Application help** - AI assists with essays, applications
- **Financial aid estimator** - Personalized aid predictions
- **College comparison mode** - "Compare college A vs B for my profile"

---

## 📞 Support

### Common Questions

**Q: Can I switch from chat to form mid-way?**
A: Yes! Click "Manual Form" in sidebar, your data is preserved.

**Q: Is my conversation private?**
A: Yes, it's only stored in your browser session and sent to OpenAI for processing.

**Q: Can I save my profile?**
A: Currently no, but you can screenshot your matches or copy the text.

**Q: What if I make a mistake in chat?**
A: Click "Reset / Start Over" to start fresh.

---

## 🎉 Try It Out!

1. Get an OpenAI API key: https://platform.openai.com/api-keys
2. Set your key: `export OPENAI_API_KEY="sk-..."`
3. Run: `.conda/bin/streamlit run src/app_streamlit_chat.py`
4. Chat and discover your perfect colleges!

---

**Built with ❤️ for educational equity, powered by AI**
