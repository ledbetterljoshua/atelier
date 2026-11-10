# Journal

Notes after each panel. What it taught, and what goes into the kit because of it.

## 001. Soča at Kobarid, 9 June 1983, 58 cm

9,235 strokes. Eleven passes at it before it stood up, which is more than I like.

**What held.** Painting the river turned off and then putting it back works. The gravel bar went
in dry, stone by stone, biggest first, and the water went over it as glazes that only reach where
the water is that deep. The drop-off made itself: nobody drew the line between pale and emerald,
it is where the glazes start stacking. The leaf's shadow is the best thing on the panel. It lies a
hand and a half to the left of the leaf, on the slope of the gravel, because at eighty centimetres
of water and a sun at 67 degrees that is where it falls (25 cm on the bed), and it is the one sharp dark on the bar. The leaf is the
only warm thing and the eye goes there first, then to its shadow, then down the lip.

The bridge's shadow came out right for the wrong reason first. I had it a great slab across the
bottom with the railing like a ladder, until I worked out the sun's actual angle: high, off to the
right, so the shadow only comes out half a metre and the balusters lie long and slanting.
And five metres up, a 2 cm bar barely throws a shadow at all; the sun is not a point. Softening
them to their real penumbra is what stopped them looking drawn. Over the channel the shadow's edge
steps back, because the bed is further down. That is a measurement and I am pleased with it.

**What didn't.**
- The sun's net on the gravel took five goes. First as thin pale lines it was chicken wire, a crackle
  glaze over everything. Fading it with depth helped. What fixed it was mixing it warm, so the water
  cools it back to white on the way up, and painting each line as a broad faint glow with one soft
  round hair down the middle. Before that every line was three bristle tracks, and read as string.
- Sky in the ripples. Long sheen strokes looked like planks, short crests looked like gulls in a
  child's drawing, long slicks looked like rain. All three are gone. The surface is now foam and the
  leaf and nothing else, and I do not think that is finished thinking.
- The glazes compound faster than the arithmetic says. A level painted at the transmission of 17 cm
  of water darkened like 35. I calibrate by eye now, and the exponents in the program are confessions,
  not physics.
- The deep channel is the weakest passage. It is right in value and dead in surface: all the glaze
  strokes run nearly the same way and from across the room it reads as rain on a window, or velvet.
  A river that deep moves in slabs and boils, not lanes. The ghost boulders on the slope and the
  blurred net down there help, and stop at about a metre.
- The gravel is too even in scale. Every stone is the same sort of stone at the same sort of size from
  top to bottom; a real bar is sorted, coarse at the head and fine at the tail.
- The relief from the stone bodies is lit by the gallery's light from the upper left, while my sun is
  on the right. With thick paint that disagreement shows as a dark rim on every pebble. I thinned the
  stones; the rims are still there if you look.

**Into the kit.** `streamline` and `with_the_current` so every water stroke runs with the river;
`glaze_by_depth`, one glaze per level that only goes where it is deep enough; `Water` for what a
depth does to light down and back; `pack_stones` and `stone` for a bed lit from the sun's side;
`sun_net` for the light on the bed; `leaf_outline` and `offset_through_water` for floating things and
where their shadows land; `tape_where` and `poly_mask` to cut tape to a region I have worked out.

**Asked of the engine.**
- Tape from a worked-out region, not only from polygons. I set `board.mask` directly through
  `tape_where`; it works, but it is reaching into the board.
- A way for a stroke's colour to change along its length. A glaze stroke that crosses depth has one
  colour for the whole run, so I cut every glaze where the bed rises past its level instead.
- Some say over the raking light in `render()`, or a stroke that leaves no body (thickness 0 works for
  glazes; I want it to be the default for them).

**Next.** The same bridge on a grey day with the river up, so there is no net of light and no
shadows to measure, and the surface has to carry the picture. I have been avoiding the surface.
