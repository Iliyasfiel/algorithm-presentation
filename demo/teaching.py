"""Executable presentation snippets; tracing/validation stay in kdtree.py.

Query boxes are closed. Input dimensions and metadata must already be valid.
The helper functions below share the production implementation's geometry.
"""
from math import inf
try:
    from .kdtree import (subtree_points, _bbox_relation, _point_in_box,
                         _distance_squared, _bbox_distance_squared)
except ImportError:
    from kdtree import (subtree_points, _bbox_relation, _point_in_box,
                        _distance_squared, _bbox_distance_squared)


def relation(node, lo, hi):
    return _bbox_relation(node.bbox_min, node.bbox_max, lo, hi)


def inside(point, lo, hi):
    return _point_in_box(point, lo, hi)


def lower_bound(q, node):
    return _bbox_distance_squared(q, node.bbox_min, node.bbox_max)


def distance2(q, point):
    return _distance_squared(q, point.coords)


# PPT:report:start
def report(node, lo, hi, out):
    if node is None:
        return
    state = relation(node, lo, hi)
    if state == "disjoint":
        return
    if state == "contained":
        out.extend(subtree_points(node))
        return
    if inside(node.point, lo, hi):
        out.append(node.point)
    report(node.left, lo, hi, out)
    report(node.right, lo, hi, out)
# PPT:report:end


# PPT:count:start
def count(node, lo, hi):
    if node is None:
        return 0
    state = relation(node, lo, hi)
    if state == "disjoint":
        return 0
    if state == "contained":
        return node.size
    hit = int(inside(node.point, lo, hi))
    return (hit + count(node.left, lo, hi)
                + count(node.right, lo, hi))
# PPT:count:end


# PPT:nearest:start
def nearest(root, q):
    best = (inf, "", None)  # 距离平方、ID、点
    def visit(node):
        nonlocal best
        if node is None or lower_bound(q, node) > best[0]:
            return
        best = min(best, (distance2(q, node.point),
                          node.id, node.point))
        children = [n for n in (node.left, node.right) if n]
        children.sort(key=lambda n: (lower_bound(q, n), n.id))
        for child in children:
            visit(child)
    visit(root)
    return best[2], best[0]
# PPT:nearest:end
