from __future__ import annotations

import html
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import build_three_chapters as source
from atm_layout_engine import chapter_layout


OUT = Path(r"C:\Users\nikit\.codex\visualizations\2026\09\24\01a0d23c-56b6-7403-accf-a0a2de250a86\all-remaining-quest-layouts-atm.html")

GROUPS = (
    ("II · Технологии", ("ae2", "appmek", "mekplus", "oritech", "silentgear", "integration", "createplus")),
    ("III · Магия", ("ars", "arsplus", "occult", "evil", "fna", "irons", "vampirism", "starlight")),
    ("IV · Ферма и остров", ("farmer", "mystical", "builder", "minecolonies")),
    ("V · Pokémon", ("pokemon", "cobblemon_advanced", "cobbleplus", "trainers", "services")),
    ("VI · Бои и боссы", ("epicfight", "apotheosis", "cataclysm", "draconic", "worldbosses", "threats")),
    ("VII · Миры и приключения", ("traveler", "atlas", "artifacts", "relics", "wildlife", "swem", "origins")),
    ("VIII · Сервер и финал", ("achievements", "community", "endgame", "finale")),
)

PALETTE = ("#4e9ab8", "#68a65c", "#a16ab2", "#c27b35", "#b95849", "#597eb4")
CHAPTER_PATHS = (
    "river", "double_arc", "terraces", "crown", "wave", "stairs", "constellation",
    "valley", "ribbon", "skyline", "braid", "islands",
)
STAGE_FORMS = ("split", "arch", "ladder", "fan", "diamond", "wave", "fork", "loop")


def group_for(namespace: str) -> str:
    for name, keys in GROUPS:
        if namespace in keys:
            return name
    return "VIII · Другое"


def stage_anchors(kind: str, count: int) -> list[tuple[float, float]]:
    xs = [10 + i * (180 / max(1, count - 1)) for i in range(count)]
    if kind == "river":
        ys = [50 + 15 * math.sin(i * 1.15) for i in range(count)]
    elif kind == "double_arc":
        ys = [55 - 23 * math.sin(i / max(1, count - 1) * math.pi * 2) for i in range(count)]
    elif kind == "terraces":
        ys = [30, 30, 48, 48, 68, 68, 48, 32, 32][:count]
    elif kind == "crown":
        ys = [58 - 30 * math.sin(i / max(1, count - 1) * math.pi) for i in range(count)]
    elif kind == "wave":
        ys = [50 + 22 * math.sin(i * math.pi / 2) for i in range(count)]
    elif kind == "stairs":
        ys = [70 - (i % 4) * 14 for i in range(count)]
    elif kind == "constellation":
        ys = [54, 31, 44, 23, 58, 72, 45, 26, 49][:count]
    elif kind == "valley":
        ys = [28 + 38 * math.sin(i / max(1, count - 1) * math.pi) for i in range(count)]
    elif kind == "ribbon":
        ys = [44 + 18 * math.sin(i * .86 + .6) for i in range(count)]
    elif kind == "skyline":
        ys = [68, 54, 54, 34, 34, 48, 26, 42, 42][:count]
    elif kind == "braid":
        ys = [34 if i % 2 == 0 else 66 for i in range(count)]
    else:
        ys = [50, 27, 68, 37, 58, 24, 64, 43, 52][:count]
    while len(ys) < count:
        ys.append(50 + 18 * math.sin(len(ys) * 1.2))
    return list(zip(xs, ys))


