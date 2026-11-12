# Atelier

Paintings made stroke by stroke in Python, by invented artists. The artists are the point: each
has a life, rules they paint by, and a kit of mechanisms that grows out of their own pictures.

## The one rule

Every mark is a stroke through `engine/`. No image models, no image files as input, and no
rendering a picture first and tracing or sampling it. An artist may know the geometry of a scene
and how light falls in it (that is drawing), and mixes each stroke's colour for where it lands.

## Layout

- `engine/` is shared and small: the board, the brush, colour, paths, supports. It changes only
  when paint itself should behave differently for everyone. Run `uv run python tools/swatch.py`
  after touching it and look at `.scratch/swatch.png`.
- `artists/<slug>/persona.md`: who they are, what they paint, the rules they hold themselves to.
- `artists/<slug>/tools.py`: mechanisms that artist developed. Another artist does not import it.
  If two artists need the same thing, it has earned a place in `engine/`.
- `artists/<slug>/journal.md`: an entry after every work. What held, what didn't, what went into
  the kit, what comes next. The journal is how a persona changes over time, so write it honestly.
- `artists/<slug>/works/NNN-slug/paint.py`: one program per painting. It writes `final.png`,
  `stages/`, and `work.json` beside itself via `engine.studio.finish`.
- `gallery/build.py` builds `_site/`.

## Making a work

1. Read the artist's persona and whole journal first. The next picture answers the last entry.
2. Write `paint.py`. Call `board.stage("...")` at each real phase so the gallery can show the
   picture being made.
3. Run it, look at `final.png`, and critique it as a painting: where does the eye go, what is the
   brightest thing and should it be, which passage is weakest. Fix and rerun. Expect three or four
   rounds.
4. Write the journal entry. Record what is still wrong.
5. `uv run python gallery/build.py`.

## Making an artist

Whoever paints as an artist invents that artist. Nobody assigns a persona, a subject or a style;
read the roster first and go somewhere it has not been.

A persona needs a reason to paint that a stranger could repeat back, a support and a way of
working specific enough to force engine or kit decisions, and a few rules that rule things out.
Dates and a place. No pastiche of a real painter. Do not start their kit until a picture needs it.

`persona.md` opens with `# Name`, then one paragraph of dates and place, then at least a
`## What <they> paint(s)` and a `## How <they> paint(s)` section, which the gallery shows.

## Changing an artist

A persona belongs to whoever is painting as them, and it is allowed to move. If the work has
outgrown a rule, break it in a picture first, say why in that journal entry, and then edit
`persona.md` to match what the artist now is. Never rewrite old journal entries.

## Asking for engine changes

When several painters are working at once, nobody edits `engine/`. Work around it in your own
`tools.py` and write what you wanted under `Asked of the engine` in the journal entry.
Between rounds the requests that more than one painter needs, or that paint plainly lacks, are
built and logged in `engine/CHANGES.md`. Read it before you start.

## Running

```bash
uv run python artists/nell-abara/works/001-vending-machine-0410/paint.py
uv run python gallery/build.py && open _site/index.html
```
