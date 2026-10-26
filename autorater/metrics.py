"""Agreement metrics between an AutoRater and human labels. No dependencies."""
from collections import Counter


def accuracy(h, j):
    return sum(x == y for x, y in zip(h, j)) / len(h)


def cohen_kappa(h, j):
    """Agreement beyond chance. >0.8 strong, 0.6-0.8 substantial, <0.4 weak."""
    n = len(h)
    po = accuracy(h, j)
    ch, cj = Counter(h), Counter(j)
    pe = sum(ch[k] * cj[k] for k in set(h) | set(j)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def weighted_kappa(h, j, lo=1, hi=5):
    """Quadratic-weighted kappa for ordinal scores (e.g. helpfulness 1-5)."""
    k = hi - lo + 1
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(h, j):
        obs[x - lo][y - lo] += 1
    n = len(h)
    rh = [sum(r) for r in obs]
    cj = [sum(obs[r][c] for r in range(k)) for c in range(k)]
    num = den = 0.0
    for a in range(k):
        for b in range(k):
            w = ((a - b) ** 2) / ((k - 1) ** 2)
            num += w * obs[a][b]
            den += w * rh[a] * cj[b] / n
    return 1.0 if den == 0 else 1 - num / den


def _ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for t in range(i, j + 1):
            ranks[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(h, j):
    rh, rj = _ranks(h), _ranks(j)
    mh, mj = sum(rh) / len(rh), sum(rj) / len(rj)
    cov = sum((a - mh) * (b - mj) for a, b in zip(rh, rj))
    vh = sum((a - mh) ** 2 for a in rh) ** 0.5
    vj = sum((b - mj) ** 2 for b in rj) ** 0.5
    return 0.0 if vh == 0 or vj == 0 else cov / (vh * vj)


def hallucination_detection(h_grounded, j_grounded):
    """Treat 'not grounded' as the positive class: how well does the judge catch hallucinations?"""
    tp = sum(h == 0 and j == 0 for h, j in zip(h_grounded, j_grounded))
    fp = sum(h == 1 and j == 0 for h, j in zip(h_grounded, j_grounded))
    fn = sum(h == 0 and j == 1 for h, j in zip(h_grounded, j_grounded))
    tn = sum(h == 1 and j == 1 for h, j in zip(h_grounded, j_grounded))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall}
