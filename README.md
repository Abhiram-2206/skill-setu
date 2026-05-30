# Skill Setu 🎯

**AI-powered career intelligence platform** that maps your skill gaps, builds a personalised learning roadmap, and analyses your resume for ATS compatibility.

---

## Features

- **Skill Gap Analyser** — Enter your current skills and a target role; the AI maps what you're missing and generates a prioritised learning path with recommended courses and a realistic timeline.
- **AI Resume Analyser** — Upload a PDF or paste your resume to get an ATS score (0–100), keyword gap analysis, section-by-section breakdown, strengths, and actionable improvement suggestions — powered by Groq (LLaMA 3.3 70B).
- **User Authentication** — Register and log in with email/password or via Google, LinkedIn, Facebook, and Yahoo OAuth.
- **Dark / Light Mode** — Toggle between themes; preference is saved in the browser.

---

## Project Structure

```
skill-setu/
├── app.py                  # Main Flask application & routes
├── auth.py                 # Authentication blueprint (manual + OAuth)
├── database.py             # SQLite setup (accounts, users, results tables)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
│
├── data/
│   ├── skills.json         # Role → required skills mapping
│   └── courses.json        # Skill → recommended courses mapping
│
├── utils/
│   ├── logic.py            # Skill gap & learning path logic
│   └── ml_model.py         # TF-IDF skill matching model
│
├── static/
│   ├── style.css           # All styles (light + dark mode)
│   ├── script.js           # Dark mode toggle, user dropdown
│   ├── resume.js           # Resume analyser UI logic
│   └── logo.jpeg           # Brand logo
│
└── templates/
    ├── index.html          # Landing page
    ├── about.html          # About page
    ├── dashboard.html      # Skill gap analyser
    ├── resume.html         # Resume analyser
    ├── login.html          # Login page
    └── register.html       # Registration page
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/skill-setu.git
cd skill-setu
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate on Mac/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# Required
SECRET_KEY=your-random-secret-key-here
GROQ_API_KEY=gsk_your-groq-key-here

# OAuth providers (optional — only add the ones you want to use)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

YAHOO_CLIENT_ID=your-yahoo-client-id
YAHOO_CLIENT_SECRET=your-yahoo-client-secret
```

Generate a secure `SECRET_KEY` with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run the application

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## Getting API Keys

### Groq (required for Resume Analyser)
1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys → Create API Key**
3. Free tier gives 14,400 requests/day — no credit card needed

### Google OAuth (optional)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Authorised redirect URI: `http://localhost:5000/auth/google/callback`
5. Copy Client ID and Secret to `.env`

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Flask session encryption key |
| `GROQ_API_KEY` | ✅ Yes | Groq API key for resume analysis |
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Optional | Google OAuth client secret |
| `LINKEDIN_CLIENT_ID` | Optional | LinkedIn OAuth client ID |
| `LINKEDIN_CLIENT_SECRET` | Optional | LinkedIn OAuth client secret |
| `FACEBOOK_CLIENT_ID` | Optional | Facebook app ID |
| `FACEBOOK_CLIENT_SECRET` | Optional | Facebook app secret |
| `YAHOO_CLIENT_ID` | Optional | Yahoo OAuth client ID |
| `YAHOO_CLIENT_SECRET` | Optional | Yahoo OAuth client secret |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| Authentication | Flask-Login, Authlib |
| AI Provider | Groq (LLaMA 3.3 70B) |
| PDF Parsing | pdfplumber |
| Skill Matching | scikit-learn (TF-IDF) |
| Frontend | HTML, CSS, Vanilla JS, Chart.js |

---

## .gitignore Recommendations

Make sure these are in your `.gitignore` before pushing to GitHub:

```
.env
*.db
__pycache__/
*.pyc
venv/
.DS_Store
```

---

## License

MIT License — free to use and modify.
