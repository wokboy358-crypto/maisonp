import csv, json, sys
from collections import Counter
csv.field_size_limit(10**9)
SRC = r'D:\Работа\mm6team\perfumes.csv'
MIN_VOTES = int(sys.argv[1]) if len(sys.argv) > 1 else 100
brands, notes, accords, pfs = {}, {}, {}, {}
PR = json.load(open(r'D:\Работа\Claude Code\perfume-finder\tools\prices.json'))

def idx(d, k):
    return d.setdefault(k, len(d))

def pairs(s, d):
    out = []
    for p in s.split('|') if s else []:
        k, _, w = p.rpartition(':')
        if not k or not w.lstrip('-').isdigit():
            k, w = p, '50'
        out += [idx(d, k.strip()), int(w)]
    return out

def num(x, m=1):
    return round(float(x) * m) if x else 0

rows, freq = [], Counter()
for r in csv.DictReader(open(SRC, encoding='utf-8')):
    if int(r['vote_count'] or 0) < MIN_VOTES:
        continue
    s = [int(r[k] or 0) for k in ('winter', 'spring', 'summer', 'autumn')]
    m = max(s)
    mask = sum(1 << i for i, v in enumerate(s) if m and v >= m * 0.6)
    d, n = int(r['day'] or 0), int(r['night'] or 0)
    dn = 1 if d > n * 1.5 else 2 if n > d * 1.5 else 0
    top, mid, base, flat = (pairs(r[k], notes) for k in ('notes_top', 'notes_middle', 'notes_base', 'notes_flat'))
    for l in (top, mid, base, flat):
        freq.update(l[0::2])
    rows.append([
        int(r['id']), r['slug'], r['name'], idx(brands, r['brand']),
        int(r['year'] or 0), {'male': 1, 'female': 2}.get(r['gender'], 0),
        num(r['rating_avg'], 100), int(r['vote_count']),
        num(r['longevity_avg'], 10), num(r['sillage_avg'], 10), num(r['price_value_avg'], 10),
        mask, dn, pairs(r['accords'], accords), top, mid, base, flat,
        [idx(pfs, x) for x in r['perfumers'].split('|') if x],
        PR.get(r['id'], [0, 0, 2]),
    ])

rows.sort(key=lambda x: -x[7])
inv = {v: k for k, v in notes.items()}
nl = list(notes)
out = 'const B=%s,N=%s,A=%s,P=%s,F=%s;' % tuple(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in (list(brands), nl, list(accords), rows, list(pfs)))
open(r'D:\Работа\Claude Code\perfume-finder\data.js', 'w', encoding='utf-8').write(out)
print(len(rows), len(brands), len(notes), len(accords), len(out) // 1024, 'KB')
print(json.dumps([inv[i] for i, _ in freq.most_common(250)], ensure_ascii=False))
print(json.dumps(list(accords), ensure_ascii=False))
