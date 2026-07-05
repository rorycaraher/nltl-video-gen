from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import typer
from rich.console import Console
from rich.table import Table
from typer.core import TyperGroup

from nltl_viz import audio as audio_mod
from nltl_viz import config, encode, interactive, postprocess, render
from nltl_viz import preset as preset_mod
from nltl_viz.audio import AudioAnalysis
from nltl_viz.preset import Preset
from nltl_viz.render import Motion, Shape

FPS = 30
SIZE = 1080
DEFAULT_COMMAND = "render"


class _DefaultCommandGroup(TyperGroup):
    """Route bare `nltl-viz [audio] [flags]` invocations to the `render`
    command, since Click otherwise consumes a leading positional value into
    the group callback's own argument before ever checking subcommand names —
    which would make an explicit `nltl-viz presets` unreachable."""

    def resolve_command(self, ctx, args):
        if not args or args[0] not in self.commands:
            args = [DEFAULT_COMMAND, *args]
        return super().resolve_command(ctx, args)


app = typer.Typer(
    add_completion=False,
    cls=_DefaultCommandGroup,
    context_settings={"ignore_unknown_options": True},
    help=(
        "Generate an audio-reactive NLTL face visualization from a music file.\n\n"
        "Usage: nltl-viz [AUDIO] [--preset NAME] [--shape face|space] "
        "[--motion deform|rigid] [--preview] "
        "[--output-dir DIR] [--config FILE] [--verbose]\n\n"
        "Run with no arguments for interactive mode."
    ),
)
console = Console()


def _frame_generator(
    analysis: AudioAnalysis, preset_obj: Preset, size: int, shape: Shape, motion: Motion
) -> Iterable[np.ndarray]:
    vignette_mask = postprocess.build_vignette_mask(size, size, preset_obj.vignette_fraction)
    rng = np.random.default_rng()
    for i in range(analysis.n_frames):
        band_values = analysis.band_energy[i]
        brightness = float(analysis.flash_brightness[i])
        color = tuple(analysis.flash_color[i])
        scale_value = float(analysis.scale_envelope[i])
        frame = render.render_frame(
            band_values, brightness, color, preset_obj, size, shape, motion, scale_value
        )
        frame = postprocess.apply_vignette(frame, vignette_mask)
        frame = postprocess.apply_grain(frame, preset_obj.grain_strength, rng)
        yield frame


def run_render(
    audio_path: Path,
    preset_name: str,
    shape: Shape,
    motion: Motion,
    output_dir: Optional[Path],
    config_path: Optional[Path],
    preview: bool,
    verbose: bool,
) -> None:
    resolved_preset = config.resolve_preset(preset_name, config_path)

    console.print()
    console.print(f"[bold]Preset[/bold]    {resolved_preset.name} — {resolved_preset.description}")
    console.print(f"[bold]Shape[/bold]     {shape.value}")
    console.print(f"[bold]Motion[/bold]    {motion.value}")
    if preview:
        console.print("[bold]Preview[/bold]   10s low-quality render")

    with console.status("Analyzing audio..."):
        analysis = audio_mod.analyze(audio_path, resolved_preset, fps=FPS)

    out_dir = output_dir if output_dir is not None else audio_path.parent
    suffix = "viz_preview" if preview else "viz"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = out_dir / f"{audio_path.stem}_{suffix}_{timestamp}.mp4"

    total_frames = min(analysis.n_frames, FPS * 10) if preview else analysis.n_frames
    duration_sec = 10.0 if preview else analysis.duration_sec

    console.print(f"[bold]Output[/bold]    {output_path}")
    console.print()

    frames = _frame_generator(analysis, resolved_preset, SIZE, shape, motion)
    encode.render_video(
        frames,
        audio_path=audio_path,
        output_path=output_path,
        width=SIZE,
        height=SIZE,
        fps=FPS,
        duration_sec=duration_sec,
        total_frames=total_frames,
        preview=preview,
        verbose=verbose,
    )
    console.print(f"[green]Done[/green] → {output_path}")


def _run_interactive() -> None:
    try:
        choices = interactive.run()
        run_render(
            choices.audio_path,
            choices.preset_name,
            Shape(choices.shape),
            Motion(choices.motion),
            None,
            None,
            False,
            False,
        )
    except Exception as exc:  # surface any failure as a clean CLI error, not a traceback
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"\nTo run this again without prompts:\n  {choices.headless_command()}")


@app.callback(invoke_without_command=True)
def default_callback(ctx: typer.Context) -> None:
    """Generate an audio-reactive NLTL face visualization from a music file.

    Run with no arguments for interactive mode."""
    # Click short-circuits truly-zero-arg invocations straight to the group
    # callback without ever reaching resolve_command, so the zero-args ->
    # interactive-mode path has to be handled here rather than in render_cmd.
    if ctx.invoked_subcommand is not None:
        return
    _run_interactive()


@app.command(DEFAULT_COMMAND, hidden=True)
def render_cmd(
    audio: Optional[Path] = typer.Argument(None, help="Path to the input audio file"),
    preset: str = typer.Option("industrial", "--preset", "-p", help="Visual preset"),
    shape: Shape = typer.Option(Shape.face, "--shape", help="Shape to visualize: face or space"),
    motion: Motion = typer.Option(
        Motion.deform, "--motion", help="Motion style: deform (per-band outline push) or rigid (uniform scale)"
    ),
    preview: bool = typer.Option(False, "--preview", help="Render a 10s low-quality preview"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML file with custom presets"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show raw ffmpeg output during render"),
) -> None:
    """Generate an audio-reactive NLTL face visualization from a music file."""
    if audio is None:
        _run_interactive()
        return

    try:
        run_render(audio, preset, shape, motion, output_dir, config_path, preview, verbose)
    except Exception as exc:  # surface any failure as a clean CLI error, not a traceback
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("presets")
def presets_cmd() -> None:
    """List available built-in presets."""
    table = Table(title="Built-in presets")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    for name in preset_mod.names():
        p = preset_mod.get(name)
        table.add_row(name, p.description)
    console.print(table)


if __name__ == "__main__":
    app()
