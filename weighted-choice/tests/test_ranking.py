import sys
import unittest
from math import isclose, nan, inf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ranking as rk


def crit(w_cost=0.4, w_ben=0.6):
    return [{"id": "price", "weight": w_cost, "is_benefit": False},
            {"id": "access", "weight": w_ben, "is_benefit": True}]


DEMO = [{"name": "A", "price": 400, "access": 8},
        {"name": "B", "price": 300, "access": 6},
        {"name": "C", "price": 500, "access": 10}]


class Tests(unittest.TestCase):
    def test_demo_order_and_scores(self):  # звичайний сценарій
        r = rk.rank_alternatives(DEMO, crit())
        self.assertEqual([x["name"] for x in r], ["C", "A", "B"])
        for x, s in zip(r, (0.6, 0.5, 0.4)):
            self.assertTrue(isclose(x["score"], s))

    def test_wrong_direction_changes_result(self):  # помилковий напрям
        wrong = [{"id": "price", "weight": 0.4, "is_benefit": True},
                 {"id": "access", "weight": 0.6, "is_benefit": True}]
        r = {x["name"]: x["score"] for x in rk.rank_alternatives(DEMO, wrong)}
        # порядок C, A, B збігається, але підсумкові числа інші: 1.0 / 0.5 / 0.0
        self.assertTrue(isclose(r["C"], 1.0))
        self.assertTrue(isclose(r["B"], 0.0))

    def test_constant_column(self):  # граничний: сталий критерій
        data = [{**a, "access": 5} for a in DEMO]
        r = rk.rank_alternatives(data, crit())
        for x in r:
            self.assertEqual(x["normalized"][1], 1.0)
        self.assertEqual([x["name"] for x in r], ["B", "A", "C"])

    def test_bad_weight_sum(self):  # помилковий: сума ваг
        with self.assertRaises(ValueError):
            rk.rank_alternatives(DEMO, crit(0.5, 0.6))

    def test_negative_weight(self):
        with self.assertRaises(ValueError):
            rk.validate_weights([1.2, -0.2])

    def test_nan_rejected_with_name(self):
        with self.assertRaises(ValueError) as cm:
            rk.normalize([1, nan, 3], True, "price")
        self.assertIn("price", str(cm.exception))
        with self.assertRaises(ValueError):
            rk.normalize([1, inf], True, "price")

    def test_duplicate_alternative_same_score(self):  # контрольний сценарій
        data = DEMO + [{"name": "A2", "price": 400, "access": 8}]
        r = {x["name"]: x["score"] for x in rk.rank_alternatives(data, crit())}
        self.assertTrue(isclose(r["A"], r["A2"]))

    def test_tie_is_shown_not_hidden(self):
        data = DEMO + [{"name": "A2", "price": 400, "access": 8}]
        ranked = rk.rank_alternatives(data, crit())
        places = dict(zip([x["name"] for x in ranked], rk.assign_places(ranked)))
        self.assertEqual(places["A"], places["A2"])
        self.assertTrue(places["A"].endswith("="))

    def test_single_criterion_change_changes_only_its_contribution(self):
        base = {x["name"]: x for x in rk.rank_alternatives(DEMO, crit())}
        data = [dict(a) for a in DEMO]
        data[0]["access"] = 9  # A: 8 -> 9, межі (6..10) не змінились
        new = {x["name"]: x for x in rk.rank_alternatives(data, crit())}
        self.assertTrue(isclose(base["A"]["contributions"][0], new["A"]["contributions"][0]))
        self.assertGreater(new["A"]["contributions"][1], base["A"]["contributions"][1])

    def test_extreme_value_shifts_scale(self):  # межі нормалізації
        data = DEMO + [{"name": "D", "price": 2000, "access": 7}]
        before = rk.normalize([400, 300, 500], False)[0]
        after = rk.rank_alternatives(data, crit())
        a = next(x for x in after if x["name"] == "A")
        self.assertNotAlmostEqual(before, a["normalized"][0])

    def test_constraints_applied_before_ranking(self):
        cons = [{"criterion": "access", "op": ">=", "value": 7, "description": "access>=7"}]
        ok, bad = rk.filter_feasible(DEMO, cons)
        self.assertEqual([a["name"] for a in ok], ["A", "C"])
        self.assertEqual(bad[0][0]["name"], "B")

    def test_reweight_sums_to_one(self):
        w = rk.reweight([0.45, 0.25, 0.30], 0, 0.6)
        self.assertTrue(isclose(sum(w), 1.0))
        self.assertTrue(isclose(w[0], 0.6))

    def test_fixed_bounds_clamped(self):
        r = rk.normalize([50, 150], True, "x", bounds=(0, 100))
        self.assertEqual(r, [0.5, 1.0])


if __name__ == "__main__":
    unittest.main()
