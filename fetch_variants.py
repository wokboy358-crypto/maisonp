import urllib.request,re,json,time,html,sys,gzip,threading,os
from concurrent.futures import ThreadPoolExecutor
base=sys.argv[1]
need=sorted({u for v in json.load(open(base+'\\matched.json',encoding='utf-8')).values() for u in v})
cache_f=base+'\\variants.json'
cache=json.load(open(cache_f,encoding='utf-8')) if os.path.exists(cache_f) else {}
todo=[u for u in need if u not in cache]
print('need',len(need),'todo',len(todo),flush=True)
lock=threading.Lock()
VOL=re.compile(r'(\d+(?:[.,]\d+)?)\s?мл')
def get(u):
    for k in range(4):
        try:
            r=urllib.request.Request('https://randewoo.ru'+u,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36','Accept-Language':'ru-RU,ru;q=0.9','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(r,timeout=40) as f:
                b=f.read()
                if f.headers.get('Content-Encoding')=='gzip': b=gzip.decompress(b)
                return b.decode('utf-8','replace')
        except Exception as e:
            time.sleep(4*(k+1))
    return None
def work(u):
    h=get(u)
    time.sleep(0.3)
    if h is None: return
    vs=[]
    for t in re.findall(r'<li class="s-productType[^>]*>',h):
        a={k:html.unescape(v) for k,v in re.findall(r'(data-[\w-]+)="([^"]*)"',t)}
        v=a.get('data-variant','').lower();p=a.get('data-price')
        if not p or not v: continue
        if any(w in v for w in ('уценк','тестер','tester','набор','сет ','подар')): continue
        m=VOL.search(v)
        if m: vs.append([float(m.group(1).replace(',','.')),int(p)])
    with lock:
        cache[u]=vs
        if len(cache)%200==0:
            json.dump(cache,open(cache_f,'w',encoding='utf-8'),ensure_ascii=False)
            print(len(cache),flush=True)
with ThreadPoolExecutor(7) as ex:
    list(ex.map(work,todo))
json.dump(cache,open(cache_f,'w',encoding='utf-8'),ensure_ascii=False)
print('DONE',len(cache),flush=True)

