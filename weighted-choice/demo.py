"""Демонстраційний приклад: min-max нормалізація та зважений рейтинг трьох майданчиків."""
from math import isclose, isfinite

rows = [("A", 400, 8), ("B", 300, 6), ("C", 500, 10)]
weights = [0.4, 0.6]
benefit = [False, True]  # вартість - витрати, доступність - вигода


def normalize(values, is_benefit):
    if not values or not all(isfinite(x) for x in values):
        raise ValueError("Потрібні скінченні значення")
    low, high = min(values), max(values)
    if high == low:
        return [1.0 for _ in values]  # Однакова оцінка сталого критерію.
    if is_benefit:
        return [(x - low) / (high - low) for x in values]
    return [(high - x) / (high - low) for x in values]


if len(weights) != len(benefit) or any(w < 0 for w in weights):
    raise ValueError("Некоректні ваги")
if not isclose(sum(weights), 1.0):
    raise ValueError("Сума ваг має дорівнювати 1")

columns = [normalize([row[j + 1] for row in rows], direction)
           for j, direction in enumerate(benefit)]
rank = []
for i, row in enumerate(rows):
    score = sum(w * col[i] for w, col in zip(weights, columns))
    rank.append((row[0], score))

print(sorted(rank, key=lambda item: item[1], reverse=True))
assert isclose(dict(rank)["C"], 0.6)
