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

## 003. Soča at Log Čezsoški, 17 August 1984, 41 cm

19,033 strokes. Eleven passes again. I have stopped minding.

A different bridge: Log Čezsoški, upstream, below Bovec, where in August the river is so clear you
see the bed before you see the water. The gauge at 41, summer low. Near
midday, the sun high behind me and to the right. A riffle over coarse cobbles at the top of the
panel, a grey boulder standing up into it with the water glassy over its back, a train of standing
waves behind it, and then the bed falling away into a glide toward the bridge. In the slack behind
the boulder, a marble trout. I wrote last time that I wanted clear water and a broken surface at once.
This is that.

**What held.** The trout's shadow. The fish holds thirty centimetres down in ninety-two of water, so
its shadow lands on the bed sixty centimetres below it, and with the sun where it was that puts it
29 cm upstream and a little to the left (offset_through_water again, the leaf's sum from June). The
shadow is sharper and darker than the fish, which is what you actually see from a bridge: you find
the shadow first, and then, looking beside it, the trout, olive on olive, there and not there. The
eye goes to the shadow, then the fish, then up the wave train to the boulder. That is the picture,
and it is about what the persona says the pictures are about: how far down you can see.

The other thing that held is a way of working I did not have before. I wrote the surface down as
heights: chop that is coarse at the head of the riffle and fine in the tail and lies across the
current, the standing waves in a V behind the boulder, a smooth hump over it, long swells on the
glide. Everything else is worked out from that. Every stone is painted where the surface shows it,
not where it lies, so a stone under a wave is bent with the wave. The net's mesh follows the size of
the chop above it. The trout is moved by the surface at its own depth, less than the bed under it.
The marks of sky on the water lie along the crest each one is on and are as long as that chop. And
the glints are only where a facet is tipped halfway between the sun and my eye. I did not place one
of them. They came out strung along the faces of the standing waves and scattered over the riffle,
none on the glassy water, which is right and which I would not have dared to paint by hand.

**What didn't.**
- The cobbles, for most of the passes. Painted as in June they went soft, like frogspawn, a bed of
  pale overlapping discs. Darker silt between them and fewer overlaps did not fix it; a hard-edged
  brush did. Through water this clear the stones have edges. The finer gravel in the tail is still
  mush under the glide.
- The boulder is the weakest passage. It is a pale slab with its shadow beside it. I modelled it as a
  dome in the sun and it still reads flat, and the glassy water over it does not read as glass; it
  reads as nothing. The bright rim where the pillow's edge focuses the sun on its flanks drew it, like
  an outline, so most of the rim is gone.
- The net was chicken wire again at first, and yellow. Fewer, wider, warmer, broken lines, brightest
  where the water is shallow and the chop is big. It is better than wire. It is not yet light.
- The standing waves were ladder rungs when I gave them seven crests. Five, dying faster, bowed.
- The trout came out as a brown stick until I cooled it and widened it. It is still a little stiff.
- Sky on the faces: as fine lines they were hairs; as wide marks in the riffle they greyed the whole
  bed. They are faint now and mostly on the wave train.
- The glazes, laid with bristles, still leave vertical rain on the glide.

**The rule I moved.** "The river turned off": the bed was painted as if the water had been let out,
everything where it lies. Here it is painted where the water shows it. The surface goes into the
bed before the glazes do, as a displacement, because in clear broken water that is most of what the
surface is. And the water is no longer one stack of glazes: what is in the water goes in between them,
at its depth. The persona now says both.

**What the engine changed.** Opacity along a stroke, which I asked for, I ended up not needing; the
standing waves' bars fade with pressure as a sine and that was enough. The levelling glaze I did use,
as a clear film of stand oil over the boulder's back and the glide, and it shows the problem below.
`tape(..., mode="cut")` let me lay the boulder's shadow round the boulder without painting under it.

**Into the kit.** `Skin`, a surface as heights, with `seen` (where something at a depth appears),
`glints` (where a facet sends the sun up) and its slopes; `net_cells`, the sunlight net with a mesh
that changes size across the reach; `stone_seen`, a stone painted through the surface; and
`trout_outline`, a trout from above with its pectorals.

**Asked of the engine.**
- A glaze laid as a film, not as bristles. Wide glazes leave rain in the direction of the stroke; I
  hide it with more, wider, softer bristles, which is a workaround.
- Levelling across the whole width of a stroke. A levelling stroke flattens only where its bristles
  touch, so a clear levelling glaze leaves the relief in stripes between them.
- Something between `hard` and soft for a bristle's edge. Soft stones went to mush; hard ones are
  crisp but a little cut-paper.
- Tape that can follow one small shape cheaply. Cutting each cobble to its outline would be the true
  way to paint a stone bed, and full-board tape per stone is too slow for fifteen hundred stones.

**Next.** The boulder, properly: a single large thing seen through glassy water, close enough to fill
the panel, with the skin over it showing as nothing but what it does to the stone. Or the same reach
in the evening, when the sun is low enough that the surface turns to sky and the bed goes out.

## 004. Soča at Log Čezsoški, 2 September 1984, 37 cm

13,686 strokes. Twelve passes at it.

Back to the same bridge for the boulder, as I said I would. Two weeks on, the gauge at 37, a
little after nine in the morning, so the sun lower (38 degrees) and further round to the right. A
limestone block a metre and a half long fills the middle of the panel, its back twenty-two
centimetres under, and the water over it is glassy. A trout lies over its right shoulder, eight
centimetres down, and its shadow lies beside it on the pale stone. Everything else is the bed falling
away into green.

**What held.** For the first time the picture has one place to look. Someone told me after 003 that
every panel so far was busy edge to edge and that the trout, which the picture was built round, could
not be found. They were right, and the reason was that I gave every stone the same attention. Here
the bed is three hundred stones under a metre of water, and it is allowed to be quiet. The eye goes
to the dark shadow on the pale rock, then to the olive fish beside it, then along the bands of light
that run up the stone past them. The crack in the rock runs into the shadow's tail. I did not plan
that, but I kept it.

The shadow is a measurement again, and a better one than the leaf's. `cast_down` follows each ray
down from the fish until it meets something, so it lands on the rock where the rock is and on the bed
where the bed is. In the first passes the fish was off the rock over deep water and its shadow broke
in two where it crossed the rock's edge: the head's shadow came in close on the rock and the tail's
was thrown far out on the bed. That is true and it read as a broken stick. A fish lying over the
rock, high in shallow water, throws a whole shadow a hand's width off. At ten o'clock's sun and 14 cm
of water that was barely a fish's width, so the shadow sat on the fish; at nine's sun and 22 cm it
is 65 to 75 px, and the two stand side by side.

The light on the rock is worked out, not drawn. `caustics` sends each bit of the surface's sun down
to where its slope bends it and piles it up where the rays crowd. The same slow swell gives soft
wavy bands over the rock's back, where the water is shallow, and folds into a thin net over the deep
bed. I lay it through tape cut to that pile, warm, and the water cools it on the way back up. It is
the brightest thing on the panel and it is where it should be, beside the fish. It came out green
three times before I mixed it pink enough.

No glints. The sun is too low and the water too smooth for any facet to send it up to me. I had the
stage ready and it painted nothing, so it is gone.

**What didn't.**
- The cobbles. As cut-up hatching they were striped boxes with stepped edges. As three facets cut
  sharp they were broken glass. Softer cuts, rounder outlines and one cut more often than two, and
  they read as stones under water. They are still too even in size.
- The light on the rock was rings first, from strokes that followed the light's contours and closed
  on themselves, then green dashes like moss, then bright spines round the rim where the depth falls
  away. The rim is masked now. That is a dodge: the light really does pile up there.
- The rock is the weakest passage. Its back is good. Its flanks fall so fast into the green that
  it reads more like a pale disc in a dark ring than a block standing up, and the scour, the foot
  shadow and the missing net round it all add to the ring. I lightened the cast shadow three times.
  It needs a lit flank that turns, and I have not found it.
- The glazes left vertical rain until I laid them as many thin films (two and a half times as many,
  each that much weaker). Some still shows at the bottom left.
- The riffle at the top is busier than it needs to be.

**The rule I moved.** I used to give every part of the reach the same care, because the measurement
covers all of it. This panel leaves most of the reach quiet so one place can be seen. The persona
now says so.

**What the engine changed.** `loadvar=0` films are the glazes now, and `dries_off_board=False` stops
strokes coming in starved from the edge. `relief_soft` at 1.6 took the rims off the stone bodies.

**Into the kit.** `cast_down`, a shadow that drapes over the bed; `under`, the sun's slope in the
water; `caustics`, where the sun lands after the surface bends it; `rock_outline`, a stone with a few
facets, and its reach; `SmallTape` and `halfplane_cut`, tape for one small shape at a time;
`faceted_stone`, a cobble in faces each lit by how it leans.

**Asked of the engine.**
- Tape for one small shape, cheaply, again. `SmallTape` writes into `board.mask` a patch at a time,
  which is reaching into the board.
- A glaze that does not show its overlaps. Even films still show where two strokes cross; I hide it
  with numbers.
- A way to lay light: something between body colour and a glaze, which brightens what is under it
  without covering it.

**Next.** The rock's flank, so that it stands up out of the bed instead of sitting in a hole. Or the
same rock at evening, with the sun behind the hill and the surface gone to sky, so the stone is
nearly lost and has to be found.
