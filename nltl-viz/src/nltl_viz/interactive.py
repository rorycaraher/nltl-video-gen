from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import questionary

from nltl_viz import preset as preset_mod
from nltl_viz import shapes as shapes_mod

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".aiff", ".aif", ".ogg", ".m4a"}


@dataclass
class Choices:
    audio_path: Path
    preset_name: str
    shape: str
    motion: str

    def headless_command(self) -> str:
        return (
            f"nltl-viz --preset {self.preset_name} --shape {self.shape} "
            f"--motion {self.motion} {self.audio_path}"
        )


def scan_audio_files(cwd: Path) -> list[Path]:
    return sorted(p for p in cwd.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS)


def run() -> Choices:
    cwd = Path.cwd()
    audio_files = scan_audio_files(cwd)
    if not audio_files:
        extensions = ", ".join(sorted(AUDIO_EXTENSIONS))
        raise RuntimeError(f"no audio files found in {cwd} (looked for {extensions})")

    audio_answer = questionary.select("Audio file", choices=[str(p) for p in audio_files]).ask()
    if audio_answer is None:
        raise RuntimeError("cancelled")

    preset_choices = [
        questionary.Choice(title=f"{name} — {preset_mod.get(name).description}", value=name)
        for name in preset_mod.names()
    ]
    preset_answer = questionary.select("Preset", choices=preset_choices).ask()
    if preset_answer is None:
        raise RuntimeError("cancelled")

    shape_choices = [
        questionary.Choice(title="face — the NLTL face", value="face"),
        questionary.Choice(title="space — the NLTL space (the face's inverse)", value="space"),
    ] + [
        questionary.Choice(title=f"{name} — custom shape", value=name)
        for name in shapes_mod.names(shapes_mod.default_shapes_path())
    ]
    shape_answer = questionary.select("Shape", choices=shape_choices).ask()
    if shape_answer is None:
        raise RuntimeError("cancelled")

    motion_choices = [
        questionary.Choice(title="deform — perimeter distorts per frequency band", value="deform"),
        questionary.Choice(title="rigid — perimeter stays in proportion, scales with overall loudness", value="rigid"),
        questionary.Choice(
            title="pulse — constant size and shape, reactivity via fill opacity", value="pulse"
        ),
    ]
    motion_answer = questionary.select("Motion", choices=motion_choices).ask()
    if motion_answer is None:
        raise RuntimeError("cancelled")

    return Choices(
        audio_path=Path(audio_answer),
        preset_name=preset_answer,
        shape=shape_answer,
        motion=motion_answer,
    )