def make_stage_nodes(
    stage_index: int,
    anchor: tuple[float, float],
    next_anchor: tuple[float, float] | None,
    titles: list[str],
    form: str,
) -> tuple[list[dict], list[list[str]], str]:
    ax, ay = anchor
    if next_anchor:
        nx, ny = next_anchor
        width = max(9.0, nx - ax - 2.2)
        dy = ny - ay
    else:
        width, dy = 11.0, 0.0

    count = len(titles)
    root = f"s{stage_index + 1:02d}_01"
    nodes = [{"id": root, "title": titles[0], "x": ax, "y": ay, "main": True}]
    edges: list[list[str]] = []
    if count == 1:
        return nodes, edges, root

    # Each form keeps a clear entry and exit. Branches stay local to their stage,
    # which is how the final SNBT coordinates will be generated after approval.
    ids = [f"s{stage_index + 1:02d}_{i + 1:02d}" for i in range(count)]
    available = max(7.0, min(18.0, width))

    if form == "split" and count >= 6:
        upper = list(range(1, (count + 1) // 2))
        lower = list(range((count + 1) // 2, count - 1))
        end = count - 1
        for branch, sign in ((upper, -1), (lower, 1)):
            prev = 0
            for order, idx in enumerate(branch, 1):
                t = order / (len(branch) + 1)
                nodes.append({"id": ids[idx], "title": titles[idx], "x": ax + available * t, "y": ay + sign * (7 + math.sin(t * math.pi) * 7), "main": False})
                edges.append([ids[prev], ids[idx]])
                prev = idx
            edges.append([ids[prev], ids[end]])
        nodes.append({"id": ids[end], "title": titles[end], "x": ax + available, "y": ay + dy * .55, "main": True})
    elif form == "diamond" and count >= 5:
        end = count - 1
        middle = list(range(1, end))
        upper = middle[::2]
        lower = middle[1::2]
        for branch, sign in ((upper, -1), (lower, 1)):
            prev = 0
            for order, idx in enumerate(branch, 1):
                t = order / (len(branch) + 1)
                nodes.append({"id": ids[idx], "title": titles[idx], "x": ax + available * t, "y": ay + sign * (7 + 6 * math.sin(t * math.pi)), "main": False})
                edges.append([ids[prev], ids[idx]])
                prev = idx
            edges.append([ids[prev], ids[end]])
        nodes.append({"id": ids[end], "title": titles[end], "x": ax + available, "y": ay + dy * .5, "main": True})
    elif form == "ladder":
        for i in range(1, count):
            t = i / (count - 1)
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + (-1 if i % 2 else 1) * 7 + dy * t * .45, "main": i == count - 1})
            edges.append([ids[i - 1], ids[i]])
            if i >= 3 and i % 2:
                edges.append([ids[i - 2], ids[i]])
    elif form == "fan":
        hub = min(3, count - 1)
        for i in range(1, count):
            if i <= hub:
                t = i / max(1, hub)
                x, y = ax + available * .34 * t, ay + dy * .18 * t
                parent = i - 1
            else:
                spoke = i - hub - 1
                spokes = count - hub - 1
                angle = -1.0 + 2.0 * spoke / max(1, spokes - 1)
                x = ax + available * (.55 + .42 * math.cos(angle))
                y = ay + dy * .45 + 15 * math.sin(angle)
                parent = hub
            nodes.append({"id": ids[i], "title": titles[i], "x": x, "y": y, "main": i <= hub})
            edges.append([ids[parent], ids[i]])
    elif form == "fork":
        trunk = max(2, count // 3)
        for i in range(1, count):
            if i <= trunk:
                t = i / trunk
                x, y, parent = ax + available * .45 * t, ay + dy * .25 * t, i - 1
            else:
                branch = i - trunk - 1
                total = count - trunk - 1
                sign = -1 if branch % 2 == 0 else 1
                rank = branch // 2 + 1
                x = ax + available * (.48 + .45 * rank / max(1, math.ceil(total / 2)))
                y = ay + dy * .45 + sign * (6 + rank * 4)
                parent = trunk if rank == 1 else i - 2
            nodes.append({"id": ids[i], "title": titles[i], "x": x, "y": y, "main": i <= trunk})
            edges.append([ids[parent], ids[i]])
    elif form == "loop":
        for i in range(1, count):
            t = i / (count - 1)
            angle = math.pi * (1.15 + 1.7 * t)
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + 14 * math.sin(angle) + dy * t * .45, "main": i in (count - 1,)})
            edges.append([ids[i - 1], ids[i]])
    else:  # arch / wave
        for i in range(1, count):
            t = i / (count - 1)
            curve = (-15 * math.sin(t * math.pi)) if form == "arch" else (10 * math.sin(t * math.pi * 2))
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + curve + dy * t * .5, "main": i == count - 1})
            edges.append([ids[i - 1], ids[i]])

    return nodes, edges, ids[-1]


def make_chapter(namespace: str, index: int, config: dict) -> dict:
    layout = chapter_layout(namespace, index, config)
    nodes = layout["nodes"]
    edges = layout["edges"]
    stage_meta = layout["stages"]
    for stage_index, stage in enumerate(stage_meta):
        stage["color"] = PALETTE[stage_index % len(PALETTE)]
    stage_by_number = {i + 1: stage for i, stage in enumerate(stage_meta)}
    for node in nodes:
        stage = stage_by_number[int(node["id"][1:3])]
        node["stage"] = stage["name"]
        node["phase"] = stage["phase"]
        node["color"] = stage["color"]

    return {
        "namespace": namespace,
        "title": config["title"],
        "icon": config.get("icon", "minecraft:book"),
        "group": group_for(namespace),
        "style": layout["style"],
        "nodes": nodes,
        "edges": edges,
        "stages": stage_meta,
    }


