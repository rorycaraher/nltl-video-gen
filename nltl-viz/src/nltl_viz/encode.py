from __future__ import annotations

import subprocess
from contextlib import nullcontext
from pathlib import Path
from typing import Iterable

import numpy as np
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn


def build_ffmpeg_cmd(
    audio_path: Path,
    output_path: Path,
    width: int,
    height: int,
    fps: int,
    duration_sec: float,
    preview: bool,
) -> list[str]:
    quality = ["-preset", "ultrafast", "-crf", "35"] if preview else ["-preset", "medium", "-crf", "20"]
    return [
        "ffmpeg",
        "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-i", str(audio_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        *quality,
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration_sec:.3f}",
        "-shortest",
        str(output_path),
    ]


def render_video(
    frames: Iterable[np.ndarray],
    *,
    audio_path: Path,
    output_path: Path,
    width: int,
    height: int,
    fps: int,
    duration_sec: float,
    total_frames: int,
    preview: bool,
    verbose: bool,
) -> None:
    cmd = build_ffmpeg_cmd(audio_path, output_path, width, height, fps, duration_sec, preview)
    stdout = None if verbose else subprocess.DEVNULL
    stderr = None if verbose else subprocess.PIPE

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)

    progress_cm = nullcontext() if verbose else Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} frames"),
        TimeRemainingColumn(),
    )

    with progress_cm as progress:
        task = progress.add_task("Rendering", total=total_frames) if progress else None
        count = 0
        for frame in frames:
            try:
                proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break
            count += 1
            if progress:
                progress.update(task, completed=count)
            if preview and count >= total_frames:
                break
        try:
            proc.stdin.close()
        except OSError:
            pass

    _, stderr_output = proc.communicate()
    if proc.returncode != 0:
        message = stderr_output.decode(errors="replace") if stderr_output else "(no ffmpeg output captured)"
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}):\n{message}")
