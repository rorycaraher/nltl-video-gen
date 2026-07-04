# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

A collection of independent CLI tools for generating video content for the NLTL project. Each tool lives in its own subdirectory with its own language, dependencies, and README — there is no shared code between them. See each tool's own `CLAUDE.md` for its build/lint/test commands and architecture:

- **[`nltl-clip/`](nltl-clip/CLAUDE.md)** — Go. Animates a still image to music via ffmpeg filter graphs.
- **[`nltl-viz/`](nltl-viz/CLAUDE.md)** — Python. Fully generative audio visualizer (no image input).

## Documentation and description language

This project is deliberately style/appearance/aesthetic-agnostic. Descriptions of presets, CLI help text, README copy, and code comments must describe what a setting technically *does*, never what genre, mood, or aesthetic it evokes.

- Bad: `"the default techno look"`, `"a moody, filmic finish"`, `"cool vibe"`, `"cinematic feel"`.
- Good: `"moderate deform amplitude, medium onset sensitivity"`, `"grain and vignette applied as a post-process over every frame"`.

If you're tempted to reach for a genre or mood word, name the parameter and its effect instead. This applies across both `nltl-clip` and `nltl-viz`.
