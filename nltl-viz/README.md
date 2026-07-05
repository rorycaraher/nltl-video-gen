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

## Development

```bash
uv sync --group dev
uv run pytest
```
