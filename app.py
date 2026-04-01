from flask import Flask, render_template, request, jsonify
import json

from utils.logic import generate_learning_path, generate_timeline
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
    user_skills = [s.lower() for s in user_skills]
    required_skills = skill_data[target_role]

    feedback = []

    for skill in required_skills:
        if skill.lower() not in user_skills:
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

    confidence = score - 5 if score > 50 else score + 5

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