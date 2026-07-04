# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory. See the [repo-root CLAUDE.md](../CLAUDE.md) for cross-cutting conventions (in particular the documentation/description language rule) that also apply here.

## Commands

```bash
go build -o nltl-clip ./cmd/nltl-clip/   # build
go vet ./...                              # lint
./nltl-clip --preset industrial --bpm 138 --preview demo.wav cover.jpg
```

There are no Go test files in this module yet.

## Architecture

`cmd/nltl-clip/main.go` (Cobra CLI) resolves a `Profile` (output dimensions, `internal/profile`) and a `Preset` (visual parameters, `internal/preset`, optionally overridden via `--config` YAML through `internal/config`), then calls `Preset.BuildFilter()` to generate a single ffmpeg `-vf` filter-graph string (zoompan/jitter/brightness expressions, BPM-synced or time-based) and hands it to `internal/ffmpeg.Render`, which shells out to ffmpeg directly — ffmpeg itself is the visual engine here, not just an encoder.

Zero-args invocation drops into `internal/interactive` (a `huh`-based TUI form) instead of requiring flags.

Presets and profiles both follow the same shape: a flat struct, a small hardcoded built-in map, `Get(name) (T, bool)`, and a sorted `Names()`. Custom presets loaded via `--config` are checked first and fall back to the built-in map by name.
