"""Бібліотека прозорого зваженого рейтингу: читання даних, перевірки,
min-max нормалізація, відбір допустимих варіантів, рейтинг із внесками."""
import csv
import operator
from math import isclose, isfinite

OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
       "<": operator.lt, "==": operator.eq}
TIE_TOL = 1e-9


def normalize(values, is_benefit, name="критерій", bounds=None, constant_score=1.0):
    """Min-max нормалізація до шкали, де більше = краще.

    bounds=(low, high) - фіксовані зовнішні межі (додаткове завдання);
    значення поза межами обрізаються до [0, 1].
    Сталий стовпець (high == low) -> constant_score для всіх (погоджене правило).
    """
    if not values:
        raise ValueError(f"Критерій '{name}': порожній список значень")
    for x in values:
        if not isfinite(x):
            raise ValueError(f"Критерій '{name}': нескінченне значення або NaN ({x})")
    low, high = bounds if bounds else (min(values), max(values))
    if high == low:
        return [constant_score for _ in values]
    if is_benefit:
        res = [(x - low) / (high - low) for x in values]
    else:
        res = [(high - x) / (high - low) for x in values]
    if bounds:
        res = [min(1.0, max(0.0, r)) for r in res]
    return res


def validate_weights(weights):
    if not weights or any((not isfinite(w)) or w < 0 for w in weights):
        raise ValueError("Некоректні ваги: потрібні скінченні невід'ємні числа")
    if not isclose(sum(weights), 1.0, abs_tol=1e-9):
        raise ValueError(f"Сума ваг має дорівнювати 1, зараз {sum(weights):.6f}")


def reweight(weights, index, new_value):
    """Змінює одну вагу, решту масштабує пропорційно, щоб сума була 1."""
    rest = sum(w for i, w in enumerate(weights) if i != index)
    if rest == 0:
        raise ValueError("Неможливо перенормувати: решта ваг нульова")
    k = (1.0 - new_value) / rest
    return [new_value if i == index else w * k for i, w in enumerate(weights)]


def read_criteria(path):
    """criteria.csv: id, title, unit, direction (cost|benefit), weight, rationale."""
    with open(path, newline="", encoding="utf-8") as f:
        crit = list(csv.DictReader(f))
    for c in crit:
        if c["direction"] not in ("cost", "benefit"):
            raise ValueError(f"Критерій {c['id']}: напрям має бути cost або benefit")
        c["weight"] = float(c["weight"])
        c["is_benefit"] = c["direction"] == "benefit"
    validate_weights([c["weight"] for c in crit])
    return crit


def read_alternatives(path, criteria):
    """alternatives.csv: name + по одній колонці на критерій (id критерію)."""
    ids = [c["id"] for c in criteria]
    alts = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = ["name"] + ids
        if header != expected:
            raise ValueError(f"Заголовок CSV {header} не збігається з очікуваним {expected}")
        for line_no, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"Рядок {line_no}: {len(row)} полів замість {len(header)}")
            alt = {"name": row[0]}
            for cid, raw in zip(ids, row[1:]):
                try:
                    val = float(raw)
                except ValueError:
                    raise ValueError(f"Рядок {line_no}, критерій '{cid}': '{raw}' не число")
                if not isfinite(val):
                    raise ValueError(f"Рядок {line_no}, критерій '{cid}': NaN/нескінченність")
                alt[cid] = val
            alts.append(alt)
    return alts


def read_constraints(path):
    """constraints.csv: criterion, op, value, description."""
    with open(path, newline="", encoding="utf-8") as f:
        cons = list(csv.DictReader(f))
    for c in cons:
        if c["op"] not in OPS:
            raise ValueError(f"Невідомий оператор {c['op']}")
        c["value"] = float(c["value"])
    return cons


def filter_feasible(alts, constraints):
    """Обов'язкові пороги перевіряються ДО рейтингу (сума допускає компенсацію)."""
    ok, rejected = [], []
    for a in alts:
        violated = [c["description"] for c in constraints
                    if not OPS[c["op"]](a[c["criterion"]], c["value"])]
        (rejected if violated else ok).append((a, violated) if violated else a)
    return ok, rejected


def rank_alternatives(alts, criteria, bounds=None):
    """Повертає список словників (name, score, normalized, contributions), відсортований
    за спаданням score. Нормалізація - по допустимих варіантах."""
    weights = [c["weight"] for c in criteria]
    validate_weights(weights)
    cols = []
    for c in criteria:
        b = bounds.get(c["id"]) if bounds else None
        cols.append(normalize([a[c["id"]] for a in alts], c["is_benefit"], c["id"], b))
    result = []
    for i, a in enumerate(alts):
        norm = [col[i] for col in cols]
        contrib = [w * r for w, r in zip(weights, norm)]
        result.append({"name": a["name"], "score": sum(contrib),
                       "normalized": norm, "contributions": contrib})
    result.sort(key=lambda r: r["score"], reverse=True)
    return result


def assign_places(ranked):
    """Нічия не ховається: однакові бали отримують однакове місце ('1=')."""
    places, i = [], 0
    while i < len(ranked):
        j = i
        while j + 1 < len(ranked) and isclose(ranked[j + 1]["score"], ranked[i]["score"],
                                              abs_tol=TIE_TOL):
            j += 1
        label = f"{i + 1}=" if j > i else str(i + 1)
        places.extend([label] * (j - i + 1))
        i = j + 1
    return places
