"""Deterministic correctness and metadata tests for demo/kdtree.py."""

from __future__ import annotations

import math
import random
import unittest

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
        subtree_ids,
        subtree_points,
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
        subtree_ids,
        subtree_points,
        tree_height,
        validate_tree,
    )


FIXED_POINTS = [
    Point("A", (2, 3, 4)),
    Point("B", (5, 4, 2)),
    Point("C", (9, 6, 7)),
    Point("D", (4, 7, 9)),
    Point("E", (8, 1, 5)),
    Point("F", (7, 2, 8)),
    Point("G", (1, 8, 6)),
    Point("H", (3, 5, 1)),
    Point("I", (6, 9, 3)),
    Point("J", (10, 14, 12)),
    Point("K", (12, 10, 15)),
    Point("L", (14, 12, 10)),
    Point("M", (11, 15, 13)),
    Point("N", (15, 13, 11)),
    Point("O", (13, 11, 14)),
]


def brute_range_ids(
    points: list[Point],
    lower: tuple[int | float, ...],
    upper: tuple[int | float, ...],
) -> list[str]:
    return sorted(
        point.id
        for point in points
        if all(
            lower[index] <= coordinate <= upper[index]
            for index, coordinate in enumerate(point.coords)
        )
    )


def brute_nearest(
    points: list[Point],
    query: tuple[int | float, ...],
) -> tuple[str, int | float]:
    return min(
        (
            sum((query[index] - coordinate) ** 2 for index, coordinate in enumerate(point.coords)),
            point.id,
        )
        for point in points
    )[1], min(
        (
            sum((query[index] - coordinate) ** 2 for index, coordinate in enumerate(point.coords)),
            point.id,
        )
        for point in points
    )[0]


