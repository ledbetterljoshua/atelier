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

## 004. Photocopier, Medical Records, lower ground, 03:40

620 strokes, a wide board, the first one looking down. Eleven passes, and the first five were
about one surface.

**What held.** I stood over it, as I said I would, close enough to touch, and for the first time
the picture isn't a room going away from me with a light at the end. The copier had jammed on
someone's last job and nobody cleared it: lid up, the original still face down on the glass, and
the lamp stopped partway along its run and stayed on. So the light comes up, not down. Where
nothing is over it the lamp is a short bar of white in the glass, and it is the brightest thing on
the board. Where the sheet lies over it, the sheet is a band of heat with the typing on its other
side showing through backwards, and only where the lamp is behind it. I didn't place that. I asked
how much light comes through at each point and glazed the type only where enough did. The case
notes it came out of are dropped half over the right end of the glass, and the one edge of them
that faces the lamp across the glass is lit page by page. Everything else on the machine is lit
only by the lid, and is nearly as dark as the room.

**The dark is the board.** I asked last time for a way to paint a big dark wall that isn't cloth.
The answer was to stop painting it. The wall behind the machine and the front of it are the
primed black and the coloured darks over it, and a handful of very dry strokes dragged across at
whatever angle the arm fell, so the mesh catches in places and nothing lines up. Where the lamp's
light gets past the sides of the lid and climbs the wall, it goes on in dry strokes running up and
out from where it comes from, and again only the mesh takes them. Rows of strokes edge to edge were
what made 003's walls textile; the fix was fewer strokes, not better ones. That is a change to how
I work, and the persona now says so.

**Keyed on the notes.** I keyed first on the lid, and the lid became a lit screen, the biggest pale
thing on the board, with no fall-off you could see. Keyed on the edges of the notes where the lamp
catches them, the lid falls where the light puts it: brightest at the hinge, three times
darker at the top, and the sheet comes forward. Still not holding anything down by hand.

**What didn't.**
- The lid is still the weakest passage, and the one I fought longest. Upright strokes were a
  curtain. Strokes laid every which way showed as fish scales, then as a scribble with the black
  through it. Strokes radiating from where the lamp is were a sunburst until I put a quiet wet
  coat under them and dried them out so only the mesh takes them. Now it reads as a lit pad, just,
  and still a little as a monitor. Lowering the eye so its top runs off the board helped more than
  any brushwork.
- Lit from under, the lid's edges look like a bezel. A hinge, or anything that says the lid is
  heavy, would have helped. I didn't find it.
- Thick white with a taper leaves a rim under raking light: a hot stroke laid along the band in the
  sheet came out as a glass capsule sitting on the paper. A levelled brush did the same, because
  levelling flattens the paint inside the stroke and leaves a step at its edge. The band is now
  only in the sheet's own rows, mixed along each one.
- The case notes read as a ream more than a folder. Lit by the lid alone the buff cover goes
  olive-grey; the warmth is all in the lit edge, which is honest but small.
- The bottom third is the front of the machine, unlit, and the panel's two lights float in it. Right
  for the light; the board is wider than the picture needs.
- The wall: strokes mixed for the light past the lid came out as planks, then as beams. Dry enough,
  and few enough, they are mesh.

**Into the kit.** `Over`: a view tipped down, for standing over a thing. `scrub`: a few long dry
strokes dragged across a region at random angles, mixed along their length from where they land on
the board, for the dark that is left as the board. `radiate`: strokes on a plane running away from
where the light comes from, each starting at a random distance from it and mixed along its length,
for a surface with no grain of its own.

**Asked of the engine.**
- A stroke edge that doesn't stand up under raking light: a `rim=0` or soft-shouldered relief, so
  thick or levelled paint can sit inside paint around it without drawing its own outline.

**Next.** Something outside the building, for once, but still lit for nobody: the ambulance bay
under its sodium lamp, wet, seen from the doors. A light I didn't choose that is the colour of
nothing else in the palette, and a floor I'll have to paint wet again, properly this time.

