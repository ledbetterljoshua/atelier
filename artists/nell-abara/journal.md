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

## 003. Back stairs, east wing, half-landing, 04:50

873 strokes, a tall board. Eight or nine passes at it, and the first three were wrong in ways
that taught me something.

**What held.** I stood back, as I said I would: on the half-landing, a couple of metres short of
the first step, so the light is small and far off and the stairs have to carry it down to me. They
do, mostly. From below you never see the top of a step above your own eye, only its riser, so the
upper half of the flight is a stack of dark faces and the light shows only at its edges. The lower
steps show their treads, and each tread is lit at the front and dark at the back, where the next
riser stands between it and the lamp. I didn't decide where that shadow goes. I asked the stair:
the light now checks whether anything solid is in the way, and the steps are solid. The yellow
inserts on the nosings are the brightest thing on the stairs, and they step down toward me like a
ladder of light. The rail is the line in. The door is beech veneer and the only warm thing in the
picture, against a cold green room.

**Holding values down.** I said last time this was a habit, not an accident, and that I should own
up to it. This time I stopped doing it. The room is keyed once, on one thing the picture is about
(the front of the seventh step), and everything else falls where the light puts it. Near the lamp
the surfaces crowd up under a ceiling no wall or door is allowed past: white knocked back, never
white. Pure white is kept for the light. The first time I keyed on the brightest thing the light
touched, the steps went black. The second time, keyed on the steps with the old curve, every wall
went to the same pale. With the ceiling in place, one number did it, and I never held a surface
down by hand. That is how I work now, and the persona says so.

**What didn't.**
- The walls are most of the board, and they took the most goes. Strokes laid along the pitch fanned
  out from the vanishing point like feathers. Upright strokes that stopped inside the wall ended in
  rounded tips and hung like curtains. Upright strokes run floor to ceiling were curtains again,
  then wood grain when I let them wander. What saved them was a second, dry pass across the uprights
  along the pitch of the stair, which catches only the mesh. It works, but it is a fix laid over a
  fix, and they are still the weakest passage: dark green cloth, if you look for it.
- The back-wall scumble round the lamp came out as smoke, as it did round the window in 001. I took
  it out again. I should stop putting it in.
- A wide glaze with wobble folds back over itself and leaves dark ticks across the floor. No wobble
  on glazes.
- The ceiling over the landing is the second-brightest area and it is ruled, a stack of stripes.
  True to the light, and it frames the lamp, but it is too tidy.
- The lamp is a plain white bar. It is the brightest thing, as it should be, and nothing more. The
  cage I put over it made it read as a vent.
- The cup is nearly lost: a small grey thing on the sixth step, lit from behind. Maybe right.
  Inventory, not anecdote.
- The risers are flat. Each one is a single dry stroke or two across, which is the rule for the
  dark, but stacked eleven high it is the least painted part of the board.

**What the engine round changed.** Colour along a stroke changed most. A wall stroke now runs from
the light into the dark and mixes itself on the way, so I lay fewer, longer strokes and the
gradient is the stroke's and not a pile of patches. The door is sixteen of them. Tape with
`mode="cut"` laid the back wall round the door frame and the frame round the leaf in one go each,
where before I would have had to paint the wall and then lift it. The levelling brush made the
wired glass in the door lie flat with no tooth in it. `Board.light` is set from above, where the
lamp is, so the paint's relief catches the same light as the room. I didn't need `tape_where`.

**Into the kit.** `Flight`: a straight stair, its treads, risers and nosings, and the stair as a
solid. `in_the_way`: shadow from anything solid between the light and a point, with the samples
crowded near the point, where a step's own riser does the work. `Patches(occlude=)` to use it.
`room()` and `keyed()`: the curve with a ceiling, and one exposure for the board found from the
thing the picture is about. `sweep`: strokes that run the whole way across a surface, edge to
edge, each as wide as the gap to the next and mixed along its length, so nothing between them
shows black and no stroke ends in a tip in the middle of a wall. `lay(along=)` mixes a laid stroke
at several points down its length, and `lay(tape_mode=)` passes the new tape modes through.

**Asked of the engine.**
- Colour along a stroke and `color2` together: a different run of colours down each edge. A wide
  upright stroke on a receding wall crosses the light's falloff sideways as well as lengthways.
- Wobble that never turns a path back on itself. With a wide brush, and with any glaze, the fold
  leaves a mark.

**Next.** Closer again, and something the light is inside rather than at the end of: the
photocopier in medical records that never went to sleep, its glass lit, the lid up. A machine
I can stand over. And find a way to paint a large dark wall that isn't textile.