class KdTreeCorrectnessTests(unittest.TestCase):
    def test_fixed_case_tree_queries_and_trace(self) -> None:
        build_trace: list[dict[str, object]] = []
        root = build(FIXED_POINTS, dimension=3, trace=build_trace)
        self.assertIsNotNone(root)
        assert root is not None
        self.assertEqual(root._tree_ids, {point.id for point in FIXED_POINTS})
        self.assertEqual(root.id, "E")
        self.assertIsNotNone(root.left)
        self.assertIsNotNone(root.right)
        assert root.left is not None and root.right is not None
        self.assertEqual(root.left.id, "H")
        self.assertEqual(root.right.id, "L")
        self.assertEqual(len(build_trace), 15)
        self.assertEqual(build_trace[0]["type"], "build")
        self.assertEqual(build_trace[0]["nodeId"], "E")
        expected_preorder: list[str] = []

        def collect_preorder(node: Node | None) -> None:
            if node is None:
                return
            expected_preorder.append(node.id)
            collect_preorder(node.left)
            collect_preorder(node.right)

        collect_preorder(root)
        self.assertEqual(
            [event["nodeId"] for event in build_trace],
            expected_preorder,
        )
        self.assertEqual(
            [point.id for point in subtree_points(root)],
            expected_preorder,
        )
        self.assertEqual(subtree_ids(root), sorted(expected_preorder))
        all_ids = sorted(point.id for point in FIXED_POINTS)
        for event in build_trace:
            self.assertEqual(event["type"], "build")
            self.assertIn("nodeId", event)
            self.assertIn("depth", event)
            self.assertIn("axis", event)
            event_ids = (
                list(event["leftIds"]) + [event["nodeId"]] + list(event["rightIds"])
            )
            self.assertEqual(len(event_ids), len(set(event_ids)))
            self.assertEqual(len(event_ids), event["size"])
            self.assertTrue(set(event_ids).issubset(all_ids))
            if event["nodeId"] == "E":
                self.assertEqual(sorted(event_ids), all_ids)

        range_trace: list[dict[str, object]] = []
        lower = (3, 2, 1)
        upper = (9, 7, 8)
        report = range_report(root, lower, upper, range_trace)
        report_ids = [point.id for point in report]
        expected_traversal_ids = [
            point.id
            for point in subtree_points(root)
            if all(
                lower[index] <= coordinate <= upper[index]
                for index, coordinate in enumerate(point.coords)
            )
        ]
        self.assertEqual(report_ids, expected_traversal_ids)
        self.assertEqual(sorted(report_ids), ["B", "C", "F", "H"])
        self.assertEqual(range_count(root, lower, upper), 4)
        event_types = {event["type"] for event in range_trace}
        self.assertIn("visit", event_types)
        self.assertIn("prune_disjoint", event_types)
        self.assertIn("accept_subtree", event_types)
        self.assertIn("point_hit", event_types)
        for event in range_trace:
            self.assertIsInstance(event["nodeId"], str)
            if event["type"] in {"prune_disjoint", "accept_subtree"}:
                self.assertIn("ids", event)
                self.assertIn("subtreeIds", event)
                self.assertEqual(event["ids"], event["subtreeIds"])
                self.assertEqual(event["ids"], sorted(event["ids"]))
                self.assertIsInstance(event["bbox"], dict)

        nearest_trace: list[dict[str, object]] = []
        point, distance_squared = nearest(root, (6, 3, 3), nearest_trace)
        self.assertIsNotNone(point)
        assert point is not None
        self.assertEqual(point.id, "B")
        self.assertEqual(distance_squared, 3)
        self.assertTrue(
            {"visit", "update_best", "prune_distance"}.issubset(
                {event["type"] for event in nearest_trace}
            )
        )
        self.assertEqual(validate_tree(root)["size"], 15)

    def test_random_queries_match_brute_force(self) -> None:
        rng = random.Random(412)
        for dimension in (1, 2, 3, 5, 8):
            for count in (0, 1, 7, 32):
                points = [
                    Point(
                        f"D{dimension}-N{count}-{index:03d}",
                        tuple(rng.randint(-3, 3) for _ in range(dimension)),
                    )
                    for index in range(count)
                ]
                root = build(points, dimension=dimension)
                metadata = validate_tree(root)
                self.assertEqual(metadata["size"], count)
                self.assertTrue(metadata["valid"])

                boundary = points[0].coords if points else tuple(0 for _ in range(dimension))
                boxes = [
                    (boundary, boundary),
                    (
                        tuple(-10 for _ in range(dimension)),
                        tuple(10 for _ in range(dimension)),
                    ),
                    (
                        tuple(20 for _ in range(dimension)),
                        tuple(21 for _ in range(dimension)),
                    ),
                ]
                for _ in range(20):
                    lower = tuple(rng.randint(-4, 3) for _ in range(dimension))
                    upper = tuple(
                        lower[index] + rng.randint(0, 7)
                        for index in range(dimension)
                    )
                    boxes.append((lower, upper))

                for lower, upper in boxes:
                    expected = brute_range_ids(points, lower, upper)
                    report = range_report(root, lower, upper)
                    self.assertEqual(
                        sorted(point.id for point in report),
                        expected,
                    )
                    self.assertEqual(range_count(root, lower, upper), len(expected))

                for _ in range(15):
                    query = tuple(rng.randint(-5, 5) for _ in range(dimension))
                    point, distance_squared = nearest(root, query)
                    if not points:
                        self.assertIsNone(point)
                        self.assertEqual(distance_squared, math.inf)
                    else:
                        expected_id, expected_distance = brute_nearest(points, query)
                        self.assertIsNotNone(point)
                        assert point is not None
                        self.assertEqual(point.id, expected_id)
                        self.assertEqual(distance_squared, expected_distance)

    def test_duplicate_coordinates_use_smallest_id_for_ties(self) -> None:
        points = [
            Point("Z", (1, 1, 1)),
            Point("A", (1, 1, 1)),
            Point("M", (1, 1, 1)),
            Point("Q", (4, 4, 4)),
        ]
        root = build(points)
        point, distance_squared = nearest(root, (1, 1, 1))
        self.assertIsNotNone(point)
        assert point is not None
        self.assertEqual((point.id, distance_squared), ("A", 0))
        closed = range_report(root, (1, 1, 1), (1, 1, 1))
        self.assertEqual(sorted(item.id for item in closed), ["A", "M", "Z"])
        self.assertEqual(range_count(root, (1, 1, 1), (1, 1, 1)), 3)

    def test_insert_preserves_queries_and_metadata(self) -> None:
        rng = random.Random(90210)
        points = [
            Point(
                f"P{index:03d}",
                tuple(rng.randint(-4, 4) for _ in range(3)),
            )
            for index in range(35)
        ]
        root = build(points)
        self.assertEqual(root._tree_ids, {point.id for point in points})
        for index in range(35, 65):
            point = Point(
                f"P{index:03d}",
                tuple(rng.randint(-5, 5) for _ in range(3)),
            )
            points.append(point)
            insert_trace: list[dict[str, object]] = []
            root = insert(root, point, trace=insert_trace)
            self.assertEqual(root._tree_ids, {item.id for item in points})
            self.assertEqual(insert_trace[-1]["type"], "insert_attach")
            metadata = validate_tree(root)
            self.assertEqual(metadata["size"], len(points))
            self.assertTrue(metadata["valid"])

            query = tuple(rng.randint(-6, 6) for _ in range(3))
            expected_id, expected_distance = brute_nearest(points, query)
            actual, actual_distance = nearest(root, query)
            self.assertIsNotNone(actual)
            assert actual is not None
            self.assertEqual((actual.id, actual_distance), (expected_id, expected_distance))

            lower = tuple(rng.randint(-6, 0) for _ in range(3))
            upper = tuple(value + rng.randint(0, 8) for value in lower)
            expected_ids = brute_range_ids(points, lower, upper)
            self.assertEqual(
                sorted(
                    item.id for item in range_report(root, lower, upper)
                ),
                expected_ids,
            )
            self.assertEqual(range_count(root, lower, upper), len(expected_ids))

        with self.assertRaisesRegex(ValueError, "duplicate"):
            insert(root, points[-1])

    def test_root_id_registry_survives_repeated_root_rebuilds(self) -> None:
        root = None
        expected_ids: set[str] = set()
        root_rebuild_count = 0

        for value in range(1, 33):
            point = Point(f"T{value:02d}", (value, value, value))
            trace: list[dict[str, object]] = []
            root = insert(
                root,
                point,
                rebalance=True,
                alpha=0.75,
                trace=trace,
            )
            expected_ids.add(point.id)
            self.assertEqual(root._tree_ids, expected_ids)
            self.assertEqual(validate_tree(root)["size"], value)

            selected = [
                event for event in trace if event["type"] == "rebalance_select"
            ]
            if selected and selected[0]["depth"] == 0:
                root_rebuild_count += 1
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    insert(root, point, rebalance=True)
                self.assertEqual(root._tree_ids, expected_ids)
                self.assertEqual(validate_tree(root)["size"], value)

        self.assertGreaterEqual(root_rebuild_count, 3)
        stack = [root.left, root.right]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            self.assertIsNone(node._tree_ids)
            stack.extend((node.left, node.right))

    def test_local_rebuild_reduces_monotonic_chain_height(self) -> None:
        plain_root = None
        balanced_root = None
        rebuild_count = 0
        balanced_heights: list[int] = []
        plain_heights: list[int] = []
        for value in range(1, 32):
            point = Point(f"T{value:02d}", (value, value, value))
            plain_root = insert(plain_root, point)
            trace: list[dict[str, object]] = []
            balanced_root = insert(
                balanced_root,
                point,
                rebalance=True,
                alpha=0.75,
                trace=trace,
            )
            rebuild_count += sum(
                event["type"] == "insert_rebuild" for event in trace
            )
            plain_heights.append(tree_height(plain_root))
            balanced_heights.append(tree_height(balanced_root))

        self.assertEqual(plain_heights, list(range(1, 32)))
        self.assertGreater(rebuild_count, 0)
        self.assertLess(balanced_heights[-1], plain_heights[-1])
        self.assertLess(balanced_heights[-1] * 2, plain_heights[-1])
        self.assertEqual(validate_tree(plain_root)["size"], 31)
        self.assertEqual(validate_tree(balanced_root)["size"], 31)
        self.assertEqual(
            subtree_ids(plain_root),
            subtree_ids(balanced_root),
        )

        query = (16, 16, 16)
        plain_best, plain_distance = nearest(plain_root, query)
        balanced_best, balanced_distance = nearest(balanced_root, query)
        self.assertIsNotNone(plain_best)
        self.assertIsNotNone(balanced_best)
        assert plain_best is not None and balanced_best is not None
        self.assertEqual((plain_best.id, plain_distance), ("T16", 0))
        self.assertEqual((balanced_best.id, balanced_distance), ("T16", 0))

    def test_serialized_node_shape_and_validation(self) -> None:
        root = build(FIXED_POINTS)
        serialized = node_to_dict(root)
        self.assertIsNotNone(serialized)
        assert serialized is not None and root is not None
        self.assertEqual(
            set(serialized),
            {"id", "point", "axis", "size", "bbox", "left", "right"},
        )
        self.assertEqual(serialized["id"], root.id)
        self.assertEqual(serialized["point"], list(root.point.coords))
        self.assertEqual(serialized["size"], 15)

        root.size = 14
        with self.assertRaisesRegex(ValueError, "size"):
            validate_tree(root)
        root.size = 15
        root.bbox_min = (0, 0, 0)
        with self.assertRaisesRegex(ValueError, "bbox minimum"):
            validate_tree(root)

    def test_input_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build([Point("A", (1, 2)), Point("A", (3, 4))])
        with self.assertRaisesRegex(ValueError, "range bounds"):
            range_report(build(FIXED_POINTS), (1, 2), (3, 4))
        with self.assertRaisesRegex(ValueError, "lower coordinates"):
            range_count(build(FIXED_POINTS), (3, 2, 1), (2, 4, 5))
        with self.assertRaisesRegex(ValueError, "query must"):
            nearest(build(FIXED_POINTS), (1, 2))
        with self.assertRaisesRegex(ValueError, "alpha"):
            insert(build(FIXED_POINTS), Point("X", (0, 0, 0)), rebalance=True, alpha=0.5)
        self.assertEqual(subtree_points(None), [])


if __name__ == "__main__":
    unittest.main()
