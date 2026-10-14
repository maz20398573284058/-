# Матриця рішення: вибір місця для навчального семінару
# Метод: min-max нормалізація + зважена сума
import csv
from math import isclose, isfinite

# ---------- Налаштування (контракт) ----------
criteria = ["cost_uah", "walk_min", "tech_score_1_5"]  # колонки CSV
benefit = [False, False, True]   # False = витрата, True = вигода
weights = [0.4, 0.2, 0.4]        # ціна, дорога, техніка
max_cost = 8000                  # обмеження 1: бюджет не більше 8000 грн
min_capacity = 40                # обмеження 2: не менше 40 місць
constant_score = 1.0             # правило для сталого стовпця


def load_rows(path):
    """Читає CSV і перевіряє, що всі числа скінченні."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line_no, rec in enumerate(csv.DictReader(f), start=2):
            for col in criteria + ["capacity_people"]:
                value = float(rec[col])
                if not isfinite(value):
                    raise ValueError(f"Рядок {line_no}: '{col}' не є скінченним числом")
                rec[col] = value
            rows.append(rec)
    return rows


def check_weights(w):
    if len(w) != len(benefit) or any(x < 0 for x in w):
        raise ValueError("Некоректні ваги")
    if not isclose(sum(w), 1.0):
        raise ValueError(f"Сума ваг = {sum(w)}, а має дорівнювати 1")


def normalize(values, is_benefit, bounds=None):
    if not values or not all(isfinite(x) for x in values):
        raise ValueError("Потрібні скінченні значення")
    low, high = bounds if bounds else (min(values), max(values))
    if high == low:
        return [constant_score for _ in values]  # сталий критерій
    if is_benefit:
        return [(x - low) / (high - low) for x in values]
    return [(high - x) / (high - low) for x in values]


def rank(rows, w, bounds=None):
    """Повертає список (назва, підсумок, внески по критеріях), від кращого."""
    check_weights(w)
    columns = [normalize([row[c] for row in rows], direction,
                         bounds[c] if bounds else None)
               for c, direction in zip(criteria, benefit)]
    result = []
    for i, row in enumerate(rows):
        parts = [wj * col[i] for wj, col in zip(w, columns)]
        result.append((row["name"], sum(parts), parts))
    return sorted(result, key=lambda item: item[1], reverse=True)


def show(title, result):
    print(f"\n=== {title} ===")
    best = result[0][1]
    for name, score, parts in result:
        tie = "  <- НІЧИЯ з лідером" if name != result[0][0] and isclose(score, best) else ""
        print(f"{name:<26}{score:.4f}  ({' + '.join(f'{p:.3f}' for p in parts)}){tie}")


# ---------- 1. Дані та обмеження (до рейтингу) ----------
all_rows = load_rows("venues.csv")
rows = []
for r in all_rows:
    if r["cost_uah"] > max_cost:
        print(f"Відсіяно: {r['name']} (ціна {r['cost_uah']:g} > {max_cost})")
    elif r["capacity_people"] < min_capacity:
        print(f"Відсіяно: {r['name']} (місць {r['capacity_people']:g} < {min_capacity})")
    else:
        rows.append(r)

# ---------- 2. Базовий рейтинг ----------
base = rank(rows, weights)
show("Базовий рейтинг, ваги 0.4 / 0.2 / 0.4", base)
assert base[0][0] == "Зал бібліотеки" and isclose(base[0][1], 0.65)

# ---------- 3. Ручна перевірка одного рядка (Актовий зал) ----------
print("\nРучна перевірка: Актовий зал")
hall = rows[0]
for c, direction, w in zip(criteria, benefit, weights):
    col = [r[c] for r in rows]
    low, high = min(col), max(col)
    score = (hall[c] - low) / (high - low) if direction else (high - hall[c]) / (high - low)
    print(f"  {c}: x={hall[c]:g}, min={low:g}, max={high:g}, "
          f"норм={score:.3f}, вага={w}, внесок={w * score:.3f}")

# ---------- 4. Сталий критерій ----------
flat = [dict(r, tech_score_1_5=4.0) for r in rows]
show("Сталий критерій: техніка = 4 у всіх", rank(flat, weights))

# ---------- 5. Помилкова сума ваг ----------
try:
    rank(rows, [0.5, 0.3, 0.4])
except ValueError as e:
    print(f"\nПомилку суми ваг виявлено: {e}")

# ---------- 6. Нічия: копія альтернативи ----------
copy_rows = rows + [dict(rows[0], name="Актовий зал (копія)")]
tie_result = rank(copy_rows, weights)
show("Копія альтернативи (очікується нічия)", tie_result)
scores = {name: score for name, score, _ in tie_result}
assert isclose(scores["Актовий зал"], scores["Актовий зал (копія)"])

# ---------- 7. Зміна одного критерію всередині діапазону ----------
changed = [dict(r) for r in rows]
for r in changed:
    if r["name"] == "Лабораторна аудиторія":
        r["walk_min"] = 11.0   # було 12; min=5 і max=15 не змінились
before = next(p for n, s, p in base if n == "Лабораторна аудиторія")
after = next(p for n, s, p in rank(changed, weights) if n == "Лабораторна аудиторія")
print(f"\nЛабораторна, дорога 12 -> 11 хв: внески {[round(x, 3) for x in before]} -> {[round(x, 3) for x in after]}")
assert before[0] == after[0] and before[2] == after[2] and after[1] > before[1]

# ---------- 8. Чутливість до ваги ціни ----------
print("\nЧутливість до ваги ціни (інші ваги нормуються пропорційно):")
for wc in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    k = (1 - wc) / (1 - weights[0])
    w = [wc, weights[1] * k, weights[2] * k]
    res = rank(rows, w)
    print(f"  вага ціни {wc}: лідер {res[0][0]} ({res[0][1]:.3f}), другий {res[1][0]} ({res[1][1]:.3f})")

# ---------- 9. Вплив крайнього значення ----------
extra = rows + [{"name": "Дорогий, але допустимий", "cost_uah": 7900.0,
                 "walk_min": 12.0, "tech_score_1_5": 3.0, "capacity_people": 60.0}]
show("Додано варіант з ціною 7900 (змінились межі min-max)", rank(extra, weights))

# ---------- 10. Додатково: фіксовані зовнішні межі ----------
fixed = {"cost_uah": (0, 8000), "walk_min": (0, 30), "tech_score_1_5": (1, 5)}
show("Фіксовані межі (ціна 0-8000, дорога 0-30, техніка 1-5)", rank(rows, weights, fixed))
show("Фіксовані межі + додатковий варіант", rank(extra, weights, fixed))
