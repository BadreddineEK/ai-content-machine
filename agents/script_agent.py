"""script_agent.py - Node 2: Script generation via OpenRouter Llama 4."""
import os
import json
import re
import requests
from typing import Dict
from utils.prompt_builder import build_script_prompt

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-4-scout:free"


def generate_script(topic: Dict, config: dict) -> Dict:
    """Generate a structured video script from a topic using OpenRouter Llama 4.

    Returns dict with keys: hook, corps, cta, mots_cles_visuels.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    duree = config.get("duree_cible", 60)
    mots_par_minute = config.get("mots_par_minute", 150)
    word_count = int(duree * mots_par_minute / 60)

    prompt = build_script_prompt(topic, config, word_count)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/BadreddineEK/ai-content-machine",
        "X-Title": "AI Content Machine",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": config.get("style_script", "")},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
    }

    try:
        r = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return _parse_script(content, topic)
    except Exception as e:
        return _fallback_script(topic, config)


def _parse_script(content: str, topic: Dict) -> Dict:
    """Parse JSON script from LLM response."""
    content = re.sub(r"```[a-z]*", "", content).strip()
    try:
        data = json.loads(content)
        return {
            "hook": data.get("hook", ""),
            "corps": data.get("corps", data.get("body", "")),
            "cta": data.get("cta", ""),
            "mots_cles_visuels": data.get("mots_cles_visuels", data.get("keywords", [topic["titre"]])),
        }
    except (json.JSONDecodeError, KeyError):
        # Try to extract sections from plain text
        return {
            "hook": _extract_section(content, "hook", content[:100]),
            "corps": _extract_section(content, "corps", content),
            "cta": _extract_section(content, "cta", "Abonne-toi pour plus de contenu !"),
            "mots_cles_visuels": [topic["titre"]],
        }


def _extract_section(content: str, key: str, default: str) -> str:
    """Extract a section from plain text LLM response."""
    pattern = rf"(?i){key}[:\s]+(.+?)(?=\n\n|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else default


def _fallback_script(topic: Dict, config: dict) -> Dict:
    """Fallback script when API is unavailable."""
    titre = topic["titre"]
    niche = config.get("niche", "")
    return {
        "hook": f"Est-ce que tu savais ca sur {niche} ? Ca va tout changer !",
        "corps": (
            f"Aujourd'hui on parle de: {titre}. "
            f"Voici ce que la science dit sur {niche}. "
            "Point numero 1: commence par comprendre le concept de base. "
            "Point numero 2: applique cette technique au quotidien. "
            "Point numero 3: mesure tes resultats chaque semaine. "
            "Des etudes montrent que 80 pourcent des gens ignorent ces principes fondamentaux."
        ),
        "cta": "Abonne-toi et active la cloche pour ne rater aucune video !",
        "mots_cles_visuels": [niche, "cerveau", "science", "motivation", "succes"],
    }
