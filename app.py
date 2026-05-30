from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, UserMixin, current_user, login_required
from dotenv import load_dotenv
import json
import os
import re

load_dotenv()

import unicodedata

def clean_resume_text(text):
    """Remove zero-width spaces, control chars, and normalize unicode before sending to AI."""
    # Remove common invisible/problematic unicode characters
    for ch in ['\u200b', '\u200c', '\u200d', '\u200e', '\u200f', '\ufeff', '\u00ad']:
        text = text.replace(ch, '')
    # Normalize unicode (handles ligatures, accented chars, etc.)
    text = unicodedata.normalize('NFKC', text)
    # Remove control characters except newline and tab
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C' or c in '\n\t')
    # Collapse excessive whitespace
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

from utils.logic import generate_learning_path, generate_timeline, SKILL_ALIASES
from utils.ml_model import match_skills
from database import init_db, get_connection

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'skill-setu-dev-secret-2024')

# ── Flask-Login setup ──────────────────────────────────────────────────────────

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access that page.'


class AccountUser(UserMixin):
    def __init__(self, id, name, email, avatar_url=None):
        self.id         = id
        self.name       = name
        self.email      = email
        self.avatar_url = avatar_url
    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    from auth import get_account_by_id
    account = get_account_by_id(int(user_id))
    if not account:
        return None
    return AccountUser(
        id=account['id'],
        name=account['name'],
        email=account['email'],
        avatar_url=account.get('avatar_url')
    )


# ── Auth blueprint ─────────────────────────────────────────────────────────────
from auth import auth_bp, init_oauth
app.register_blueprint(auth_bp)
init_oauth(app)

# ── Initialize DB & data ───────────────────────────────────────────────────────
init_db()

with open('data/skills.json') as f:
    skill_data = json.load(f)

with open('data/courses.json') as f:
    course_data = json.load(f)


# ── Skill analysis helpers ─────────────────────────────────────────────────────

def generate_resume_feedback(user_skills, target_role, skill_data):
    user_skills_lower = [s.lower() for s in user_skills if s.strip().lower() != "none"]
    user_skills_expanded = set(user_skills_lower)
    for s in user_skills_lower:
        if s in SKILL_ALIASES:
            for canonical in SKILL_ALIASES[s]:
                user_skills_expanded.add(canonical)

    required_skills = skill_data[target_role]
    feedback = []
    for skill in required_skills:
        if skill.lower() not in user_skills_expanded:
            feedback.append(f"You should learn {skill} to improve your profile.")

    if not feedback:
        feedback.append("Your profile is well aligned with the selected role.")
    return feedback


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    roles = list(skill_data.keys())
    return render_template('dashboard.html', roles=roles)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    raw_skills  = data['skills']
    target_role = data['role']

    user_text = " ".join(raw_skills)
    ai_skills = match_skills(user_text)
    user_skills = list(set(raw_skills + ai_skills))

    path, missing_skills, score = generate_learning_path(user_skills, target_role, skill_data)
    timeline = generate_timeline(missing_skills)

    skill_map = {k.strip().lower(): k for k in course_data}
    recommendations = {}
    for skill in missing_skills:
        skill_clean = skill.strip().lower()
        if skill_clean in skill_map:
            original_key = skill_map[skill_clean]
            recommendations[original_key] = course_data[original_key]

    feedback = generate_resume_feedback(user_skills, target_role, skill_data)

    required_skills = skill_data[target_role]
    required_lower  = {s.lower() for s in required_skills}

    from utils.logic import SKILL_ALIASES
    user_skills_lower = [s.strip().lower() for s in user_skills if s.strip().lower() != "none"]
    user_skills_expanded = set(user_skills_lower)
    for s in user_skills_lower:
        if s in SKILL_ALIASES:
            for canonical in SKILL_ALIASES[s]:
                user_skills_expanded.add(canonical)

    raw_skill_count = len([s for s in raw_skills if s.strip().lower() != "none"])
    richness    = min(raw_skill_count / max(len(required_skills), 1), 1.0) * 40
    matched_count = sum(1 for r in required_lower if r in user_skills_expanded)
    relevance   = (matched_count / len(required_skills)) * 45
    specificity = (matched_count / len(user_skills_expanded)) * 15 if user_skills_expanded else 0
    confidence  = min(int(richness + relevance + specificity), 99)

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (skills, role) VALUES (?, ?)",
                   (json.dumps(user_skills), target_role))
    user_id = cursor.lastrowid
    cursor.execute("""INSERT INTO results (user_id, score, learning_path, timeline, courses)
                      VALUES (?, ?, ?, ?, ?)""",
                   (user_id, score, json.dumps(path), json.dumps(timeline),
                    json.dumps(recommendations)))
    conn.commit()
    conn.close()

    return jsonify({
        "learning_path":   path,
        "score":           score,
        "confidence":      confidence,
        "courses":         recommendations,
        "feedback":        feedback,
        "timeline":        timeline,
        "detected_skills": ai_skills
    })


