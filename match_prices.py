import json, re, sys, unicodedata, statistics, math
from collections import defaultdict, Counter
base = sys.argv[1]
d = open(r'D:\Работа\Claude Code\perfume-finder\data.js', encoding='utf-8').read()
m = re.match(r'const B=(\[.*?\]),N=(\[.*?\]),A=(\[.*?\]),P=(\[.*?\]),F=(\[.*\]);\s*$', d, re.S)
B, N, A, P, F = (json.loads(m.group(i)) for i in range(1, 6))
rw = [x for x in json.load(open(base + r'\rw_items_all.json', encoding='utf-8')) if x['hi'] > 0]
print('priced randewoo items', len(rw))

def strip(s):
    s = unicodedata.normalize('NFKD', s.lower().replace('ё', 'е'))
    return ''.join(c for c in s if not unicodedata.combining(c))
def key(s):
    return re.sub(r'[^a-zа-я0-9]', '', strip(s))
STOP = {'by', 'de', 'the', 'maison', 'parfums', 'parfum', 'perfumes', 'paris', 'london', 'new', 'york', 'eau', 'house', 'of', 'and', 'la', 'le', 'les', 'du', 'des', 'di', 'for', 'fragrances', 'beauty', 'cosmetics', 'collection'}
GEN = {'eau', 'de', 'parfum', 'toilette', 'cologne', 'edp', 'edt', 'edc', 'extrait', 'pour', 'homme', 'femme', 'for', 'him', 'her', 'men', 'women', 'man', 'woman', 'the', 'and', 'by', 'new', 'духи', 'туалетная', 'парфюмерная', 'вода', 'le', 'la', 'les', 'и', 'replica'}
def toks(s, stop=STOP):
    return frozenset(w for w in re.findall(r'[a-zа-я0-9]+', strip(s).replace('&', ' and ')) if w not in stop and not re.fullmatch(r'(19|20)\d\d', w))
CONC = {'Парфюмерная вода': ['eaudeparfum'], 'Туалетная вода': ['eaudetoilette'], 'Духи': ['parfum', 'extraitdeparfum'], 'Одеколон': ['eaudecologne'], 'Экстракт': ['extrait', 'extraitdeparfum']}
NOISE = re.compile(r'\b(eau de parfum|eau de toilette|eau de cologne|extrait de parfum|edp|edt|edc|парфюмерная вода|туалетная вода|одеколон)\b', re.I)

byid = {p[0]: p for p in P}
ds = defaultdict(lambda: defaultdict(list))
for p in P:
    ds[p[3]][key(p[2])].append(p[0])
btoks = {i: toks(b) for i, b in enumerate(B)}
bykey = defaultdict(list)
for i, b in enumerate(B):
    bykey[key(b)].append(i)
tok2b = defaultdict(set)
for i, t in btoks.items():
    for w in t:
        tok2b[w].add(i)
rb_cache = {}
def brands_for(rb):
    if rb in rb_cache:
        return rb_cache[rb]
    out = set(bykey.get(key(rb), []))
    t = toks(rb)
    if t and all(w in tok2b for w in t):
        out |= set.intersection(*[tok2b[w] for w in t])
    if len(t) > 1:
        for i, bt in btoks.items():
            if bt and bt <= t and any(len(w) >= 4 for w in bt):
                out.add(i)
    rb_cache[rb] = out
    return out

pairs = defaultdict(list)
def add(pid, x):
    pairs[pid].append(x)
brand_items = defaultdict(list)
unmatched = []
for x in rw:
    bs = brands_for(x['b'])
    for bi in bs:
        brand_items[bi].append(x)
    name = NOISE.sub(' ', x['n'])
    base_k = key(name)
    sufs = [base_k + s for s in CONC.get(x['t'], [])]
    ny = key(re.sub(r'\b(19|20)\d\d\b', '', name))
    cands = [key(x['n']), ny] + (sufs + [base_k] if x['t'] in ('Парфюмерная вода', 'Духи', 'Экстракт') else [base_k] + sufs)
    hit = None
    for bi in bs:
        for k in cands:
            if k and k in ds[bi]:
                hit = ds[bi][k]
                break
        if hit:
            break
    if hit:
        for pid in hit:
            add(pid, x)
    else:
        unmatched.append((x, bs))
n1 = len(pairs)
print('pass1 perfumes', n1)

ts = defaultdict(lambda: defaultdict(list))
for p in P:
    ts[p[3]][toks(p[2], GEN | STOP)].append(p[0])
rest = []
for x, bs in unmatched:
    t = toks(x['n'], GEN | STOP)
    hit = None
    if t:
        for bi in bs:
            if t in ts[bi]:
                hit = ts[bi][t]
                break
    if hit:
        for pid in hit:
            add(pid, x)
    else:
        rest.append((x, bs, t))
print('pass2 perfumes', len(pairs) - n1)
n2 = len(pairs)
for x, bs, t in rest:
    if not t:
        continue
    best, bj = None, 0
    for bi in bs:
        for tt, idl in ts[bi].items():
            if not tt:
                continue
            inter = len(t & tt)
            if inter == 0:
                continue
            j = inter / len(t | tt)
            if j > bj and (len(t) > 1 or tt == t):
                best, bj = idl, j
    if best and bj >= 0.75:
        for pid in best:
            add(pid, x)
print('pass3 perfumes', len(pairs) - n2, 'total direct', len(pairs), 'of', len(P))

out = {str(pid): sorted({x['u'] for x in its if x.get('u')}) for pid, its in pairs.items()}
json.dump(out, open(base + r'\matched.json', 'w'), ensure_ascii=False)
bi_out = {str(bi): sorted({x['u'] for x in its if x.get('u')}) for bi, its in brand_items.items()}
json.dump(bi_out, open(base + r'\brand_urls.json', 'w'), ensure_ascii=False)
print('matched perfumes', len(out), 'urls', len({u for v in out.values() for u in v}))