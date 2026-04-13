"""main.py — Orchestrateur principal du pipeline AI Content Machine."""
import typer
import yaml
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

load_dotenv()
console = Console()
app = typer.Typer(help="AI Content Machine — Générateur de vidéos verticales automatisé")


def load_config(niche: str) -> dict:
    """Load niche configuration from YAML file."""
    niche_path = Path(f"config/niches/{niche}.yaml")
    if not niche_path.exists():
        console.print(f"[red]Niche '{niche}' introuvable dans config/niches/[/red]")
        raise typer.Exit(1)
    with open(niche_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.command()
def run(
    niche: str = typer.Option(..., "--niche", "-n", help="Niche à utiliser (ex: psychologie)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Génère le script uniquement, sans vidéo"),
    no_upload: bool = typer.Option(False, "--no-upload", help="Génère la vidéo sans upload YouTube"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Mode interactif pour choisir le sujet"),
    auto: bool = typer.Option(False, "--auto", help="Ignore les confirmations (mode autonome)"),
    schedule: bool = typer.Option(False, "--schedule", help="Programme la publication à H+1"),
):
    """Lance le pipeline complet de génération de contenu."""
    from agents.veille_agent import fetch_trending_topics
    from agents.script_agent import generate_script
    from agents.tts_agent import generate_tts
    from agents.subtitle_agent import generate_subtitles
    from agents.visual_agent import fetch_video_clips
    from agents.video_agent import assemble_video
    from publisher.youtube_publisher import upload_to_youtube
    from utils.file_manager import prepare_directories
    from utils.logger import get_logger

    logger = get_logger()
    prepare_directories()

    console.print(Panel(f"[bold cyan]AI Content Machine[/bold cyan] — Niche: [yellow]{niche}[/yellow]", expand=False))

    # 1. Load config
    logger.info("Chargement de la configuration...")
    config = load_config(niche)
    console.print(f"[green]✓[/green] Config chargée: {config['niche']}")

    # 2. Veille agent
    logger.info("Recherche des sujets tendance...")
    with console.status("[bold green]Recherche des tendances via Perplexity Sonar..."):
        topics = fetch_trending_topics(config)

    console.print(f"[green]✓[/green] {len(topics)} sujets trouvés")
    for i, t in enumerate(topics):
        console.print(f"  {i+1}. [bold]{t['titre']}[/bold] (score: {t['score']}/10)")

    # 3. Topic selection
    if interactive:
        choice = Prompt.ask("Choisissez un sujet", choices=[str(i) for i in range(1, len(topics)+1)])
        selected_topic = topics[int(choice) - 1]
    else:
        selected_topic = max(topics, key=lambda x: x['score'])
        console.print(f"[green]✓[/green] Sujet auto-sélectionné: [bold]{selected_topic['titre']}[/bold]")

    # 4. Script agent
    logger.info("Génération du script...")
    with console.status("[bold green]Génération du script via OpenRouter Llama 4..."):
        script = generate_script(selected_topic, config)

    console.print(Panel(
        f"[bold]HOOK:[/bold] {script['hook']}\n\n[bold]CORPS:[/bold] {script['corps'][:200]}...\n\n[bold]CTA:[/bold] {script['cta']}",
        title="Script Généré", border_style="cyan"
    ))

    if not auto:
        if not Confirm.ask("Valider ce script et continuer ?"):
            console.print("[yellow]Pipeline annulé.[/yellow]")
            raise typer.Exit(0)

    if dry_run:
        console.print("[yellow]Mode --dry-run: pipeline arrêté après génération du script.[/yellow]")
        raise typer.Exit(0)

    # 5. TTS agent
    logger.info("Génération de la voix off...")
    with console.status("[bold green]Synthèse vocale edge-tts..."):
        audio_path, audio_duration = generate_tts(script, config)
    console.print(f"[green]✓[/green] Audio généré: {audio_path} ({audio_duration:.1f}s)")

    # 6. Subtitle agent
    logger.info("Génération des sous-titres...")
    with console.status("[bold green]Transcription Whisper..."):
        srt_path = generate_subtitles(audio_path)
    console.print(f"[green]✓[/green] Sous-titres: {srt_path}")

    # 7. Visual agent
    logger.info("Téléchargement des clips visuels...")
    with console.status("[bold green]Téléchargement clips Pexels..."):
        clips = fetch_video_clips(script['mots_cles_visuels'], config)
    console.print(f"[green]✓[/green] {len(clips)} clips téléchargés")

    # 8. Video agent
    logger.info("Assemblage de la vidéo...")
    import re
    from datetime import date
    slug = re.sub(r'[^a-z0-9]+', '-', selected_topic['titre'].lower())[:40]
    output_name = f"{niche}_{date.today().strftime('%Y%m%d')}_{slug}.mp4"
    with console.status("[bold green]Assemblage FFmpeg 9:16..."):
        video_path = assemble_video(clips, audio_path, srt_path, output_name, config)
    console.print(f"[green]✓[/green] Vidéo générée: {video_path}")

    if no_upload:
        console.print("[yellow]Mode --no-upload: vidéo non uploadée.[/yellow]")
        console.print(Panel(f"[bold green]Pipeline terminé ![/bold green]\nVidéo: {video_path}", expand=False))
        raise typer.Exit(0)

    # 9. YouTube publisher
    logger.info("Upload YouTube...")
    with console.status("[bold green]Upload vers YouTube..."):
        video_url = upload_to_youtube(video_path, selected_topic, script, config, schedule=schedule)
    console.print(f"[green]✓[/green] Vidéo uploadée: {video_url}")

    console.print(Panel(f"[bold green]Pipeline terminé avec succès ![/bold green]\nURL: {video_url}", expand=False))


@app.command("list-niches")
def list_niches():
    """Affiche les niches disponibles."""
    niches_dir = Path("config/niches")
    if not niches_dir.exists():
        console.print("[red]Dossier config/niches introuvable.[/red]")
        raise typer.Exit(1)
    niches = [f.stem for f in niches_dir.glob("*.yaml")]
    console.print(Panel("\n".join(f"  • [cyan]{n}[/cyan]" for n in niches), title="Niches disponibles", expand=False))


if __name__ == "__main__":
    app()
