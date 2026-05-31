import matplotlib.pyplot as plt


def plot_route_profile(sim_df, output_path="route_profile.png"):
    """
    Save route profile chart with speed and power overlay.
    """

    if sim_df.empty:
        raise ValueError("sim_df is empty.")

    df = sim_df.copy()
    df["relative_elevation_m"] = df["elev_delta_m"].cumsum()
    df["relative_elevation_m"] = (
        df["relative_elevation_m"] - df["relative_elevation_m"].min()
    )

    x = df["cum_dist_km"]

    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.plot(x, df["relative_elevation_m"], label="Elevation")
    ax1.fill_between(x, df["relative_elevation_m"], alpha=0.15)
    ax1.set_xlabel("Distance (km)")
    ax1.set_ylabel("Relative elevation (m)")
    ax1.set_title("Route Profile")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, df["speed_kmh"], linestyle="--", label="Speed (km/h)")
    ax2.plot(x, df["target_power_w"], linestyle=":", label="Power (W)")
    ax2.set_ylabel("Speed / Power")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path


def plot_fueling_curves(sim_df, output_path="fueling_curves.png"):
    """
    Save cumulative carbs, sweat, and sodium chart.
    """

    if sim_df.empty:
        raise ValueError("sim_df is empty.")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(sim_df["cum_time_h"], sim_df["cum_carbs_g"], label="Carbs (g)")
    ax.plot(sim_df["cum_time_h"], sim_df["cum_sweat_l"], label="Sweat (L)")
    ax.plot(sim_df["cum_time_h"], sim_df["cum_sodium_mg"], label="Sodium (mg)")

    ax.set_xlabel("Time (h)")
    ax.set_title("Cumulative Fueling / Hydration Load")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path