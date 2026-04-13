"""prompt_builder.py - LLM prompt construction utilities."""
from typing import Dict


def build_script_prompt(topic: Dict, config: dict, word_count: int) -> str:
    """Build the script generation prompt for the LLM.

    Returns a formatted prompt string ready for the LLM API.
    """
    niche = config.get("niche", "")
    langue = config.get("langue", "fr")
    duree = config.get("duree_cible", 60)
    style = config.get("style_script", "")

    prompt = f"""Tu dois generer un script video de {duree} secondes sur le sujet suivant:

SUJET: {topic['titre']}
DESCRIPTION: {topic.get('description', '')}
NICHE: {niche}
LANGUE: {langue}
NOMBRE DE MOTS CIBLE: ~{word_count} mots

STYLE DEMANDE:
{style}

Retourne UNIQUEMENT un objet JSON valide avec exactement ces cles:
{{
  "hook": "[phrase d'accroche choc de 3-5 secondes, max 20 mots]",
  "corps": "[developpement principal de ~45 secondes, continu, sans puces]",
  "cta": "[call-to-action final de 10-15 secondes, max 30 mots]",
  "mots_cles_visuels": ["mot1", "mot2", "mot3", "mot4", "mot5"]
}}

REGLES IMPORTANTES:
- Le hook doit etre choc et intrigant, pas banal
- Le corps doit etre fluide, parle (oral), pas ecrit
- Les mots cles visuels servent a trouver des videos stock sur Pexels
- Pas de markdown, pas de code fences, juste le JSON
- Total: environ {word_count} mots pour {duree}s de video"""

    return prompt


def build_veille_prompt(niche: str, query: str, langue: str) -> str:
    """Build the veille/research prompt for Perplexity."""
    return (
        f"Recherche les 5 sujets les plus viraux et tendance pour la niche '{niche}' "
        f"en ce moment (requete: {query}). "
        f"Reponds en {langue} avec un JSON: {{topics: [{{titre, description, score}}]}}"
    )
