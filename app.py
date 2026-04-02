from flask import Flask, render_template, request, jsonify
import json

from utils.logic import generate_learning_path, generate_timeline, SKILL_ALIASES
from utils.ml_model import match_skills
from database import init_db, get_connection

app = Flask(__name__)

# Initialize DB
init_db()

with open('data/skills.json') as f:
    skill_data = json.load(f)

with open('data/courses.json') as f:
    course_data = json.load(f)


def generate_resume_feedback(user_skills, target_role, skill_data):
    # Filter out None — absolute beginner marker carries no skill credit
    user_skills_lower = [s.lower() for s in user_skills if s.strip().lower() != "none"]

    # Expand aliases (list-based): mysql/postgresql -> sql + sql/nosql, etc.
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


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    roles = list(skill_data.keys())
    return render_template('dashboard.html', roles=roles)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    raw_skills = data['skills']
    target_role = data['role']

    # 🔥 AI Skill Extraction
    user_text = " ".join(raw_skills)
    ai_skills = match_skills(user_text)

    # Merge user + AI skills
    user_skills = list(set(raw_skills + ai_skills))

    # 🔹 Core Logic
    path, missing_skills, score = generate_learning_path(
        user_skills, target_role, skill_data
    )

    timeline = generate_timeline(missing_skills)

    # 🔥 FIXED COURSE MATCHING
    skill_map = {k.strip().lower(): k for k in course_data}
    recommendations = {}

    for skill in missing_skills:
        skill_clean = skill.strip().lower()

        if skill_clean in skill_map:
            original_key = skill_map[skill_clean]
            recommendations[original_key] = course_data[original_key]

    feedback = generate_resume_feedback(user_skills, target_role, skill_data)

    # Confidence = how certain the AI is about its assessment.
    # Driven by 3 independent signals — not derived from score:
    #   1. Input richness: more skills provided = more data to reason from
    #   2. Skill relevance: how many user skills directly match role requirements
    #   3. Specificity: ratio of role-relevant skills vs total skills given
    required_skills = skill_data[target_role]
    required_lower = {s.lower() for s in required_skills}

    from utils.logic import SKILL_ALIASES
    user_skills_lower = [s.strip().lower() for s in user_skills if s.strip().lower() != "none"]
    user_skills_expanded = set(user_skills_lower)
    for s in user_skills_lower:
        if s in SKILL_ALIASES:
            for canonical in SKILL_ALIASES[s]:
                user_skills_expanded.add(canonical)

    # Signal 1: input richness — more skills typed = AI has more to work with (caps at 40pts)
    raw_skill_count = len([s for s in raw_skills if s.strip().lower() != "none"])
    richness = min(raw_skill_count / max(len(required_skills), 1), 1.0) * 40

    # Signal 2: direct role relevance — matched skills / total required (caps at 45pts)
    matched_count = sum(1 for r in required_lower if r in user_skills_expanded)
    relevance = (matched_count / len(required_skills)) * 45

    # Signal 3: specificity — what fraction of user skills are role-relevant (caps at 15pts)
    if user_skills_expanded:
        specificity = (matched_count / len(user_skills_expanded)) * 15
    else:
        specificity = 0

    confidence = min(int(richness + relevance + specificity), 99)

    # 🔥 DATABASE SAVE
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (skills, role) VALUES (?, ?)",
        (json.dumps(user_skills), target_role)
    )
    user_id = cursor.lastrowid

    cursor.execute(
        """INSERT INTO results 
        (user_id, score, learning_path, timeline, courses)
        VALUES (?, ?, ?, ?, ?)""",
        (
            user_id,
            score,
            json.dumps(path),
            json.dumps(timeline),
            json.dumps(recommendations)
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "learning_path": path,
        "score": score,
        "confidence": confidence,
        "courses": recommendations,
        "feedback": feedback,
        "timeline": timeline,
        "detected_skills": ai_skills
    })


@app.route('/history')
def history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT users.role, users.skills, results.score
    FROM users
    JOIN results ON users.id = results.user_id
    ORDER BY users.id DESC
    LIMIT 10
    """)

    data = cursor.fetchall()
    conn.close()

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)