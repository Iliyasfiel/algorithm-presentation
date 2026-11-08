"""General-dimensional KD-tree implemented with the Python standard library.

The public functions operate on immutable :class:`Point` objects.  Coordinates
may be integers or finite floats.  A node owns one point, one splitting axis,
two child pointers, a subtree size, and a tight axis-aligned bounding box.

Determinism rules
-----------------
* Build and insertion compare ``(coordinate_on_axis, point_id)``.
* A range query uses closed intervals.
* Nearest-neighbour ties are resolved by the smallest point ID.
* Trace events contain sorted IDs, so exported data is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Iterable, Mapping, MutableSequence, Sequence


Number = int | float
Trace = MutableSequence[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class Point:
    """A uniquely identified point in a common d-dimensional space."""

    id: str
    coords: tuple[Number, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("point ID must be a non-empty string")
        coords = tuple(self.coords)
        if not coords:
            raise ValueError(f"point {self.id!r} must have at least one coordinate")
        for coordinate in coords:
            if isinstance(coordinate, bool) or not isinstance(coordinate, Real):
                raise TypeError(
                    f"point {self.id!r} has a non-numeric coordinate: "
                    f"{coordinate!r}"
                )
            if not math.isfinite(float(coordinate)):
                raise ValueError(
                    f"point {self.id!r} has a non-finite coordinate: "
                    f"{coordinate!r}"
                )
        object.__setattr__(self, "coords", coords)

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "coords": list(self.coords)}


@dataclass(slots=True)
class Node:
    """One KD-tree node.

    ``id`` is a convenience alias for ``point.id``.  Tree mutations through
    :func:`insert` update ``size`` and ``bbox`` on the changed path.  Only the
    current tree root stores the complete ID set used for O(1) duplicate checks.
    """

    point: Point
    axis: int
    left: Node | None = None
    right: Node | None = None
    size: int = 1
    bbox_min: tuple[Number, ...] = ()
    bbox_max: tuple[Number, ...] = ()
    _tree_ids: set[str] | None = None

    @property
    def id(self) -> str:
        return self.point.id

    @property
    def bbox(self) -> tuple[tuple[Number, ...], tuple[Number, ...]]:
        return self.bbox_min, self.bbox_max


def _coerce_point(value: Point | Mapping[str, Any]) -> Point:
    if isinstance(value, Point):
        return value
    if isinstance(value, Mapping):
        try:
            return Point(str(value["id"]), tuple(value["coords"]))
        except KeyError as exc:
            raise ValueError("point mappings require 'id' and 'coords'") from exc
    raise TypeError(f"expected Point or mapping, got {type(value).__name__}")


def _coerce_points(
    points: Iterable[Point | Mapping[str, Any]],
    dimension: int | None,
) -> tuple[list[Point], int | None, set[str]]:
    normalized = [_coerce_point(point) for point in points]
    inferred_dimension = len(normalized[0].coords) if normalized else dimension
    if inferred_dimension is None:
        return normalized, None, set()
    if (
        isinstance(inferred_dimension, bool)
        or not isinstance(inferred_dimension, int)
        or inferred_dimension <= 0
    ):
        raise ValueError("dimension must be a positive integer")
    if dimension is not None and dimension != inferred_dimension:
        raise ValueError(
            f"dimension mismatch: expected {dimension}, got {inferred_dimension}"
        )

    seen_ids: set[str] = set()
    for point in normalized:
        if len(point.coords) != inferred_dimension:
            raise ValueError(
                f"point {point.id!r} has {len(point.coords)} coordinates; "
                f"expected {inferred_dimension}"
            )
        if point.id in seen_ids:
            raise ValueError(f"duplicate point ID: {point.id!r}")
        seen_ids.add(point.id)
    return normalized, inferred_dimension, seen_ids


def _bbox_relation(
    bbox_min: Sequence[Number],
    bbox_max: Sequence[Number],
    lower: Sequence[Number],
    upper: Sequence[Number],
) -> str:
    disjoint = any(
        bbox_max[index] < lower[index] or bbox_min[index] > upper[index]
        for index in range(len(lower))
    )
    if disjoint:
        return "disjoint"
    contained = all(
        bbox_min[index] >= lower[index] and bbox_max[index] <= upper[index]
        for index in range(len(lower))
    )
    return "contained" if contained else "partial"


def _bbox_distance_squared(
    query: Sequence[Number],
    bbox_min: Sequence[Number],
    bbox_max: Sequence[Number],
) -> Number:
    total: Number = 0
    for index, coordinate in enumerate(query):
        low = bbox_min[index]
        high = bbox_max[index]
        if coordinate < low:
            delta = low - coordinate
            total += delta * delta
        elif coordinate > high:
            delta = coordinate - high
            total += delta * delta
    return total


def _distance_squared(
    first: Sequence[Number],
    second: Sequence[Number],
) -> Number:
    total: Number = 0
    for left, right in zip(first, second, strict=True):
        delta = left - right
        total += delta * delta
    return total


def _point_key(point: Point, axis: int) -> tuple[Number, str]:
    return point.coords[axis], point.id


def _make_node(
    point: Point,
    axis: int,
    left: Node | None,
    right: Node | None,
) -> Node:
    bbox_min = list(point.coords)
    bbox_max = list(point.coords)
    size = 1
    for child in (left, right):
        if child is None:
            continue
        size += child.size
        for index in range(len(bbox_min)):
            bbox_min[index] = min(bbox_min[index], child.bbox_min[index])
            bbox_max[index] = max(bbox_max[index], child.bbox_max[index])
    return Node(
        point=point,
        axis=axis,
        left=left,
        right=right,
        size=size,
        bbox_min=tuple(bbox_min),
        bbox_max=tuple(bbox_max),
    )


def _refresh_node(node: Node) -> None:
    bbox_min = list(node.point.coords)
    bbox_max = list(node.point.coords)
    size = 1
    for child in (node.left, node.right):
        if child is None:
            continue
        size += child.size
        for index in range(len(bbox_min)):
            bbox_min[index] = min(bbox_min[index], child.bbox_min[index])
            bbox_max[index] = max(bbox_max[index], child.bbox_max[index])
    node.size = size
    node.bbox_min = tuple(bbox_min)
    node.bbox_max = tuple(bbox_max)


def subtree_points(node: Node | None) -> list[Point]:
    """Return all points in a subtree.

    Results use preorder traversal and are not sorted by point ID.  Keeping the
    traversal order makes collection O(m) without changing rebuild semantics.
    """

    points: list[Point] = []
    stack = [] if node is None else [node]
    while stack:
        current = stack.pop()
        points.append(current.point)
        if current.right is not None:
            stack.append(current.right)
        if current.left is not None:
            stack.append(current.left)
    return points


def subtree_ids(node: Node | None) -> list[str]:
    """Return sorted IDs for deterministic trace events."""

    return sorted(point.id for point in subtree_points(node))


def tree_height(root: Node | None) -> int:
    """Return node count on the longest root-to-leaf path."""

    if root is None:
        return 0
    maximum = 0
    stack: list[tuple[Node, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        maximum = max(maximum, depth)
        if node.left is not None:
            stack.append((node.left, depth + 1))
        if node.right is not None:
            stack.append((node.right, depth + 1))
    return maximum


def tree_dimension(root: Node | None) -> int | None:
    return None if root is None else len(root.point.coords)


def _bbox_dict(node: Node) -> dict[str, list[Number]]:
    return {"min": list(node.bbox_min), "max": list(node.bbox_max)}


def _build_balanced(
    points: list[Point],
    depth: int,
    dimension: int,
    trace: Trace | None,
) -> Node | None:
    if not points:
        return None
    axis = depth % dimension
    ordered = sorted(points, key=lambda point: _point_key(point, axis))
    middle = len(ordered) // 2
    left_trace: list[dict[str, Any]] | None = [] if trace is not None else None
    right_trace: list[dict[str, Any]] | None = [] if trace is not None else None
    left = _build_balanced(
        ordered[:middle],
        depth + 1,
        dimension,
        left_trace,
    )
    right = _build_balanced(
        ordered[middle + 1 :],
        depth + 1,
        dimension,
        right_trace,
    )
    node = _make_node(ordered[middle], axis, left, right)
    if trace is not None:
        trace.append(
            {
                "type": "build",
                "nodeId": node.id,
                "point": list(node.point.coords),
                "depth": depth,
                "axis": axis,
                "size": node.size,
                "bbox": _bbox_dict(node),
                "leftChildId": None if left is None else left.id,
                "rightChildId": None if right is None else right.id,
                "leftIds": subtree_ids(left),
                "rightIds": subtree_ids(right),
            }
        )
        assert left_trace is not None and right_trace is not None
        trace.extend(left_trace)
        trace.extend(right_trace)
    return node


def build(
    points: Iterable[Point | Mapping[str, Any]],
    depth: int = 0,
    dimension: int | None = None,
    trace: Trace | None = None,
) -> Node | None:
    """Build a balanced KD-tree by median splits.

    The split axis is ``depth % dimension``.  Even-sized sets choose the
    upper-median point at index ``len(points) // 2``.  Equal coordinates are
    broken by point ID.
    """

    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        raise ValueError("depth must be a non-negative integer")
    normalized, inferred_dimension, tree_ids = _coerce_points(points, dimension)
    if not normalized:
        return None
    assert inferred_dimension is not None
    root = _build_balanced(normalized, depth, inferred_dimension, trace)
    assert root is not None
    root._tree_ids = tree_ids
    return root


def _validate_box(
    lower: Sequence[Number],
    upper: Sequence[Number],
    dimension: int,
) -> tuple[tuple[Number, ...], tuple[Number, ...]]:
    low = tuple(lower)
    high = tuple(upper)
    if len(low) != dimension or len(high) != dimension:
        raise ValueError(
            f"range bounds must both have {dimension} coordinates"
        )
    for low_value, high_value in zip(low, high):
        if low_value > high_value:
            raise ValueError("lower coordinates must not exceed upper coordinates")
    return low, high


def _validate_query(
    query: Sequence[Number],
    dimension: int,
) -> tuple[Number, ...]:
    normalized = tuple(query)
    if len(normalized) != dimension:
        raise ValueError(
            f"query must have {dimension} coordinates, got {len(normalized)}"
        )
    return normalized


def _point_in_box(
    point: Point,
    lower: Sequence[Number],
    upper: Sequence[Number],
) -> bool:
    return all(
        lower[index] <= coordinate <= upper[index]
        for index, coordinate in enumerate(point.coords)
    )


def _range_search(
    root: Node,
    lower: tuple[Number, ...],
    upper: tuple[Number, ...],
    trace: Trace | None,
    collect: bool,
) -> list[Point] | int:
    found: list[Point] = []
    count = 0

    def walk(node: Node) -> None:
        nonlocal count
        relation = _bbox_relation(
            node.bbox_min,
            node.bbox_max,
            lower,
            upper,
        )
        if trace is not None:
            trace.append(
                {
                    "type": "visit",
                    "nodeId": node.id,
                    "relation": relation,
                    "bbox": _bbox_dict(node),
                }
            )
        if relation == "disjoint":
            if trace is not None:
                stable_ids = subtree_ids(node)
                trace.append(
                    {
                        "type": "prune_disjoint",
                        "nodeId": node.id,
                        "size": node.size,
                        "bbox": _bbox_dict(node),
                        "ids": stable_ids,
                        "subtreeIds": list(stable_ids),
                    }
                )
            return
        if relation == "contained":
            if trace is not None:
                stable_ids = subtree_ids(node)
                trace.append(
                    {
                        "type": "accept_subtree",
                        "nodeId": node.id,
                        "size": node.size,
                        "bbox": _bbox_dict(node),
                        "ids": stable_ids,
                        "subtreeIds": list(stable_ids),
                    }
                )
            if collect:
                found.extend(subtree_points(node))
            else:
                count += node.size
            return

        if _point_in_box(node.point, lower, upper):
            if collect:
                found.append(node.point)
            else:
                count += 1
            if trace is not None:
                trace.append(
                    {
                        "type": "point_hit",
                        "nodeId": node.id,
                        "hitId": node.id,
                        "point": list(node.point.coords),
                    }
                )
        if node.left is not None:
            walk(node.left)
        if node.right is not None:
            walk(node.right)

    walk(root)
    return found if collect else count


def range_report(
    root: Node | None,
    lower: Sequence[Number],
    upper: Sequence[Number],
    trace: Trace | None = None,
) -> list[Point]:
    """Report all points in the closed box without promising ID order."""

    if root is None:
        return []
    dimension = len(root.point.coords)
    low, high = _validate_box(lower, upper, dimension)
    result = _range_search(root, low, high, trace, collect=True)
    assert isinstance(result, list)
    return result


def range_count(
    root: Node | None,
    lower: Sequence[Number],
    upper: Sequence[Number],
    trace: Trace | None = None,
) -> int:
    """Count points in the closed query box without reporting every point."""

    if root is None:
        return 0
    dimension = len(root.point.coords)
    low, high = _validate_box(lower, upper, dimension)
    result = _range_search(root, low, high, trace, collect=False)
    assert isinstance(result, int)
    return result


def nearest(
    root: Node | None,
    query: Sequence[Number],
    trace: Trace | None = None,
) -> tuple[Point | None, float | Number]:
    """Return ``(point, squared_distance)`` for the nearest point.

    Ties compare ``(squared distance, ID)``.  An empty tree returns
    ``(None, math.inf)``.  A subtree is pruned only when its distance lower
    bound is strictly greater than the current best distance, which preserves
    the smallest-ID tie rule.
    """

    if root is None:
        return None, math.inf
    dimension = len(root.point.coords)
    normalized_query = _validate_query(query, dimension)
    best_point: Point | None = None
    best_squared: float | Number = math.inf

    def visit(node: Node) -> None:
        nonlocal best_point, best_squared
        lower_bound = _bbox_distance_squared(
            normalized_query,
            node.bbox_min,
            node.bbox_max,
        )
        if trace is not None:
            trace.append(
                {
                    "type": "visit",
                    "nodeId": node.id,
                    "lowerBoundSquared": lower_bound,
                    "bestId": None if best_point is None else best_point.id,
                    "bestSquared": (
                        None if best_point is None else best_squared
                    ),
                    "bbox": _bbox_dict(node),
                }
            )
        if float(lower_bound) > float(best_squared):
            if trace is not None:
                stable_ids = subtree_ids(node)
                trace.append(
                    {
                        "type": "prune_distance",
                        "nodeId": node.id,
                        "lowerBoundSquared": lower_bound,
                        "bestId": None if best_point is None else best_point.id,
                        "bestSquared": best_squared,
                        "bbox": _bbox_dict(node),
                        "ids": stable_ids,
                        "subtreeIds": list(stable_ids),
                    }
                )
            return

        point_squared = _distance_squared(normalized_query, node.point.coords)
        if best_point is None or (
            point_squared,
            node.point.id,
        ) < (
            best_squared,
            best_point.id,
        ):
            best_point = node.point
            best_squared = point_squared
            if trace is not None:
                trace.append(
                    {
                        "type": "update_best",
                        "nodeId": node.id,
                        "bestId": node.point.id,
                        "bestSquared": point_squared,
                    }
                )

        children: list[tuple[float | Number, str, Node]] = []
        if node.left is not None:
            children.append(
                (
                    _bbox_distance_squared(
                        normalized_query,
                        node.left.bbox_min,
                        node.left.bbox_max,
                    ),
                    node.left.id,
                    node.left,
                )
            )
        if node.right is not None:
            children.append(
                (
                    _bbox_distance_squared(
                        normalized_query,
                        node.right.bbox_min,
                        node.right.bbox_max,
                    ),
                    node.right.id,
                    node.right,
                )
            )
        children.sort(key=lambda item: (item[0], item[1]))
        for _, _, child in children:
            visit(child)

    visit(root)
    return best_point, best_squared


def _ensure_tree_ids(root: Node) -> set[str]:
    if root._tree_ids is not None:
        return root._tree_ids

    tree_ids: set[str] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        if current.id in tree_ids:
            raise ValueError(f"duplicate point ID: {current.id!r}")
        tree_ids.add(current.id)
        if current.right is not None:
            stack.append(current.right)
        if current.left is not None:
            stack.append(current.left)
    root._tree_ids = tree_ids
    return tree_ids


def insert(
    root: Node | None,
    point: Point | Mapping[str, Any],
    depth: int = 0,
    rebalance: bool = False,
    alpha: float = 0.75,
    dimension: int | None = None,
    trace: Trace | None = None,
) -> Node:
    """Insert one point and return the resulting root.

    ``rebalance=False`` performs plain insertion.  With ``rebalance=True``,
    after updating the insertion path, the root-most subtree satisfying
    ``max(left.size, right.size) > alpha * size`` is rebuilt exactly once.
    Rebuilding starts from the original depth of that subtree, preserving the
    global ``depth % dimension`` axis convention.

    The function mutates nodes on the insertion path.  Callers should use the
    returned root even though ordinary insertion usually returns ``root``.
    """

    new_point = _coerce_point(point)
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        raise ValueError("depth must be a non-negative integer")
    if not 0.5 < float(alpha) < 1.0:
        raise ValueError("alpha must satisfy 0.5 < alpha < 1")

    inferred_dimension = (
        len(new_point.coords) if root is None else len(root.point.coords)
    )
    if dimension is not None and dimension != inferred_dimension:
        raise ValueError(
            f"dimension mismatch: expected {dimension}, "
            f"got {len(new_point.coords)}"
        )
    if len(new_point.coords) != inferred_dimension:
        raise ValueError(
            f"new point has {len(new_point.coords)} coordinates; "
            f"tree uses {inferred_dimension}"
        )
    if root is None:
        axis = depth % inferred_dimension
        leaf = _make_node(new_point, axis, None, None)
        leaf._tree_ids = {new_point.id}
        if trace is not None:
            trace.append(
                {
                    "type": "insert_attach",
                    "nodeId": leaf.id,
                    "depth": depth,
                    "axis": axis,
                }
            )
        return leaf

    tree_ids = _ensure_tree_ids(root)
    if new_point.id in tree_ids:
        raise ValueError(f"duplicate point ID: {new_point.id!r}")

    path: list[Node] = []
    parent: Node | None = None
    side: str | None = None
    current: Node | None = root
    current_depth = depth
    while current is not None:
        path.append(current)
        new_key = _point_key(new_point, current.axis)
        current_key = _point_key(current.point, current.axis)
        direction = "left" if new_key < current_key else "right"
        if trace is not None:
            trace.append(
                {
                    "type": "insert_visit",
                    "nodeId": current.id,
                    "newId": new_point.id,
                    "depth": current_depth,
                    "axis": current.axis,
                    "direction": direction,
                }
            )
        parent = current
        side = direction
        current = current.left if direction == "left" else current.right
        current_depth += 1

    assert parent is not None and side is not None
    leaf = _make_node(
        new_point,
        current_depth % inferred_dimension,
        None,
        None,
    )
    if side == "left":
        parent.left = leaf
    else:
        parent.right = leaf
    if trace is not None:
        trace.append(
            {
                "type": "insert_attach",
                "nodeId": leaf.id,
                "parentId": parent.id,
                "side": side,
                "depth": current_depth,
                "axis": leaf.axis,
            }
        )

    for node in reversed(path):
        _refresh_node(node)
    tree_ids.add(new_point.id)

    if not rebalance:
        return root

    candidate_index: int | None = None
    for index, node in enumerate(path):
        left_size = 0 if node.left is None else node.left.size
        right_size = 0 if node.right is None else node.right.size
        if max(left_size, right_size) > alpha * node.size:
            candidate_index = index
            break
    if candidate_index is None:
        return root

    candidate = path[candidate_index]
    old_height = tree_height(candidate)
    rebuild_depth = depth + candidate_index
    rebuild_points = subtree_points(candidate)
    if trace is not None:
        trace.append(
            {
                "type": "rebalance_select",
                "nodeId": candidate.id,
                "depth": rebuild_depth,
                "size": candidate.size,
                "oldHeight": old_height,
                "subtreeIds": subtree_ids(candidate),
            }
        )

    rebuild_trace: list[dict[str, Any]] | None = [] if trace is not None else None
    rebuilt = _build_balanced(
        rebuild_points,
        rebuild_depth,
        inferred_dimension,
        rebuild_trace,
    )
    assert rebuilt is not None
    if trace is not None and rebuild_trace is not None:
        for event in rebuild_trace:
            event["phase"] = "rebuild"
            event["triggerNodeId"] = candidate.id
            trace.append(event)

    if candidate_index == 0:
        candidate._tree_ids = None
        rebuilt._tree_ids = tree_ids
        new_root = rebuilt
    else:
        rebuilt_parent = path[candidate_index - 1]
        if rebuilt_parent.left is candidate:
            rebuilt_parent.left = rebuilt
        elif rebuilt_parent.right is candidate:
            rebuilt_parent.right = rebuilt
        else:
            raise AssertionError("lost rebuilt subtree connection")
        new_root = root
        for node in reversed(path[:candidate_index]):
            _refresh_node(node)

    if trace is not None:
        trace.append(
            {
                "type": "insert_rebuild",
                "nodeId": candidate.id,
                "newRootId": rebuilt.id,
                "depth": rebuild_depth,
                "size": rebuilt.size,
                "oldHeight": old_height,
                "newHeight": tree_height(rebuilt),
            }
        )
    return new_root


def node_to_dict(node: Node | None) -> dict[str, Any] | None:
    """Convert a tree to the JSON node convention used by the demo."""

    if node is None:
        return None
    return {
        "id": node.id,
        "point": list(node.point.coords),
        "axis": node.axis,
        "size": node.size,
        "bbox": _bbox_dict(node),
        "left": node_to_dict(node.left),
        "right": node_to_dict(node.right),
    }


def validate_tree(root: Node | None) -> dict[str, Any]:
    """Validate size, bbox, axes, ID uniqueness, and split ordering.

    This is intentionally active code rather than a debug-only assertion:
    generated demo data records its successful result as metadata.
    """

    if root is None:
        return {
            "valid": True,
            "size": 0,
            "height": 0,
            "dimension": None,
            "tightBoundingBoxes": True,
            "deterministicSplits": True,
        }
    dimension = len(root.point.coords)
    seen_ids: set[str] = set()

    def check(
        node: Node,
        depth: int,
    ) -> tuple[
        int,
        tuple[Number, ...],
        tuple[Number, ...],
        list[Point],
    ]:
        if node.id in seen_ids:
            raise ValueError(f"duplicate node ID: {node.id!r}")
        seen_ids.add(node.id)
        expected_axis = depth % dimension
        if node.axis != expected_axis:
            raise ValueError(
                f"node {node.id!r} has axis {node.axis}; "
                f"expected {expected_axis}"
            )

        expected_min = list(node.point.coords)
        expected_max = list(node.point.coords)
        expected_size = 1
        descendant_points: list[Point] = []
        for child, side in ((node.left, "left"), (node.right, "right")):
            if child is None:
                continue
            child_size, child_min, child_max, child_points = check(
                child,
                depth + 1,
            )
            expected_size += child_size
            descendant_points.extend(child_points)
            for index in range(dimension):
                expected_min[index] = min(expected_min[index], child_min[index])
                expected_max[index] = max(expected_max[index], child_max[index])
            parent_key = _point_key(node.point, node.axis)
            for descendant in child_points:
                child_key = _point_key(descendant, node.axis)
                if side == "left" and child_key > parent_key:
                    raise ValueError(
                        f"left subtree point {descendant.id!r} "
                        f"violates split at {node.id!r}"
                    )
                if side == "right" and child_key < parent_key:
                    raise ValueError(
                        f"right subtree point {descendant.id!r} "
                        f"violates split at {node.id!r}"
                    )

        if node.size != expected_size:
            raise ValueError(
                f"node {node.id!r} size is {node.size}; "
                f"expected {expected_size}"
            )
        if tuple(expected_min) != node.bbox_min:
            raise ValueError(f"node {node.id!r} has an incorrect bbox minimum")
        if tuple(expected_max) != node.bbox_max:
            raise ValueError(f"node {node.id!r} has an incorrect bbox maximum")
        descendant_points.append(node.point)
        return (
            expected_size,
            tuple(expected_min),
            tuple(expected_max),
            descendant_points,
        )

    total_size, _, _, _ = check(root, 0)
    if root._tree_ids is not None and root._tree_ids != seen_ids:
        raise ValueError("root tree ID registry is incorrect")
    return {
        "valid": True,
        "size": total_size,
        "height": tree_height(root),
        "dimension": dimension,
        "tightBoundingBoxes": True,
        "deterministicSplits": True,
    }


__all__ = [
    "Node",
    "Point",
    "build",
    "insert",
    "nearest",
    "node_to_dict",
    "range_count",
    "range_report",
    "subtree_ids",
    "subtree_points",
    "tree_dimension",
    "tree_height",
    "validate_tree",
]
