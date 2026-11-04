"""Flat-pattern drawing of the pyrometer mounting bracket, with bend lines.

The STEP (exported from SolidWorks) is the 3 mm flat blank; it carries no bend
data, so the bend lines below are constructed from the blank's geometry: each
runs across the 20 mm strip, perpendicular to its 40 deg axis, from the relief
corner where the strip leaves the base plate. That puts each bend 15 mm from
its Ø12.1 hole centre. Confirm direction, angle and inside radius with the
designer.
"""
import math
from pathlib import Path

from cadgen import read_step
from cadgen import eng_drawing as ed
from cadgen.eng_drawing import Sheet, eng_drawing

HERE = Path(__file__).parent
T = 3.0                                  # sheet thickness
AXIS = 40.0                              # strip axis, deg from +X
U = (math.cos(math.radians(AXIS)), math.sin(math.radians(AXIS)))
N = (-U[1], U[0])                        # across the strip
STRIP_W = 20.0
EDGE_PT = (19.311, -38.171)              # a point on the strip's long edge

PIVOT = (10.0, 7.5)                      # Ø5.1 pivot hole
SLOT_R, SLOT_W, SLOT_HALF = 20.0, 5.1, 10.0
HOLE_A = (18.2450, -26.0113)             # Ø12.1, lower ear
HOLE_B = (93.3175, 36.9816)              # Ø12.1, upper ear
RELIEF_A = (23.308, -8.709)              # bend 1 starts at this relief corner
RELIEF_B = (75.399, 35.0)                # bend 2 starts at this relief corner


def _across(p):
    """Bend line: from relief corner p across the strip to its long edge."""
    d = (p[0] - EDGE_PT[0]) * N[0] + (p[1] - EDGE_PT[1]) * N[1]
    return p, (p[0] - d * N[0], p[1] - d * N[1])


BENDS = [_across(RELIEF_A), _across(RELIEF_B)]


def along(t, n=0.0):
    """Point t mm along the strip axis from HOLE_A, n mm across it (+ toward the base)."""
    return (HOLE_A[0] + t * U[0] + n * N[0], HOLE_A[1] + t * U[1] + n * N[1])


PITCH, BEND_TO_HOLE, HOLE_TO_END = 98.0, 15.0, 10.0
SLOT_ENDS = [(PIVOT[0] + SLOT_R * math.cos(math.radians(90 + a)),
              PIVOT[1] + SLOT_R * math.sin(math.radians(90 + a))) for a in (SLOT_HALF, -SLOT_HALF)]

# (p1, p2, offset in model mm). Offsets are signed to the left of p1 -> p2; the
# strip's long edge is 10 mm right of its axis, so the chain sits outside it.
ALIGNED = [
    # chain along the axis: end - hole - bend ... bend - hole - end
    (along(-HOLE_TO_END), along(0), -18),
    (along(0), along(BEND_TO_HOLE), -18),
    (along(PITCH - BEND_TO_HOLE), along(PITCH), -18),
    (along(PITCH), along(PITCH + HOLE_TO_END), -18),
    # hole pitch, one row further out
    (along(0), along(PITCH), -26),
    # strip width, across the upper ear beyond its tip
    (along(PITCH, STRIP_W / 2), along(PITCH, -STRIP_W / 2), HOLE_TO_END + 8),
]


# ---- bend lines: cadgen has no bend-line primitive, so add a BEND layer after
# the sheet renders, locating the top view from its two Ø12.1 holes.
_orig_render = ed._render_sheet


def _render_with_bends(sheet, **kw):
    doc = _orig_render(sheet, **kw)
    msp = doc.modelspace()
    # the STEP splits each hole into two half arcs; one entity per centre
    found = {}
    for c in msp.query("CIRCLE ARC"):
        if c.dxf.layer == "VISIBLE" and abs(c.dxf.radius - 6.05 * sheet.scale) < 0.01:
            found.setdefault((round(c.dxf.center.x, 3), round(c.dxf.center.y, 3)), c)
    big = sorted(found.values(), key=lambda c: c.dxf.center.x)
    if len(big) != 2:
        raise RuntimeError(f"bend lines: expected 2 Ø12.1 holes on the sheet, found {len(big)}")
    s = big[0].dxf.radius / 6.05
    ox = big[0].dxf.center.x - HOLE_A[0] * s
    oy = big[0].dxf.center.y - HOLE_A[1] * s
    chk = (HOLE_B[0] * s + ox - big[1].dxf.center.x, HOLE_B[1] * s + oy - big[1].dxf.center.y)
    if math.hypot(*chk) > 0.05:
        raise RuntimeError(f"bend lines: top view is not a plain XY projection (miss {chk})")
    to = lambda p: (p[0] * s + ox, p[1] * s + oy)
    if "BEND" not in doc.layers:
        doc.layers.add("BEND", color=7, linetype="PHANTOM", lineweight=25)
    from ezdxf.enums import TextEntityAlignment
    for i, (a, b) in enumerate(BENDS, 1):
        # run the line 3 mm past the blank each side, as a bend line is printed
        a3 = (a[0] + 3 * N[0], a[1] + 3 * N[1]); b3 = (b[0] - 3 * N[0], b[1] - 3 * N[1])
        msp.add_line(to(a3), to(b3), dxfattribs={"layer": "BEND", "ltscale": 0.4})
        # short tag on the bend line, on the ear side and the half away from the
        # aligned-dimension extension lines (those run on the long-edge half)
        t_ear = -3.5 if i == 1 else 3.5          # B1's ear is toward -U, B2's toward +U
        lab = (a[0] + (b[0] - a[0]) * 0.42 + t_ear * U[0], a[1] + (b[1] - a[1]) * 0.42 + t_ear * U[1])
        t = msp.add_text(f"B{i}", height=3.0, dxfattribs={"layer": "NOTES", "rotation": AXIS - 90})
        t.set_placement(to(lab), align=TextEntityAlignment.MIDDLE_CENTER)

    # Slot centre line (R20 about the pivot) and its two end radials, on CENTER.
    c = to(PIVOT)
    msp.add_arc(c, SLOT_R * s, 90 - SLOT_HALF - 4, 90 + SLOT_HALF + 4, dxfattribs={"layer": "CENTER"})
    for e in SLOT_ENDS:
        msp.add_line(c, to(e), dxfattribs={"layer": "CENTER"})

    # Aligned dimensions along / across the 40 deg strip. cadgen only draws
    # horizontal and vertical dimensions, so these are written here with the
    # same dimstyle and the same per-view dimlfac, so they print true size.
    for p1, p2, dist in ALIGNED:
        d = msp.add_aligned_dim(p1=to(p1), p2=to(p2), distance=dist * s, dimstyle="Standard",
                                override={"dimlfac": 1.0 / s}, dxfattribs={"layer": "DIM"})
        d.render()
    return doc


