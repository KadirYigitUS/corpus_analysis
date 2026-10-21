"""Compact JSON serialization and downsampling helpers for SPA chart payloads."""

import math
from typing import Any

import numpy as np
import pandas as pd


def nan_to_none(val: Any) -> Any:
    """Recursively replace NaN/inf with None for clean JSON serialization."""
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, dict):
        return {k: nan_to_none(v) for k, v in val.items()}
    if isinstance(val, list):
        return [nan_to_none(v) for v in val]
    return val


def df_to_table_payload(df: pd.DataFrame, title: str = "") -> dict[str, Any]:
    """Convert pandas DataFrame into a structured TableGrid payload."""
    clean_df = df.copy()
    columns = []
    for col in clean_df.columns:
        dtype_str = str(clean_df[col].dtype)
        col_type = "int" if "int" in dtype_str else ("float" if "float" in dtype_str else "str")
        columns.append({"key": str(col), "label": str(col), "type": col_type})

    rows = []
    for _, row in clean_df.iterrows():
        rows.append({str(k): nan_to_none(v) for k, v in row.to_dict().items()})

    return {
        "title": title,
        "columns": columns,
        "rows": rows,
        "total": len(rows),
    }


def downsample_even(arr: list[Any] | np.ndarray, max_points: int) -> list[Any]:
    """Evenly downsample a 1D sequence to at most max_points."""
    n = len(arr)
    if n <= max_points:
        return list(arr)
    idx = np.linspace(0, n - 1, max_points).astype(int)
    if isinstance(arr, list):
        return [arr[i] for i in idx]
    return [arr[i] for i in idx]


def downsample_logrank(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    """Downsample rank-frequency dataframe preserving dense low ranks."""
    if len(df) <= max_points:
        return df
    dense_k = min(30, len(df))
    head_df = df.iloc[:dense_k]
    rem_df = df.iloc[dense_k:]
    rem_k = max_points - dense_k
    if len(rem_df) > rem_k and rem_k > 0:
        log_idx = np.geomspace(1, len(rem_df) - 1, rem_k).astype(int)
        log_idx = np.unique(log_idx)
        sampled_rem = rem_df.iloc[log_idx]
        return pd.concat([head_df, sampled_rem], ignore_index=True)
    return df
