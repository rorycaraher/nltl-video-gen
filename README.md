# nltl-video-gen

A collection of command-line tools for generating video content for the NLTL project. Each tool lives in its own subdirectory with its own language, dependencies, and README.

## Tools

### [nltl-clip](nltl-clip/)

Generates animated social media video clips from a music file and a still image. Go + ffmpeg, with BPM-synced zoom/jitter/brightness filters and per-platform output profiles (Instagram square/story, YouTube).

### [nltl-viz](nltl-viz/)

Generates an audio-reactive music visualizer clip from a music file alone — no image input — or overlays the same visualization with transparency onto a video file, analyzing the video's own audio track. The outline of a chosen shape (the NLTL face, or NLTL space — its inverse) deforms in real time to the track's frequency content, with rhythmic flashes at detected transients, flashes coloured by spectrum content at that time. Python, librosa, cairo.

## Structure

Each tool is self-contained — its own dependency management, its own build/run instructions, no shared code between them. See each tool's README for requirements, installation, and usage.
