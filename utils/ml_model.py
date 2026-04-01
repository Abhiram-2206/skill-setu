from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

skill_corpus = [
    "python pandas numpy data analysis scripting",
    "sql database mysql queries",
    "machine learning ai ml neural networks deep learning",
    "statistics probability data analysis",
    "html css javascript frontend web development",
    "react frontend framework",
    "docker containers devops",
    "ci cd pipelines devops",
    "cloud aws azure gcp",
    "linux operating system",
    "cybersecurity networking ethical hacking",
    "data visualization charts graphs tableau",
    "excel spreadsheets analysis",
    "figma ui ux design prototyping"
]

skill_labels = [
    "Python",
    "SQL",
    "Machine Learning",
    "Statistics",
    "HTML",
    "React",
    "Docker",
    "CI/CD",
    "Cloud Computing",
    "Linux",
    "Cyber Security Fundamentals",
    "Data Visualization",
    "Excel",
    "Figma"
]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(skill_corpus)


def match_skills(user_text):
    user_vec = vectorizer.transform([user_text])
    similarity = cosine_similarity(user_vec, vectors)[0]

    matched = []

    for i, score in enumerate(similarity):
        if score > 0.2:
            matched.append(skill_labels[i])

    return matched