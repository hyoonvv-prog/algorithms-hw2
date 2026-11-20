"""Compare separate chaining and linear probing across load factors."""

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path

from src.hash_table import HashTable, LinearProbingHashTable


CAPACITY = 1009
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT_DIRECTORY = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ComparisonMeasurement:
    load_factor: float
    item_count: int
    chaining_success_measured: float
    chaining_success_theory: float
    chaining_unsuccessful_measured: float
    chaining_unsuccessful_theory: float
    linear_success_measured: float
    linear_success_theory: float
    linear_unsuccessful_measured: float
    linear_unsuccessful_theory: float


def measure(
    capacity: int = CAPACITY,
    load_factors: tuple[float, ...] = LOAD_FACTORS,
) -> list[ComparisonMeasurement]:
    if type(capacity) is not int:
        raise TypeError("capacity must be an integer")
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if not load_factors or any(not 0 < load < 1 for load in load_factors):
        raise ValueError("load factors must be between 0 and 1")

    key_generator = random.Random(2026)
    keys: list[str] = []
    unique_keys: HashTable[bool] = HashTable(capacity * 2)
    while len(keys) < capacity:
        key = f"item-{key_generator.getrandbits(64):016x}"
        found, _, _ = unique_keys.find(key)
        if not found:
            unique_keys.set(key, True)
            keys.append(key)

    miss_generator = random.Random(2027)
    miss_keys = [
        f"absent-{miss_generator.getrandbits(64):016x}" for _ in range(capacity)
    ]
    results = []
    for requested_load in load_factors:
        item_count = round(requested_load * capacity)
        if item_count <= 0 or item_count >= capacity:
            raise ValueError("capacity must produce a non-empty table below full load")
        selected_keys = keys[:item_count]
        chaining: HashTable[int] = HashTable(capacity)
        linear: LinearProbingHashTable[int] = LinearProbingHashTable(capacity)
        for value, key in enumerate(selected_keys):
            chaining.set(key, value)
            linear.set(key, value)

        measured = [0, 0, 0, 0]
        for key, missing_key in zip(selected_keys, miss_keys[:item_count]):
            found, _, count = chaining.find(key)
            if not found:
                raise RuntimeError("chaining table lost an inserted key")
            measured[0] += count

            found, _, count = chaining.find(missing_key)
            if found:
                raise RuntimeError("missing key unexpectedly matched in chaining table")
            measured[1] += count

            found, _, count = linear.find(key)
            if not found:
                raise RuntimeError("linear table lost an inserted key")
            measured[2] += count

            found, _, count = linear.find(missing_key)
            if found:
                raise RuntimeError("missing key unexpectedly matched in linear table")
            measured[3] += count

        load_factor = item_count / capacity
        results.append(
            ComparisonMeasurement(
                load_factor=load_factor,
                item_count=item_count,
                chaining_success_measured=measured[0] / item_count,
                chaining_success_theory=1 + load_factor / 2,
                chaining_unsuccessful_measured=measured[1] / item_count,
                chaining_unsuccessful_theory=load_factor,
                linear_success_measured=measured[2] / item_count,
                linear_success_theory=0.5 * (1 + 1 / (1 - load_factor)),
                linear_unsuccessful_measured=measured[3] / item_count,
                linear_unsuccessful_theory=0.5 * (1 + 1 / (1 - load_factor) ** 2),
            )
        )
    return results


