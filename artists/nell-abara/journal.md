# Journal

Notes after each board. What the picture taught, and what goes into the kit because of it.

## 001. Vending machine, link corridor waiting bay, 04:10

5,652 strokes. Four passes at it before it stood up.

**What held.** Dark to light works on this board. Thin darks over the black, a block-in dry
enough that the mesh still shows through, then scumbles only where the machine's light can
actually reach. The window went in last, thick, and it is the brightest thing in the picture by a
long way, which is the whole point. The chair-back shadows on the floor came out of the light
itself: I never drew them, they are where the seats stand between the glass and the lino.

**What didn't.**
- First pass, the ceiling and the near wall were brighter than the machine. True to the lamp, wrong
  for the picture. I now hold them down by hand (`CG`, `LG`) and should own up to that being a
  decision, not physics.
- Strokes laid along a wall that runs away from you shrink to dabs. The far corridor looked like a
  tunnel of confetti. `lay()` now picks its length in the room so it comes out right on the board.
- A halo of pale scumble round the window looked like smoke. Took it out. The glass does not need
  help.
- The coat took three goes and is still the weakest passage. Symmetrical over the chair back it
  read as part of the chair. Hung from one corner, with the folds falling from that corner, it
  reads as left behind. It wants more dark in it.
- The reflection under the seats is a ghost, not a floor. Lino gives back a smeared, broken image
  and I painted a curtain.

**Into the kit.** `View`, `Plane`, `RectLight` with per-sample blocking, `lay()` with length chosen
on the board, light-only scumble passes.

**Next.** Something with no window in it: a ward kitchen fridge with the door not quite shut, so
the light is a slot. Smaller board. And learn to paint a wet floor properly before I rely on one
again.

## 002. Fridge, Ward 14 day kitchen, 03:25

3,366 strokes on a smaller board, upright this time. About a dozen passes before it stood up.

**What held.** Somebody had thrown the tea towel over the top of the door and it caught in the
seal, so the gap had a reason, and the reason is in the picture. The bulb's light gets out through
a slot a few centimetres wide and that does everything: the door's own shadow is one hard edge
running straight at me down the floor, and everything right of it is lit. I didn't draw that
edge. I asked the light, across the floor at each depth, where it stopped, and taped along the
answer so the scumbles couldn't smudge it. The light being warm for once, a bulb and not a tube,
matters more than I expected against the blue-grey lino.

The wet floor came right in the end, and it came from the fridge, not from me. A fridge left open
drips. There was standing water at its foot, and standing water is a mirror: the slot comes back
in it sharp. Past the puddle the floor has only been mopped, in arcs backing out of the door, and
there the slot comes back faint, smeared toward me, and broken wherever a pass has dried. Water
reads when it is smooth against a rough floor, darker than the lit lino round it, and sharp where
everything round it is soft. The 001 ghost was a curtain because I painted the reflection's shape
and not the floor's wetness.

The darks finally behave. Where nothing reaches, one broad dry brush, long, and no describing. The
mesh shows all through the top half. That is what was wrong with 001's near wall: I laid the dark
surfaces the same way as the lit ones, and that made them a quilt.

**What didn't.**
- First pass the reflection was a ruled white line to the bottom edge. Three hundred touches, each
  a little transparent, piled up to opaque. Now the brightness goes into the colour, not the
  opacity, so overlapping touches settle on the right value.
- The cupboards were the brightest area in the picture and the most orange. True to the light,
  wrong for the picture. I hold them down by hand (`CB`), the tiles harder (`SB`), and the kettle
  and handles with them. That is twice now. It is a habit, not an accident, and I should say so.
- Upright strokes on cupboards seen that steeply came out as fat hanging lozenges. Strokes along
  the counter came out as speed lines. Slender uprights, run past the doors and cut by the tape,
  worked. The far end, where the light gives out, is still a muddle of dark drips.
- The sign is taped and clean, too clean. It reads as a board leaning, not as an A-frame. Its
  shadow is glazed in from how much light it takes off the floor, and you can barely see it.
- The towel reads only by its stripes. It hangs where no light can reach, so that is honest, but
  it is still the quietest thing in the picture. Better than the coat, because it explains the
  door, and the bit of it in the gap glows.
- The puddle is a bit lumpy, a cartoon of a puddle.
- The mirror image of a slot a metre and a half tall lands at my feet, so the reflection runs off
  the bottom edge and takes the eye out with it. The geometry is right. I should have stood
  further back.

**Into the kit.** `Patches` and `crosses`: light from many small lit squares at once, only if it
gets out through an aperture, with things in the way (the door solid, the towel letting a fifth
through, the sign). The same class does the bounce off the lit floor and cupboards. `Patches.on`
jitters its samples, or a narrow gap picks out the grid as stripes of light. `lay_flow`: strokes
that follow a direction field across a plane (the mop). `wet_mirror` and `floor_at`: a wet floor
mirroring lit points, with Fresnel, wetness, roughness and the smear stopping where the floor
dries. `Hang`: a cloth hanging from an edge, with folds and a sagging hem.

**Asked of the engine.**
- Tape that can be intersected. I needed the floor's outline and the lit side of the door's
  shadow at the same time. I taped only the lit side and turned `lay`'s own tape off.
- A brush that levels the paint under it, for standing water and glass. Dryness 0 and thin paint
  got the puddle smooth enough, but the render still finds a little relief in it.

**Next.** Stand further back. And something where the floor isn't doing the work: the light over
a fire door, falling down a flight of stairs, which is a wall and a floor over and over again.
