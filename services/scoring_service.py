import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

FILLER_WORDS = ["um", "uh", "like", "actually", "basically", "you know", "sort of", "kind of"]


def _clean(text):
    return re.sub(r"[^a-z0-9\s]", "", text.lower())


def count_filler_words(transcript):
    cleaned = _clean(transcript)
    count = 0
    for filler in FILLER_WORDS:
        count += len(re.findall(rf"\b{re.escape(filler)}\b", cleaned))
    return count


def keyword_coverage(transcript, ideal_keywords):
    cleaned = _clean(transcript)
    words_present = sum(1 for kw in ideal_keywords if kw.lower() in cleaned)
    if not ideal_keywords:
        return 0.0
    return round((words_present / len(ideal_keywords)) * 100, 1)


def content_similarity_score(transcript, ideal_keywords):
    """
    Builds a synthetic 'ideal answer' from the keyword list and measures
    TF-IDF cosine similarity against the transcript. This is a lightweight
    stand-in for a full semantic model — good enough to reward answers that
    actually touch on the right concepts, without needing a large model.
    """
    ideal_answer = " ".join(ideal_keywords)
    if not transcript.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([transcript, ideal_answer])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(similarity * 100, 1)
    except ValueError:
        # Happens if transcript has no meaningful tokens (e.g. all filler)
        return 0.0


def word_count(transcript):
    return len(_clean(transcript).split())


def score_answer(transcript, ideal_keywords, engagement_score=None, smile_score=None):
    """
    Combines content relevance, keyword coverage, answer length, and filler
    word usage into an overall score out of 100. Webcam-derived engagement
    and smile scores (0-100) are folded in if available, otherwise the
    score is computed from speech/content alone.
    """
    content_score = content_similarity_score(transcript, ideal_keywords)
    coverage = keyword_coverage(transcript, ideal_keywords)
    fillers = count_filler_words(transcript)
    words = word_count(transcript)

    # Length score: reward substantive answers (30-200 words is a healthy range)
    if words < 10:
        length_score = 20
    elif words > 200:
        length_score = 80
    else:
        length_score = min(100, 40 + words * 0.8)

    # Filler penalty: each filler word above 2 costs a few points, capped
    filler_penalty = min(30, max(0, (fillers - 2) * 5))

    base_components = [content_score, coverage, length_score]
    weights = [0.45, 0.35, 0.20]

    if engagement_score is not None and smile_score is not None:
        base_components += [engagement_score, smile_score]
        weights = [0.35, 0.25, 0.15, 0.15, 0.10]

    weighted = sum(c * w for c, w in zip(base_components, weights))
    overall = max(0, round(weighted - filler_penalty, 1))

    return {
        "content_score": content_score,
        "keyword_coverage": coverage,
        "filler_count": fillers,
        "engagement_score": engagement_score if engagement_score is not None else 0,
        "smile_score": smile_score if smile_score is not None else 0,
        "overall_score": min(100, overall),
    }
