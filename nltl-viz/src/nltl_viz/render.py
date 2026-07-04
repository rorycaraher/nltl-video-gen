from __future__ import annotations

import cairo
import numpy as np

from nltl_viz.preset import Preset

_BASE_HALF_FRACTION = 0.35
_FLASH_VISIBLE_THRESHOLD = 0.02


def cosine_interp_cyclic(values: np.ndarray, t: np.ndarray | float) -> np.ndarray:
    """Cyclic cosine interpolation: monotonic between control points, no overshoot,
    passes exactly through every control point at t = i/len(values)."""
    values = np.asarray(values, dtype=np.float64)
    n = len(values)
    t_arr = np.mod(np.asarray(t, dtype=np.float64), 1.0)
    idx_f = t_arr * n
    i0 = np.floor(idx_f).astype(int) % n
    i1 = (i0 + 1) % n
    u = idx_f - np.floor(idx_f)
    blend = (1.0 - np.cos(u * np.pi)) / 2.0
    return values[i0] * (1.0 - blend) + values[i1] * blend


def _polygon_vertices(size: int) -> np.ndarray:
    """The NLTL face: inscribed in a bounding square, top-left and bottom-left
    at the box's own corners, bottom-right at 2/3 width along the bottom edge,
    top-right at 2/3 width x 1/3 height (an interior point of the box, not on
    any box edge). Clockwise from top-left."""
    cx = cy = size / 2.0
    half = _BASE_HALF_FRACTION * size
    x0, y0 = cx - half, cy - half
    side = 2.0 * half
    return np.array(
        [
            (x0, y0),
            (x0 + (2.0 / 3.0) * side, y0 + (1.0 / 3.0) * side),
            (x0 + (2.0 / 3.0) * side, y0 + side),
            (x0, y0 + side),
        ],
        dtype=np.float64,
    )


def _polygon_centroid(vertices: np.ndarray) -> tuple[float, float]:
    x, y = vertices[:, 0], vertices[:, 1]
    x_next, y_next = np.roll(x, -1), np.roll(y, -1)
    cross = x * y_next - x_next * y
    area = cross.sum() / 2.0
    cx = ((x + x_next) * cross).sum() / (6.0 * area)
    cy = ((y + y_next) * cross).sum() / (6.0 * area)
    return float(cx), float(cy)


def _polygon_perimeter_points(
    t: np.ndarray, vertices: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Arc-length-proportional position on the polygon boundary at parameter
    t in [0,1) — so a control point index maps to actual distance traveled
    around the perimeter, not an equal share per edge."""
    starts = vertices
    ends = np.roll(vertices, -1, axis=0)
    edge_vectors = ends - starts
    edge_lengths = np.hypot(edge_vectors[:, 0], edge_vectors[:, 1])
    cum_lengths = np.concatenate([[0.0], np.cumsum(edge_lengths)])
    total_length = cum_lengths[-1]

    t = np.mod(np.asarray(t, dtype=np.float64), 1.0)
    target = t * total_length
    seg_idx = np.clip(
        np.searchsorted(cum_lengths, target, side="right") - 1, 0, len(vertices) - 1
    )
    local_frac = (target - cum_lengths[seg_idx]) / edge_lengths[seg_idx]

    points = starts[seg_idx] + edge_vectors[seg_idx] * local_frac[:, None]
    return points[:, 0], points[:, 1]


def deformed_polygon_points(
    band_values: np.ndarray, size: int, amplitude: float, n_samples: int = 256
) -> tuple[np.ndarray, tuple[float, float]]:
    vertices = _polygon_vertices(size)
    centroid = _polygon_centroid(vertices)
    t = np.linspace(0.0, 1.0, n_samples, endpoint=False)
    bx, by = _polygon_perimeter_points(t, vertices)
    d = cosine_interp_cyclic(band_values, t)
    scale = 1.0 + amplitude * d
    x = centroid[0] + (bx - centroid[0]) * scale
    y = centroid[1] + (by - centroid[1]) * scale
    return np.stack([x, y], axis=1), centroid


def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def draw_flash(
    ctx: cairo.Context,
    brightness: float,
    color: tuple[float, float, float],
    preset: Preset,
    size: int,
    center: tuple[float, float],
) -> None:
    if brightness <= _FLASH_VISIBLE_THRESHOLD:
        return
    cx, cy = center
    radius = preset.flash_size * 0.5 * size * (0.4 + 0.6 * min(brightness, 1.0))
    if radius <= 0:
        return
    r, g, b = (c / 255.0 for c in color)
    alpha = min(brightness, 1.0)
    gradient = cairo.RadialGradient(cx, cy, 0.0, cx, cy, radius)
    gradient.add_color_stop_rgba(0.0, r, g, b, alpha)
    gradient.add_color_stop_rgba(1.0, r, g, b, 0.0)
    ctx.set_source(gradient)
    ctx.paint()


def draw_frame(
    ctx: cairo.Context,
    points: np.ndarray,
    flash_brightness: float,
    flash_color: tuple[float, float, float],
    preset: Preset,
    size: int,
    center: tuple[float, float],
) -> None:
    bg = _hex_to_rgb01(preset.background_color)
    ctx.set_source_rgb(*bg)
    ctx.paint()

    draw_flash(ctx, flash_brightness, flash_color, preset, size, center)

    outline_rgb = _hex_to_rgb01(preset.outline_color)
    ctx.set_source_rgb(*outline_rgb)
    ctx.set_line_width(max(1.0, size * 0.004))
    ctx.move_to(points[0, 0], points[0, 1])
    for px, py in points[1:]:
        ctx.line_to(px, py)
    ctx.close_path()
    ctx.stroke()


def surface_to_rgb24(
    surface: cairo.ImageSurface, width: int, height: int
) -> np.ndarray:
    """cairo.FORMAT_ARGB32 is premultiplied, native-endian — BGRA in memory on
    little-endian — with row stride possibly padded beyond width*4."""
    surface.flush()
    stride = surface.get_stride()
    buf = np.ndarray(
        shape=(height, stride // 4, 4), dtype=np.uint8, buffer=surface.get_data()
    )
    buf = buf[:, :width, :]
    rgb = buf[:, :, [2, 1, 0]]
    return np.ascontiguousarray(rgb)


def render_frame(
    band_values: np.ndarray,
    flash_brightness: float,
    flash_color: tuple[float, float, float],
    preset: Preset,
    size: int,
) -> np.ndarray:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surface)
    points, centroid = deformed_polygon_points(
        band_values, size, preset.deform_amplitude
    )
    draw_frame(ctx, points, flash_brightness, flash_color, preset, size, centroid)
    return surface_to_rgb24(surface, size, size)
