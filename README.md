# Atelier

Paintings made in code, one brush stroke at a time, by artists who do not exist.

**Gallery: https://ledbetterljoshua.github.io/atelier/**

Each painting is a Python program. It places every stroke through a small simulated paint engine:
a row of bristles that each carry their own colour and load, run dry, pick up wet paint from the
board, and skip over the tooth of the support when the brush is dry. No image model is involved,
and nothing is rendered first and traced.

The paintings are made by personas. Each has a life, a reason for painting, rules they keep, and
a kit of mechanisms that grows out of their own work. Their journals record what each picture
taught them. Whoever paints as an artist invented that artist, and is free to change them.

## Artists

- **Nell Abara** (b. 1961, Bradford). Night porter. Paints things left on, between two and five in
  the morning, on the rough side of hardboard offcuts primed black.
  [persona](artists/nell-abara/persona.md) · [journal](artists/nell-abara/journal.md)
- **Zala Hrovat** (b. 1951, Tolmin). River gauge reader. Paints the Soča straight down from the
  bridge parapet: the bed first, as if the river were turned off, then the water back in as glazes,
  one per depth.
  [persona](artists/zala-hrovat/persona.md) · [journal](artists/zala-hrovat/journal.md)
- **Carmela Zammit** (b. 1949, Ħamrun). Laundry worker. Paints the washing on the roof with the low
  sun behind it, because the cloth is the only way to see the wind.
  [persona](artists/carmela-zammit/persona.md) · [journal](artists/carmela-zammit/journal.md)
- **Gavino Cossu** (b. 1968, Castelsardo). Cork mill worker who sang contra in a Holy Week choir
  until his hearing went. Paints the chant from inside the four voices: time left to right, pitch
  up the board, one brushload per breath.
  [persona](artists/gavino-cossu/persona.md) · [journal](artists/gavino-cossu/journal.md)

## Run it

```bash
uv sync
uv run python artists/nell-abara/works/001-vending-machine-0410/paint.py
uv run python gallery/build.py && open _site/index.html
```

How the project is worked on is in [CLAUDE.md](CLAUDE.md).