ed._render_sheet = _render_with_bends


@eng_drawing(out="pyrometer_mounting_bracket_flat.pdf")
def pyrometer_mounting_bracket_drawing():
    part = read_step(HERE / "pyrometer_mounting_bracket.step")
    sheet = Sheet("A3", scale=1.5, title="PYROMETER MOUNTING BRACKET - FLAT PATTERN",
                  part_number="PYRO-BRKT-01", material=f"SHEET {T:g} THK", revision="A",
                  author="greg", ink="mono",
                  notes=["FLAT PATTERN SHOWN, 3 THK.",
                         "BEND LINES B1, B2 SHOWN PHANTOM. BOTH UP 90°.",
                         "BEND LINES PERP. TO 40° STRIP AXIS.",
                         "SLOT SYMMETRICAL ABOUT VERTICAL C/L OF Ø5.1 PIVOT.",
                         "DIMENSIONS IN ( ) ARE REFERENCE.",
                         "BREAK SHARP EDGES."])
    top = sheet.view(part, "top", at=(230, 162), label="FLAT PATTERN (VIEW FROM TOP)")
    k = sheet.scale
    X0, X1, Y0, Y1 = 0.0, 106.179, -38.873, 49.843          # blank extents

    def above(row, y):  return (Y1 - y) * k + 10 + 8 * row
    def below(row, y):  return -((y - Y0) * k + 10 + 8 * row)
    def right(row, x):  return (X1 - x) * k + 10 + 8 * row
    def left(row, x):   return -((x - X0) * k + 10 + 8 * row)

    # Datums: the base plate's left edge (x = 0) and bottom edge (y = 0).
    # The strip is located by the lower Ø12.1 hole and the 40° angle; everything
    # on it is then dimensioned along / across its axis (aligned dims, added in
    # the render hook). Base edges that end on a bend line are reference only.
    O = (0, 0, 0)
    top.overall()
    # bottom: pivot and lower hole from the left edge, base bottom edge (ref)
    top.dim(O, (*PIVOT, 0), orientation="h", offset=below(0, 0))
    top.dim(O, (*HOLE_A, 0), orientation="h", offset=below(1, HOLE_A[1]))
    # top: base top edge (ref, set by bend 2)
    top.dim((0, 35, 0), (RELIEF_B[0], 35, 0), orientation="h", offset=above(0, 35), text="(<>)")
    # left: pivot up, lower hole down (same row), then base height
    top.dim(O, (*PIVOT, 0), orientation="v", offset=left(0, 0))
    top.dim(O, (*HOLE_A, 0), orientation="v", offset=left(0, 0))
    top.dim(O, (0, 35, 0), orientation="v", offset=left(1, 0))
    # features
    top.hole((*PIVOT, 0), 5.1, thru=True, angle=200, label="PIVOT")
    top.hole((*HOLE_A, 0), 12.1, thru=True, count=2, angle=200)
    top.note("SLOT 5.1 WIDE ON R20", (PIVOT[0], PIVOT[1] + SLOT_R + SLOT_W / 2, 0), offset=(-44, 22))
    top.angle((*PIVOT, 0), (*SLOT_ENDS[1], 0), (*SLOT_ENDS[0], 0), offset=13)
    top.angle(RELIEF_B + (0,), (95.0, 35.0, 0), (92.252, 49.141, 0), offset=12)
    top.radius((3, 3, 0), 3, angle=225, text="6× R3")
    return sheet


if __name__ == "__main__":
    pyrometer_mounting_bracket_drawing()
