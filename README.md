# ai-content-machine

Pipeline Python automatise pour generer des videos verticales 9:16 (60s) pour YouTube Shorts et Instagram Reels.

Changez de niche = changez de fichier config. Pret a tourner en local.

## Schema du pipeline

```
config/psychologie.yaml
        |
        v
[veille_agent]  ---> Perplexity Sonar API --> topics trending
        |
        v
[script_agent]  ---> OpenRouter (Llama 4)  --> script 60s structure
        |
        v
[tts_agent]     ---> edge-tts              --> audio.mp3
        |
        v
[subtitle_agent] --> Whisper local         --> subtitles.srt
        |
        v
[visual_agent]  ---> Pexels API            --> video clips
        |
        v
[video_agent]   ---> FFmpeg                --> final_video.mp4
        |
        v
[youtube_publisher] -> YouTube Data API v3 --> Shorts publie
```

## Structure du projet

```
ai-content-machine/
ss config/
ss   psychologie.yaml
ss   finance.yaml
ss agents/
ss   veille_agent.py
ss   script_agent.py
ss   tts_agent.py
ss   subtitle_agent.py
ss   visual_agent.py
ss   video_agent.py
ss publisher/
ss   __init__.py
ss   youtube_publisher.py
ss utils/
ss   logger.py
ss   file_manager.py
ss   prompt_builder.py
ss outputs/
ss temp/
ss credentials/
ss main.py
ss requirements.txt
ss .env.example
ss .gitignore
ss README.md
```

## Installation

### Prerequis

- Python 3.11+
- FFmpeg installe et dans le PATH
- `uv` ou `pip`

### 1. Cloner le repo

```bash
git clone https://github.com/BadreddineEK/ai-content-machine.git
cd ai-content-machine
```

### 2. Installer les dependances

```bash
pip install -r requirements.txt
```

Ou avec uv:

```bash
uv pip install -r requirements.txt
```

### 3. Configurer les variables d environnement

```bash
cp .env.example .env
# Editer .env et remplir vos cles API
```

### 4. Configurer YouTube OAuth2

1. Aller sur Google Cloud Console
2. Creer un projet et activer YouTube Data API v3
3. Telecharger `client_secrets.json` dans `credentials/`
4. Au premier lancement, une fenetre OAuth2 s ouvrira

## Utilisation

### Lancer le pipeline complet

```bash
python main.py run --config config/psychologie.yaml
```

### Choisir le topic manuellement

```bash
python main.py run --config config/psychologie.yaml --topic "Les biais cognitifs qui sabotent vos decisions"
```

### Lancer sans publier sur YouTube

```bash
python main.py run --config config/psychologie.yaml --no-publish
```

### Tester un seul agent

```bash
python main.py test-agent veille --config config/finance.yaml
python main.py test-agent script --config config/psychologie.yaml --topic "test topic"
```

## Creer une nouvelle niche

1. Copier un fichier de config existant:

```bash
cp config/psychologie.yaml config/ma_niche.yaml
```

2. Editer `config/ma_niche.yaml`:
   - Changer `niche: ma_niche`
   - Adapter les `keywords` pour votre domaine
   - Changer la voix TTS si besoin
   - Adapter les `style_keywords` pour les visuels Pexels
   - Mettre a jour les `tags` YouTube

3. Lancer:

```bash
python main.py run --config config/ma_niche.yaml
```

## Variables d environnement

| Variable | Description |
|---|---|
| `PERPLEXITY_API_KEY` | Cle API Perplexity Sonar |
| `OPENROUTER_API_KEY` | Cle API OpenRouter |
| `PEXELS_API_KEY` | Cle API Pexels |

## Stack technique

- **Veille**: Perplexity Sonar API
- **Script**: OpenRouter (Llama 4 Maverick - gratuit)
- **TTS**: edge-tts (voix neurales Microsoft)
- **Subtitles**: Whisper (local, openai-whisper)
- **Visuels**: Pexels API
- **Montage**: FFmpeg via moviepy
- **Publication**: YouTube Data API v3
- **CLI**: Typer + Rich

## Licence

MIT
