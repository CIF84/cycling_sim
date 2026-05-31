import pandas as pd

from gpx_utils import build_segments, build_manual_route


def test_segment_builder_from_points():
    df = pd.DataFrame(
        {
            "lat": [0, 0, 0, 0],
            "lon": [0, 0.001, 0.002, 0.003],
            "ele": [100, 105, 110, 115],
            "step_dist_m": [0, 100, 100, 100],
            "cum_dist_m": [0, 100, 200, 300],
        }
    )

    segments = build_segments(
        df,
        segment_length_m=200,
        elevation_smooth_window=1,
    )

    assert len(segments) > 0
    assert "grade_pct" in segments.columns
    assert segments["dist_m"].sum() > 0


def test_manual_route_builder():
    segments = build_manual_route(
        distance_km=10,
        elevation_gain_m=200,
        segment_length_m=1000,
    )

    assert len(segments) == 10
    assert round(segments["dist_m"].sum()) == 10000
    assert round(segments["elev_gain_m"].sum()) == 200