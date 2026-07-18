from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RESERVED_NAMES = {"face", "space"}


@dataclass(frozen=True)
class CustomShape:
    """A user-drawn Shape: vertices are fractions in [0,1] of the same
    bounding square face/space are defined within, in click order (winding
    direction doesn't affect the centroid or fill, so it's not constrained)."""

    name: str
    vertices: tuple[tuple[float, float], ...]


def default_shapes_path() -> Path:
    return Path.home() / ".config" / "nltl-viz" / "shapes.yaml"


def load(path: Path) -> list[CustomShape]:
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text())
    except OSError as exc:
        raise ValueError(f"reading {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"parsing {path}: {exc}") from exc

    if not raw or "shapes" not in raw:
        return []

    shapes: list[CustomShape] = []
    for entry in raw["shapes"]:
        vertices = tuple((float(x), float(y)) for x, y in entry["vertices"])
        shapes.append(CustomShape(name=entry["name"], vertices=vertices))
    return shapes


def save_all(path: Path, shapes: list[CustomShape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = {
        "shapes": [
            {"name": s.name, "vertices": [[x, y] for x, y in s.vertices]}
            for s in shapes
        ]
    }
    path.write_text(yaml.safe_dump(raw, sort_keys=False))


def upsert(path: Path, shape: CustomShape) -> None:
    """Save `shape`, replacing any existing custom shape of the same name."""
    remaining = [s for s in load(path) if s.name != shape.name]
    remaining.append(shape)
    save_all(path, remaining)


def delete(path: Path, name: str) -> None:
    shapes = load(path)
    remaining = [s for s in shapes if s.name != name]
    if len(remaining) == len(shapes):
        raise ValueError(f"custom shape {name!r} not found in {path}")
    save_all(path, remaining)


def get(path: Path, name: str) -> CustomShape | None:
    for s in load(path):
        if s.name == name:
            return s
    return None


def names(path: Path) -> list[str]:
    return sorted(s.name for s in load(path))


def validate_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("a shape name is required")
    if name in RESERVED_NAMES:
        raise ValueError(f"{name!r} is reserved for the built-in shape — choose a different name")


def _cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segments_intersect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
) -> bool:
    """Proper intersection test between two segments — shared endpoints (as
    between polygon edges that are adjacent, or the closing edge) are
    excluded by the caller, not by this function."""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def validate_simple_polygon(vertices: tuple[tuple[float, float], ...]) -> None:
    """Raise ValueError naming the crossing edges if any two non-adjacent
    edges intersect — the shoelace centroid and arc-length perimeter
    parametrization both silently assume a simple polygon."""
    n = len(vertices)
    if n < 3:
        raise ValueError(f"a shape needs at least 3 vertices, got {n}")

    edges = [(vertices[i], vertices[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue  # adjacent edges share an endpoint, not a crossing
            p1, p2 = edges[i]
            p3, p4 = edges[j]
            if _segments_intersect(p1, p2, p3, p4):
                raise ValueError(
                    f"edges {i} and {j} cross — the shape must be a simple "
                    "(non-self-intersecting) polygon"
                )


def resolve(name: str, shapes_file: Path | None):
    """Resolve a `--shape` name to a `Shape` or `CustomShape`. `face`/`space`
    always resolve to the built-ins regardless of shapes-file contents."""
    from nltl_viz.render import Shape  # deferred: render.py imports CustomShape from here

    if name in RESERVED_NAMES:
        return Shape(name)

    path = shapes_file if shapes_file is not None else default_shapes_path()
    custom = get(path, name)
    if custom is not None:
        return custom

    available = sorted(RESERVED_NAMES | set(names(path)))
    raise ValueError(f"shape {name!r} not found — available: {', '.join(available)}")
