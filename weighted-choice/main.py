"""Рейтинг майданчиків для семінару: відбір допустимих варіантів -> нормалізація ->
зважена сума -> перевірка чутливості. Результати пишуться в results/."""
import csv
from pathlib import Path

import ranking as rk

BASE = Path(__file__).parent
criteria = rk.read_criteria(BASE / "data" / "criteria.csv")
alts = rk.read_alternatives(BASE / "data" / "alternatives.csv", criteria)
constraints = rk.read_constraints(BASE / "data" / "constraints.csv")
ids = [c["id"] for c in criteria]

print("== Вихідна таблиця ==")
print(f"{'Варіант':26}" + "".join(f"{c['id'] + ' (' + c['unit'] + ')':>16}" for c in criteria))
for a in alts:
    print(f"{a['name']:26}" + "".join(f"{a[i]:>16g}" for i in ids))

feasible, rejected = rk.filter_feasible(alts, constraints)
print("\n== Відсіяні за обмеженнями ==")
for a, why in rejected:
    print(f"{a['name']}: {'; '.join(why)}")

ranked = rk.rank_alternatives(feasible, criteria)
places = rk.assign_places(ranked)

print("\n== Нормалізована матриця (більше = краще) ==")
print(f"{'Варіант':26}" + "".join(f"{i:>12}" for i in ids))
for r in ranked:
    print(f"{r['name']:26}" + "".join(f"{x:>12.4f}" for x in r["normalized"]))

print("\n== Рейтинг ==")
print(f"{'Місце':6}{'Варіант':26}{'Бал':>8}  внески (" + ", ".join(ids) + ")")
for p, r in zip(places, ranked):
    print(f"{p:6}{r['name']:26}{r['score']:>8.4f}  " + ", ".join(f"{x:.4f}" for x in r["contributions"]))

win, runner = ranked[0], ranked[1]
print("\n== Інтерпретація ==")
for k, c in enumerate(criteria):
    d = win["contributions"][k] - runner["contributions"][k]
    print(f"{c['title']:28} внесок переможця {win['contributions'][k]:.4f} vs "
          f"{runner['contributions'][k]:.4f} (різниця {d:+.4f})")
print(f"Відрив переможця від другого місця: {win['score'] - runner['score']:.4f}")

print("\n== Чутливість: вага вартості (решта масштабується пропорційно) ==")
base_w = [c["weight"] for c in criteria]
sens = []
for w_cost in (0.1, 0.3, 0.45, 0.6, 0.8):
    w = rk.reweight(base_w, 0, w_cost)
    crit2 = [{**c, "weight": wi} for c, wi in zip(criteria, w)]
    top = rk.rank_alternatives(feasible, crit2)
    sens.append((w_cost, top[0]["name"], top[0]["score"]))
    print(f"w(cost)={w_cost:<5} -> {top[0]['name']} ({top[0]['score']:.4f})")

print("\n== Додатково: фіксовані зовнішні межі замість min/max набору ==")
bounds = {"cost": (1000, 8000), "capacity": (20, 100), "distance": (0, 5)}
fixed = rk.rank_alternatives(feasible, criteria, bounds=bounds)
for p, r in zip(rk.assign_places(fixed), fixed):
    print(f"{p:4}{r['name']:26}{r['score']:.4f}")

out = BASE / "results"
out.mkdir(exist_ok=True)
with open(out / "ranking.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["place", "name", "score"] + [f"norm_{i}" for i in ids] + [f"contrib_{i}" for i in ids])
    for p, r in zip(places, ranked):
        w.writerow([p, r["name"], f"{r['score']:.6f}"]
                   + [f"{x:.6f}" for x in r["normalized"]] + [f"{x:.6f}" for x in r["contributions"]])
print(f"\nЗбережено: {out / 'ranking.csv'}")
