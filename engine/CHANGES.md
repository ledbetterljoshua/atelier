# Engine changes

What changed in shared paint, and which painter's work asked for it. Existing works must render
pixel-identical after any change here.

## Round 1 (after Nell 002, Zala 001, Carmela 001)

- **Colour along a stroke.** `board.stroke(pts, brush, color)` takes one colour, a list of colours
  spread evenly along the stroke, or `fn(t) -> colour`. Bristles keep their own streaks and still
  pick up wet paint. Asked by Zala (glazes crossing depth) and Carmela (folds running from shadow
  into light).
- **Tape that combines.** `tape(..., mode=)` and the new `tape_where(region, ...)` take
  `"replace"` (default), `"and"`, `"or"` or `"cut"`. `tape_where` takes an (h, w) array or
  `fn(X, Y) -> 0..1`. Asked by all three: Nell (floor and the lit side of a shadow at once), Zala
  (a worked-out region), Carmela (inside and outside together).
- **Levelling.** `Brush(level=1.0)` lets paint settle flat and glossy: it takes the relief and the
  board's tooth out from under it in the render. For standing water and glass. Asked by Nell.
- **Light.** `Board(..., light=(lx, ly))` or `board.light` sets where the raking light comes from
  for every stage and the final. Asked by Zala. Glazes already leave no body; `thickness` only
  applies to opaque paint.

## Round 2 (after Nell 003, Zala 002, Carmela 002, Gavino 001)

- **Both edges of a double-loaded brush can run.** `color2` takes the same forms as `color` (one
  colour, a list along the stroke, or `fn(t)`). Asked by Nell.
- **Opacity along a stroke.** `stroke(..., opacity=[1.0, 0.2])` or `opacity=fn(t)` scales how much
  paint leaves the brush without changing the width. Asked by Zala.
- **A glaze that levels.** `level` now works on glazes too. Asked by Zala.
- **A brush held at one angle.** `Brush(angle=radians)` keeps the row of bristles at that angle on
  the board instead of turning it with the path, so a curve goes thick and thin. Asked by Gavino.
- **Pressure as a field.** `pressure` may be an (h, w) array over the board, read where the stroke
  passes. Asked by Gavino.
- **One-sided feathers.** `tape(..., feather=, edge="in" | "out")`. Asked by Carmela.
- **`Board.light`** is a direction; its length scales nothing. Halve the relief with
  `render(relief=0.5)` if you want less of it. Asked by Zala.

Not built:
- **Wobble that never doubles back** (Nell). Fixing `paths.wobble` would move every existing work.
  Keep `wobble` under about a quarter of the stroke's length on board, or clamp it in your kit.

A note asked for by Gavino: dark paint over a light ground half-covers per stroke at ordinary
opacity, and `pickup` then drags the grey along. For a true dark over light, raise `opacity`, lower
`pickup`, or let it dry first.

## Round 3 (after Nell 004, Zala 003, Carmela 003, Gavino 002, Itzel 001)

- **A stroke from off the board arrives loaded.** Set `board.dries_off_board = False` and bristles
  stop losing paint on steps off the edge. The default stays `True` so earlier works keep their
  look; new works should set it. Asked by Carmela and Itzel.
- **Dryness along a stroke.** `stroke(..., dryness=[0.9, 0.0])` or `dryness=fn(t)` replaces the
  brush's dryness as the stroke goes, so a stroke can start scratchy and fill in. Asked by Gavino.
- **An even film.** `Brush(loadvar=0.0, jitter=0.0, gap=0.0)` loads every bristle alike, for wide
  glazes without bristle streaks in the colour. Asked by Zala. Relief between bristles still shows
  under the raking light; see the next item.
- **Softer relief.** `board.relief_soft` (default 0.7 px) is how much the paint's height is softened
  before it is lit. Raise it to 2 or 3 and stroke edges stop drawing rims. Asked by Nell.