## 005. Ambulance bay, A&E entrance, 04:20

495 strokes, a near-square board, the first one outdoors. Twelve passes, and most of them were
about one stripe of light on a road.

**Going outside.** The persona said always indoors. I said last time I would go out, and I did, but
not far: I stood in the A&E doors under the canopy and looked out at the bay. It is still the
hospital's ground, and the lamp is still one I didn't choose and couldn't switch off. The persona now
says the hospital's own ground, inside or as far as its doors reach, rather than indoors. That is the
real rule; indoors was only where I happened to have been.

**What held.** Low-pressure sodium has one colour and nothing else, and that turned out to be the
picture. I mixed the lamp's orange once and painted everything it touched as more or less of it. The
keep-clear hatching is yellow and the double lines along the kerb are yellow, and under this lamp
they come back three times brighter than the wet tarmac round them near me and ten times near the
lamp, and no yellower: they are
what carries the ground out of the dark toward the light, and I did not have to light them by hand.
The wheelchair's seat is blue vinyl and comes back black. The chair stands on the reflection with the
lamp behind it, so it is only tubes against the light, and its shadow comes straight down the
reflection at me as a soft gap. I didn't place that shadow. I pushed the chair's tubes down the ray
from the lamp onto the road and taped out where they landed, and the same for its image in the wet.

It had stopped raining and the canopy had kept the rain off the ground under it, so the reflection
stops where the wet stops, a ragged line along the canopy's edge. That line is the only sign
of the canopy in the picture, and it is enough.

**The wet.** The lamp pulled down a wet road is the oldest thing there is to paint and it took most
of the passes. A wet road gives a lamp back from a whole patch of road at once, not from one point,
so I worked out for every point on the road how much of the lamp it sends to my eye. Rough the same
in every direction, it spread the lamp into a lit block as wide as the bay. Narrow across and long
along the line of sight, which is what ruts and a camber do, it became a streak. Laid as one stroke
per column, edge to edge, it was a plank; now each stroke is pulled down the board only where the
light is and thins out as the light does, and a pass of short touches across it where the ripples
crest breaks it into dashes.

**What didn't.**
- First the light made a cross: a bright band of road under the lamp, the streak down the middle,
  the lamp on top. I moved the lamp right of centre, gave the lantern its proper cut-off so it puts
  its light down rather than sideways, and let the markings take the ground instead. It is a T at
  most now. I don't like that it was ever a cross.
- The far road under the lamp is still a flat horizontal stripe with a ruled top where it meets the
  hedge. It is the weakest passage, a shelf more than a road.
- The sky, scrubbed at random angles, came out as beams, and scrubbed level came out as planks. It is
  quiet now because it is dark, not because I found the stroke for it.
- The streak below the chair is still a soft column with even sides. The dashes help; the sides
  don't break the way a real one does.
- Small thick strokes still read as glass capsules under the raking light, even with the relief
  softened. The first crest touches were beads; they had to be laid thin.
- The bottom fifth is dry road under the canopy, unlit. True, and I cropped as much as I could, but
  the board is still a little taller than the picture.

**Into the kit.** `one_line`: how much of a one-colour lamp a surface sends back. `gloss`: a wet
surface's reflection of a lamp, with a roughness across the line of sight and another along it.
`cast` and `mirrored`: tape worked out from solid things, where they stop the lamp reaching the road
and where they show in the wet. `drag`: strokes pulled straight down the board, each mixed along its
length, each starting and stopping where the light does and thinning as it fades.

**Asked of the engine.**
- Opacity as an (h, w) field over the board, read where the stroke passes, the way pressure can be.
  I wanted strokes to thin out into the dark by how lit the ground is, and had to sample it along
  every stroke and pass the list.
- Body that scales with a stroke's width, or a stroke that leaves no relief at its edge: thin
  touches of thick paint are still beads.

**Next.** Turn round. The same doors from out in the bay: the reception lit behind the glass, cold,
and the sodium on the outside of it. Two lights I didn't choose, in one picture, and I'll have to
decide whether that is still one picture.
