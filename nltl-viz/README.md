# nltl-viz

A CLI tool for generating audio-reactive music visualization video clips from a short audio file. Fully generative — no image input. The outline of the NLTL face continuously deforms with the track's frequency content, and a center flash fires on each detected onset, colored by the moment's spectral centroid.

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

# Interactive mode — prompts for audio file + preset
nltl-viz
```

Output files are saved alongside the audio file, named `{trackname}_viz_{timestamp}.mp4` (or `{trackname}_viz_preview_{timestamp}.mp4` for `--preview`) — each render gets its own file so re-running with different settings never overwrites a previous output.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--preset`, `-p` | `industrial` | Visual preset |
| `--preview` | `false` | Render a 10s low-quality preview to check the look |
| `--output-dir`, `-o` | same as audio | Where to write the output file |
| `--config`, `-c` | — | YAML file with custom presets |
| `--verbose`, `-v` | `false` | Show raw ffmpeg output during render |

## Presets

| Name | Description |
|------|--------------|
| `industrial` | Moderate deform, medium onset sensitivity — the default techno look |
| `subtle` | Calmer, slower breathing, lighter grain/vignette |
| `aggressive` | Punchier deform and flash, faster attack, heavier grain/vignette |

Run `nltl-viz presets` to list them.

## Custom Presets

Copy `nltl-viz.yaml.example` to `nltl-viz.yaml` and edit the values — see that file for a full field reference. Custom presets fall back to built-ins if the name isn't found in the config file.

## How it reacts to audio

- The NLTL face's perimeter is divided into 32 frequency bands, distributed proportionally to each edge's actual length (so the long edges get more control points than the short ones), smoothed frame-to-frame with an attack/release envelope so the shape breathes rather than vibrates, and interpolated into one continuous deformed outline. The shape deforms outward/inward from its own centroid, not the canvas center, so it stays recognizable as it moves — and the intentional blank space to the right of the face is preserved.
- Each detected onset (a "hit") triggers a flash centered on the face's centroid, with a fixed-duration decay; a harder hit is brighter/larger, but every flash fades at the same rate.
- The flash's color is a live blend between two configurable colors, driven by the track's spectral centroid — bass-heavy moments skew toward `bass_color`, treble-heavy moments skew toward `treble_color`.
- Grain and vignette are applied as a post-process over every frame for a filmic, moody finish (no image input, no desaturation pass — the palette is deliberately muted already).

## Development

```bash
uv sync --group dev
uv run pytest
```
