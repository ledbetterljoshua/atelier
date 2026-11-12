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
