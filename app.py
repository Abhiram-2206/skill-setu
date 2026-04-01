from flask import Flask, render_template, request, jsonify
import json

from utils.logic import generate_learning_path, generate_timeline
from utils.ml_model import match_skills

app = Flask(__name__)

with open('data/skills.json') as f:
    skill_data = json.load(f)

with open('data/courses.json') as f:
    course_data = json.load(f)


# 🔹 SIMPLE FEEDBACK FUNCTION (REPLACES resume_parser)
def generate_resume_feedback(user_skills, target_role, skill_data):
    user_skills = [s.lower() for s in user_skills]
    required_skills = skill_data[target_role]

    explanations = {
        "python": "important for programming and automation",
        "sql": "used for handling databases and data queries",
        "statistics": "needed for data analysis and understanding patterns",
        "machine learning": "used for building predictive models"
    }

    feedback = []

    for skill in required_skills:
        if skill.lower() not in user_skills:
            reason = explanations.get(skill.lower(), "important for this role")
            feedback.append(f"You should learn {skill} as it is {reason}.")

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

    # Convert list → text for NLP
    user_text = " ".join(raw_skills)

    # 🔥 ML-based extraction
    ml_skills = match_skills(user_text)

    # Combine ML + user input (fallback safety)
    user_skills = list(set(raw_skills + ml_skills))

    target_role = data['role']

    # Core logic
    path, missing_skills, score = generate_learning_path(
        user_skills, target_role, skill_data
    )

    # Timeline
    timeline = generate_timeline(missing_skills)

    # Courses
    recommendations = {}
    for skill in missing_skills:
        for key in course_data:
            if skill.lower() == key.lower():
                recommendations[key] = course_data[key]

    # Feedback (now internal)
    feedback = generate_resume_feedback(user_skills, target_role, skill_data)

    confidence = score - 5 if score > 50 else score + 5

    return jsonify({
        "learning_path": path,
        "score": score,
        "confidence": confidence,
        "courses": recommendations,
        "feedback": feedback,
        "timeline": timeline
    })


if __name__ == '__main__':
    app.run(debug=True)