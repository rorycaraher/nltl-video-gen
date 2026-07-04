# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory. See the [repo-root CLAUDE.md](../CLAUDE.md) for cross-cutting conventions (in particular the documentation/description language rule) that also apply here.

## Commands

uv-managed. Run from this directory:

```bash
uv sync --group dev              # install deps (needs: brew install cairo pkg-config)
uv run pytest                    # run all tests
uv run pytest tests/test_ema.py::test_constant_input_is_steady_state   # single test
uv run ruff check .              # lint
uv run nltl-viz --preview demo.wav
```

## Architecture

The pipeline deliberately keeps ffmpeg as a dumb encoder only (raw RGB frames piped to its stdin, muxed with the original audio) — audio analysis and rendering are done entirely in Python so they aren't constrained by what an ffmpeg filter graph can express:

1. **`audio.py`** decodes the full track with librosa up front and produces per-*video*-frame arrays (not per-audio-sample): smoothed log-spaced band energies, a precomputed flash brightness envelope (onset detection, decayed and combined via elementwise `max` so overlapping onsets don't blow out to solid white), and a precomputed flash color per frame (spectral centroid lerped between two configured hex colors). `hop_length` is chosen as `sample_rate / fps` specifically so analysis-frame indices align 1:1 with output video frames with no resampling step.
2. **`render.py`** draws each frame in Cairo. Two shapes are supported (`Shape` enum, `--shape` flag, default `face`): `face` (an arbitrary quadrilateral, not a square) and `space` (the same bounding square minus the face — a concave pentagon sharing the face's diagonal and short vertical edge as its own boundary, so the two are exact complements). Either shape's perimeter is parametrized by actual arc length (not an equal split per edge) so band control points map to real distance traveled around the boundary regardless of how uneven the edges are. Both the shape's deformation and the flash's position scale from the polygon's own centroid (computed via the shoelace formula, which works for either shape regardless of convexity), not canvas center, so the shape stays recognizable as it reacts and the flash reads as being inside the shape rather than in empty canvas space. `deform_amplitude` is applied identically regardless of shape — there's no special-casing for `space`'s concave reflex vertex; if a preset's amplitude ever produces a self-intersecting outline near that corner, that's the first place to look.
3. **`postprocess.py`** applies grain and vignette as plain numpy ops on the rendered RGB buffer.
4. **`encode.py`** pipes frames to ffmpeg's stdin as raw RGB24 and drives a determinate Rich progress bar (frame count is known up front, unlike nltl-clip which can't observe ffmpeg's internal progress).
5. **`cli.py`** has a non-obvious Click/Typer detail: `nltl-viz <audio>` (a bare positional argument) and `nltl-viz presets` (an explicit subcommand) must coexist. A plain Typer callback can't do this — Click's group-level argument parsing consumes a leading positional token before ever checking subcommand names. The fix is a custom `_DefaultCommandGroup(TyperGroup)` that overrides `resolve_command` to prepend the hidden `render` command when the first token isn't a known subcommand, combined with `context_settings={"ignore_unknown_options": True}` so the group's own parser doesn't reject subcommand-specific flags like `--preset` before dispatch happens. If you touch the CLI's argument/subcommand structure, re-verify all three invocation shapes (bare filename, flags-first, zero-args interactive, explicit `presets`) — each one broke independently while this was first built.

Presets follow the same shape as nltl-clip's: a flat dataclass of numeric fields, a small hardcoded built-in dict, and an optional YAML config file whose entries are checked first and fall back to the built-ins by name.
