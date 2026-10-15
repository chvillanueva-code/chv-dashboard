import os, json, html, urllib.request, datetime

TZ = datetime.timezone(datetime.timedelta(hours=-3), "ART")  # America/Buenos_Aires, sin DST
TEAM = "3137758"; ESC = "901717699397"
TOK = os.environ["CLICKUP_API_TOKEN"]
def get(url):
    r = urllib.request.Request(url, headers={"Authorization": TOK})
    return json.load(urllib.request.urlopen(r, timeout=60))
spaces = {s["id"]: s["name"] for s in get(f"https://api.clickup.com/api/v2/team/{TEAM}/space")["spaces"]}
tasks, page = [], 0
while True:
    d = get(f"https://api.clickup.com/api/v2/team/{TEAM}/task?subtasks=true&include_closed=false&page={page}")
    tasks += d["tasks"]
    if d.get("last_page", True) or not d["tasks"]: break
    page += 1
now = datetime.datetime.now(TZ); today = now.date()
def dt(ms): return datetime.datetime.fromtimestamp(int(ms)/1000, TZ) if ms else None
rows = []
for t in tasks:
    due = dt(t.get("due_date"))
    rows.append(dict(
        name=t["name"], space=spaces.get(t["space"]["id"], t["space"]["id"]),
        folder="" if t["folder"].get("hidden") else t["folder"].get("name", ""),
        list=t["list"]["name"], list_id=t["list"]["id"], status=t["status"]["status"],
        status_color=t["status"].get("color", "#999"), due=due.date() if due else None,
        prio=(t.get("priority") or {}).get("priority"), url=t["url"],
        who=", ".join(a.get("initials") or a.get("username") or "" for a in t["assignees"]),
        upd=dt(t.get("date_updated")), sub=bool(t.get("parent"))))
rows.sort(key=lambda r: (r["due"] or datetime.date.max, r["name"].lower()))
over = [r for r in rows if r["due"] and r["due"] < today]
tod = [r for r in rows if r["due"] == today]
week = [r for r in rows if r["due"] and today < r["due"] <= today + datetime.timedelta(days=7)]
nod = [r for r in rows if not r["due"]]
PR = {"urgent": ("Urgente", "#d93025"), "high": ("Alta", "#f9a825"), "normal": ("Normal", "#1a73e8"), "low": ("Baja", "#9aa0a6")}
e = html.escape
def card(r):
    p = PR.get(r["prio"]); pb = f'<span class="b" style="background:{p[1]}">{p[0]}</span>' if p else ""
    due = r["due"].strftime("%d/%m/%Y") if r["due"] else "sin fecha"
    loc = " › ".join(x for x in (r["space"], r["folder"], r["list"]) if x)
    return (f'<li class="t" data-space="{e(r["space"])}" data-q="{e((r["name"]+" "+loc).lower())}">'
            f'<a href="{e(r["url"])}" target="_blank" rel="noopener">{"↳ " if r["sub"] else ""}{e(r["name"])}</a> {pb}'
            f'<div class="m"><span class="st" style="border-color:{e(r["status_color"])}">{e(r["status"])}</span> · {due} · {e(loc)}'
            f'{" · "+e(r["who"]) if r["who"] else ""}</div></li>')
def sec(title, items, cls=""):
    return f'<section class="s {cls}"><h2>{e(title)} <small>({len(items)})</small></h2><ul>{"".join(map(card, items)) or "<li class=e>Nada por acá 🎉</li>"}</ul></section>'
order = ["ASUNTOS", "(A) INMOBILIARIA", "(1) PERSONAL", "(D) COMERCIAL", "ACOMODAR"]
order += [s for s in sorted(set(r["space"] for r in rows)) if s not in order]
by = "".join(sec(s, [r for r in rows if r["space"] == s]) for s in order)
esc = [r for r in rows if r["list_id"] == ESC]
opts = "".join(f'<option>{e(s)}</option>' for s in order)
cards = [("Vencidas", len(over), "#d93025"), ("Vencen hoy", len(tod), "#ef6c00"), ("Esta semana", len(week), "#1a73e8"), ("Sin fecha", len(nod), "#5f6368"), ("Total abiertas", len(rows), "#202124")]
out = f'''<!doctype html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tareas CHV</title><style>
body{{font-family:system-ui,sans-serif;background:#f6f7f9;color:#202124;margin:0;padding:12px;max-width:1000px;margin:auto}}
h1{{font-size:1.4em;margin:.3em 0}} .u{{color:#5f6368;font-size:.9em}}
.cs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:12px 0}}
.c{{background:#fff;border-radius:10px;padding:10px;border-top:4px solid}} .c b{{font-size:1.8em;display:block}}
.f{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}} .f input,.f select{{padding:8px;border:1px solid #ccc;border-radius:8px;font-size:1em;flex:1;min-width:150px}}
.s{{background:#fff;border-radius:10px;padding:8px 12px;margin-bottom:12px;border-left:5px solid #dadce0}}
.red{{border-color:#d93025}} .red h2{{color:#d93025}} .ora{{border-color:#ef6c00}} .ora h2{{color:#ef6c00}} .esc{{border-color:#8e24aa;background:#faf5fc}}
h2{{font-size:1.1em}} ul{{list-style:none;padding:0;margin:0}} .t{{padding:7px 0;border-bottom:1px solid #eee}}
.t a{{color:#1a0dab;text-decoration:none;font-weight:500}} .m{{font-size:.82em;color:#5f6368;margin-top:2px}}
.b{{color:#fff;font-size:.72em;padding:1px 6px;border-radius:8px}} .st{{border-left:4px solid;padding-left:4px;text-transform:uppercase}} .e{{color:#5f6368}}
details>summary{{cursor:pointer;font-weight:600;margin:8px 0}}</style></head><body>
<h1>Tareas de Christian</h1><div class="u">Última actualización: {now.strftime("%d/%m/%Y %H:%M")} (ART)</div>
<div class="cs">{"".join(f'<div class="c" style="border-color:{c}"><b>{n}</b>{l}</div>' for l,n,c in cards)}</div>
<div class="f"><input id="q" placeholder="Buscar tarea..."><select id="sp"><option value="">Todos los espacios</option>{opts}</select></div>
{sec("Vencidas", over, "red")}{sec("Hoy", tod, "ora")}{sec("Próximos 7 días", week)}{sec("⭐ ESCRITORIO", esc, "esc")}
<h2>Por espacio</h2>{by}{sec("Sin fecha", nod)}
<script>const q=document.getElementById("q"),sp=document.getElementById("sp");function f(){{const v=q.value.toLowerCase(),s=sp.value;
document.querySelectorAll(".t").forEach(li=>li.style.display=(!s||li.dataset.space===s)&&li.dataset.q.includes(v)?"":"none")}}q.oninput=f;sp.onchange=f;</script>
</body></html>'''
os.makedirs("out", exist_ok=True); open("out/index.html", "w").write(out)
print(f"tasks={len(rows)} vencidas={len(over)} hoy={len(tod)} semana={len(week)} sinfecha={len(nod)}")
