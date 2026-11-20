"""Measure separate-chaining lookup costs and compare them with theory."""

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.hash_table import HashTable


CAPACITY = 1009
OUTPUT_DIRECTORY = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Measurement:
    load_factor: float
    item_count: int
    successful_measured: float
    successful_theory: float
    unsuccessful_measured: float
    unsuccessful_theory: float


def measure() -> list[Measurement]:
    measurements = []
    key_generator = random.Random(2026)
    keys: list[str] = []
    unique_keys: HashTable[bool] = HashTable(CAPACITY)
    while len(keys) < 4 * CAPACITY:
        key = f"item-{key_generator.getrandbits(64):016x}"
        found, _, _ = unique_keys.find(key)
        if not found:
            unique_keys.set(key, True)
            keys.append(key)

    miss_generator = random.Random(2027)
    miss_keys = [
        f"absent-{miss_generator.getrandbits(64):016x}"
        for _ in range(4 * CAPACITY)
    ]
    for quarter_steps in range(1, 17):
        requested_load = quarter_steps / 4
        item_count = round(requested_load * CAPACITY)
        table: HashTable[int] = HashTable(CAPACITY)
        for index, key in enumerate(keys[:item_count]):
            table.set(key, index)

        successful_comparisons = 0
        unsuccessful_comparisons = 0
        for key, miss_key in zip(keys[:item_count], miss_keys[:item_count]):
            found, _, comparisons = table.find(key)
            if not found:
                raise RuntimeError("inserted key was not found during measurement")
            successful_comparisons += comparisons

            found, _, comparisons = table.find(miss_key)
            if found:
                raise RuntimeError("absent key unexpectedly matched during measurement")
            unsuccessful_comparisons += comparisons

        load_factor = item_count / CAPACITY
        measurements.append(
            Measurement(
                load_factor=load_factor,
                item_count=item_count,
                successful_measured=successful_comparisons / item_count,
                successful_theory=1 + load_factor / 2,
                unsuccessful_measured=unsuccessful_comparisons / item_count,
                unsuccessful_theory=load_factor,
            )
        )
    return measurements


def write_csv(measurements: list[Measurement], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "load_factor",
                "items",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for result in measurements:
            writer.writerow(
                (
                    f"{result.load_factor:.4f}",
                    result.item_count,
                    f"{result.successful_measured:.4f}",
                    f"{result.successful_theory:.4f}",
                    f"{result.unsuccessful_measured:.4f}",
                    f"{result.unsuccessful_theory:.4f}",
                )
            )


def write_svg(measurements: list[Measurement], path: Path) -> None:
    width, height = 900, 520
    left, right, top, bottom = 78, 28, 54, 72
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum = max(
        max(
            result.successful_measured,
            result.successful_theory,
            result.unsuccessful_measured,
            result.unsuccessful_theory,
        )
        for result in measurements
    )
    y_max = max(1, math.ceil(maximum * 1.1))

    def x_position(load_factor: float) -> float:
        return left + load_factor / 4 * plot_width

    def y_position(value: float) -> float:
        return top + (y_max - value) / y_max * plot_height

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="28" text-anchor="middle" font-family="sans-serif" '
        'font-size="18">Separate chaining: lookup comparisons by load factor</text>',
    ]

    for tick in range(y_max + 1):
        y = y_position(tick)
        lines.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
                f'y2="{y:.2f}" stroke="#e5e7eb"/>',
                f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12">{tick}</text>',
            )
        )
    for tick in range(5):
        x = x_position(float(tick))
        lines.extend(
            (
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
                f'y2="{height - bottom}" stroke="#f3f4f6"/>',
                f'<text x="{x:.2f}" y="{height - bottom + 22}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="12">{tick}</text>',
            )
        )

    lines.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" '
            'stroke="#111827"/>',
            f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" '
            f'y2="{height - bottom}" stroke="#111827"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 18}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14">Load factor (items / buckets)</text>',
            f'<text x="20" y="{top + plot_height / 2}" text-anchor="middle" '
            f'transform="rotate(-90 20 {top + plot_height / 2})" '
            'font-family="sans-serif" font-size="14">Average key comparisons</text>',
        )
    )

    series: tuple[tuple[str, Callable[[Measurement], float], str], ...] = (
        ("Successful measured", lambda result: result.successful_measured, "#2563eb"),
        ("Successful theory (1 + α/2)", lambda result: result.successful_theory, "#93c5fd"),
        ("Unsuccessful measured", lambda result: result.unsuccessful_measured, "#dc2626"),
        ("Unsuccessful theory (α)", lambda result: result.unsuccessful_theory, "#fca5a5"),
    )
    legend_y = top + 16
    for index, (label, get_value, color) in enumerate(series):
        points = " ".join(
            f"{x_position(result.load_factor):.2f},"
            f"{y_position(get_value(result)):.2f}"
            for result in measurements
        )
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            'stroke-width="2.5"/>'
        )
        legend_x = left + 10 + (index % 2) * 375
        y = legend_y + (index // 2) * 24
        lines.extend(
            (
                f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 24}" y2="{y}" '
                f'stroke="{color}" stroke-width="3"/>',
                f'<text x="{legend_x + 32}" y="{y + 4}" font-family="sans-serif" '
                f'font-size="12">{label}</text>',
            )
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    measurements = measure()
    csv_path = OUTPUT_DIRECTORY / "probe_results.csv"
    svg_path = OUTPUT_DIRECTORY / "probe_results.svg"
    write_csv(measurements, csv_path)
    write_svg(measurements, svg_path)

    largest_success_gap = max(
        abs(result.successful_measured - result.successful_theory)
        for result in measurements
    )
    largest_failure_gap = max(
        abs(result.unsuccessful_measured - result.unsuccessful_theory)
        for result in measurements
    )
    print(f"Wrote {csv_path} and {svg_path}")
    print(
        "Largest measured/theory gaps: "
        f"successful={largest_success_gap:.4f}, "
        f"unsuccessful={largest_failure_gap:.4f} comparisons"
    )


if __name__ == "__main__":
    main()
