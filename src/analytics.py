import logging

import pandas as pd

from src.pace import format_pace

logger = logging.getLogger(__name__)

# (label, canonical_miles, tolerance_miles)
# Tolerance is asymmetric in spirit but implemented as ± for simplicity.
CANONICAL_DISTANCES: list[tuple[str, float, float]] = [
    ("5K", 3.107, 0.3),
    ("10K", 6.214, 0.4),
    ("10 Mile", 10.0, 0.5),
    ("Half Marathon", 13.109, 0.6),
    ("25K", 15.534, 0.8),
    ("Marathon", 26.219, 1.0),
    ("50K", 31.069, 1.5),
    ("50 Mile", 50.0, 2.0),
    ("100K", 62.137, 3.0),
    ("100 Mile", 100.0, 5.0),
]

_KM_TO_MI = 0.621371


def _to_miles(distance: float, unit: str) -> float:
    """Convert a distance value to miles."""
    if "km" in unit.lower() or "kilometer" in unit.lower():
        return distance * _KM_TO_MI
    return distance


def _canonical_label(dist_miles: float) -> str | None:
    """Return the canonical distance label if within tolerance, else None."""
    for label, canonical, tolerance in CANONICAL_DISTANCES:
        if abs(dist_miles - canonical) <= tolerance:
            return label
    return None


def get_pr_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build a personal records table with the fastest time per canonical distance.

    Fastest is determined by min/mile pace, so GAP is not used here — raw
    effort across a standard distance is the right comparator for PRs.

    Args:
        df: Race history DataFrame from load_race_history().

    Returns:
        DataFrame with columns: Distance, Time, Pace, Date, Race Name, Type.
        One row per matched canonical distance, sorted by distance ascending.
        Empty DataFrame if no races match any canonical distance.
    """
    records = []

    for _, row in df.iterrows():
        pace = row.get("Pace")
        if not row.get("Time") or pd.isna(pace) or pace <= 0:
            continue

        try:
            dist_miles = _to_miles(float(row["Distance"]), str(row["Unit"]))
        except (ValueError, TypeError):
            continue

        label = _canonical_label(dist_miles)
        if label is None:
            continue

        order = next(i for i, d in enumerate(CANONICAL_DISTANCES) if d[0] == label)
        records.append(
            {
                "Distance": label,
                "_order": order,
                "Time": row["Time"],
                "Pace": row["Pace"],
                "Date": row["Date"],
                "Race Name": row["Name"],
                "Type": row["Type"],
            }
        )

    if not records:
        return pd.DataFrame()

    df_records = pd.DataFrame(records)

    # Keep the row with the minimum pace (fastest min/mile) per canonical distance.
    idx = df_records.groupby("Distance")["Pace"].idxmin()
    df_pr = df_records.loc[idx].copy()
    df_pr = df_pr.sort_values("_order").drop(columns=["_order"])

    df_pr["Pace"] = df_pr["Pace"].apply(format_pace)
    df_pr["Date"] = pd.to_datetime(df_pr["Date"]).dt.strftime("%Y-%m-%d")

    return df_pr[["Distance", "Time", "Pace", "Date", "Race Name", "Type"]]


def get_volume_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate race count and total miles per calendar year.

    Args:
        df: Race history DataFrame from load_race_history().

    Returns:
        DataFrame with columns: Year (str), Races, Miles. Sorted by Year ascending.
        Year is cast to string so Plotly treats it as a categorical axis,
        preserving even spacing across years with no races.
    """
    df_out = df.copy()

    def _row_miles(row: pd.Series) -> float:
        try:
            return _to_miles(float(row["Distance"]), str(row["Unit"]))
        except (ValueError, TypeError):
            return 0.0

    df_out["dist_miles"] = df_out.apply(_row_miles, axis=1)

    df_agg = (
        df_out.groupby("Year")
        .agg(Races=("Name", "count"), Miles=("dist_miles", "sum"))
        .reset_index()
        .sort_values("Year")
    )
    df_agg["Year"] = df_agg["Year"].astype(str)

    return df_agg