@app.route('/history')
def history():
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.role, users.skills, results.score
        FROM users
        JOIN results ON users.id = results.user_id
        ORDER BY users.id DESC LIMIT 10
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


# ── Resume Analyser ────────────────────────────────────────────────────────────

@app.route('/resume')
@login_required
def resume():
    roles = list(skill_data.keys())
    return render_template('resume.html', roles=roles)


@app.route('/analyse-resume', methods=['POST'])
def analyse_resume():
    """Accepts either JSON (pasted text) or multipart form (PDF upload)."""
    try:
        from groq import Groq
    except ImportError:
        return jsonify({"error": "groq package not installed. Run: pip install groq"}), 500

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "GROQ_API_KEY environment variable is not set."}), 500

    resume_text = ''
    target_role = ''
    job_desc    = ''

    # ── PDF upload mode ──
    if request.files.get('resume_pdf'):
        try:
            import pdfplumber
        except ImportError:
            return jsonify({"error": "pdfplumber not installed. Run: pip install pdfplumber"}), 500

        pdf_file = request.files['resume_pdf']
        try:
            with pdfplumber.open(pdf_file) as pdf:
                resume_text = '\n'.join(
                    page.extract_text() or '' for page in pdf.pages
                )
            resume_text = clean_resume_text(resume_text)
        except Exception as e:
            return jsonify({"error": f"Could not read PDF: {e}"}), 400

        target_role = request.form.get('target_role', '').strip()
        job_desc    = request.form.get('job_description', '').strip()

    # ── JSON / paste mode ──
    else:
        data        = request.json or {}
        resume_text = clean_resume_text(data.get("resume_text") or "")
        target_role = (data.get("target_role") or "").strip()
        job_desc    = (data.get("job_description") or "").strip()

    if not resume_text or len(resume_text) < 50:
        return jsonify({"error": "Resume text is too short or could not be extracted."}), 400

    # ── Build prompt ──
    role_line    = f"Target role: {target_role}" if target_role else "No specific role provided — give a general analysis."
    jd_block     = f"\n\nJOB DESCRIPTION PROVIDED:\n{job_desc[:3000]}" if job_desc else "\n\nNo job description was provided."
    role_keywords = skill_data.get(target_role, [])
    role_kw_hint  = f"\n\nKnown required skills for '{target_role}': {', '.join(role_keywords)}" if role_keywords else ""
    kw_note       = ' (prioritise keywords from the job description and role requirements)' if job_desc or role_keywords else ''

    prompt = f"""You are an expert ATS (Applicant Tracking System) resume analyst and career coach.

Analyse the following resume and return ONLY a valid JSON object — no markdown, no commentary outside the JSON.

{role_line}{jd_block}{role_kw_hint}

RESUME:
{resume_text[:6000]}

Return this exact JSON structure:
{{
  "ats_score": <integer 0-100>,
  "target_role": "<role targeted, or 'General'>",
  "section_scores": {{
    "Contact & Summary": <0-100>,
    "Work Experience": <0-100>,
    "Skills": <0-100>,
    "Education": <0-100>,
    "Formatting": <0-100>
  }},
  "strengths":    ["<up to 5 specific strengths>"],
  "improvements": ["<up to 6 specific areas to improve>"],
  "keywords": {{
    "present": ["<keywords found>"],
    "missing": ["<important keywords absent{kw_note}>"]
  }},
  "suggestions": ["<5-8 concrete, actionable suggestions>"]
}}

Rules:
- ats_score must reflect real ATS likelihood.
- strengths and improvements must be specific to this resume.
- Return ONLY the JSON. No preamble. No trailing text."""

    # ── Call Groq ──
    try:
        client  = Groq(api_key=api_key)
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "You are a resume analyst. Respond with valid JSON only. No markdown, no extra text."},
                {"role": "user", "content": prompt}
            ]
        )
        raw = message.choices[0].message.content.strip()

        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'^```\s*',     '', raw)
        raw = re.sub(r'\s*```$',     '', raw)
        raw = raw.strip()

        if not raw.startswith('{'):
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                return jsonify({"error": "AI did not return valid JSON. Please try again."}), 500
            raw = m.group(0).strip()

        result = json.loads(raw)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI returned malformed JSON: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
