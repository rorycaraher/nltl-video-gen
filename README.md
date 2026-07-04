# nltl-video-gen

A collection of command-line tools for generating video content for the NLTL project. Each tool lives in its own subdirectory with its own language, dependencies, and README.

## Tools

### [nltl-clip](nltl-clip/)

Generates animated social media video clips from a music file and a still image. Go + ffmpeg, with BPM-synced zoom/jitter/brightness filters and per-platform output profiles (Instagram square/story, YouTube).

### [nltl-viz](nltl-viz/)

Generates an audio-reactive music visualizer clip from a music file alone — no image input. The outline of the NLTL face deforms in real time to the track's frequency content, with a color-shifting flash on each detected onset. Python, driven by real audio analysis (FFT bands, onset detection, spectral centroid) rather than a fixed BPM, with frames composited in Cairo and piped straight to ffmpeg for encoding.

## Structure

Each tool is self-contained — its own dependency management, its own build/run instructions, no shared code between them. See each tool's README for requirements, installation, and usage.
