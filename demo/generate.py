"""Generate deterministic KD-tree demo data and measured experiment artifacts.

Run from the repository root:

    python demo/generate.py

All outputs are written below ``demo/output``.  Timings come from the current
machine; they are measured rather than embedded as expected values.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time
from typing import Any, Callable, Iterable, Sequence

try:
    from .kdtree import (
        Node,
        Point,
        build,
        insert,
        nearest,
        node_to_dict,
        range_count,
        range_report,
        tree_height,
        validate_tree,
    )
except ImportError:
    from kdtree import (  # type: ignore[no-redef]
        Node,
        Point,
        build,
        insert,
        nearest,
        node_to_dict,
        range_count,
        range_report,
        tree_height,
        validate_tree,
    )


DEMO_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DEMO_DIR / "output"

FIXED_POINT_ROWS = [
    ("A", (2, 3, 4)),
    ("B", (5, 4, 2)),
    ("C", (9, 6, 7)),
    ("D", (4, 7, 9)),
    ("E", (8, 1, 5)),
    ("F", (7, 2, 8)),
    ("G", (1, 8, 6)),
    ("H", (3, 5, 1)),
    ("I", (6, 9, 3)),
    ("J", (10, 14, 12)),
    ("K", (12, 10, 15)),
    ("L", (14, 12, 10)),
    ("M", (11, 15, 13)),
    ("N", (15, 13, 11)),
    ("O", (13, 11, 14)),
]

RANGE_LOWER = (3, 2, 1)
RANGE_UPPER = (9, 7, 8)
EXPECTED_RANGE_IDS = ["B", "C", "F", "H"]
NEAREST_QUERY = (6, 3, 3)
EXPECTED_NEAREST_ID = "B"
EXPECTED_NEAREST_DISTANCE_SQUARED = 3
ALPHA = 0.75


def fixed_points() -> list[Point]:
    return [Point(point_id, coords) for point_id, coords in FIXED_POINT_ROWS]


def _brute_range(
    points: Sequence[Point],
    lower: Sequence[float | int],
    upper: Sequence[float | int],
) -> list[Point]:
    return [
        point
        for point in points
        if all(
            lower[index] <= coordinate <= upper[index]
            for index, coordinate in enumerate(point.coords)
        )
    ]


def _brute_nearest(
    points: Sequence[Point],
    query: Sequence[float | int],
) -> tuple[Point, float | int]:
    def rank(point: Point) -> tuple[float | int, str]:
        distance_squared = sum(
            (query[index] - coordinate) ** 2
            for index, coordinate in enumerate(point.coords)
        )
        return distance_squared, point.id

    return min(points, key=rank), rank(min(points, key=rank))[0]


def _make_points(
    count: int,
    dimension: int,
    rng: random.Random,
    prefix: str,
) -> list[Point]:
    return [
        Point(
            f"{prefix}{index:07d}",
            tuple(rng.random() for _ in range(dimension)),
        )
        for index in range(count)
    ]


def _make_range_queries(
    count: int,
    dimension: int,
    rng: random.Random,
    volume_fraction: float,
) -> list[tuple[tuple[float, ...], tuple[float, ...]]]:
    side = min(1.0, volume_fraction ** (1.0 / dimension))
    half_side = side / 2.0
    queries: list[tuple[tuple[float, ...], tuple[float, ...]]] = []
    for _ in range(count):
        if math.isclose(half_side, 0.5):
            center = tuple(0.5 for _ in range(dimension))
        else:
            center = tuple(
                rng.uniform(half_side, 1.0 - half_side)
                for _ in range(dimension)
            )
        lower = tuple(value - half_side for value in center)
        upper = tuple(value + half_side for value in center)
        queries.append((lower, upper))
    return queries


def _median_per_query_ms(
    operations: Sequence[Callable[[], Any]],
    repeats: int,
) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        for operation in operations:
            operation()
        elapsed = time.perf_counter() - started
        samples.append(elapsed * 1000.0 / len(operations))
    return statistics.median(samples)


def _median_build_ms(
    points: Sequence[Point],
    dimension: int,
    repeats: int,
) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        root = build(points, dimension=dimension)
        elapsed = time.perf_counter() - started
        if root is None or root.size != len(points):
            raise AssertionError("benchmark build returned an invalid root")
        samples.append(elapsed * 1000.0)
    return statistics.median(samples)


def _trace_range_visits(
    root: Node,
    queries: Iterable[tuple[Sequence[float], Sequence[float]]],
) -> tuple[list[int], list[int]]:
    visits: list[int] = []
    reported: list[int] = []
    for lower, upper in queries:
        trace: list[dict[str, Any]] = []
        result = range_report(root, lower, upper, trace=trace)
        visits.append(sum(event["type"] == "visit" for event in trace))
        reported.append(len(result))
    return visits, reported


def _trace_nearest_visits(
    root: Node,
    queries: Iterable[Sequence[float]],
) -> list[int]:
    visits: list[int] = []
    for query in queries:
        trace: list[dict[str, Any]] = []
        nearest(root, query, trace=trace)
        visits.append(sum(event["type"] == "visit" for event in trace))
    return visits


def _benchmark_case(
    *,
    point_count: int,
    dimension: int,
    range_query_count: int,
    seed: int,
    repeats: int,
    volume_fraction: float,
    suite: str,
) -> dict[str, Any]:
    rng = random.Random(seed)
    points = _make_points(
        point_count,
        dimension,
        rng,
        prefix=f"{suite}{dimension}D{point_count}-",
    )
    range_queries = _make_range_queries(
        range_query_count,
        dimension,
        rng,
        volume_fraction,
    )
    nearest_queries = [
        tuple(rng.random() for _ in range(dimension))
        for _ in range(range_query_count)
    ]

    build_ms = _median_build_ms(points, dimension, repeats=max(3, repeats))
    root = build(points, dimension=dimension)
    if root is None:
        raise AssertionError("non-empty benchmark data produced an empty tree")
    validate_tree(root)

    range_results_match = True
    count_results_match = True
    expected_range_results: list[list[Point]] = []
    for lower, upper in range_queries:
        expected = _brute_range(points, lower, upper)
        expected_range_results.append(expected)
        actual = range_report(root, lower, upper)
        if sorted(point.id for point in actual) != sorted(
            point.id for point in expected
        ):
            range_results_match = False
        if range_count(root, lower, upper) != len(expected):
            count_results_match = False

    nearest_results_match = True
    for query in nearest_queries:
        expected_point, expected_distance = _brute_nearest(points, query)
        actual_point, actual_distance = nearest(root, query)
        if (
            actual_point is None
            or actual_point.id != expected_point.id
            or not math.isclose(
                float(actual_distance),
                float(expected_distance),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            nearest_results_match = False

    kd_range_operations = [
        lambda lower=lower, upper=upper: range_report(root, lower, upper)
        for lower, upper in range_queries
    ]
    brute_range_operations = [
        lambda lower=lower, upper=upper: _brute_range(points, lower, upper)
        for lower, upper in range_queries
    ]
    kd_nearest_operations = [
        lambda query=query: nearest(root, query)
        for query in nearest_queries
    ]
    brute_nearest_operations = [
        lambda query=query: _brute_nearest(points, query)
        for query in nearest_queries
    ]

    kd_range_ms = _median_per_query_ms(kd_range_operations, repeats)
    brute_range_ms = _median_per_query_ms(brute_range_operations, repeats)
    kd_nearest_ms = _median_per_query_ms(kd_nearest_operations, repeats)
    brute_nearest_ms = _median_per_query_ms(brute_nearest_operations, repeats)

    range_visits, reported_counts = _trace_range_visits(root, range_queries)
    nearest_visits = _trace_nearest_visits(root, nearest_queries)
    expected_reported_counts = [len(result) for result in expected_range_results]
    if reported_counts != expected_reported_counts:
        range_results_match = False

    return {
        "suite": suite,
        "n": point_count,
        "d": dimension,
        "queries": range_query_count,
        "build_ms_median": round(build_ms, 6),
        "range_kd_ms_per_query": round(kd_range_ms, 6),
        "range_brute_ms_per_query": round(brute_range_ms, 6),
        "range_speedup_kd_over_brute": (
            round(brute_range_ms / kd_range_ms, 6) if kd_range_ms > 0 else None
        ),
        "range_mean_visited_nodes": round(statistics.mean(range_visits), 3),
        "range_median_visited_nodes": statistics.median(range_visits),
        "range_visited_ratio": round(statistics.mean(range_visits) / point_count, 6),
        "range_mean_reported_points": round(
            statistics.mean(reported_counts),
            3,
        ),
        "nearest_kd_ms_per_query": round(kd_nearest_ms, 6),
        "nearest_brute_ms_per_query": round(brute_nearest_ms, 6),
        "nearest_speedup_kd_over_brute": (
            round(brute_nearest_ms / kd_nearest_ms, 6)
            if kd_nearest_ms > 0
            else None
        ),
        "nearest_mean_visited_nodes": round(statistics.mean(nearest_visits), 3),
        "nearest_median_visited_nodes": statistics.median(nearest_visits),
        "nearest_visited_ratio": round(
            statistics.mean(nearest_visits) / point_count,
            6,
        ),
        "range_results_match_brute": range_results_match,
        "count_results_match_brute": count_results_match,
        "nearest_results_match_brute": nearest_results_match,
        "tree_metadata_valid": True,
    }


def run_benchmarks(quick: bool = False) -> dict[str, Any]:
    if quick:
        sizes = [100, 200, 400]
        dimensions = [2, 3, 5]
        dimension_point_count = 128
        repeats = 2
    else:
        sizes = [250, 500, 1000, 2000]
        dimensions = [2, 3, 5, 10, 20]
        dimension_point_count = 512
        repeats = 3

    by_size = [
        _benchmark_case(
            point_count=point_count,
            dimension=3,
            range_query_count=20,
            seed=42 + point_count,
            repeats=repeats,
            volume_fraction=0.015,
            suite="size",
        )
        for point_count in sizes
    ]
    by_dimension = [
        _benchmark_case(
            point_count=dimension_point_count,
            dimension=dimension,
            range_query_count=16,
            seed=4200 + dimension * 101,
            repeats=repeats,
            volume_fraction=0.08,
            suite="dimension",
        )
        for dimension in dimensions
    ]

    return {
        "metadata": {
            "measured_at_utc": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "timer": "time.perf_counter",
            "timing_statistic": (
                f"median of {repeats} repeated full query batches, "
                "reported per query"
            ),
            "visited_nodes_method": (
                "recorded in a separate trace-enabled pass; tracing is excluded "
                "from timed query batches"
            ),
            "range_timing_scope": (
                "KD-tree and brute-force timings both include result-list "
                "materialisation but neither sorts result IDs"
            ),
            "range_volume_fraction": {
                "size_experiment": 0.015,
                "dimension_experiment": 0.08,
                "note": (
                    "Each dimension's side length is volume_fraction**(1/d), "
                    "subject to the [0,1]^d domain."
                ),
            },
            "seed_policy": (
                "fixed seeds per case for reproducible datasets and queries; "
                "wall-clock timings still vary by run"
            ),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "quick_mode": quick,
        },
        "bySize": by_size,
        "byDimension": by_dimension,
    }


def build_dynamic_data() -> dict[str, Any]:
    plain_root: Node | None = None
    balanced_root: Node | None = None
    balanced_timing_root: Node | None = None
    rebuilds = 0
    plain_cumulative_ms = 0.0
    balanced_cumulative_ms = 0.0
    steps: list[dict[str, Any]] = []

    for value in range(1, 32):
        point = Point(f"T{value:02d}", (value, value, value))

        started = time.perf_counter()
        plain_root = insert(plain_root, point, rebalance=False)
        plain_cumulative_ms += (time.perf_counter() - started) * 1000.0

        trace: list[dict[str, Any]] = []
        balanced_root = insert(
            balanced_root,
            point,
            rebalance=True,
            alpha=ALPHA,
            trace=trace,
        )
        started = time.perf_counter()
        balanced_timing_root = insert(
            balanced_timing_root,
            point,
            rebalance=True,
            alpha=ALPHA,
            trace=None,
        )
        balanced_cumulative_ms += (time.perf_counter() - started) * 1000.0

        rebuild_events = [
            event for event in trace if event["type"] == "insert_rebuild"
        ]
        rebuilds += len(rebuild_events)
        steps.append(
            {
                "n": value,
                "heightPlain": tree_height(plain_root),
                "heightBalanced": tree_height(balanced_root),
                "rebuilds": rebuilds,
                "rebuiltSize": (
                    rebuild_events[-1]["size"] if rebuild_events else 0
                ),
                "plainCumulativeMs": round(plain_cumulative_ms, 6),
                "balancedCumulativeMs": round(balanced_cumulative_ms, 6),
                "plainTree": node_to_dict(plain_root),
                "balancedTree": node_to_dict(balanced_root),
            }
        )

    if (
        plain_root is None
        or balanced_root is None
        or balanced_timing_root is None
    ):
        raise AssertionError("dynamic experiment unexpectedly produced no tree")
    if node_to_dict(balanced_root) != node_to_dict(balanced_timing_root):
        raise AssertionError("timed and traced balanced trees diverged")
    return {
        "dimension": 3,
        "alpha": ALPHA,
        "sequence": "p_t=(t,t,t), t=1..31",
        "steps": steps,
        "plainTree": node_to_dict(plain_root),
        "balancedTree": node_to_dict(balanced_root),
        "validation": {
            "plain": validate_tree(plain_root),
            "balanced": validate_tree(balanced_root),
            "balancedTimingTreeMatchesDisplayed": True,
            "timingExcludesTraceRecording": True,
        },
        "totalPlainInsertMs": round(plain_cumulative_ms, 6),
        "totalBalancedInsertMs": round(balanced_cumulative_ms, 6),
    }


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty benchmark CSV")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format_number(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 100:
        return f"{value:.0f}"
    if magnitude >= 10:
        return f"{value:.1f}"
    if magnitude >= 1:
        return f"{value:.2f}"
    if magnitude == 0:
        return "0"
    return f"{value:.4f}"


def _write_svg_chart(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    x_values: Sequence[float | int],
    series: Sequence[dict[str, Any]],
    force_zero: bool = True,
) -> None:
    if len(x_values) < 2:
        raise ValueError("line charts require at least two x values")
    all_values = [
        float(value)
        for line in series
        for value in line["values"]
    ]
    minimum = 0.0 if force_zero else min(all_values)
    maximum = max(all_values)
    if math.isclose(maximum, minimum):
        maximum = minimum + 1.0
    padding = (maximum - minimum) * 0.08
    y_min = minimum
    y_max = maximum + padding

    width = 960
    height = 560
    left = 82
    right = 34
    top = 112
    bottom = 72
    plot_width = width - left - right
    plot_height = height - top - bottom

    def x_position(index: int) -> float:
        return left + plot_width * index / (len(x_values) - 1)

    def y_position(value: float) -> float:
        return top + plot_height * (1.0 - (value - y_min) / (y_max - y_min))

    elements = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" '
            'role="img">'
        ),
        f"<title>{html.escape(title)}</title>",
        (
            "<style>"
            "text{font-family:'Segoe UI',Arial,sans-serif;fill:#1f2937}"
            ".title{font-size:24px;font-weight:700}"
            ".axis{font-size:14px;fill:#374151}"
            ".tick{font-size:12px;fill:#4b5563}"
            ".grid{stroke:#d1d5db;stroke-width:1}"
            ".frame{fill:#ffffff;stroke:#9ca3af;stroke-width:1.5}"
            ".line{fill:none;stroke-width:3;stroke-linejoin:round;"
            "stroke-linecap:round}"
            "</style>"
        ),
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="{left}" y="38">{html.escape(title)}</text>',
        (
            f'<rect class="frame" x="{left}" y="{top}" '
            f'width="{plot_width}" height="{plot_height}"/>'
        ),
    ]

    y_tick_count = 5
    for tick_index in range(y_tick_count + 1):
        ratio = tick_index / y_tick_count
        value = y_min + (y_max - y_min) * ratio
        y = y_position(value)
        elements.append(
            f'<line class="grid" x1="{left}" y1="{y:.2f}" '
            f'x2="{left + plot_width}" y2="{y:.2f}"/>'
        )
        elements.append(
            f'<text class="tick" x="{left - 12}" y="{y + 4:.2f}" '
            f'text-anchor="end">{_format_number(value)}</text>'
        )

    x_stride = max(1, math.ceil(len(x_values) / 8))
    x_indices = set(range(0, len(x_values), x_stride))
    x_indices.add(len(x_values) - 1)
    for index in sorted(x_indices):
        x = x_position(index)
        elements.append(
            f'<line class="grid" x1="{x:.2f}" y1="{top}" '
            f'x2="{x:.2f}" y2="{top + plot_height}"/>'
        )
        elements.append(
            f'<text class="tick" x="{x:.2f}" y="{top + plot_height + 24}" '
            f'text-anchor="middle">{html.escape(str(x_values[index]))}</text>'
        )

    legend_x = left
    for line_index, line in enumerate(series):
        color = line["color"]
        name = html.escape(str(line["name"]))
        y = 62 + (line_index % 2) * 18
        x = legend_x + (line_index // 2) * 390
        elements.append(
            f'<line class="line" x1="{x}" y1="{y}" x2="{x + 28}" '
            f'y2="{y}" stroke="{color}"/>'
        )
        elements.append(
            f'<text class="axis" x="{x + 36}" y="{y + 4}">{name}</text>'
        )

        points = " ".join(
            f"{x_position(index):.2f},{y_position(float(value)):.2f}"
            for index, value in enumerate(line["values"])
        )
        elements.append(
            f'<polyline class="line" points="{points}" stroke="{color}"/>'
        )
        for index, value in enumerate(line["values"]):
            x = x_position(index)
            y = y_position(float(value))
            tooltip = html.escape(
                f"{line['name']} · {x_label}={x_values[index]} · "
                f"{y_label}={_format_number(float(value))}"
            )
            elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" '
                f'fill="#ffffff" stroke="{color}" stroke-width="2">'
                f"<title>{tooltip}</title></circle>"
            )

    elements.extend(
        [
            (
                f'<text class="axis" x="{left + plot_width / 2}" '
                f'y="{height - 22}" text-anchor="middle">'
                f"{html.escape(x_label)}</text>"
            ),
            (
                f'<text class="axis" transform="translate(22 '
                f'{top + plot_height / 2}) rotate(-90)" '
                'text-anchor="middle">'
                f"{html.escape(y_label)}</text>"
            ),
            "</svg>",
        ]
    )
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def _write_charts(
    output_dir: Path,
    benchmarks: dict[str, Any],
    dynamic: dict[str, Any],
) -> list[str]:
    by_size = benchmarks["bySize"]
    by_dimension = benchmarks["byDimension"]
    steps = dynamic["steps"]
    chart_names: list[str] = []

    range_time_name = "benchmark_range_time.svg"
    _write_svg_chart(
        output_dir / range_time_name,
        title="3D range query time by point count",
        x_label="Point count N",
        y_label="Milliseconds per query",
        x_values=[row["n"] for row in by_size],
        series=[
            {
                "name": "KD-tree",
                "color": "#2563eb",
                "values": [row["range_kd_ms_per_query"] for row in by_size],
            },
            {
                "name": "Brute force",
                "color": "#dc2626",
                "values": [row["range_brute_ms_per_query"] for row in by_size],
            },
        ],
    )
    chart_names.append(range_time_name)

    visit_name = "benchmark_visited_ratio.svg"
    _write_svg_chart(
        output_dir / visit_name,
        title="3D visited-node ratio by point count",
        x_label="Point count N",
        y_label="Mean visited nodes / N",
        x_values=[row["n"] for row in by_size],
        series=[
            {
                "name": "Range query",
                "color": "#0f766e",
                "values": [row["range_visited_ratio"] for row in by_size],
            },
            {
                "name": "Nearest query",
                "color": "#d97706",
                "values": [row["nearest_visited_ratio"] for row in by_size],
            },
        ],
    )
    chart_names.append(visit_name)

    dimension_name = "benchmark_dimension.svg"
    _write_svg_chart(
        output_dir / dimension_name,
        title="Range query time across dimensions",
        x_label="Dimension d",
        y_label="Milliseconds per query",
        x_values=[row["d"] for row in by_dimension],
        series=[
            {
                "name": "KD-tree range",
                "color": "#2563eb",
                "values": [row["range_kd_ms_per_query"] for row in by_dimension],
            },
            {
                "name": "Brute range",
                "color": "#dc2626",
                "values": [
                    row["range_brute_ms_per_query"] for row in by_dimension
                ],
            },
            {
                "name": "KD-tree nearest",
                "color": "#0f766e",
                "values": [
                    row["nearest_kd_ms_per_query"] for row in by_dimension
                ],
            },
            {
                "name": "Brute nearest",
                "color": "#d97706",
                "values": [
                    row["nearest_brute_ms_per_query"] for row in by_dimension
                ],
            },
        ],
    )
    chart_names.append(dimension_name)

    dynamic_name = "dynamic_height.svg"
    _write_svg_chart(
        output_dir / dynamic_name,
        title="Monotonic insertion: tree height",
        x_label="Inserted point count n",
        y_label="Height in nodes",
        x_values=[step["n"] for step in steps],
        series=[
            {
                "name": "Plain insertion",
                "color": "#dc2626",
                "values": [step["heightPlain"] for step in steps],
            },
            {
                "name": "Alpha rebuild",
                "color": "#2563eb",
                "values": [step["heightBalanced"] for step in steps],
            },
            {
                "name": "Cumulative rebuilds",
                "color": "#7c3aed",
                "values": [step["rebuilds"] for step in steps],
            },
        ],
    )
    chart_names.append(dynamic_name)
    return chart_names


def generate(quick: bool = False) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    points = fixed_points()
    build_events: list[dict[str, Any]] = []
    root = build(points, dimension=3, trace=build_events)
    if root is None:
        raise AssertionError("fixed demo build produced an empty tree")
    fixed_validation = validate_tree(root)

    range_events: list[dict[str, Any]] = []
    range_result = range_report(
        root,
        RANGE_LOWER,
        RANGE_UPPER,
        trace=range_events,
    )
    result_ids = sorted(point.id for point in range_result)
    if result_ids != EXPECTED_RANGE_IDS:
        raise AssertionError(
            f"fixed range result changed: {result_ids!r}"
        )
    reported_count = range_count(root, RANGE_LOWER, RANGE_UPPER)
    if reported_count != len(EXPECTED_RANGE_IDS):
        raise AssertionError("range count and report disagree")

    nearest_events: list[dict[str, Any]] = []
    nearest_point, nearest_distance_squared = nearest(
        root,
        NEAREST_QUERY,
        trace=nearest_events,
    )
    if nearest_point is None:
        raise AssertionError("fixed nearest query returned no point")
    if (
        nearest_point.id != EXPECTED_NEAREST_ID
        or nearest_distance_squared != EXPECTED_NEAREST_DISTANCE_SQUARED
    ):
        raise AssertionError("fixed nearest result changed")

    dynamic = build_dynamic_data()
    benchmarks = run_benchmarks(quick=quick)

    _write_csv(
        OUTPUT_DIR / "benchmarks_by_size.csv",
        benchmarks["bySize"],
    )
    _write_csv(
        OUTPUT_DIR / "benchmarks_by_dimension.csv",
        benchmarks["byDimension"],
    )
    _write_csv(
        OUTPUT_DIR / "dynamic_steps.csv",
        [
            {
                "n": step["n"],
                "heightPlain": step["heightPlain"],
                "heightBalanced": step["heightBalanced"],
                "rebuilds": step["rebuilds"],
                "rebuiltSize": step["rebuiltSize"],
                "plainCumulativeMs": step["plainCumulativeMs"],
                "balancedCumulativeMs": step["balancedCumulativeMs"],
            }
            for step in dynamic["steps"]
        ],
    )
    chart_names = _write_charts(OUTPUT_DIR, benchmarks, dynamic)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data: dict[str, Any] = {
        "meta": {
            "title": "Python KD-tree 3D demonstration",
            "schemaVersion": 1,
            "generatedAtUtc": generated_at,
            "dimension": 3,
            "pointCount": len(points),
            "buildTraversal": "preorder: root, left subtree, right subtree",
            "rangeIntervals": "closed",
            "rangeResultOrder": (
                "traversal order from range_report; no ID ordering guarantee"
            ),
            "rangeEventIds": (
                "prune_disjoint and accept_subtree expose sorted full-subtree "
                "IDs in ids and subtreeIds"
            ),
            "coordinateTieBreak": "point id (lexicographic ascending)",
            "nearestTieBreak": "smallest squared distance, then point id",
            "dynamicTreeSnapshots": (
                "Every dynamic step includes complete plainTree and "
                "balancedTree snapshots."
            ),
            "benchmarkNotice": (
                "All timing and visited-node values were measured on generation; "
                "rerun and compare using the same environment."
            ),
        },
        "points": [point.as_dict() for point in points],
        "tree": node_to_dict(root),
        "buildEvents": build_events,
        "range": {
            "lower": list(RANGE_LOWER),
            "upper": list(RANGE_UPPER),
            "closed": True,
            "result": result_ids,
            "count": reported_count,
            "events": range_events,
        },
        "nearest": {
            "query": list(NEAREST_QUERY),
            "result": nearest_point.id,
            "distanceSquared": nearest_distance_squared,
            "events": nearest_events,
        },
        "dynamic": dynamic,
        "benchmarks": benchmarks,
        "validation": {
            "fixedTree": fixed_validation,
            "fixedRangeMatchesExpected": result_ids == EXPECTED_RANGE_IDS,
            "fixedNearestMatchesExpected": (
                nearest_point.id == EXPECTED_NEAREST_ID
                and nearest_distance_squared
                == EXPECTED_NEAREST_DISTANCE_SQUARED
            ),
            "allBenchmarkResultsMatchBrute": all(
                row["range_results_match_brute"]
                and row["count_results_match_brute"]
                and row["nearest_results_match_brute"]
                for row in benchmarks["bySize"] + benchmarks["byDimension"]
            ),
        },
        "artifacts": {
            "json": "data.json",
            "javascript": "data.js",
            "csv": [
                "benchmarks_by_size.csv",
                "benchmarks_by_dimension.csv",
                "dynamic_steps.csv",
            ],
            "svg": chart_names,
        },
    }

    json_text = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    (OUTPUT_DIR / "data.json").write_text(
        json_text + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "data.js").write_text(
        f"window.KD_DATA = {json_text};\n",
        encoding="utf-8",
    )
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="use smaller benchmark sizes for a fast smoke run",
    )
    arguments = parser.parse_args(argv)

    data = generate(quick=arguments.quick)
    final_step = data["dynamic"]["steps"][-1]
    print(f"Wrote {OUTPUT_DIR / 'data.json'}")
    print(f"Wrote {OUTPUT_DIR / 'data.js'}")
    print(
        "Dynamic final state: "
        f"plain height={final_step['heightPlain']}, "
        f"balanced height={final_step['heightBalanced']}, "
        f"rebuilds={final_step['rebuilds']}"
    )
    print(
        "Validation: "
        f"fixed={data['validation']['fixedTree']['valid']}, "
        f"benchmarks_match_brute="
        f"{data['validation']['allBenchmarkResultsMatchBrute']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
