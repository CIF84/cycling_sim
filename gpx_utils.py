import math

import gpxpy
import numpy as np
import pandas as pd


def haversine_m(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS points in meters.
    """

    r = 6_371_000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(a))


def load_gpx(path):
    """
    Load GPX track points into a DataFrame.

    Returns:
        DataFrame with lat, lon, ele, step distance, and cumulative distance.
    """

    with open(path, "r", encoding="utf-8") as file:
        gpx = gpxpy.parse(file)

    rows = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                rows.append(
                    {
                        "lat": point.latitude,
                        "lon": point.longitude,
                        "ele": point.elevation,
                    }
                )

    if not rows:
        raise ValueError("No GPX track points found.")

    df = pd.DataFrame(rows)

    df["ele"] = (
        df["ele"]
        .interpolate()
        .bfill()
        .ffill()
    )

    distances = [0.0]

    for i in range(1, len(df)):
        distance = haversine_m(
            df.loc[i - 1, "lat"],
            df.loc[i - 1, "lon"],
            df.loc[i, "lat"],
            df.loc[i, "lon"],
        )

        distances.append(distance)

    df["step_dist_m"] = distances
    df["cum_dist_m"] = df["step_dist_m"].cumsum()

    return df


def build_segments(
    df_points,
    segment_length_m=200,
    elevation_smooth_window=7,
):
    """
    Convert GPX points into stable route segments.

    Each segment contains:
    - segment_id
    - start_km
    - end_km
    - dist_m
    - grade_pct
    - elev_delta_m
    - elev_gain_m
    - elev_loss_m
    """

    if df_points.empty:
        raise ValueError("df_points is empty.")

    df = df_points.copy()

    df["ele_smooth"] = (
        df["ele"]
        .rolling(
            window=elevation_smooth_window,
            center=True,
            min_periods=1,
        )
        .mean()
    )

    max_dist = df["cum_dist_m"].max()

    boundaries = np.arange(
        0,
        max_dist + segment_length_m,
        segment_length_m,
    )

    segments = []

    for i in range(len(boundaries) - 1):

        start_d = boundaries[i]
        end_d = boundaries[i + 1]

        chunk = df[
            (df["cum_dist_m"] >= start_d)
            & (df["cum_dist_m"] < end_d)
        ]

        if len(chunk) < 2:
            continue

        dist_m = chunk["step_dist_m"].sum()

        if dist_m <= 0:
            continue

        ele_start = chunk["ele_smooth"].iloc[0]
        ele_end = chunk["ele_smooth"].iloc[-1]

        delta_ele = ele_end - ele_start

        grade_pct = (delta_ele / dist_m) * 100

        segments.append(
            {
                "segment_id": len(segments) + 1,
                "start_km": start_d / 1000,
                "end_km": min(end_d, max_dist) / 1000,
                "dist_m": dist_m,
                "grade_pct": grade_pct,
                "elev_delta_m": delta_ele,
                "elev_gain_m": max(delta_ele, 0),
                "elev_loss_m": max(-delta_ele, 0),
            }
        )

    if not segments:
        raise ValueError("No valid route segments created.")

    return pd.DataFrame(segments)


def build_manual_route(
    distance_km,
    elevation_gain_m,
    segment_length_m=200,
):
    """
    Build a simple synthetic route with constant average gradient.

    Useful for testing without a GPX file.
    """

    total_dist_m = distance_km * 1000

    if total_dist_m <= 0:
        raise ValueError("distance_km must be greater than 0.")

    avg_grade_pct = (elevation_gain_m / total_dist_m) * 100

    n_segments = max(
        1,
        math.ceil(total_dist_m / segment_length_m),
    )

    segments = []

    for i in range(n_segments):
        start_m = i * segment_length_m
        end_m = min((i + 1) * segment_length_m, total_dist_m)
        dist_m = end_m - start_m

        elev_delta_m = dist_m * avg_grade_pct / 100

        segments.append(
            {
                "segment_id": i + 1,
                "start_km": start_m / 1000,
                "end_km": end_m / 1000,
                "dist_m": dist_m,
                "grade_pct": avg_grade_pct,
                "elev_delta_m": elev_delta_m,
                "elev_gain_m": max(elev_delta_m, 0),
                "elev_loss_m": max(-elev_delta_m, 0),
            }
        )

    return pd.DataFrame(segments)