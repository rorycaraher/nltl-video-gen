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

1. **`audio.py`** decodes the full track with librosa up front and produces per-*video*-frame arrays (not per-audio-sample): smoothed log-spaced band energies, a smoothed overall-loudness (RMS) envelope for `Motion.rigid`, a precomputed flash brightness envelope (onset detection, decayed and combined via elementwise `max` so overlapping onsets don't blow out to solid white), and a precomputed flash color per frame (spectral centroid lerped between two configured hex colors). `hop_length` is chosen as `sample_rate / fps` specifically so analysis-frame indices align 1:1 with output video frames with no resampling step. The RMS envelope is log-compressed with `20*log10` (amplitude-domain), not the `10*log10` used for the power-domain band energies, then percentile-normalized the same way — different compression constant, same normalization pattern.
2. **`render.py`** draws each frame in Cairo, along two independent axes:
   - **`Shape`** (`--shape` flag, default `face`): `face` (an arbitrary quadrilateral, not a square) or `space` (the same bounding square minus the face — a concave pentagon sharing the face's diagonal and short vertical edge as its own boundary, so the two are exact complements). Both the shape's motion and the flash's position scale from the polygon's own centroid (shoelace formula, works for either shape regardless of convexity), not canvas center.
   - **`Motion`** (`--motion` flag, default `deform`): `deform` distorts the perimeter per-band (arc-length-parametrized, so control points map to real distance traveled around the boundary regardless of how uneven the edges are — `deform_amplitude`), stroked outline, gradient-blob flash. `rigid` keeps the shape's plain proportions and instead uniformly scales the whole thing from its centroid, driven by the RMS envelope oscillating both directions around baseline (`scale_amplitude`, `scaled_polygon_points`) — solid flat fill instead of a stroke, and the flash becomes a smaller solid-filled concentric copy of the same shape (`draw_inner_shape`) rather than a radial gradient. `deform_amplitude`/`scale_amplitude` are deliberately separate preset fields (not one field reinterpreted by mode) so a preset's numbers don't silently change meaning depending on an unrelated flag. Neither shape nor motion special-cases `space`'s concave reflex vertex — if a preset's amplitude ever produces visible self-intersection near that corner, that's the first place to look.
3. **`postprocess.py`** applies grain and vignette as plain numpy ops on the rendered RGB buffer.
4. **`encode.py`** pipes frames to ffmpeg's stdin as raw RGB24 and drives a determinate Rich progress bar (frame count is known up front, unlike nltl-clip which can't observe ffmpeg's internal progress).
5. **`cli.py`** has a non-obvious Click/Typer detail: `nltl-viz <audio>` (a bare positional argument) and `nltl-viz presets` (an explicit subcommand) must coexist. A plain Typer callback can't do this — Click's group-level argument parsing consumes a leading positional token before ever checking subcommand names. The fix is a custom `_DefaultCommandGroup(TyperGroup)` that overrides `resolve_command` to prepend the hidden `render` command when the first token isn't a known subcommand, combined with `context_settings={"ignore_unknown_options": True}` so the group's own parser doesn't reject subcommand-specific flags like `--preset` before dispatch happens. If you touch the CLI's argument/subcommand structure, re-verify all three invocation shapes (bare filename, flags-first, zero-args interactive, explicit `presets`) — each one broke independently while this was first built.

Presets follow the same shape as nltl-clip's: a flat dataclass of numeric fields, a small hardcoded built-in dict, and an optional YAML config file whose entries are checked first and fall back to the built-ins by name.
