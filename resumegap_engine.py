"""
resumegap_engine.py
====================
LOCKED — Day 199 finalized core engine for ResumeGapAI (deployed at
resumegapai.streamlit.app). This is the Day 204 Raw Data layer. Do NOT modify
during Day 204 practice tasks — today's work happens only in resumegap_mcp_server.py.

Functions:
    clean_text(text)                    -> str
    tfidf_similarity_naive(resume, jd)  -> float (0-100)
    tfidf_similarity_fixed(resume, jd)  -> float (0-100)
    gap_words(resume, jd, top_n=8)      -> list[str]
    match_band(score)                   -> str
    analyze_resume_gap(resume, jd, top_n=8) -> dict
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

BACKGROUND_CORPUS = [
    "experienced professional seeking growth opportunities in a fast paced environment",
    "responsible for managing projects and delivering results on time and within budget",
    "strong communication and collaboration skills working with cross functional teams",
    "proficient in Microsoft Office including Excel Word and PowerPoint for reporting",
    "bachelor degree in relevant field with several years of professional experience",
    "seeking a motivated candidate with strong analytical and problem solving skills",
    "must have excellent written and verbal communication skills and attention to detail",
    "experience working in an agile environment with sprint planning and stand ups",
    "candidate should have strong leadership skills and experience managing a team",
    "looking for someone who can work independently and also collaborate with stakeholders",
]


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # space, not '' -- Day198 bugfix
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tfidf_similarity_naive(resume: str, jd: str) -> float:
    docs = [clean_text(resume), clean_text(jd)]
    vec = TfidfVectorizer(stop_words=list(ENGLISH_STOP_WORDS))
    matrix = vec.fit_transform(docs)
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return round(sim * 100, 2)


def tfidf_similarity_fixed(resume: str, jd: str) -> float:
    docs = BACKGROUND_CORPUS + [clean_text(resume), clean_text(jd)]
    vec = TfidfVectorizer(stop_words=list(ENGLISH_STOP_WORDS))
    matrix = vec.fit_transform(docs)
    resume_vec = matrix[-2:-1]
    jd_vec = matrix[-1:]
    sim = cosine_similarity(resume_vec, jd_vec)[0][0]
    return round(sim * 100, 2)


def gap_words(resume: str, jd: str, top_n: int = 8) -> list:
    resume_clean = clean_text(resume)
    jd_clean = clean_text(jd)
    docs = BACKGROUND_CORPUS + [resume_clean, jd_clean]
    vec = TfidfVectorizer(stop_words=list(ENGLISH_STOP_WORDS))
    matrix = vec.fit_transform(docs)
    feature_names = vec.get_feature_names_out()

    jd_vector = matrix[-1].toarray()[0]
    resume_words = set(resume_clean.split())

    scored = [
        (feature_names[i], jd_vector[i])
        for i in range(len(feature_names))
        if jd_vector[i] > 0 and feature_names[i] not in resume_words
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [word for word, _score in scored[:top_n]]


def match_band(score: float) -> str:
    if score >= 70:
        return "Strong Match"
    elif score >= 45:
        return "Moderate Match"
    else:
        return "Weak Match"


def analyze_resume_gap(resume: str, jd: str, top_n: int = 8) -> dict:
    score = tfidf_similarity_fixed(resume, jd)
    band = match_band(score)
    gaps = gap_words(resume, jd, top_n)
    return {"similarity_score": score, "match_band": band, "gap_words": gaps}
