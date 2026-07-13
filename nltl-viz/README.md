# nltl-viz

A CLI tool for generating audio-reactive music visualization video clips from a short audio file. Fully generative — no image input. The outline of the chosen shape (the NLTL face, or NLTL space — its inverse) continuously deforms with the track's frequency content, and a flash fires on each detected onset, colored by the moment's spectral centroid.

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages the Python version and dependencies)
- [ffmpeg](https://ffmpeg.org) in your PATH
- Cairo + pkg-config (pycairo builds against system Cairo): `brew install cairo pkg-config` on macOS

## Install

```bash
cd nltl-viz
uv sync
```

## Usage

```
nltl-viz [audio] [flags]
```

```bash
# Preview 10 seconds before committing to a full render
nltl-viz --preset industrial --preview demo.wav

# Full render
nltl-viz --preset aggressive demo.wav

# Custom preset from a config file
nltl-viz --config nltl-viz.yaml --preset my-preset demo.wav

# Render the inverse shape, NLTL space
nltl-viz --shape space demo.wav

# Rigid motion — perimeter stays in proportion, scales with overall loudness
nltl-viz --motion rigid demo.wav

# Interactive mode — prompts for audio file, preset, shape, and motion
nltl-viz
```

Output files are saved alongside the audio file, named `{trackname}_viz_{timestamp}.mp4` (or `{trackname}_viz_preview_{timestamp}.mp4` for `--preview`) — each render gets its own file so re-running with different settings never overwrites a previous output.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--preset`, `-p` | `industrial` | Visual preset |
| `--shape` | `face` | Shape to visualize: `face` or `space` (its inverse) |
| `--motion` | `deform` | Motion style: `deform` (perimeter distorts per frequency band) or `rigid` (perimeter stays in proportion, scales with overall loudness) |
| `--preview` | `false` | Render a 10s low-quality preview to check the look |
| `--output-dir`, `-o` | same as audio | Where to write the output file |
| `--config`, `-c` | — | YAML file with custom presets |
| `--verbose`, `-v` | `false` | Show raw ffmpeg output during render |

## Presets

| Name | Description |
|------|--------------|
| `industrial` | Moderate deform, medium onset sensitivity |
| `subtle` | Calmer, slower breathing, lighter grain/vignette |
| `aggressive` | Punchier deform and flash, faster attack, heavier grain/vignette |

Run `nltl-viz presets` to list them.

## Custom Presets

Copy `nltl-viz.yaml.example` to `nltl-viz.yaml` and edit the values — see that file for a full field reference. Custom presets fall back to built-ins if the name isn't found in the config file.

## Shapes

- `face` (default) — the NLTL face, inscribed in a bounding square with the intentional blank space to its right preserved.
- `space` — the same bounding square minus the NLTL face: the complementary shape, sharing the face's diagonal and short vertical edge as its own boundary.

## Motion styles

- `deform` (default) — the chosen shape's perimeter is divided into 32 frequency bands, distributed proportionally to each edge's actual length (so the long edges get more control points than the short ones), smoothed frame-to-frame with an attack/release envelope so the shape breathes rather than vibrates, and interpolated into one continuous deformed outline. The shape deforms outward/inward from its own centroid, not the canvas center, so it stays recognizable as it moves.
- `rigid` — the shape's proportions never distort; instead the whole shape scales uniformly larger and smaller around its own centroid, driven by the track's overall loudness (an RMS envelope, smoothed the same way as the band energies). The outer shape is a solid flat fill instead of a stroked outline, and the reactive element is a smaller solid-filled concentric copy of the same shape instead of a soft gradient — flat, hard-edged regions throughout, no gradients.

## How it reacts to audio

- Each detected onset (a "hit") triggers the reactive element (a soft gradient blob in `deform`, a smaller solid copy of the shape in `rigid`) with a fixed-duration decay; a harder hit is brighter/larger, but every flash fades at the same rate.
- Its color is a live blend between two configurable colors, driven by the track's spectral centroid — bass-heavy moments skew toward `bass_color`, treble-heavy moments skew toward `treble_color`.
- Grain and vignette are applied as a post-process over every frame (no image input, no desaturation pass — the palette is deliberately muted already).

## Components

The pipeline runs as four independent stages, each owned by a different library, so audio analysis and rendering aren't constrained by what an ffmpeg filter graph can express:

| Stage | File | Library | Role |
|-------|------|---------|------|
| Audio analysis | `audio.py` | [librosa](https://librosa.org) | Decodes the audio file once, up front, and produces one value per *output video frame* (not per audio sample) for: band energy per frequency band (STFT), onset strength/timing, spectral centroid, and an RMS loudness envelope. |
| Frame rendering | `render.py` | [pycairo](https://pycairo.readthedocs.io) | Draws the shape outline/fill and flash for each frame from the arrays `audio.py` precomputed — this is the only stage that draws anything. |
| Post-processing | `postprocess.py` | [numpy](https://numpy.org) | Applies grain and vignette to each rendered frame as array operations on the raw RGB buffer. |
| Encoding | `encode.py` | [ffmpeg](https://ffmpeg.org) (subprocess) | Muxes the piped raw RGB24 frames with the original audio track. ffmpeg does no filtering or effects work — it's a dumb encoder, all image work already happened in Python. |

Supporting modules: `preset.py`/`config.py` define and load the numeric fields (`deform_amplitude`, `flash_decay_ms`, colors, etc.) that `audio.py` and `render.py` read; `cli.py` (built on [typer](https://typer.tiangolo.com)) wires the four stages together per-frame and exposes the flags documented above; `interactive.py` (built on [questionary](https://questionary.readthedocs.io)) is the prompt-driven entry point used when no audio file is passed on the command line.

### What reacts to audio, and where it's computed

All audio reactivity is resolved once in `audio.py` before any frame is drawn — `render.py` only ever reads precomputed per-frame values, it does no audio analysis of its own:

- Shape motion — `deform` reads per-band energy; `rigid` reads the RMS loudness envelope.
- Flash brightness — reads onset strength/timing (decayed per frame, combined across overlapping onsets with an elementwise `max`).
- Flash/gradient color — reads spectral centroid, blended between `bass_color` and `treble_color`.

## Development

```bash
uv sync --group dev
uv run pytest
```
