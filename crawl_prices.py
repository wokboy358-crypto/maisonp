import urllib.request,re,json,time,html,sys
base=sys.argv[1]
def get(u):
    for k in range(4):
        try:
            r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36','Accept-Language':'ru-RU,ru;q=0.9'})
            with urllib.request.urlopen(r,timeout=40) as f: return f.read().decode('utf-8','replace')
        except Exception as e:
            time.sleep(5*(k+1))
    return ''
items={}
empty=0
for p in range(1,330):
    h=get('https://randewoo.ru/category/parfyumeriya?page=%d'%p)
    tags=re.findall(r'<li class="products__item[^>]*>',h)
    n=0
    for t in tags:
        a={k:html.unescape(v) for k,v in re.findall(r'(data-[\w-]+)="([^"]*)"',t)}
        key=a.get('data-url') or a.get('data-real-product-id')
        if not key: continue
        items[key]={'b':a.get('data-brand',''),'n':a.get('data-name','').strip(),'t':a.get('data-product-type',''),'lo':int(a.get('data-min-price') or 0),'hi':int(a.get('data-max-price') or 0),'c':a.get('data-category',''),'u':a.get('data-url','')}
        n+=1
    print(p,n,len(items),flush=True)
    if n==0:
        empty+=1
        if empty>=3: break
    else: empty=0
    if p%20==0: json.dump(list(items.values()),open(base+'\\rw_items2.json','w',encoding='utf-8'),ensure_ascii=False)
    time.sleep(1.2)
json.dump(list(items.values()),open(base+'\\rw_items2.json','w',encoding='utf-8'),ensure_ascii=False)
print('DONE',len(items),flush=True)