def build_data() -> list[dict]:
    return [make_chapter(namespace, index, config) for index, (namespace, config) in enumerate(source.CHAPTERS.items())]


def build_fragment(chapters: list[dict]) -> str:
    data = json.dumps(chapters, ensure_ascii=False, separators=(",", ":"))
    nav = []
    for group_name, keys in GROUPS:
        buttons = []
        for key in keys:
            chapter = next((item for item in chapters if item["namespace"] == key), None)
            if chapter:
                buttons.append(f'<button class="pta-chapter" data-key="{html.escape(key)}"><span>{html.escape(chapter["title"])}</span><b>{len(chapter["nodes"])} кв.</b></button>')
        if buttons:
            nav.append(f'<section><h3>{html.escape(group_name)}</h3>{"".join(buttons)}</section>')

    return f'''<div id="pta-atm-preview" class="pta-shell">
<style>
#pta-atm-preview{{--paper:#eee7d8;--ink:#3f3a34;--muted:#807767;--line:#746c62;--gold:#b87a2b;font-family:"Segoe UI",Arial,sans-serif;color:var(--ink);height:720px;display:grid;grid-template-columns:300px 1fr;background:#d7d0c3;border:1px solid #59544c;box-shadow:0 18px 50px #0008;overflow:hidden}}
#pta-atm-preview *{{box-sizing:border-box}} .pta-side{{background:#262b31;color:#e8e4dc;border-right:3px solid #101317;display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden}}
.pta-brand{{padding:16px 18px 14px;background:linear-gradient(180deg,#343b43,#24292f);border-bottom:1px solid #0c0e11}} .pta-brand strong{{font-size:18px;letter-spacing:.02em}} .pta-brand small{{display:block;color:#b9c2cb;margin-top:4px}}
.pta-scope{{padding:10px 14px;font-size:12px;line-height:1.4;color:#d1b37f;background:#201d18;border-bottom:1px solid #111}}
.pta-nav{{overflow:auto;padding:6px 7px 18px;scrollbar-color:#626974 #23272c}} .pta-nav section{{margin-top:10px}} .pta-nav h3{{font-size:11px;letter-spacing:.1em;color:#9ca6af;margin:8px 8px 5px;text-transform:uppercase}}
.pta-chapter{{width:100%;display:flex;gap:8px;align-items:center;justify-content:space-between;border:0;background:transparent;color:#d8dce0;text-align:left;padding:7px 9px;border-radius:3px;cursor:pointer;font:inherit}}
.pta-chapter:hover{{background:#343b42}} .pta-chapter.active{{background:#d8c7aa;color:#27231e;box-shadow:inset 3px 0 #bd762a}} .pta-chapter span{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px}} .pta-chapter b{{font-size:10px;opacity:.65;white-space:nowrap}}
.pta-main{{min-width:0;min-height:0;height:100%;overflow:hidden;display:grid;grid-template-rows:72px minmax(0,1fr) 116px;background:var(--paper)}} .pta-top{{display:flex;align-items:center;gap:14px;padding:12px 18px;background:linear-gradient(180deg,#eee7d8,#e5dccb);border-bottom:2px solid #b7ab98}}
.pta-icon{{width:42px;height:42px;display:grid;place-items:center;background:#30363c;border:3px solid #a98d61;transform:rotate(45deg);box-shadow:0 2px 0 #0005}} .pta-icon span{{transform:rotate(-45deg);font-size:20px;color:#f5ddb2}}
.pta-title{{min-width:0;flex:1}} .pta-title h2{{font-family:Georgia,serif;font-size:21px;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .pta-title p{{margin:4px 0 0;color:#786f62;font-size:12px}}
.pta-controls{{display:flex;gap:5px}} .pta-controls button{{width:34px;height:31px;border:1px solid #8f8578;background:#f5efe3;color:#4e473f;border-radius:2px;cursor:pointer;font-weight:700}} .pta-controls button:hover{{background:#fffaf0}}
.pta-viewport{{position:relative;min-height:0;overflow:hidden;background-color:#eee7d8;background-image:linear-gradient(#8d827018 1px,transparent 1px),linear-gradient(90deg,#8d827018 1px,transparent 1px);background-size:28px 28px;cursor:grab}} .pta-viewport.dragging{{cursor:grabbing}} #pta-graph{{width:100%;height:100%;display:block;touch-action:none}}
.pta-edge{{stroke:#706a62;stroke-width:.55;fill:none;opacity:.74}} .pta-edge.main{{stroke-width:.9;opacity:.9}} .pta-stage-route{{fill:none;stroke-width:1.4;opacity:.16;stroke-linecap:round;stroke-linejoin:round}}
.pta-node{{cursor:pointer}} .pta-node circle,.pta-node rect{{fill:#2d3033;stroke:#ada79e;stroke-width:.45;filter:url(#nodeShadow)}} .pta-node.main circle,.pta-node.main rect{{stroke-width:.85}} .pta-node:hover circle,.pta-node:hover rect,.pta-node.selected circle,.pta-node.selected rect{{stroke:#fff3ce;stroke-width:1.2}}
.pta-node text{{font-size:2.3px;fill:#fff;text-anchor:middle;dominant-baseline:central;font-family:"Segoe UI Symbol",sans-serif;pointer-events:none}} .pta-stage-label{{font-family:Georgia,serif;font-size:2.7px;font-weight:700;paint-order:stroke;stroke:#eee7d8;stroke-width:1px;stroke-linejoin:round}}
.pta-stage-chip{{font-size:1.8px;fill:#696158;paint-order:stroke;stroke:#eee7d8;stroke-width:.75px}}
.pta-info{{display:grid;grid-template-columns:1.3fr .8fr .8fr;gap:18px;padding:12px 18px;background:#e8dfce;border-top:2px solid #b7ab98}} .pta-info h4{{font-family:Georgia,serif;font-size:16px;margin:0 0 5px}} .pta-info p{{font-size:12px;line-height:1.45;margin:0;color:#625b52}} .pta-info b{{display:block;font-size:10px;color:#9a6a2e;letter-spacing:.09em;text-transform:uppercase;margin-bottom:6px}}
.pta-legend{{position:absolute;left:12px;bottom:10px;background:#efe8dbdd;border:1px solid #ad9f8a;padding:6px 9px;font-size:10px;color:#5e574e;pointer-events:none}}
@media(max-width:900px){{#pta-atm-preview{{grid-template-columns:235px 1fr}} .pta-main{{grid-template-rows:70px 1fr 128px}} .pta-info{{grid-template-columns:1fr 1fr}} .pta-info>div:first-child{{grid-column:1/-1}}}}
</style>
<aside class="pta-side"><div class="pta-brand"><strong>PokeTech Arcana</strong><small>Книга развития · макет</small></div><div class="pta-scope">41 глава для согласования<br>Первые 3 главы исключены</div><nav class="pta-nav">{''.join(nav)}</nav></aside>
<main class="pta-main"><header class="pta-top"><div class="pta-icon"><span>✦</span></div><div class="pta-title"><h2 id="pta-title"></h2><p id="pta-subtitle"></p></div><div class="pta-controls"><button id="pta-minus" aria-label="Уменьшить">−</button><button id="pta-fit" aria-label="Показать всю главу">◇</button><button id="pta-plus" aria-label="Увеличить">+</button></div></header>
<div class="pta-viewport" id="pta-viewport"><svg id="pta-graph" viewBox="0 0 210 92" role="img" aria-label="Макет квестовой главы"><defs><filter id="nodeShadow" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy=".6" stdDeviation=".35" flood-opacity=".48"/></filter></defs><g id="pta-world"></g></svg><div class="pta-legend">Серая линия — зависимость · цвет — этап · крупный узел — переход</div></div>
<footer class="pta-info"><div><h4 id="pta-node-title">Выберите квест</h4><p id="pta-node-desc">Нажмите на значок, чтобы увидеть название и этап.</p></div><div><b>Цель</b><p id="pta-goal">Квесты расположены так же, как будут в FTB Quests.</p></div><div><b>Награда</b><p>Будет подобрана под текущий шаг после утверждения разметки.</p></div></footer></main>
<script>
(()=>{{
const chapters={data}; const root=document.getElementById('pta-atm-preview'); const svg=root.querySelector('#pta-graph'); const world=root.querySelector('#pta-world'); const viewport=root.querySelector('#pta-viewport');
let chapter=chapters[0], zoom=1, panX=0, panY=0, dragging=false, lastX=0,lastY=0;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
function coords(c){{return [6+c.x,8+c.y*.78]}}
function render(key){{chapter=chapters.find(c=>c.namespace===key)||chapters[0]; zoom=1;panX=0;panY=0; root.querySelectorAll('.pta-chapter').forEach(b=>b.classList.toggle('active',b.dataset.key===chapter.namespace));root.querySelector('#pta-title').textContent=chapter.title;root.querySelector('#pta-subtitle').textContent=`${{chapter.group}} · ${{chapter.nodes.length}} заданий · композиция: ${{chapter.style}}`;
const byId=Object.fromEntries(chapter.nodes.map(n=>[n.id,n])); let routes=''; chapter.stages.forEach((s,i)=>{{const next=chapter.stages[i+1];if(!next)return;const [x1,y1]=coords(s),[x2,y2]=coords(next);const mx=(x1+x2)/2;routes+=`<path class="pta-stage-route" stroke="${{s.color}}" d="M${{x1}},${{y1}} C${{mx}},${{y1}} ${{mx}},${{y2}} ${{x2}},${{y2}}"/>`;}});
let edges=chapter.edges.map((e,i)=>{{const a=byId[e[0]],b=byId[e[1]];if(!a||!b)return'';const [x1,y1]=coords(a),[x2,y2]=coords(b);const bend=Math.max(1.5,Math.abs(x2-x1)*.32);return`<path class="pta-edge ${{a.main&&b.main?'main':''}}" d="M${{x1}},${{y1}} C${{x1+bend}},${{y1}} ${{x2-bend}},${{y2}} ${{x2}},${{y2}}"/>`;}}).join('');
let labels=chapter.stages.map(s=>{{const [x,y]=coords(s);return`<text class="pta-stage-label" x="${{x}}" y="${{y-5.2}}" fill="${{s.color}}">${{esc(s.name)}}</text><text class="pta-stage-chip" x="${{x}}" y="${{y-2.4}}">${{esc(s.phase)}} · ${{esc(s.form)}}</text>`}}).join('');
let nodes=chapter.nodes.map((n,i)=>{{const [x,y]=coords(n);const glyph=n.main?'◆':(i%5===0?'⚙':i%3===0?'✦':'●');return`<g class="pta-node ${{n.main?'main':''}}" data-id="${{n.id}}" transform="translate(${{x}} ${{y}})">${{n.main?`<rect x="-1.9" y="-1.9" width="3.8" height="3.8" rx=".4" transform="rotate(45)" stroke="${{n.color}}"/>`:`<circle r="1.55" stroke="${{n.color}}"/>`}}<text>${{glyph}}</text><title>${{esc(n.title)}}</title></g>`}}).join(''); world.innerHTML=routes+edges+labels+nodes; applyTransform(); world.querySelectorAll('.pta-node').forEach(el=>el.addEventListener('click',()=>selectNode(el.dataset.id))); selectNode(chapter.nodes[0].id);}}
function selectNode(id){{world.querySelectorAll('.pta-node').forEach(n=>n.classList.toggle('selected',n.dataset.id===id));const n=chapter.nodes.find(n=>n.id===id);if(!n)return;root.querySelector('#pta-node-title').textContent=n.title;root.querySelector('#pta-node-desc').textContent=`${{n.phase}} · ${{n.stage}}. Этот узел будет иметь те же SNBT-координаты, форму и связи, которые показаны в макете.`}}
function applyTransform(){{world.setAttribute('transform',`translate(${{panX}} ${{panY}}) scale(${{zoom}})`);}}
root.querySelectorAll('.pta-chapter').forEach(b=>b.addEventListener('click',()=>render(b.dataset.key)));root.querySelector('#pta-plus').onclick=()=>{{zoom=Math.min(2.4,zoom*1.18);applyTransform()}};root.querySelector('#pta-minus').onclick=()=>{{zoom=Math.max(.55,zoom/1.18);applyTransform()}};root.querySelector('#pta-fit').onclick=()=>{{zoom=1;panX=0;panY=0;applyTransform()}};
viewport.addEventListener('pointerdown',e=>{{dragging=true;lastX=e.clientX;lastY=e.clientY;viewport.classList.add('dragging');viewport.setPointerCapture(e.pointerId)}});viewport.addEventListener('pointermove',e=>{{if(!dragging)return;const r=viewport.getBoundingClientRect();panX+=(e.clientX-lastX)*210/r.width;panY+=(e.clientY-lastY)*92/r.height;lastX=e.clientX;lastY=e.clientY;applyTransform()}});viewport.addEventListener('pointerup',()=>{{dragging=false;viewport.classList.remove('dragging')}});viewport.addEventListener('wheel',e=>{{e.preventDefault();zoom=Math.max(.55,Math.min(2.4,zoom*(e.deltaY<0?1.1:.91)));applyTransform()}},{{passive:false}});
render(chapters[0].namespace);
}})();
</script></div>'''


def main() -> None:
    chapters = build_data()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_fragment(chapters), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(chapters)} chapters)")


if __name__ == "__main__":
    main()
