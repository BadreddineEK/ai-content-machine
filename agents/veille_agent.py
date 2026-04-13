"""veille_agent.py - Node 1: Trending topics via Perplexity Sonar API."""
import os
import requests
from datetime import date
from typing import List, Dict

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def fetch_trending_topics(config: dict) -> List[Dict]:
    """Fetch trending topics using Perplexity Sonar. Returns list of 5 topics."""
    api_key = os.environ.get("PERPLEXITY_API_KEY", "")
    query = f"{config['recherche_query']} - {date.today().isoformat()}"
    langue = config.get("langue", "fr")
    niche = config.get("niche", "")
    system_prompt = (
        f"Tu es un expert en veille de contenu pour la niche '{niche}'. "
        f"Reponds en {langue}. Retourne EXACTEMENT un JSON avec cle 'topics': "
        "liste de 5 objets {titre, description, score (1-10)}. Pas de texte autour."
    )
    user_prompt = f"5 sujets tendance pour: {query}. JSON uniquement."
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        r = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return _parse_topics(content)
    except Exception:
        return _fallback_topics(niche)


def _parse_topics(content: str) -> List[Dict]:
    """Parse JSON topics from Perplexity response."""
    import json, re
    content = re.sub(r"```[a-z]*", "", content).strip()
    try:
        data = json.loads(content)
        topics = data.get("topics", [])
        return [
            {
                "titre": t.get("titre", t.get("title", "Sujet")),
                "description": t.get("description", ""),
                "score": int(t.get("score", 5)),
            }
            for t in topics
        ][:5]
    except (json.JSONDecodeError, KeyError):
        return _fallback_topics("general")


def _fallback_topics(niche: str) -> List[Dict]:
    """Fallback topics when API is unavailable."""
    return [
        {"titre": f"Les secrets de {niche} que personne ne te dit", "description": "Tendance virale.", "score": 8},
        {"titre": f"Comment {niche} change ta vie en 30 jours", "description": "Transformation.", "score": 7},
        {"titre": f"Top 5 erreurs en {niche}", "description": "Eviter les pieges.", "score": 6},
        {"titre": f"L erreur numero 1 en {niche}", "description": "Conseil pratique.", "score": 8},
        {"titre": f"{niche.capitalize()} et performance mentale", "description": "Mindset.", "score": 6},
    ]
