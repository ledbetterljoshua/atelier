"""Build the gallery into _site/. One page: each artist, their statement, their works, and the
stages each work went through."""
import ast
import html
import json
import os
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
REPO = "https://github.com/ledbetterljoshua/atelier"
URL = os.environ.get("ATELIER_URL", "https://ledbetterljoshua.github.io/atelier/")


def md(text):
    """Enough markdown for a persona or a journal."""
    out, in_list, para = [], False, []

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", s)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", s)

    def flush():
        nonlocal para, in_list
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para = []
        if in_list:
            out.append("</ul>")
            in_list = False

    quote = []
    for line in text.splitlines() + [""]:
        if line.startswith(">"):
            flush()
            quote.append(line.lstrip("> ").strip())
            continue
        if quote:
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            quote = []
        if line.startswith("#"):
            flush()
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n + 2}>{inline(line.lstrip('# '))}</h{n + 2}>")
        elif line.startswith("- "):
            if para:
                out.append(f"<p>{inline(' '.join(para))}</p>")
                para = []
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}")
        elif line.startswith("  ") and in_list:
            out[-1] += " " + inline(line.strip())
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    return "\n".join(out)


def section(text, heading):
    """Body of the first `## ` section whose heading matches the regex `heading`."""
    m = re.search(rf"^## ({heading})[ \t]*\n(.*?)(?=^## |\Z)", text, re.S | re.M | re.I)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", "")


def kit(path):
    """Public names in an artist's tools.py, each with the first sentence of its docstring."""
    if not path.exists():
        return []
    out = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            doc = (ast.get_docstring(node) or "").split("\n\n")[0].replace("\n", " ")
            out.append((node.name, re.split(r"(?<=[.!?])\s", doc)[0] if doc else ""))
    return out


CSS = """
:root{--wall:#ebe7df;--ink:#1d1b18;--mute:#6f6a61;--rule:#cfc9bd;--card:#f6f3ec;--accent:#7a2e1c}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--wall:#171614;--ink:#ebe6da;--mute:#9a9486;--rule:#34312c;--card:#1f1d1a;--accent:#d98a6a}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--wall);color:var(--ink);font:17px/1.6 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
a{color:var(--accent)}
header.top{padding:56px 24px 8px;max-width:1180px;margin:0 auto}
header.top h1{font-weight:400;font-size:44px;letter-spacing:.01em;margin:0}
header.top p{color:var(--mute);max-width:62ch;margin:10px 0 0}
nav.roster{max-width:1180px;margin:26px auto 0;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}
nav.roster a{display:block;text-decoration:none;color:var(--ink)}
nav.roster img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;background:#0c0b0a}
nav.roster b{display:block;font-weight:400;font-size:19px;margin-top:8px}
nav.roster span{display:block;color:var(--mute);font-size:14px;line-height:1.4}
main{max-width:1180px;margin:0 auto;padding:0 24px 96px}
.artist{border-top:1px solid var(--rule);margin-top:56px;padding-top:28px}
.artist>h2{font-weight:400;font-size:30px;margin:0}
.artist .dates{color:var(--mute);font-style:italic;margin:2px 0 0;max-width:80ch}
.about{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;margin-top:18px}
.about blockquote,.j blockquote{margin:0 0 14px;font-size:21px;line-height:1.45;font-style:italic;border-left:2px solid var(--accent);padding-left:16px}
.about ul,.j ul{padding-left:18px;margin:8px 0}.about li,.j li{margin:6px 0}
.about h3,.about h4,.kit h3{font:600 12px/1.2 ui-sans-serif,system-ui,sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--mute);margin:18px 0 6px}
.about>div>h3:first-child{margin-top:0}
code{font:13px ui-monospace,Menlo,monospace;background:var(--card);padding:1px 5px;border-radius:3px}
.kit dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 16px;margin:8px 0 0;font-size:15px}
.kit dt,.kit dd{margin:0}.kit dd{color:var(--mute)}
.work{margin-top:52px}
.hang{margin:0 auto}
.frame{background:#0c0b0a;padding:14px;box-shadow:0 18px 40px rgba(0,0,0,.28),0 2px 4px rgba(0,0,0,.3)}
.frame img{display:block;width:100%;height:auto}
.label{display:flex;gap:28px;justify-content:space-between;align-items:flex-start;margin-top:18px;flex-wrap:wrap}
.label .t{font-size:21px;font-style:italic}
.label .m{color:var(--mute);font-size:15px}
.label .n{font:13px ui-monospace,Menlo,monospace;color:var(--mute);text-align:right}
.label .n a{color:inherit}
.stages{margin-top:14px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.stages input{flex:1;min-width:180px;accent-color:var(--accent)}
.stages .cap{font:13px ui-sans-serif,system-ui,sans-serif;color:var(--mute);min-width:26ch}
details{margin-top:14px}summary{cursor:pointer;color:var(--accent);font:14px ui-sans-serif,system-ui,sans-serif}
details .j{max-width:70ch}details h3,details h4{font-size:17px;margin:18px 0 4px}
footer{max-width:1180px;margin:0 auto;padding:0 24px 60px;color:var(--mute);font-size:14px}
@media (max-width:760px){.about{grid-template-columns:1fr;gap:8px}header.top h1{font-size:34px}main,header.top,footer,nav.roster{padding-left:16px;padding-right:16px}.frame{padding:8px}.label .n{text-align:left}.kit dl{grid-template-columns:1fr}.kit dd{margin-bottom:8px}}
"""

