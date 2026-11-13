# Atelier

Work made in code by invented artists. The artists are the point: each has a life, rules they
work by, a medium they chose, and a kit of mechanisms that grows out of their own pieces.

## The one rule

Every work is made by a program in this repo, written by the artist. No image, video or sound
models, and no image, video or audio files as input. Nothing is rendered first and then traced
or sampled. An artist may know the geometry of a scene and how light falls in it (that is
drawing).

Anything else is the artist's choice: the medium, the language, the tools, what the work is.

## Media

There is no shared engine that everyone has to use. Each artist picks or builds a medium:
the stroke-based paint in `engine/`, something of their own in `artists/<slug>/`, a library,
a different language, a piece that moves, sounds, or responds to the viewer. Whatever it is
has to be specific enough to force decisions, and it belongs to that artist.

- `engine/` is the paint the first five artists chose: bristle strokes, wet and dry, tooth.
  Anyone may use it. Don't change what it does to work that already exists; if an artist wants
  paint to behave differently, they copy it into their own folder and change it there.
  `engine/CHANGES.md` is its history.
- An artist's own medium and mechanisms live in `artists/<slug>/` (`tools.py` or whatever
  suits). Another artist does not import them.
- Dependencies an artist adds go through `uv add` (Python) or are vendored in their folder, and
  the work must run again from a clean checkout.

## Layout

- `artists/<slug>/persona.md`: who they are, what they make, the rules they hold themselves to.
- `artists/<slug>/journal.md`: an entry after every work. What held, what didn't, what went into
  the kit, what comes next. The journal is how a persona changes over time, so write it honestly.
- `artists/<slug>/works/NNN-slug/`: one program per work, and what it writes beside itself.
- `gallery/build.py` builds `_site/`.

## What a work hands the gallery

Every work directory needs:

- `final.png`: the work as a still. For a piece that moves or responds, the frame that best
  stands for it.
- `work.json` with at least `title`. Optional: `year`, `medium` (wall-label text), `made`
  (date), `program` (the main file, default `paint.py`), `strokes` or `marks`, and `stages`
  (`[{"name", "file", "strokes"?}]`, stills of the work being made, in order).
- Optionally a `live` entry in `work.json` naming a file in the work directory (an `.html` page
  with everything it needs beside it, or a `.mp4`, `.webm`, `.mp3`, `.wav`). The gallery copies
  the file and its folder and shows it on the work's page.

`engine.studio.finish` writes all of this for engine paintings. Other media write it themselves.

## Making a work

1. Read the artist's persona and whole journal first. The next work answers the last entry.
2. Write the program. Save stills at each real phase so the gallery can show it being made.
3. Run it, look at the result, and critique it as a work: where does the eye or ear go, what is
   the loudest thing and should it be, which passage is weakest. Fix and rerun. Expect three or
   four rounds.
4. Write the journal entry. Record what is still wrong.
5. `uv run python gallery/build.py`.

## Making an artist

Whoever works as an artist invents that artist. Nobody assigns a persona, a subject, a medium or a
style; read the roster first and go somewhere it has not been.

A persona needs a reason to make things that a stranger could repeat back, a medium and a way of
working specific enough to force decisions, and a few rules that rule things out. Dates and a
place. No pastiche of a real artist. Do not start their kit until a work needs it.

`persona.md` opens with `# Name`, then one paragraph of dates and place, then at least a
`## What <they> make(s)` and a `## How <they> work(s)` section (any heading starting `What` and
`How` will do), which the gallery shows.

## Changing an artist

A persona belongs to whoever is working as them, and it is allowed to move, medium included. If
the work has outgrown a rule, break it in a work first, say why in that journal entry, and then
edit `persona.md` to match what the artist now is. Never rewrite old journal entries.

## Running

```bash
uv run python artists/nell-abara/works/001-vending-machine-0410/paint.py
uv run python gallery/build.py && open _site/index.html
```
