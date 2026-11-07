import json, re, sys, statistics, math
from collections import defaultdict, Counter
base = sys.argv[1]
d = open(r'D:\Работа\Claude Code\perfume-finder\data.js', encoding='utf-8').read()
m = re.match(r'const B=(\[.*?\]),N=(\[.*?\]),A=(\[.*?\]),P=(\[.*?\]),F=(\[.*\]);\s*$', d, re.S)
B, N, A, P, F = (json.loads(m.group(i)) for i in range(1, 6))
matched = json.load(open(base + r'\matched.json', encoding='utf-8'))
var = json.load(open(base + r'\variants.json', encoding='utf-8'))
byid = {p[0]: p for p in P}
print('variants fetched', len(var), 'of', len({u for v in matched.values() for u in v}))

ratios = []
for u, vs in var.items():
    pr = {v: p for v, p in vs if p > 0}
    if 50.0 in pr and 100.0 in pr and pr[50.0] > 0:
        ratios.append(pr[100.0] / pr[50.0])
r = statistics.median(ratios) if ratios else 1.7
alpha = math.log(r) / math.log(2)
print('ratio 100/50', round(r, 3), 'alpha', round(alpha, 3), 'n', len(ratios))
def eq100(vol, price):
    return price * (100.0 / vol) ** alpha

res = {}
src = {}
for pid, urls in matched.items():
    got = defaultdict(list)
    for u in urls:
        for v, p in var.get(u, []):
            if p > 0 and 20 <= v <= 250:
                got[v].append(p)
    if not got:
        continue
    if 100.0 in got:
        vol = 100.0
    elif 50.0 in got:
        vol = 50.0
    else:
        vol = min(got, key=lambda v: (abs(v - 100), -len(got[v])))
    price = statistics.median(got[vol])
    res[int(pid)] = [int(round(price / 10) * 10), int(vol), 0]
    src[int(pid)] = eq100(vol, price)
c = Counter(v[1] for v in res.values())
print('direct perfumes', len(res), 'volumes', c.most_common(6))

bv = defaultdict(float); bn = Counter(); br_ = defaultdict(list)
for p in P:
    bv[p[3]] += p[7]; bn[p[3]] += 1; br_[p[3]].append(p[6] / 100)
def feats(p):
    notes = len(p[14]) // 2 + len(p[15]) // 2 + len(p[16]) // 2 + len(p[17]) // 2
    yr = min(2025, max(1940, p[4] or 2005))
    return [1.0, math.log(bv[p[3]] + 1), math.log(bn[p[3]]), math.log(p[7] + 1), p[6] / 100, (p[10] / 10) if p[10] else 3.0, (yr - 2000) / 20, 1.0 if p[5] == 1 else 0.0, 1.0 if p[5] == 2 else 0.0, math.log(notes + 1), statistics.mean(br_[p[3]])]
def solve(X, y, lam=1.0):
    k = len(X[0])
    A_ = [[sum(r_[i] * r_[j] for r_ in X) + (lam if i == j and i > 0 else 0) for j in range(k)] for i in range(k)]
    b_ = [sum(r_[i] * t for r_, t in zip(X, y)) for i in range(k)]
    for i in range(k):
        piv = max(range(i, k), key=lambda r_: abs(A_[r_][i]))
        A_[i], A_[piv] = A_[piv], A_[i]; b_[i], b_[piv] = b_[piv], b_[i]
        for r_ in range(k):
            if r_ != i:
                f = A_[r_][i] / A_[i][i]
                for cc in range(i, k):
                    A_[r_][cc] -= f * A_[i][cc]
                b_[r_] -= f * b_[i]
    return [b_[i] / A_[i][i] for i in range(k)]
tr = [byid[pid] for pid in res if pid in byid]
X = [feats(p) for p in tr]
y = [math.log(src[p[0]]) for p in tr]
w = solve(X, y)
pr = [sum(a * b for a, b in zip(w, x)) for x in X]
mu = sum(y) / len(y)
print('regression R2', round(1 - sum((a - b) ** 2 for a, b in zip(pr, y)) / sum((a - mu) ** 2 for a in y), 3))

bsrc = defaultdict(list)
for pid, v in src.items():
    bsrc[byid[pid][3]].append(v)
k1 = k2 = 0
for p in P:
    if p[0] in res:
        continue
    if p[3] in bsrc:
        res[p[0]] = [int(round(statistics.median(bsrc[p[3]]) / 100) * 100), 100, 1]
        k1 += 1
    else:
        x = feats(p)
        v = math.exp(sum(a * b for a, b in zip(w, x)))
        res[p[0]] = [int(round(min(max(v, 1200), 60000) / 100) * 100), 100, 2]
        k2 += 1
print('kind0', sum(1 for v in res.values() if v[2] == 0), 'kind1', k1, 'kind2', k2)
json.dump({str(k): v for k, v in res.items()}, open(base + r'\prices.json', 'w'), separators=(',', ':'))
for p in sorted(P, key=lambda p: -p[7])[:15]:
    print(B[p[3]], '|', p[2], '|', res[p[0]])
