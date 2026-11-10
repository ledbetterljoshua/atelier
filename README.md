# Atelier

Paintings made in code, one brush stroke at a time, by artists who do not exist.

Each painting is a Python program. It places every stroke through a small simulated paint engine:
a row of bristles that each carry their own colour and load, run dry, pick up wet paint from the
board, and skip over the tooth of the support when the brush is dry. No image model is involved,
and nothing is rendered first and traced.

The paintings are made by personas. Each has a life, a reason for painting, rules they keep, and
a kit of mechanisms that grows out of their own work. Their journals record what each picture
taught them.

## Artists

- **Nell Abara** (b. 1961, Bradford). Night porter. Paints things left on, between two and five in
  the morning, on the rough side of hardboard offcuts primed black.
  [persona](artists/nell-abara/persona.md) · [journal](artists/nell-abara/journal.md)

## Run it

```bash
uv sync
uv run python artists/nell-abara/works/001-vending-machine-0410/paint.py
uv run python gallery/build.py && open _site/index.html
```

How the project is worked on is in [CLAUDE.md](CLAUDE.md).
