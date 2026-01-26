import re
import json
import requests
from django.conf import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL_PRIMARY = "llama-3.3-70b-versatile"
GROQ_MODEL_FALLBACK = "llama-3.1-8b-instant"


def clean_text(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def build_prompt(text: str, mode: str, movie_title: str = "", movie_overview: str = "") -> str:
    movie_title = (movie_title or "").strip()
    movie_overview = (movie_overview or "").strip()

    context = ""
    if movie_title:
        context += f"Movie title: {movie_title}\n"
    if movie_overview:
        context += f"Movie overview: {movie_overview}\n"

    base = (
        f"{context}\n"
        f"User review:\n{text}\n\n"
    )

    if mode == "rewrite":
        return base + "Rewrite this review in clean, polished English. Keep the meaning."

    if mode == "shorten":
        return base + "Shorten this review under 180 characters. Keep it sharp."

    if mode == "funny":
        return base + f"Write a funny review about {movie_title or 'this movie'} based on the user review."

    if mode == "roast":
        return base + f"Roast {movie_title or 'this movie'} in a humorous way. Not abusive. No slurs."

    if mode == "professional":
        return base + "Rewrite this review in a professional and formal tone."

    if mode == "hype":
        return base + f"Rewrite this as an excited, hyped review for {movie_title or 'this movie'}."

    if mode == "savage_1star":
        return base + f"Rewrite as a savage brutal 1-star review for {movie_title or 'this movie'}. No hate speech."

    return base + "Rewrite this review."


def groq_chat(messages: list) -> str:
    api_key = getattr(settings, "GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY missing")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    def call_model(model_name: str) -> str:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 350,
        }

        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

        if res.status_code != 200:
            raise RuntimeError(f"Groq error {res.status_code}: {res.text[:500]}")

        data = res.json()
        return data["choices"][0]["message"]["content"].strip()

    try:
        return call_model(GROQ_MODEL_PRIMARY)
    except Exception:
        return call_model(GROQ_MODEL_FALLBACK)


def ai_rewrite_review(text: str, mode: str = "rewrite", movie_title: str = "", movie_overview: str = "") -> str:
    text = clean_text(text)

    if not text:
        if not movie_title:
            raise ValueError("Movie title missing")

        prompt = (
            f"Movie title: {movie_title}\n"
            f"Movie overview: {movie_overview}\n\n"
            "Write a fresh movie review.\n"
            "Keep it realistic, human-like, not robotic.\n"
            "Length: 5-8 lines.\n"
        )

        messages = [
            {"role": "system", "content": "You write movie reviews. Output only the final review text."},
            {"role": "user", "content": prompt},
        ]

        return groq_chat(messages)

    prompt = build_prompt(text, mode, movie_title=movie_title, movie_overview=movie_overview)

    messages = [
        {"role": "system", "content": "You write movie reviews. Output only the final rewritten review text."},
        {"role": "user", "content": prompt},
    ]

    return groq_chat(messages)



def ai_extract_pros_cons(text: str) -> dict:
    text = clean_text(text)
    if not text:
        raise ValueError("Empty text")

    prompt = (
        f"User review:\n{text}\n\n"
        "Extract Pros and Cons from this review.\n"
        "Return JSON only in this format:\n"
        '{"pros":["..."],"cons":["..."]}\n'
        "No extra text."
    )

    messages = [
        {"role": "system", "content": "Extract pros and cons from reviews. Return JSON only."},
        {"role": "user", "content": prompt},
    ]

    raw = groq_chat(messages)

    try:
        data = json.loads(raw)
        pros = data.get("pros", [])
        cons = data.get("cons", [])
        return {
            "pros": pros[:6] if isinstance(pros, list) else [],
            "cons": cons[:6] if isinstance(cons, list) else [],
        }
    except Exception:
        return {"pros": [], "cons": []}
