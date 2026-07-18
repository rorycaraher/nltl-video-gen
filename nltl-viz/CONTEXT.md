# NLTL Viz

Generates an audio-reactive polygon animation from a music file (or overlays it onto a video), driven entirely by Python-side audio analysis and Cairo rendering.

## Language

**Shape**:
A named polygon rendered by the tool, selected via `--shape <name>`. Either built-in (`face`, `space`) or a custom shape.
_Avoid_: figure, outline (as a synonym for the whole concept)

**Custom shape**:
A user-defined Shape created with the shape editor and saved under a name in the shapes file. Cannot be named `face` or `space` — those two names are reserved for the built-ins and are rejected at save time.

**Bounding square**:
The canonical square every Shape — built-in or custom — is defined within: half-width `0.35 * size`, centered on the canvas. Guarantees all shapes render at the same visual scale and position regardless of which one is selected.

**Shape editor**:
The local-web-app tool (`nltl-viz shapes edit [name]`) for creating or modifying a custom shape by placing vertices in the bounding square. Shows only the static polygon being drawn — no live animated deform/rigid/flash preview; `--preview` (the existing 10s render) already covers seeing a shape under motion.

**Shapes file**:
The YAML file storing custom shapes by name, default `~/.config/nltl-viz/shapes.yaml`, overridable via `--shapes-file`. Looked up before falling back to the built-in `face`/`space` shapes when resolving `--shape <name>`.

**Pulse** (a Motion):
The shape stays a constant size and proportion — no deformation, no scaling — and is drawn as one solid, flat-colored silhouette. Audio reactivity is expressed entirely as that fill's opacity, floor 0%, ceiling always below 100%. Has no flash element and no bass/treble color-lerp — those belong to `deform`/`rigid` only.
_Avoid_: breathing, throbbing (as synonyms for this Motion specifically — describe the opacity mechanic, not an impression of it)
