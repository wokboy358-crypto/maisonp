import json, re
src = r'D:\Работа\mm6team\perfumes.jsonl'
d = open(r'D:\Работа\Claude Code\perfume-finder\data.js', encoding='utf-8').read()
names = set(json.loads(re.search(r'N=(\[.*?\]),A=', d, re.S).group(1)))
out = {}
for line in open(src, encoding='utf-8'):
    o = json.loads(line)
    n = o.get('notes') or {}
    for t in list((n.get('tiered') or {}).values()) + [n.get('flat') or []]:
        for x in t:
            if x['name'] in names and x.get('image_id') and x['name'] not in out:
                out[x['name']] = x['image_id']
open(r'D:\Работа\Claude Code\perfume-finder\notes_img.js', 'w', encoding='utf-8').write('const NI=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';')
print(len(names), len(out))
