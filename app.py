import re, threading, time
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
MAX_NUM, STOP_MISSES = 30000, 60
cache, jobs = {}, {}

@app.get("/health")
def health():
    return "ok"

def clean(v):
    return re.sub(r"\s*[\d.,]+%$", "", v.strip())

def fetch(slug, n):
    try:
        r = requests.get(f"https://t.me/nft/{slug}-{n}", timeout=15)
        if r.status_code != 200:
            return None
        rows = {}
        for tr in BeautifulSoup(r.text, "html.parser").select("tr"):
            th, td = tr.find("th"), tr.find("td")
            if th and td:
                rows[th.get_text(strip=True).lower()] = td
        if "backdrop" not in rows:
            return None
        o = rows.get("owner")
        a = o.find("a") if o else None
        return {"num": n, "backdrop": clean(rows["backdrop"].get_text()),
                "model": clean(rows["model"].get_text()) if "model" in rows else "",
                "owner": a["href"] if a else ""}
    except Exception:
        return None

def scan(slug):
    data = cache.setdefault(slug, {})
    jobs[slug] = {"done": False, "checked": 0}
    misses, num = 0, 1
    with ThreadPoolExecutor(8) as ex:
        while num <= MAX_NUM and misses < STOP_MISSES:
            batch = list(range(num, num + 40))
            for n, g in zip(batch, ex.map(lambda n: data.get(n) or fetch(slug, n), batch)):
                if g:
                    data[n] = g
                    misses = 0
                else:
                    misses += 1
            num += 40
            jobs[slug]["checked"] = num
    jobs[slug]["done"] = True

@app.post("/search")
def search():
    name = request.json["name"]
    slug = re.sub(r"[^A-Za-z0-9]", "", name)
    if slug not in jobs:
        threading.Thread(target=scan, args=(slug,), daemon=True).start()
        time.sleep(0.2)
    return jsonify(slug=slug)

@app.get("/status")
def status():
    slug, bd = request.args["slug"], request.args["backdrop"].strip().lower()
    items = [g for g in list(cache.get(slug, {}).values()) if g["backdrop"].lower() == bd]
    j = jobs.get(slug, {})
    return jsonify(done=j.get("done", False), checked=j.get("checked", 0),
                   items=[{**g, "url": f"https://t.me/nft/{slug}-{g['num']}"} for g in items[:100]])

PAGE = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<title>Поиск подарков</title>
<body style="font-family:sans-serif;max-width:600px;margin:20px auto;padding:0 12px">
<h2>Поиск подарков</h2>
<input id=name placeholder="Название (Plush Pepe)" style="width:100%;padding:10px;margin:4px 0">
<input id=bd placeholder="Фон (Midnight Blue)" style="width:100%;padding:10px;margin:4px 0">
<button onclick=go() style="padding:10px 20px">Найти</button>
<p id=info></p><div id=res></div>
<script>
let timer;
async function go(){
  clearInterval(timer);
  const name=document.getElementById('name').value, bd=document.getElementById('bd').value;
  const r=await (await fetch('/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})})).json();
  const poll=async()=>{
    const s=await (await fetch(`/status?slug=${r.slug}&backdrop=${encodeURIComponent(bd)}`)).json();
    document.getElementById('info').textContent=(s.done?'Готово. ':'Идёт поиск, проверено ~'+s.checked+'. ')+'Найдено: '+s.items.length;
    document.getElementById('res').innerHTML=s.items.map(g=>
      `<p>#${g.num} · ${g.model}<br><a href="${g.url}" target=_blank>подарок</a>`+
      (g.owner?` · <a href="${g.owner}" target=_blank>профиль владельца</a>`:' · владелец скрыт')+`</p>`).join('');
    if(s.done) clearInterval(timer);
  };
  poll(); timer=setInterval(poll,3000);
}
</script>"""

@app.get("/")
def index():
    return render_template_string(PAGE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
