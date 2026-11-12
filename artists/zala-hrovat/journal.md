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

## 002. Soča at Kobarid, 4 November 1983, 112 cm

59,142 strokes. Eleven passes again, and most of them spent on one thing: the surface.

Same bridge, same parapet, five months on. Two days of rain and the gauge at 112, fifty-four above
June. The river was carrying the mountain, milky green-grey, and low cloud: no net of light on
the bed, no shadows to work out, and no bed for most of the reach. I wrote last time that the
surface would have to carry the picture. It does, and it took the picture eleven goes to let it.

**What held.** The picture is built on one fact I did not know until I had painted it wrong twice.
Under cloud, broken water is the light water, because every little facet tipped toward the sky
sends some of it back; smooth water is the dark water, a window with no glare on it. So the bar,
where the river riffles fast and shallow, is a pale skin of small marks, and the channel is darker
and held together by the boils: domes of water coming up off the lip of the bar, glassy, with the
chop breaking against their edges and foam held on the crease upstream and torn off the sides.
What a boil brought up stays smooth as it is carried off, and those slick trails are what finally
broke the lanes. Nothing in the channel runs straight now except where the river does.

The hazel branch coming down the seam is the only warm thing and the eye goes there first, then
down its line to the big boil, then on to the one under me. Its butt end is under. I painted that
part before the river went in, as the rule says, and the silt took it completely, which is true
of water like that and loses the idea. I left it.

**What didn't.**
- The boils took six goes. Radial strokes made bells and then dandelions; pale tops made lily pads;
  an outline made them drawn; dark and flat made ink stains; rings going out across them made tree
  rings. What is there now is dark glassy water laid flat to the edge, a little lighter toward the
  rim where the dome tips to the sky, and two or three broken wrinkles. They are still a little
  stamped.
- The chop was fur, then rice, then gulls. Small crescents lying across the current, a dark back
  and, more often than not, a light face, thousands of them, is what reads. It is a texture and not
  yet a surface: on the bar half of the panel it is one even felt, and the ghost stones under it
  read as pale coins.
- The foam was dotted lines in arcs a hand's width off each boil, like the motion lines in a comic.
  It belongs on the crease itself.
- I tried to put myself in. A boil came up under me and I painted my head and the parapet in it, and
  it was the sign on a lavatory door. Then I worked out why it could not be right anyway: the smooth
  water is already the dark water, and a dark reflection in it does not show. Scraped.
- The lower right still has green lanes where the glazes show between the silt. Less than in June.

**The rule I broke.** "Nothing opaque in between." Silt is not a glaze. Flood water sends light back
before it reaches the bed, so glazes alone made it clear and dark, a June river in the wrong colour.
The silt went on as a thin scumble with the current, heavier where there is more water to hold it.
The boils are opaque too, laid flat. The persona now says so.

**What the engine changed.** Colour along a stroke: the glazes no longer stop where the bed comes up.
`glaze_through` mixes each one for every place it crosses, so a stroke runs from the bar over the
lip into the channel getting darker as it goes. That is what the river does, and the drop-off came
out softer and truer than 001's cut edge. The engine's `tape_where` replaced mine everywhere in this
panel, and `mode="and"` let me tape half of each curled leaf inside its outline without building
the mask myself. The levelling brush is the boils and the slicks: it flattens the chop and the stones
under them, so in the render they are glossy and still while everything round them has tooth. I
gave the board a grey window light at about half strength, since there was no sun to agree with.

**Into the kit.** `colors_along` and `glaze_through`, glazes that cross depth; `Boils`, which pushes
the current outward from each boil, knows its uneven edge, and says where its top and crease are;
`stone_under_cloud`, a stone lit by the whole sky; `foam_lace`, foam as strands that part and rejoin.
My old `tape_where` stays for 001.

**Asked of the engine.**
- A glaze that also levels. `level` only works on opaque paint, so the glassy boils had to be
  body colour. A transparent film that leaves the surface flat is what stand oil glaze does.
- Opacity along a stroke, like colour. The slick trails should fade as they go; I used pressure,
  which narrows them as well.
- Say what the length of `Board.light` means. A shorter vector gives weaker relief, and I relied on it.

**Next.** The surface is a texture now and needs to be a surface: the same chop should change with
what is under it, bigger over the bar head and finer in the tail, and run in trains. And I want a
day when the water is clear and the surface is broken, both at once, so the net of light comes
back through a skin of chop and I have to paint both.