def write_csv(measurements: list[ComparisonMeasurement], path: Path) -> None:
    columns = (
        "load_factor",
        "items",
        "chaining_success_measured",
        "chaining_success_theory",
        "chaining_unsuccessful_measured",
        "chaining_unsuccessful_theory",
        "linear_success_measured",
        "linear_success_theory",
        "linear_unsuccessful_measured",
        "linear_unsuccessful_theory",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        for result in measurements:
            writer.writerow(
                (
                    f"{result.load_factor:.4f}",
                    result.item_count,
                    f"{result.chaining_success_measured:.4f}",
                    f"{result.chaining_success_theory:.4f}",
                    f"{result.chaining_unsuccessful_measured:.4f}",
                    f"{result.chaining_unsuccessful_theory:.4f}",
                    f"{result.linear_success_measured:.4f}",
                    f"{result.linear_success_theory:.4f}",
                    f"{result.linear_unsuccessful_measured:.4f}",
                    f"{result.linear_unsuccessful_theory:.4f}",
                )
            )


def write_svg(measurements: list[ComparisonMeasurement], path: Path) -> None:
    if not measurements:
        raise ValueError("at least one measurement is required")
    width, height = 1000, 760
    panel_width, panel_height = 450, 300
    left, top = 72, 58
    x_span = 360
    y_span = 210
    panel_gap_x, panel_gap_y = 32, 54
    panels = (
        (
            "Chaining: successful",
            "chaining_success_measured",
            "chaining_success_theory",
            "#2563eb",
        ),
        (
            "Chaining: unsuccessful",
            "chaining_unsuccessful_measured",
            "chaining_unsuccessful_theory",
            "#dc2626",
        ),
        (
            "Linear probing: successful",
            "linear_success_measured",
            "linear_success_theory",
            "#059669",
        ),
        (
            "Linear probing: unsuccessful",
            "linear_unsuccessful_measured",
            "linear_unsuccessful_theory",
            "#9333ea",
        ),
    )
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="28" text-anchor="middle" font-family="sans-serif" '
        'font-size="19">Measured and theoretical lookup probes by load factor</text>',
    ]
    for panel_index, (title, measured_field, theory_field, color) in enumerate(panels):
        column, row = panel_index % 2, panel_index // 2
        origin_x = left + column * (panel_width + panel_gap_x)
        origin_y = top + row * (panel_height + panel_gap_y)
        plot_x = origin_x + 52
        plot_y = origin_y + 38
        plot_bottom = plot_y + y_span
        maximum = max(
            max(getattr(result, measured_field), getattr(result, theory_field))
            for result in measurements
        )
        y_max = max(1, math.ceil(maximum * 1.1))

        def x_position(load_factor: float) -> float:
            return plot_x + (load_factor - 0.1) / 0.8 * x_span

        def y_position(value: float) -> float:
            return plot_y + (y_max - value) / y_max * y_span

        lines.append(
            f'<text x="{origin_x + panel_width / 2}" y="{origin_y + 18}" '
            f'text-anchor="middle" font-family="sans-serif" font-size="15">{title}</text>'
        )
        for tick in range(y_max + 1):
            y = y_position(tick)
            lines.extend(
                (
                    f'<line x1="{plot_x}" y1="{y:.2f}" x2="{plot_x + x_span}" '
                    f'y2="{y:.2f}" stroke="#e5e7eb"/>',
                    f'<text x="{plot_x - 8}" y="{y + 4:.2f}" text-anchor="end" '
                    f'font-family="sans-serif" font-size="10">{tick}</text>',
                )
            )
        for load_factor in (0.1, 0.3, 0.5, 0.7, 0.9):
            x = x_position(load_factor)
            lines.append(
                f'<text x="{x:.2f}" y="{plot_bottom + 17}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="10">{load_factor:.1f}</text>'
            )
        for field, dash in ((measured_field, ""), (theory_field, "6 4")):
            points = " ".join(
                f"{x_position(result.load_factor):.2f},"
                f"{y_position(getattr(result, field)):.2f}"
                for result in measurements
            )
            dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
            lines.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" '
                f'stroke-width="2.5"{dash_attribute}/>'
            )
        lines.extend(
            (
                f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" '
                f'y2="{plot_bottom}" stroke="#111827"/>',
                f'<line x1="{plot_x}" y1="{plot_bottom}" x2="{plot_x + x_span}" '
                f'y2="{plot_bottom}" stroke="#111827"/>',
                f'<text x="{plot_x + x_span / 2}" y="{plot_bottom + 35}" '
                'text-anchor="middle" font-family="sans-serif" font-size="11">'
                "Load factor</text>",
                f'<line x1="{plot_x + 112}" y1="{plot_y + 12}" '
                f'x2="{plot_x + 136}" y2="{plot_y + 12}" stroke="{color}" '
                'stroke-width="2.5"/>',
                f'<text x="{plot_x + 142}" y="{plot_y + 16}" '
                'font-family="sans-serif" font-size="11">measured</text>',
                f'<line x1="{plot_x + 235}" y1="{plot_y + 12}" '
                f'x2="{plot_x + 259}" y2="{plot_y + 12}" stroke="{color}" '
                'stroke-width="2.5" stroke-dasharray="6 4"/>',
                f'<text x="{plot_x + 265}" y="{plot_y + 16}" '
                'font-family="sans-serif" font-size="11">theory</text>',
            )
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    measurements = measure()
    csv_path = OUTPUT_DIRECTORY / "compare_results.csv"
    svg_path = OUTPUT_DIRECTORY / "compare_results.svg"
    write_csv(measurements, csv_path)
    write_svg(measurements, svg_path)
    print(f"Wrote {csv_path} and {svg_path}")


if __name__ == "__main__":
    main()
