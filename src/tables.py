"""Xuất bảng kết quả song song ``.csv`` (cho máy) và ``.md`` (cho báo cáo)."""

import csv
import math
from pathlib import Path


def _format(value):
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.4g}"
    return str(value)


def write_table(rows, columns, stem):
    """Ghi ``rows`` (list of dict) ra ``<stem>.csv`` và ``<stem>.md``.

    Returns:
        ``(csv_path, md_path)``.
    """
    stem = Path(stem)
    csv_path, md_path = stem.with_suffix(".csv"), stem.with_suffix(".md")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(c, "") for c in columns])

    lines = ["| " + " | ".join(columns) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_format(row.get(c, "")) for c in columns)
                     + " |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return csv_path, md_path
