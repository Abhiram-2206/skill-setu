from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Skill corpus (expandable)
skill_corpus = [
    "python pandas numpy data analysis scripting",
    "sql database queries relational database mysql",
    "machine learning deep learning ai neural networks",
    "statistics probability data analysis hypothesis testing",
    "html css javascript web development frontend",
]

skill_labels = [
    "Python",
    "SQL",
    "Machine Learning",
    "Statistics",
    "Web Development"
]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(skill_corpus)


def match_skills(user_text):
    user_vec = vectorizer.transform([user_text])
    similarity = cosine_similarity(user_vec, vectors)[0]

    matched = []

    for i, score in enumerate(similarity):
        if score > 0.2:   # threshold
            matched.append(skill_labels[i])

    return matched