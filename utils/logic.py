
# Maps user-typed skill variants → list of canonical keys they satisfy in skills.json
SKILL_ALIASES = {
    "mysql":      ["sql", "sql/nosql"],
    "postgresql": ["sql", "sql/nosql"],
    "postgres":   ["sql", "sql/nosql"],
    "mongodb":    ["sql/nosql"],
    "nosql":      ["sql/nosql"],
    "none":       [],   # absolute beginner — credits nothing
}


def generate_learning_path(user_skills, target_role, skill_data):
    # Filter out 'None' — it carries no actual skill credit
    user_skills_raw = [s.strip().lower() for s in user_skills if s.strip().lower() != "none"]

    # Expand aliases: each alias maps to a list of canonical keys it satisfies
    user_skills_expanded = set(user_skills_raw)
    for s in user_skills_raw:
        if s in SKILL_ALIASES:
            for canonical in SKILL_ALIASES[s]:
                user_skills_expanded.add(canonical)

    required_skills = skill_data[target_role]

    total_weight = sum(required_skills.values())
    user_score = 0

    missing_skills = []

    for skill, weight in required_skills.items():
        if skill.lower() in user_skills_expanded:
            user_score += weight
        else:
            missing_skills.append((skill, weight))

    score = int((user_score / total_weight) * 100)

    missing_skills.sort(key=lambda x: x[1], reverse=True)

    learning_path = []
    for i, (skill, weight) in enumerate(missing_skills):
        learning_path.append({
            "step": i + 1,
            "skill": skill,
            "priority": "High" if weight >= 3 else "Medium"
        })

    missing_skill_names = [s[0] for s in missing_skills]

    return learning_path, missing_skill_names, score


# FIXED TIMELINE (ORDER + REALISTIC)
def generate_timeline(missing_skills):

    ideal_order = [
        "python",
        "sql",
        "statistics",
        "machine learning",
        "deep learning"
    ]

    skill_duration = {
        "python": 1,
        "sql": 1,
        "statistics": 1,
        "machine learning": 2,
        "deep learning": 2
    }

    sorted_skills = sorted(
        missing_skills,
        key=lambda x: ideal_order.index(x.lower()) if x.lower() in ideal_order else 999
    )

    timeline = []
    current_month = 1

    for skill in sorted_skills:
        duration = skill_duration.get(skill.lower(), 1)

        if duration == 1:
            timeline.append({
                "month": f"Month {current_month}",
                "skills": [skill]
            })
            current_month += 1
        else:
            timeline.append({
                "month": f"Month {current_month}\u2013{current_month + duration - 1}",
                "skills": [skill]
            })
            current_month += duration

    return timeline
