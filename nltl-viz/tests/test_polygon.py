import numpy as np

from nltl_viz.render import (
    _polygon_centroid,
    _polygon_perimeter_points,
    _polygon_vertices,
    deformed_polygon_points,
)


def test_vertices_match_expected_geometry():
    size = 300
    vertices = _polygon_vertices(size)
    cx = cy = size / 2.0
    half = 0.35 * size
    x0, y0 = cx - half, cy - half
    side = 2.0 * half

    expected = np.array(
        [
            (x0, y0),
            (x0 + (2.0 / 3.0) * side, y0 + (1.0 / 3.0) * side),
            (x0 + (2.0 / 3.0) * side, y0 + side),
            (x0, y0 + side),
        ]
    )
    assert np.allclose(vertices, expected)


def test_centroid_is_within_bounding_extent():
    vertices = _polygon_vertices(300)
    cx, cy = _polygon_centroid(vertices)
    assert vertices[:, 0].min() <= cx <= vertices[:, 0].max()
    assert vertices[:, 1].min() <= cy <= vertices[:, 1].max()


def test_perimeter_point_at_t0_is_first_vertex():
    vertices = _polygon_vertices(300)
    x, y = _polygon_perimeter_points(np.array([0.0]), vertices)
    assert np.allclose([x[0], y[0]], vertices[0])


def test_perimeter_point_at_vertex_arc_length_fraction():
    vertices = _polygon_vertices(300)
    starts = vertices
    ends = np.roll(vertices, -1, axis=0)
    edge_lengths = np.hypot(*(ends - starts).T)
    total = edge_lengths.sum()

    # fraction of perimeter traveled to reach vertex index 2
    frac_to_vertex_2 = edge_lengths[:2].sum() / total
    x, y = _polygon_perimeter_points(np.array([frac_to_vertex_2]), vertices)
    assert np.allclose([x[0], y[0]], vertices[2], atol=1e-6)


def test_zero_amplitude_matches_base_perimeter():
    vertices = _polygon_vertices(300)
    band_values = np.random.default_rng(0).uniform(0, 1, size=32)
    points, _ = deformed_polygon_points(band_values, 300, amplitude=0.0)

    n_samples = 256
    t = np.linspace(0.0, 1.0, n_samples, endpoint=False)
    bx, by = _polygon_perimeter_points(t, vertices)
    base_points = np.stack([bx, by], axis=1)

    assert np.allclose(points, base_points)


def test_deformation_scales_from_returned_centroid():
    band_values = np.full(32, 1.0)  # max deformation everywhere
    points, centroid = deformed_polygon_points(band_values, 300, amplitude=0.5)
    vertices = _polygon_vertices(300)
    n_samples = 256
    t = np.linspace(0.0, 1.0, n_samples, endpoint=False)
    bx, by = _polygon_perimeter_points(t, vertices)

    expected_x = centroid[0] + (bx - centroid[0]) * 1.5
    expected_y = centroid[1] + (by - centroid[1]) * 1.5
    assert np.allclose(points[:, 0], expected_x)
    assert np.allclose(points[:, 1], expected_y)
