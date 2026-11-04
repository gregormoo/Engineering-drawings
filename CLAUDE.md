# Engineering drawings: house rules

greg's standard for every drawing in this repo. The reference is
`parts/pyrometer_mounting_bracket/`: copy its script as the starting point for a new part.
Use the `engineering-drawing` skill (`.claude/skills/engineering-drawing/`) for the cadgen API.

## Input

- Take a **STEP** (AP214). A `.SLDPRT` can't be read without SolidWorks; ask for a STEP
  export (File > Save As > STEP AP214).
- One folder per part: `parts/<part_name>/` holding `<part_name>.step`,
  `<part_name>_drawing.py` and the rendered `<part_name>....pdf` (`out=` relative to the script).
  Also copy the PDF and script to `/mnt/project-files/drawings/` for greg.
- Install/run cadgen in the cloud container only: `cadgen +0.8.2 run <script>`, with
  `MPLCONFIGDIR` set to a scratch dir. Keep cadgen telemetry off (`cadgen +0.8.2 telemetry off`).
- Don't name a script after a stdlib module (`inspect.py` breaks cadgen's import).

## The method

1. **Read the geometry first.** List faces, holes, radii and extents (see `probe` approach:
   iterate `part.faces()`, print planes and cylinder radii/axes). Work out the design intent:
   round numbers (pitch 98, 15 from hole to bend, 20 wide strip) show what the designer
   dimensioned.
2. **Sheet-metal parts are drawn as the flat pattern** with bend lines, unless greg says
   otherwise. If the STEP has no bend data, derive bend lines from the geometry (relief
   corners, symmetric distances to holes) and state the assumption to greg. Bend lines go on
   a `BEND` layer, PHANTOM linetype, tagged `B1`, `B2`... on the ear side, away from
   extension lines. Note: "BEND LINES B1, B2 SHOWN PHANTOM. <DIRECTION> <ANGLE>°."
3. **Pick datums** on real edges (e.g. left and bottom edges of the base). Dimension
   positions from them; place each row explicitly with the `above/below/left/right(row, ...)`
   offset helpers so rows never stack or run off the frame.
4. **Fully define the part, once.** Every feature located and sized; nothing in notes that
   should be a dimension. Anything that follows from other dimensions (an edge ending on a
   bend line) is a reference dimension, `text="(<>)"`, with the note
   "DIMENSIONS IN ( ) ARE REFERENCE."
5. **Features at an angle get aligned dimensions** along and across their own axis
   (chain: end-hole-bend ... bend-hole-end, pitch one row further out, width across).
   cadgen only does horizontal/vertical, so add them in the `_render_sheet` hook with
   `msp.add_aligned_dim(..., dimstyle="Standard", override={"dimlfac": 1/s})`, locating the
   view from known hole centres. Keep the hook's self-check that raises if the holes are not
   found where expected.
6. **Holes** as callouts (`view.hole`, with `count=`), slots as R + width callout with their
   centreline arc and an angular dimension, corner radii as `n× R`.
7. **Title block**: title, part number, material/thickness, rev, author greg, A3, mono ink.
   Never invent tolerances or material grade: leave them out and ask.
8. **Render, then look at the PNG** (`pdftoppm -r 100 -png`) and fix every collision,
   upside-down text, label on a line, or dimension off the frame before sending.

## Handoff

Send the PDF and list the assumptions still open (bend direction/radius, material,
general tolerance).
