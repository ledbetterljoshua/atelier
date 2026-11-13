"""Build the gallery into _site/ from the repo's own files.

Pages: the index (every artist with their works hung in a row), one page per artist (persona, the
works in order with what each one changed, the kit), one page per work (the painting, its stages,
its wall label, its journal entry) and an about page (the rule, the engine log). Nothing here is
written by hand per artist or per work: a new directory under artists/ appears on the next build.
"""
import ast
import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = ROOT / "_site"
REPO = "https://github.com/ledbetterljoshua/atelier"
URL = os.environ.get("ATELIER_URL", "https://ledbetterljoshua.github.io/atelier/")
FONTS = ("https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600"
         "&family=Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..600&display=swap")
STANDARD = ("what held", "what didn't", "into the kit", "asked of the engine", "next", "still wrong")

esc = html.escape


# ---------------------------------------------------------------- markdown

def inline(s, code=None):
    """Inline markdown. `code(name)` may return a URL to link a code span to."""
    s = esc(s, quote=False)

    def codespan(m):
        body = m.group(1)
        href = code(html.unescape(body)) if code else None
        return f'<a class="mech" href="{href}"><code>{body}</code></a>' if href else f"<code>{body}</code>"

    s = re.sub(r"`(.+?)`", codespan, s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", s)


def md(text, code=None, h=3):
    """Enough markdown for a persona, a journal or the engine log."""
    out, para, quote, in_list = [], [], [], False

    def flush():
        nonlocal para, quote, in_list
        if para:
            out.append(f"<p>{inline(' '.join(para), code)}</p>")
        if quote:
            out.append(f"<blockquote><p>{inline(' '.join(quote), code)}</p></blockquote>")
        if in_list:
            out.append("</li></ul>")
        para, quote, in_list = [], [], False

    for line in text.splitlines() + [""]:
        if line.startswith(">"):
            if not quote:
                flush()
            quote.append(line.lstrip("> ").strip())
        elif line.startswith("#"):
            flush()
            n = min(6, len(line) - len(line.lstrip("#")) - 2 + h)
            out.append(f"<h{n}>{inline(line.lstrip('# '), code)}</h{n}>")
        elif line.startswith("- "):
            if para or quote:
                flush()
            out.append("</li><li>" if in_list else "<ul><li>")
            in_list = True
            out.append(inline(line[2:].strip(), code))
        elif line.startswith("  ") and in_list and line.strip():
            out.append(" " + inline(line.strip(), code))
        elif not line.strip():
            flush()
        else:
            if quote or in_list:
                flush()
            para.append(line.strip())
    return "\n".join(out)


def sections(text):
    """[(heading, body)] for every `## ` section; text before the first one is under ''."""
    parts = re.split(r"^## +(.+?)[ \t]*$", text, flags=re.M)
    out = [("", parts[0].strip())]
    out += [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]
    return out


def plain(s):
    """Markdown to plain text, for meta descriptions."""
    return re.sub(r"\s+", " ", re.sub(r"[*`>]", "", s)).strip()


def first_sentences(s, n=1):
    return " ".join(re.split(r"(?<=[.!?])\s+", s.strip())[:n])


def clip(s, n=200):
    s = plain(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


# ---------------------------------------------------------------- reading the repo

def kit(path):
    """Public names in an artist's tools.py, each with the first sentence of its docstring."""
    if not path.exists():
        return []
    out = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            doc = (ast.get_docstring(node) or "").split("\n\n")[0].replace("\n", " ")
            out.append({"name": node.name, "doc": first_sentences(doc) if doc else "",
                        "kind": "class" if isinstance(node, ast.ClassDef) else "def", "work": None})
    return out


def entry_parts(text):
    """Split a journal entry into (lead, [(label, body)]) on paragraphs that open `**Label.**`."""
    lead, parts = [], []
    for block in re.split(r"\n\s*\n", text.strip()):
        m = re.match(r"\*\*([^*]+?)[.:]?\*\*[ \t]*\n?(.*)", block, re.S)
        if m and (len(m.group(1)) < 60):
            parts.append([m.group(1).strip(), m.group(2).strip()])
        elif parts:
            parts[-1][1] += "\n\n" + block
        else:
            lead.append(block)
    return "\n\n".join(lead), [(a, b) for a, b in parts]


def part(work, label):
    return next((b for a, b in work["parts"] if a.lower() == label), "")


def mean_colour(im):
    r, g, b = im.convert("RGB").resize((1, 1), Image.BOX).getpixel((0, 0))
    return r, g, b


def lum(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255


def wall(mean, base, tint=0.14):
    """A wall for one picture: a neutral, leaning a little toward the picture's own average."""
    k = lum(base) / max(lum(mean), 0.02)
    mix = [min(255, round(b * (1 - tint) + min(255, m * k) * tint)) for b, m in zip(base, mean)]
    return "#%02x%02x%02x" % tuple(mix)


def images(wdir, w, out):
    """Sized WebP files for a work and its stages. Returns the stage list with their files."""
    out.mkdir(parents=True, exist_ok=True)
    final = Image.open(wdir / "final.png").convert("RGB")
    final.save(out / "full.webp", quality=90, method=4)
    stages = []
    last = len(w["stages"]) - 1
    for i, s in enumerate(w["stages"]):
        src = wdir / s.get("file", "")
        im = final if i == last or not src.exists() else Image.open(src).convert("RGB")
        im = im.copy()
        im.thumbnail((1280, 1280), Image.LANCZOS)
        im.save(out / f"s{i:02d}.webp", quality=82, method=4)
        stages.append({"name": s["name"], "strokes": s.get("strokes"), "file": f"s{i:02d}.webp"})
    small = final.copy()
    small.thumbnail((640, 640), Image.LANCZOS)
    small.save(out / "small.webp", quality=80, method=4)
    og = final.copy()
    og.thumbnail((1200, 1200), Image.LANCZOS)
    og.save(out / "og.jpg", quality=84)
    live = w.get("live")
    if live and (wdir / live).exists():
        src = (wdir / live).parent
        if src == wdir:
            shutil.copy(wdir / live, out / Path(live).name)
        else:
            shutil.copytree(src, out / src.relative_to(wdir), dirs_exist_ok=True)
    return stages, mean_colour(small)


def load():
    artists = []
    for adir in sorted((ROOT / "artists").iterdir()):
        if not (adir / "persona.md").exists() or not (adir / "works").is_dir():
            continue
        persona = (adir / "persona.md").read_text()
        secs = sections(persona)
        head = secs[0][1]
        name = head.splitlines()[0].lstrip("# ").strip()
        intro = " ".join(head.split("\n\n", 1)[1].split()) if "\n\n" in head else ""
        born = re.match(r"(b\. [^.]+)\.", intro)
        journal = (adir / "journal.md").read_text() if (adir / "journal.md").exists() else ""
        jsecs = sections(journal)
        a = {"slug": adir.name, "name": name, "first": name.split()[0], "intro": intro,
             "born": born.group(1) if born else "", "sections": secs[1:], "works": [],
             "kit": kit(adir / "tools.py"),
             "quote": (re.search(r"^> *(.+?)(?=\n\n|\Z)", persona, re.S | re.M) or [None, ""])[1]}
        a["quote"] = " ".join(x.lstrip("> ").strip() for x in a["quote"].splitlines()).strip('"“” ')
        for wdir in sorted((adir / "works").iterdir()):
            if not (wdir / "work.json").exists() or not (wdir / "final.png").exists():
                continue
            w = json.loads((wdir / "work.json").read_text())
            w.setdefault("stages", [{"name": "finished", "file": "final.png"}])
            if "size" not in w:
                with Image.open(wdir / "final.png") as im:
                    w["size"] = list(im.size)
            prog = w.get("program", "paint.py")
            num = wdir.name.split("-")[0]
            entry = next((b for h, b in jsecs if h.startswith(f"{num}.")), "")
            lead, parts = entry_parts(entry)
            src = (wdir / prog).read_text() if (wdir / prog).is_file() else ""
            stages, mean = images(wdir, w, SITE / adir.name / wdir.name)
            dark = lum(mean) < 0.28
            a["works"].append({
                "dir": wdir.name, "num": num, "title": w["title"], "year": w.get("year", ""),
                "medium": w.get("medium", ""), "size": w["size"], "strokes": w.get("strokes"),
                "marks": w.get("marks", "strokes"), "program": prog, "live": w.get("live"),
                "made": w.get("made", ""), "stages": stages, "lead": lead, "parts": parts,
                "lines": src.count("\n"), "dark": dark,
                "wall_l": wall(mean, (44, 42, 39) if dark else (228, 224, 216)),
                "wall_d": wall(mean, (30, 29, 27), 0.10),
                "uses": [k["name"] for k in a["kit"] if re.search(rf"\b{re.escape(k['name'])}\b", src)],
                "url": f"{adir.name}/{wdir.name}/", "artist": a})
        if not a["works"]:
            continue
        # Which work each mechanism came out of: the first entry that names it in backticks.
        for k in a["kit"]:
            pat = re.compile(rf"`[^`]*\b{re.escape(k['name'])}\b[^`]*`")
            for prefer in (True, False):
                for w in a["works"]:
                    text = part(w, "into the kit") if prefer else "\n".join(b for _, b in w["parts"])
                    if pat.search(text):
                        k["work"] = w["num"]
                        break
                if k["work"]:
                    break
        artists.append(a)
    return artists


def engine_rounds(artists):
    """Rounds from engine/CHANGES.md: [(title, {artist slug: work num}, [(item title, text, built)])]."""
    path = ROOT / "engine" / "CHANGES.md"
    if not path.exists():
        return "", []
    secs = sections(path.read_text())
    rounds = []
    for head, body in secs[1:]:
        after = {}
        for a in artists:
            m = re.search(rf"\b{re.escape(a['first'])} (\d{{3}})\b", head)
            if m:
                after[a["slug"]] = m.group(1)
        items, built = [], True
        for block in re.split(r"\n(?=- |\S)", body):
            if not block.startswith("- "):
                built = not block.lower().startswith("not built")
                continue
            text = " ".join(block[2:].split())
            m = re.match(r"\*\*(.+?)\.?\*\*\s*(.*)", text)
            items.append((m.group(1) if m else first_sentences(text), m.group(2) if m else "", built))
        rounds.append((re.sub(r"\s*\(.*\)$", "", head), after, items))
    return secs[0][1], rounds


# ---------------------------------------------------------------- html

def page(root, title, desc, body, og="", cls=""):
    full = f"{title} · Atelier" if title else "Atelier"
    ogtag = f'<meta property="og:image" content="{URL}{og}"><meta name="twitter:card" content="summary_large_image">' if og else ""
    icon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' "
            "fill='%231b1a17'/%3E%3Cpath d='M7 22c5-9 11-11 18-12' stroke='%23e9e4d9' stroke-width='4' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">{ogtag}
<meta name="color-scheme" content="light dark"><link rel="icon" href="{icon}">
<script>(function(){{var t;try{{t=localStorage.getItem('atelier-theme')}}catch(e){{}}document.documentElement.dataset.theme=t||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light')}})()</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="{root}site.css">
</head><body class="{cls}">
<a class="skip" href="#main">Skip to content</a>
<header class="bar"><a class="home" href="{root}">Atelier</a>
<nav><a href="{root}#artists">Artists</a><a href="{root}about/">About</a>
<button class="theme" type="button" aria-label="Switch between light and dark"><span aria-hidden="true"></span></button></nav></header>
<main id="main">{body}</main>
<footer class="foot"><p>Paintings made in code, one brush stroke at a time, by artists who do not exist. Painted by Claude.</p>
<p><a href="{root}about/">About</a> · <a href="{REPO}">Source on GitHub</a></p></footer>
<script src="{root}site.js" defer></script></body></html>"""


def write(rel, text):
    path = SITE / rel / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def plural(n, word):
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def hang(works, root, sizes="(max-width:700px) 60vw, 360px", show_artist=False):
    """Works hung in a row at one height, each with a short label."""
    out = []
    for w in works:
        ar = w["size"][0] / w["size"][1]
        who = f'<span class="who">{esc(w["artist"]["name"])}</span>' if show_artist else ""
        out.append(f"""<a class="piece" href="{root}{w['url']}" style="--ar:{ar:.4f}">
<span class="board"><img src="{root}{w['url']}small.webp" alt="" width="{w['size'][0]}" height="{w['size'][1]}" loading="lazy" decoding="async" sizes="{sizes}"></span>
<span class="cap">{who}<i>{esc(w['title'])}</i><span class="yr">{w['year']}</span></span></a>""")
    return f'<div class="hangrow">{"".join(out)}</div>'


def index_page(artists):
    total = sum(len(a["works"]) for a in artists)
    rows = []
    for a in artists:
        what = next((b for h, b in a["sections"] if re.match(r"what (?!.* not$)", h, re.I)), "")
        what = what.split("\n\n")[0]
        rows.append(f"""<section class="room-row" id="{a['slug']}">
<div class="who"><h2><a href="{a['slug']}/">{esc(a['name'])}</a></h2>
<p class="born">{esc(a['born'])}</p>
<p class="what">{inline(' '.join(what.split()))}</p>
<p class="more"><a href="{a['slug']}/">{plural(len(a['works']), 'work')}, the journal and the kit</a></p></div>
{hang(a['works'], '')}
</section>""")
    blurb = ("Work made in code by artists who do not exist. Each piece is a program the artist wrote, in a "
             "medium they chose. No image model, nothing traced.")
    body = f"""<section class="mast">
<h1>Atelier</h1>
<div class="lede"><p>Work made in code by artists who do not exist.</p>
<p class="sub">Each piece is a program its artist wrote, in a medium the artist chose: so far, mostly a simulated brush whose bristles carry their own colour, run dry, and pick up wet paint. No image model is involved and nothing is traced. The artists are invented by the model that works as them. Each keeps a journal, and the journal changes how the next piece is made.</p>
<p class="count">{plural(len(artists), 'artist')} · {plural(total, 'work')}</p></div>
</section>
<div id="artists">{''.join(rows)}</div>"""
    cover = artists[0]["works"][-1]["url"] + "og.jpg" if artists else ""
    (SITE / "index.html").write_text(page("", "", blurb, body, cover, "p-index"))


def timeline(a, rounds):
    """The works in order: what each entry said, what went into the kit, and what the engine built in reply."""
    items = []
    works = a["works"]
    for i, w in enumerate(works):
        added = [k for k in a["kit"] if k["work"] == w["num"]]
        chips = "".join(f'<a class="chip" href="#kit-{k["name"]}"><code>{esc(k["name"])}</code></a>' for k in added)
        moved = []
        for label, body in w["parts"]:
            for para in body.split("\n\n"):
                if re.search(r"persona\b.{0,12}\b(says so|says both|changed|now says)|persona changed", para, re.I):
                    sents = re.split(r"(?<=[.!?])\s+", " ".join(para.split()))
                    hit = max(j for j, s in enumerate(sents) if "ersona" in s)
                    text = " ".join(sents[max(0, hit - 1):hit + 1])
                    head = f"<b>{esc(label)}.</b> " if label.lower() not in STANDARD else ""
                    moved.append(f"<p>{head}{inline(text)}</p>")
        nxt = part(w, "next")
        ar = w["size"][0] / w["size"][1]
        items.append(f"""<li class="t-work">
<div class="t-no"><span>{w['num']}</span><span>{w['year']}</span></div>
<a class="t-img" href="../{w['url']}" style="--ar:{ar:.4f}"><img src="../{w['url']}small.webp" alt="" width="{w['size'][0]}" height="{w['size'][1]}" loading="lazy" decoding="async"></a>
<div class="t-body"><h3><a href="../{w['url']}"><i>{esc(w['title'])}</i></a></h3>
<p class="t-meta">{esc(w['medium'])}{f" · {w['strokes']:,} {w['marks']}" if w['strokes'] else ''}</p>
{f'<p class="t-lead">{inline(" ".join(w["lead"].split()))}</p>' if w['lead'] else ''}
{f'<div class="t-block"><h4>The persona moved</h4>{"".join(moved)}</div>' if moved else ''}
{f'<div class="t-block"><h4>Into the kit</h4><p class="chips">{chips}</p></div>' if chips else ''}
{f'<div class="t-block t-next"><h4>{"Next, " + esc(a["first"]) + " wrote" if i < len(works) - 1 else "Next"}</h4>{md(nxt)}</div>' if nxt else ''}
</div></li>""")
        for title, after, ritems in rounds:
            if after.get(a["slug"]) != w["num"]:
                continue
            mine = [(t, x, b) for t, x, b in ritems if re.search(rf"\b{re.escape(a['first'])}\b", x) or "all three" in x]
            if not mine:
                continue
            lis = "".join(f"<li>{inline(t)}{'' if b else ' (not built)'}</li>" for t, x, b in mine)
            items.append(f"""<li class="t-engine"><div class="t-no"><span>Engine</span></div>
<div class="t-body"><h4>{esc(title)} of engine changes. {esc(a['first'])} had asked for</h4><ul>{lis}</ul>
<p class="t-more"><a href="../about/#engine">The whole engine log</a></p></div></li>""")
    return f'<ol class="timeline">{"".join(items)}</ol>'


def artist_page(a, rounds):
    def kit_link(name):
        base = re.match(r"\w+", name)
        return f"#kit-{base.group(0)}" if base and any(k["name"] == base.group(0) for k in a["kit"]) else None

    cols, rest, mech = [], [], ""
    for h, b in a["sections"]:
        if re.match(r"(what|how) (?!.* not$)", h, re.I):
            cols.append(f'<section><h2>{esc(h)}</h2>{md(b, kit_link)}</section>')
        elif re.match(r"mechanisms", h, re.I):
            mech = b
        else:
            rest.append(f'<section><h2>{esc(h)}</h2>{md(b, kit_link)}</section>')
    groups = []
    for w in a["works"] + [None]:
        ks = [k for k in a["kit"] if k["work"] == (w["num"] if w else None)]
        if not ks:
            continue
        head = (f'<a href="../{w["url"]}">{w["num"]}. <i>{esc(w["title"])}</i></a>' if w
                else "Helpers the journal does not name")
        rows = "".join(f'<div class="k" id="kit-{k["name"]}"><dt><code>{esc(k["name"])}</code></dt><dd>{inline(k["doc"])}</dd></div>' for k in ks)
        groups.append(f'<div class="kgroup"><h3>{head}</h3><dl>{rows}</dl></div>')
    kit_html = f"""<section class="kit" id="kit"><header class="sec"><h2>The kit</h2>
<p>{plural(len(a['kit']), 'mechanism')} {esc(a['first'])} built, grouped by the picture each came out of. Nobody else uses them. <a href="{REPO}/blob/main/artists/{a['slug']}/tools.py">tools.py</a></p></header>
{f'<div class="mechnote">{md(mech)}</div>' if mech else ''}
{''.join(groups)}</section>""" if a["kit"] else ""
    body = f"""<header class="a-head">
<p class="crumb"><a href="../#artists">Artists</a></p>
<h1>{esc(a['name'])}</h1>
<p class="intro">{inline(a['intro'])}</p>
{f'<blockquote class="pull"><p>{inline(a["quote"])}</p></blockquote>' if a['quote'] else ''}
<p class="count">{plural(len(a['works']), 'work')} · <a href="#works">Work by work</a>{' · <a href="#kit">The kit</a>' if a['kit'] else ''}</p>
</header>
{hang(a['works'], '../')}
<div class="persona">{''.join(cols)}</div>
{f'<div class="persona minor">{"".join(rest)}</div>' if rest else ''}
<section class="works" id="works"><header class="sec"><h2>Work by work</h2>
<p>Each picture answers the last journal entry. This is the order they were made in, with what each one added to the kit and what it changed in the rules.</p></header>
{timeline(a, rounds)}</section>
{kit_html}"""
    desc = clip(f"{a['intro']}", 220)
    write(a["slug"], page("../", a["name"], desc, body, a["works"][-1]["url"] + "og.jpg", "p-artist"))


def nice_date(s):
    try:
        d = date.fromisoformat(s)
        return f"{d.day} {d.strftime('%B %Y')}"
    except ValueError:
        return s


def work_page(w, prev, nxt):
    a = w["artist"]
    root = "../../"
    ww, wh = w["size"]
    n = len(w["stages"])

    def kit_link(name):
        base = re.match(r"\w+", name)
        return f"{root}{a['slug']}/#kit-{base.group(0)}" if base and any(k["name"] == base.group(0) for k in a["kit"]) else None

    rows, before = [], 0
    counted = all(s.get("strokes") is not None for s in w["stages"])
    cum = [s["strokes"] if counted else 0 for s in w["stages"]]
    top = max([c - p for c, p in zip(cum, [0] + cum[:-1])] + [1])
    for i, s in enumerate(w["stages"]):
        add = cum[i] - before
        before = cum[i]
        rows.append(f"""<li><button type="button" data-i="{i}"{' aria-current="true"' if i == n - 1 else ''}>
<span class="s-n">{i + 1}</span><span class="s-name">{esc(s['name'])}</span>
<span class="s-add">{'+' + format(add, ',') if add else '·'}</span>
<span class="s-bar" style="--f:{add / top:.4f}"></span></button></li>""")
    entry = []
    if w["lead"]:
        entry.append(f'<div class="e-lead">{md(w["lead"], kit_link)}</div>')
    for label, body in w["parts"]:
        entry.append(f'<section class="e-part{" e-next" if label.lower() == "next" else ""}"><h3>{esc(label)}</h3><div>{md(body, kit_link)}</div></section>')
    asked = part(prev, "next") if prev else ""
    uses = ""
    if w["uses"]:
        names = ", ".join(f'<a class="mech" href="{root}{a["slug"]}/#kit-{k}"><code>{esc(k)}</code></a>' for k in w["uses"])
        uses = f'<p class="l-uses">Uses {len(w["uses"])} of the {len(a["kit"])} mechanisms in {esc(a["first"])}\'s kit: {names}.</p>'
    src = f"{REPO}/blob/main/artists/{a['slug']}/works/{w['dir']}/{w['program']}"
    lang = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".ts": "TypeScript", ".html": "HTML",
            ".rs": "Rust", ".glsl": "GLSL", ".frag": "GLSL", ".go": "Go", ".c": "C", ".jl": "Julia",
            ".pde": "Processing", ".lua": "Lua", ".rb": "Ruby", ".sc": "SuperCollider"}.get(Path(w["program"]).suffix, "")
    count = f"{w['strokes']:,} {w['marks']}" if w["strokes"] else ""
    live = ""
    if w["live"]:
        ext = Path(w["live"]).suffix.lower()
        if ext in (".mp4", ".webm"):
            live = f'<video controls playsinline preload="metadata" poster="s{n - 1:02d}.webp" src="{esc(w["live"])}"></video>'
        elif ext in (".mp3", ".wav", ".ogg", ".m4a"):
            live = f'<audio controls preload="metadata" src="{esc(w["live"])}"></audio>'
        else:
            live = f'<iframe src="{esc(w["live"])}" title="{esc(w["title"])}, live" loading="lazy" style="aspect-ratio:{ww / wh:.4f}"></iframe>'
        live = f'<section class="live" aria-label="The piece itself">{live}<p><a href="{esc(w["live"])}">Open the piece on its own</a></p></section>'
    marks_json = w["marks"] if w["strokes"] else ""
    stages_json = json.dumps({"w": ww, "h": wh, "full": "full.webp", "title": w["title"],
                              "marks": marks_json, "stages": w["stages"]}).replace("</", "<\\/")

    def pager(x, rel, word):
        if not x:
            return "<span></span>"
        return (f'<a rel="{rel}" class="{rel}" href="{root}{x["url"]}"><span>{word}</span>'
                f'<i>{esc(x["title"])}</i></a>')

    body = f"""<section class="room{' room-dark' if w['dark'] else ''}" style="--wall-l:{w['wall_l']};--wall-d:{w['wall_d']}">
<div class="room-in">
<figure class="hung" style="--ar:{ww / wh:.4f}">
<a class="canvas" href="full.webp" aria-label="Look closer at the painting">
<img class="base" src="s{n - 1:02d}.webp" srcset="small.webp 640w, s{n - 1:02d}.webp 1280w" sizes="(max-width:900px) 100vw, 70vw" width="{ww}" height="{wh}" alt="{esc(w['title'])}, by {esc(a['name'])}" fetchpriority="high">
<img class="over" alt="" width="{ww}" height="{wh}" hidden></a>
<figcaption><span class="now" aria-live="polite">Finished{' · ' + count if count else ''}</span>
<span class="acts"><button type="button" class="play" aria-pressed="false">Play</button><button type="button" class="zoom">Look closer</button></span></figcaption>
</figure>
<aside class="making" aria-label="How it was made">
<div class="m-head"><h2>How it was made</h2></div>
<p class="m-note">{plural(n, 'stage')}, in the order the program made them.{f" The bar is how many {w['marks']} each one took." if counted and w['strokes'] else ''} Play runs through them.</p>
<ol class="stages">{''.join(rows)}</ol>
</aside>
</div>
</section>
{live}
<div class="sheet">
<aside class="label">
<p class="l-artist"><a href="{root}{a['slug']}/">{esc(a['name'])}</a><span>{esc(a['born'])}</span></p>
<h1><i>{esc(w['title'])}</i>{f', {w["year"]}' if w['year'] else ''}</h1>
<p class="l-medium">{esc(w['medium'])}<br>{ww:,} × {wh:,} px</p>
<p class="l-code">{count + ' in ' + plural(n, 'stage') + '.<br>' if count else ''}Made by <a href="{src}">a {w['lines']:,}-line {lang + ' ' if lang else ''}program</a>{f', run on {nice_date(w["made"])}' if w['made'] else ''}.</p>
{uses}
</aside>
<article class="entry">
<header><h2>From {esc(a['first'])}'s journal</h2>
{f'<div class="e-asked"><p class="e-k">After <a href="{root}{prev["url"]}">{prev["num"]}</a>, the journal said</p>{md(asked, kit_link)}</div>' if asked else ''}
</header>
{''.join(entry) if entry else '<p class="e-none">No journal entry yet.</p>'}
</article>
</div>
<nav class="pager" aria-label="More by {esc(a['name'])}">{pager(prev, 'prev', 'Before')}<a class="up" href="{root}{a['slug']}/">{esc(a['name'])}</a>{pager(nxt, 'next', 'After')}</nav>
<script type="application/json" id="work">{stages_json}</script>
<dialog class="viewer" aria-label="{esc(w['title'])}, close view">
<div class="v-stage"><img alt="" draggable="false"></div>
<div class="v-bar"><span class="v-title"><i>{esc(w['title'])}</i><span class="v-stage-name"></span></span>
<span class="v-ctl"><button type="button" data-z="out" aria-label="Zoom out">−</button><button type="button" data-z="fit" class="v-pct">Fit</button><button type="button" data-z="in" aria-label="Zoom in">+</button><button type="button" data-z="close" class="v-close">Close</button></span></div>
</dialog>"""
    desc = clip(f"{a['name']}. {w['medium']}. {count + '. ' if count else ''}{w['lead']}", 220)
    title = f"{w['title']} · {a['name']}"
    write(Path(a["slug"]) / w["dir"], page(root, title, desc, body, w["url"] + "og.jpg", "p-work"))


def about_page(artists, intro, rounds_md):
    readme = (ROOT / "README.md").read_text() if (ROOT / "README.md").exists() else ""
    what = sections(readme)[0][1]
    what = "\n\n".join(p for p in what.split("\n\n")[1:] if not p.startswith("**Gallery"))
    claude = (ROOT / "CLAUDE.md").read_text() if (ROOT / "CLAUDE.md").exists() else ""
    cs = dict(sections(claude))
    firsts = {a["first"]: a["slug"] for a in artists}

    def link_names(h):
        return re.sub(r"\b(" + "|".join(map(re.escape, firsts)) + r")\b(?![^<]*</(?:code|a)>)",
                      lambda m: f'<a href="../{firsts[m.group(1)]}/">{m.group(1)}</a>', h) if firsts else h

    blocks = []
    for h in ("The one rule", "Media", "Making an artist", "Changing an artist"):
        if cs.get(h):
            blocks.append(f'<section class="e-part"><h3>{esc(h)}</h3><div>{md(cs[h])}</div></section>')
    path = ROOT / "engine" / "CHANGES.md"
    log = path.read_text().split("\n", 1)[1] if path.exists() else ""
    body = f"""<header class="a-head"><h1>About</h1></header>
<article class="entry about">
<div class="e-lead">{md(what)}</div>
{''.join(blocks)}
<p class="e-src">These are the project's own working rules, from <a href="{REPO}/blob/main/CLAUDE.md">CLAUDE.md</a>. The source for every painting, persona and journal is on <a href="{REPO}">GitHub</a>.</p>
</article>
<article class="entry about" id="engine">
<header><h2>The paint engine</h2></header>
<div class="e-lead"><p>The first five artists all chose the same medium: a small simulated paint engine with a board, a brush, colour, paths and supports. While they shared it, they wrote what they wanted in their journals, and between rounds the things more than one of them needed were built. This is the log of those rounds. Artists are no longer bound to it: each picks or builds their own medium, and the engine is one choice among many.</p></div>
<div class="log">{link_names(md(log, h=3))}</div>
</article>"""
    desc = "How Atelier works: the one rule, how an artist is invented and chooses a medium, and the history of the paint engine."
    write("about", page("../", "About", desc, body, cls="p-about"))


def build():
    SITE.mkdir(parents=True, exist_ok=True)
    for old in SITE.iterdir():  # emptied, not replaced, so a server already running in it keeps working
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    artists = load()
    intro, rounds = engine_rounds(artists)
    index_page(artists)
    for a in artists:
        artist_page(a, rounds)
        for i, w in enumerate(a["works"]):
            work_page(w, a["works"][i - 1] if i else None, a["works"][i + 1] if i + 1 < len(a["works"]) else None)
    about_page(artists, intro, rounds)
    for f in ("site.css", "site.js"):
        shutil.copy(HERE / f, SITE / f)
    (SITE / ".nojekyll").write_text("")
    total = sum(len(a["works"]) for a in artists)
    size = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file()) / 1e6
    print(f"gallery: {len(artists)} artists, {total} works, {size:.1f} MB -> {SITE / 'index.html'}")


if __name__ == "__main__":
    build()
