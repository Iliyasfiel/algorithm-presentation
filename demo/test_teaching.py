"""Validate that the exact code embedded in slides matches full KD-tree queries."""
import random
import unittest
from demo import teaching
from demo.kdtree import Point, build, range_report, range_count, nearest


class TeachingQueriesTests(unittest.TestCase):
    def test_general_dimensions_match_full_queries(self):
        rng = random.Random(42)
        for d in (1, 3, 7):
            points = [Point(f'P{i:03}', tuple(rng.randrange(9) for _ in range(d)))
                      for i in range(60)]
            root = build(points, dimension=d)
            for _ in range(15):
                ends = [sorted((rng.randrange(10), rng.randrange(10))) for _ in range(d)]
                lo, hi = tuple(a for a, _ in ends), tuple(b for _, b in ends)
                out = []
                teaching.report(root, lo, hi, out)
                self.assertEqual(sorted(p.id for p in out),
                                 sorted(p.id for p in range_report(root, lo, hi)))
                self.assertEqual(teaching.count(root, lo, hi), range_count(root, lo, hi))
                q = tuple(rng.randrange(10) for _ in range(d))
                self.assertEqual(teaching.nearest(root, q), nearest(root, q))

    def test_duplicate_coordinates_and_closed_boundary(self):
        root = build([Point('B', (1, 1, 1)), Point('A', (1, 1, 1)),
                      Point('C', (2, 2, 2))])
        out = []
        teaching.report(root, (1, 1, 1), (1, 1, 1), out)
        self.assertEqual(sorted(p.id for p in out), ['A', 'B'])
        self.assertEqual(teaching.count(root, (1, 1, 1), (1, 1, 1)), 2)
        self.assertEqual(teaching.nearest(root, (1, 1, 1))[0].id, 'A')

    def test_empty_tree(self):
        out = []
        teaching.report(None, (0,), (1,), out)
        self.assertEqual(out, [])
        self.assertEqual(teaching.count(None, (0,), (1,)), 0)
        self.assertEqual(teaching.nearest(None, (0,)), (None, float('inf')))


if __name__ == '__main__':
    unittest.main()
