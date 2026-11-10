"""Build the gallery into _site/. One page: each artist, their statement, their works, and the
stages each work went through."""
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


def md(text):
    """Enough markdown for a persona or a journal."""
    out, in_list, para = [], False, []

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
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
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


CSS = """
:root{--wall:#ebe7df;--ink:#1d1b18;--mute:#6f6a61;--rule:#cfc9bd;--card:#f6f3ec;--accent:#7a2e1c}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--wall:#171614;--ink:#ebe6da;--mute:#9a9486;--rule:#34312c;--card:#1f1d1a;--accent:#d98a6a}}
*{box-sizing:border-box}
body{margin:0;background:var(--wall);color:var(--ink);font:17px/1.6 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
header.top{padding:56px 24px 8px;max-width:1180px;margin:0 auto}
header.top h1{font-weight:400;font-size:44px;letter-spacing:.01em;margin:0}
header.top p{color:var(--mute);max-width:62ch;margin:10px 0 0}
main{max-width:1180px;margin:0 auto;padding:0 24px 96px}
.artist{border-top:1px solid var(--rule);margin-top:56px;padding-top:28px}
.artist>h2{font-weight:400;font-size:30px;margin:0}
.artist .dates{color:var(--mute);font-style:italic;margin:2px 0 0}
.about{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;margin-top:18px}
.about blockquote{margin:0 0 14px;font-size:21px;line-height:1.45;font-style:italic;border-left:2px solid var(--accent);padding-left:16px}
.about ul{padding-left:18px;margin:8px 0}.about li{margin:6px 0}
.about h3,.about h4{font:600 12px/1.2 ui-sans-serif,system-ui,sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--mute);margin:18px 0 6px}
code{font:13px ui-monospace,Menlo,monospace;background:var(--card);padding:1px 5px;border-radius:3px}
.work{margin-top:44px}
.frame{background:#0c0b0a;padding:14px;box-shadow:0 18px 40px rgba(0,0,0,.28),0 2px 4px rgba(0,0,0,.3)}
.frame img{display:block;width:100%;height:auto}
.label{display:flex;gap:28px;justify-content:space-between;align-items:flex-start;margin-top:18px;flex-wrap:wrap}
.label .t{font-size:21px;font-style:italic}
.label .m{color:var(--mute);font-size:15px}
.label .n{font:13px ui-monospace,Menlo,monospace;color:var(--mute);text-align:right}
.stages{margin-top:14px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.stages input{flex:1;min-width:180px;accent-color:var(--accent)}
.stages .cap{font:13px ui-sans-serif,system-ui,sans-serif;color:var(--mute);min-width:26ch}
details{margin-top:14px}summary{cursor:pointer;color:var(--accent);font:14px ui-sans-serif,system-ui,sans-serif}
details .j{max-width:70ch}details h3,details h4{font-size:17px;margin:18px 0 4px}
footer{max-width:1180px;margin:0 auto;padding:0 24px 60px;color:var(--mute);font-size:14px}
@media (max-width:760px){.about{grid-template-columns:1fr;gap:8px}header.top h1{font-size:34px}main,header.top,footer{padding-left:16px;padding-right:16px}.frame{padding:8px}}
"""

JS = """
document.querySelectorAll('.work').forEach(w=>{
  const img=w.querySelector('.frame img'),r=w.querySelector('input'),cap=w.querySelector('.cap');
  if(!r)return;const st=JSON.parse(w.dataset.stages);
  r.addEventListener('input',()=>{const s=st[r.value];img.src=s.file;cap.textContent=s.name+' \\u00b7 '+s.strokes.toLocaleString()+' strokes'});
});
"""


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "img").mkdir(parents=True)
    parts, total = [], 0
    for adir in sorted((ROOT / "artists").iterdir()):
        if not (adir / "persona.md").exists():
            continue
        persona = (adir / "persona.md").read_text()
        name = persona.splitlines()[0].lstrip("# ").strip()
        intro = persona.split("\n\n")[1].replace("\n", " ")
        journal = (adir / "journal.md").read_text() if (adir / "journal.md").exists() else ""
        works_html = []
        for wdir in sorted((adir / "works").iterdir()):
            wj = wdir / "work.json"
            if not wj.exists():
                continue
            w = json.loads(wj.read_text())
            total += 1
            slug = f"{adir.name}-{wdir.name}"
            stages = []
            for i, s in enumerate(w["stages"]):
                dst = SITE / "img" / f"{slug}-{i:02d}.jpg"
                if i == len(w["stages"]) - 1:
                    Image.open(wdir / "final.png").convert("RGB").save(dst, quality=93)
                else:
                    shutil.copy(wdir / s["file"], dst)
                stages.append({"name": s["name"], "strokes": s["strokes"], "file": f"img/{dst.name}"})
            last = stages[-1]
            num = wdir.name.split("-")[0]
            entry = section(journal, f"{num}. {w['title']}")
            works_html.append(f"""
<section class="work" data-stages='{html.escape(json.dumps(stages), quote=True)}'>
  <div class="frame"><img src="{last['file']}" alt="{html.escape(w['title'])}" width="{w['size'][0]}" height="{w['size'][1]}"></div>
  <div class="label">
    <div><div class="t">{html.escape(w['title'])}</div><div class="m">{w.get('year', '')} &middot; {html.escape(w.get('medium', ''))}</div></div>
    <div class="n">{w['strokes']:,} strokes<br>{Path(wdir, 'paint.py').read_text().count(chr(10)):,} lines of Python</div>
  </div>
  <div class="stages"><input type="range" min="0" max="{len(stages) - 1}" value="{len(stages) - 1}" aria-label="Stages of the painting">
    <span class="cap">{html.escape(last['name'])} &middot; {last['strokes']:,} strokes</span></div>
  {f'<details><summary>From the journal</summary><div class="j">{md(entry)}</div></details>' if entry else ''}
</section>""")
        left = md(section(persona, "What she paints") or section(persona, "What he paints") or section(persona, "What they paint"))
        right = md(section(persona, "How she paints") or section(persona, "How he paints") or section(persona, "How they paint"))
        parts.append(f"""
<article class="artist" id="{adir.name}">
  <h2>{html.escape(name)}</h2><p class="dates">{html.escape(intro)}</p>
  <div class="about"><div>{left}</div><div>{right}</div></div>
  {''.join(works_html)}
</article>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atelier</title><style>{CSS}</style></head><body>
<header class="top"><h1>Atelier</h1><p>Paintings made in code, one brush stroke at a time, by artists who do not exist. Each is a Python program that walks a simulated brush across a board. No image model, nothing traced. Drag the slider under a painting to watch it being made.</p></header>
<main>{''.join(parts)}</main>
<footer>{total} work{'s' if total != 1 else ''}. Painted by Claude.</footer>
<script>{JS}</script></body></html>"""
    (SITE / "index.html").write_text(page)
    print(f"gallery: {total} works -> {SITE / 'index.html'}")


if __name__ == "__main__":
    build()
