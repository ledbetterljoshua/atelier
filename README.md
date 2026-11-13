# Atelier

Work made in code by artists who do not exist.

**Gallery: https://ledbetterljoshua.github.io/atelier/**

Each artist is a persona with a life, a reason for making things, rules they keep, and a medium
they chose. Every work is a program the artist wrote. No image, video or sound model is involved,
no image is used as input, and nothing is rendered first and traced. Past that, the medium is the
artist's call, and they can change it.

So far every artist has chosen the same one: a small simulated paint engine (`engine/`) that walks
a row of bristles across a board. Each bristle carries its own colour and load, runs dry, picks up
wet paint, and skips over the tooth of the support when the brush is dry.

Each artist's kit of mechanisms grows out of their own work, and their journals record what each
piece taught them. Whoever works as an artist invented that artist, and is free to change them.

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
- **Itzel Moroyoqui** (b. 1999, Hermosillo). Delivery rider who left architecture school. Paints the
  midday shade she waits in between lunch orders, in acrylic on plywood offcuts: light first, in
  hard strokes, and colour allowed to run together only inside the shade.
  [persona](artists/itzel-moroyoqui/persona.md) · [journal](artists/itzel-moroyoqui/journal.md)

## Run it

```bash
uv sync
uv run python artists/nell-abara/works/001-vending-machine-0410/paint.py
uv run python gallery/build.py && open _site/index.html
```

How the project is worked on is in [CLAUDE.md](CLAUDE.md).
