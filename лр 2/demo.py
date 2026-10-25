"""Сценарний вибір: очікування, maximin і minimax regret.
Python 3.11+, без додаткових пакетів."""
from math import isclose, isfinite


def evaluate(matrix, probabilities):
    """Повертає для кожного рядка (очікування, найгірша корисність, найбільший regret)."""
    states = len(probabilities)
    if not matrix or states == 0 or any(len(row) != states for row in matrix):
        raise ValueError("Несумісні розміри матриці")
    if any(not isfinite(x) for row in matrix for x in row):
        raise ValueError("Потрібні скінченні наслідки")
    if any(not isfinite(p) or p < 0 for p in probabilities):
        raise ValueError("Некоректні ймовірності")
    if not isclose(sum(probabilities), 1.0):
        raise ValueError("Сума ймовірностей має дорівнювати 1")
    best = [max(row[j] for row in matrix) for j in range(states)]
    return [(
        sum(x * p for x, p in zip(row, probabilities)),
        min(row),
        max(top - x for top, x in zip(best, row)),
    ) for row in matrix]


def regret_table(matrix):
    best = [max(row[j] for row in matrix) for j in range(len(matrix[0]))]
    return best, [[top - x for top, x in zip(best, row)] for row in matrix]


def report(title, names, matrix, probabilities):
    print(f"\n=== {title} ===")
    res = evaluate(matrix, probabilities)
    print(f"{'Альт.':<18}{'E[u] (max)':>12}{'maximin (max)':>15}{'regret (min)':>14}")
    for n, (e, m, r) in zip(names, res):
        print(f"{n:<18}{e:>12.3f}{m:>15.3f}{r:>14.3f}")
    pick_e = names[max(range(len(res)), key=lambda i: res[i][0])]
    pick_m = names[max(range(len(res)), key=lambda i: res[i][1])]
    pick_r = names[min(range(len(res)), key=lambda i: res[i][2])]
    print(f"Очікування -> {pick_e} | maximin -> {pick_m} | minimax regret -> {pick_r}")
    return res


def expect_error(label, matrix, probs):
    try:
        evaluate(matrix, probs)
    except ValueError as e:
        print(f"[OK] {label}: ValueError('{e}')")
    else:
        raise AssertionError(f"{label}: помилку не піднято")


# ---------- 1. Демонстрація з методички ----------
names = ["A", "B"]
matrix = [[8, 6, 2], [4, 7, 9]]
probs = [0.5, 0.3, 0.2]
res = report("Демонстрація", names, matrix, probs)
assert [tuple(round(x, 3) for x in r) for r in res] == [(6.2, 2, 7), (5.9, 4, 4)]

# ---------- 2. Крок: нові ймовірності (0.2, 0.3, 0.5) ----------
res2 = report("Демо, ймовірності (0.2, 0.3, 0.5)", names, matrix, [0.2, 0.3, 0.5])
assert [r[1:] for r in res] == [r[1:] for r in res2]  # maximin і regret не змінились
print("maximin і regret не залежать від ймовірностей -> збігаються з п.1")

# ---------- 3. Третя альтернатива зі сталими наслідками ----------
names3 = ["A", "B", "C"]
matrix3 = [[8, 6, 2], [4, 7, 9], [5, 5, 5]]
best3, rt3 = regret_table(matrix3)
print("\nСтовпцеві максимуми з C:", best3, "(було [8, 7, 9])")
report("Демо з альтернативою C", names3, matrix3, probs)

# ---------- 4. Помилкові вхідні дані ----------
print("\n=== Перевірка помилок ===")
expect_error("рядок іншої довжини", [[8, 6, 2], [4, 7]], probs)
expect_error("від'ємна ймовірність", matrix, [0.6, 0.5, -0.1])
expect_error("сума 0.9", matrix, [0.5, 0.3, 0.1])
expect_error("NaN у матриці", [[8, float("nan"), 2], [4, 7, 9]], probs)

# ---------- 5. Граничний розподіл: стан має ймовірність 1 ----------
for j in range(3):
    p = [1.0 if k == j else 0.0 for k in range(3)]
    for row, (e, _, _) in zip(matrix, evaluate(matrix, p)):
        assert e == row[j]
print("\n[OK] Граничні розподіли: E[u] = наслідку в стані з p=1")

# ---------- 6. Самостійне завдання: формат семінару ----------
states = ["S1 низька залученість", "S2 середня", "S3 висока"]
alts = ["Лекція", "Семінар-дискусія", "Практикум", "Гібрид"]
M = [
    [6, 5, 4],     # Лекція: стабільна, але стеля низька
    [2, 6, 9],     # Семінар-дискусія: провал за пасивної групи
    [3, 8, 8],     # Практикум: сильний за середньої/високої залученості
    [6, 6, -1],    # Гібрид: у S3 технічні збої й хаос (-1)
]
P1 = [0.3, 0.4, 0.3]   # збалансований прогноз
P2 = [0.1, 0.3, 0.6]   # акцент на високій залученості

print("\n\n######## САМОСТІЙНЕ ЗАВДАННЯ ########")
print("Стани:", states)
best, rt = regret_table(M)
print("\nНайкращий наслідок у стані та хто його дає:")
for j, s in enumerate(states):
    winners = [alts[i] for i in range(len(M)) if M[i][j] == best[j]]
    print(f"  {s}: {best[j]} <- {', '.join(winners)}")
print("\nТаблиця regret:")
for n, r in zip(alts, rt):
    print(f"  {n:<18}{r}")
assert all(min(rt[i][j] for i in range(len(M))) == 0 for j in range(3))
assert all(x >= 0 for r in rt for x in r)
assert rt[0][0] == 0 and rt[3][0] == 0  # нічия в S1

r1 = report("Сценарій ймовірностей 1 (0.3, 0.4, 0.3)", alts, M, P1)
r2 = report("Сценарій ймовірностей 2 (0.1, 0.3, 0.6)", alts, M, P2)

for label, P, r in [("1", P1, r1), ("2", P2, r2)]:
    perfect = sum(p * b for p, b in zip(P, best))
    best_ev = max(x[0] for x in r)
    print(f"\nСценарій {label}: E[досконала інформація] = {perfect:.3f}, "
          f"найкраще E[u] без неї = {best_ev:.3f}, EVPI = {perfect - best_ev:.3f}")