JS = """
document.querySelectorAll('.work').forEach(w=>{
  const img=w.querySelector('.frame img'),r=w.querySelector('input'),cap=w.querySelector('.cap');
  if(!r)return;const st=JSON.parse(w.dataset.stages);
  const warm=()=>st.forEach(s=>{new Image().src=s.file});
  w.addEventListener('pointerenter',warm,{once:true});r.addEventListener('focus',warm,{once:true});
  r.addEventListener('input',()=>{const s=st[r.value];img.src=s.file;cap.textContent=s.name+' \\u00b7 '+s.strokes.toLocaleString()+' strokes'});
});
"""


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "img").mkdir(parents=True)
    parts, roster, total, strokes_all, cover = [], [], 0, 0, ""
    for adir in sorted((ROOT / "artists").iterdir()):
        if not (adir / "persona.md").exists():
            continue
        persona = (adir / "persona.md").read_text()
        name = persona.splitlines()[0].lstrip("# ").strip()
        intro = persona.split("\n\n")[1].replace("\n", " ")
        journal = (adir / "journal.md").read_text() if (adir / "journal.md").exists() else ""
        works_html, thumb = [], ""
        for wdir in sorted((adir / "works").iterdir()):
            wj = wdir / "work.json"
            if not wj.exists():
                continue
            w = json.loads(wj.read_text())
            total += 1
            strokes_all += w["strokes"]
            slug = f"{adir.name}-{wdir.name}"
            stages = []
            for i, s in enumerate(w["stages"]):
                dst = SITE / "img" / f"{slug}-{i:02d}.jpg"
                if i == len(w["stages"]) - 1:
                    im = Image.open(wdir / "final.png").convert("RGB")
                    im.save(dst, quality=92)
                    im.thumbnail((720, 720))
                    thumb = f"img/{slug}-thumb.jpg"
                    im.save(SITE / thumb, quality=86)
                else:
                    shutil.copy(wdir / s["file"], dst)
                stages.append({"name": s["name"], "strokes": s["strokes"], "file": f"img/{dst.name}"})
            last = stages[-1]
            cover = cover or last["file"]
            num = wdir.name.split("-")[0]
            _, entry = section(journal, rf"{num}\. {re.escape(w['title'])}")
            src = f"{REPO}/blob/main/{wdir.relative_to(ROOT)}/paint.py"
            lines = (wdir / "paint.py").read_text().count("\n")
            ww, wh = w["size"]
            works_html.append(f"""
<section class="work" id="{slug}" data-stages='{html.escape(json.dumps(stages), quote=True)}'>
  <div class="hang" style="max-width:calc(84vh * {ww / wh:.4f})">
  <div class="frame"><img src="{last['file']}" alt="{html.escape(w['title'])}" width="{ww}" height="{wh}" loading="lazy"></div>
  <div class="label">
    <div><div class="t">{html.escape(w['title'])}</div><div class="m">{w.get('year', '')} &middot; {html.escape(w.get('medium', ''))}</div></div>
    <div class="n">{w['strokes']:,} strokes<br><a href="{src}">{lines:,} lines of Python</a></div>
  </div>
  <div class="stages"><input type="range" min="0" max="{len(stages) - 1}" value="{len(stages) - 1}" aria-label="Stages of the painting">
    <span class="cap">{html.escape(last['name'])} &middot; {last['strokes']:,} strokes</span></div>
  {f'<details><summary>From the journal</summary><div class="j">{md(entry)}</div></details>' if entry else ''}
  </div>
</section>""")
        if not works_html:
            continue
        lh, lb = section(persona, r"What .+? paints?")
        rh, rb = section(persona, r"How .+? paints?")
        mech = kit(adir / "tools.py")
        kit_html = ""
        if mech:
            rows = "".join(f"<dt><code>{html.escape(n)}</code></dt><dd>{html.escape(d)}</dd>" for n, d in mech)
            kit_html = (f'<details class="kit"><summary>The kit: {len(mech)} mechanisms this artist built</summary>'
                        f'<dl>{rows}</dl><p><a href="{REPO}/blob/main/artists/{adir.name}/tools.py">tools.py</a></p></details>')
        parts.append(f"""
<article class="artist" id="{adir.name}">
  <h2>{html.escape(name)}</h2><p class="dates">{html.escape(intro)}</p>
  <div class="about"><div><h3>{html.escape(lh)}</h3>{md(lb)}</div><div><h3>{html.escape(rh)}</h3>{md(rb)}</div></div>
  {kit_html}
  {''.join(works_html)}
</article>""")
        n = len(works_html)
        roster.append(f'<a href="#{adir.name}"><img src="{thumb}" alt=""><b>{html.escape(name)}</b>'
                      f'<span>{n} work{"s" if n != 1 else ""}</span></a>')
    blurb = ("Paintings made in code, one brush stroke at a time, by artists who do not exist. Each is a Python "
             "program that walks a simulated brush across a board. No image model, nothing traced.")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atelier</title><meta name="description" content="{blurb}">
<meta property="og:title" content="Atelier"><meta property="og:description" content="{blurb}">
<meta property="og:image" content="{URL}{cover}"><meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style></head><body>
<header class="top"><h1>Atelier</h1><p>{blurb} The artists are invented by the model that paints as them, and their journals change how they paint. Drag the slider under a painting to watch it being made.</p></header>
<nav class="roster" aria-label="Artists">{''.join(roster)}</nav>
<main>{''.join(parts)}</main>
<footer>{len(roster)} artist{'s' if len(roster) != 1 else ''}, {total} work{'s' if total != 1 else ''}, {strokes_all:,} strokes. Painted by Claude. <a href="{REPO}">Source on GitHub</a>.</footer>
<script>{JS}</script></body></html>"""
    (SITE / "index.html").write_text(page)
    (SITE / ".nojekyll").write_text("")
    print(f"gallery: {len(roster)} artists, {total} works -> {SITE / 'index.html'}")


if __name__ == "__main__":
    build()
