# nltl-clip

A CLI tool for generating animated social media video clips from a music file and a still image. Built around ffmpeg with BPM-synced visuals and per-platform output profiles.

## Requirements

- [Go](https://go.dev) 1.21+
- [ffmpeg](https://ffmpeg.org) with ffprobe in your PATH

## Install

```bash
go install github.com/rcaraher/nltl-video-gen/cmd/nltl-clip@latest
```

Or build locally:

```bash
git clone https://github.com/rcaraher/nltl-video-gen
cd nltl-video-gen
go build -o nltl-clip ./cmd/nltl-clip/
```

## Usage

```
nltl-clip [audio] [image] [flags]
```

```bash
# Preview 10 seconds before committing to a full render
nltl-clip --preset industrial --bpm 138 --preview demo.wav cover.jpg

# Full render for Instagram feed
nltl-clip --preset industrial --bpm 138 demo.wav cover.jpg

# YouTube version
nltl-clip --profile youtube --preset dark --bpm 138 demo.wav cover.jpg

# Use a custom preset from a config file
nltl-clip --config nltl.yaml --preset my-preset --bpm 138 demo.wav cover.jpg
```

Output files are saved alongside the audio file, named `{trackname}_{profile}.mp4`.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--profile`, `-p` | `instagram-square` | Output dimensions |
| `--preset` | `industrial` | Visual style |
| `--bpm` | `0` | Track BPM for beat-synced animation (0 = time-based) |
| `--preview` | `false` | Render 10s at low quality to check the look |
| `--output-dir`, `-o` | same as audio | Where to write the output file |
| `--config`, `-c` | — | YAML file with custom presets |

## Profiles

| Name | Resolution |
|------|------------|
| `instagram-square` | 1080×1080 |
| `instagram-story` | 1080×1920 |
| `youtube` | 1920×1080 |

Run `nltl-clip profiles` to list them.

## Presets

| Name | Description |
|------|-------------|
| `industrial` | Desaturated, grainy, heavy vignette — the default techno aesthetic |
| `clean` | Full colour, minimal grain, subtle movement |
| `dark` | Deep blacks, extreme grain, maximum vignette |

Run `nltl-clip presets` to list them.

## Custom Presets

Copy `nltl.yaml.example` to `nltl.yaml` and edit the values:

```yaml
presets:
  - name: my-preset
    description: My custom look
    zoom_base: 1.02
    zoom_amp: 0.01
    zoom_beats: 8.0
    jitter_amp: 2.0
    blur_sigma: 0.6
    contrast: 1.15
    saturation: 0.7
    brightness_amp: 0.02
    brightness_beats: 4.0
    vignette_fraction: 0.167
    grain_strength: 25
```

Custom presets fall back to built-ins if the name isn't found in the config file.

## BPM Animations

When `--bpm` is set, zoom, jitter, and brightness oscillations are tied to the track's beat grid rather than fixed time intervals. The `zoom_beats` and `brightness_beats` fields in a preset control how many beats each animation cycle spans.

At 138 BPM with `zoom_beats: 8`, the zoom breath completes one cycle every ~3.5 seconds — one slow inhale per 8 beats.
