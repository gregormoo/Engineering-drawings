"""Motor mount v2: triangulated truss legs on the existing NEMA 17 L-bracket.
Axes as in greg's STEP: Y up, board at Y=-116.15, bracket underside at Y=0, motor side +Z."""
from build123d import *
import sys
SRC=sys.argv[1]; OUT=sys.argv[2]
H=116.15          # board to bracket underside (greg)
T=4.0             # wall / panel thickness
BASE=4.0          # base ring thickness
M=7.0             # truss member width
RING=10.0         # base ring width
YB=-H; YT=-H+BASE
ZR=-60.0; ZF=5.0  # bracket rear / front edges
ZF_BOT=35.0       # wall front edge at the base, reaches under the motor
XL=-8.0; XR=58.0; ZB0=ZR-10; ZB1=ZF_BOT+10
SCREW=3.1; CSK=6.3  # M3 clearance, 90 deg countersink

s=import_step(SRC)
bracket = s & Pos(0,200,0)*Box(400,400,400)

def poly(pts): return Face(Wire.make_polygon([Vector(*p) for p in pts],close=True))
def truss_face(outline, tris, edge, r=3):
    outer=poly(outline); res=outer
    for t in tris:
        hole=offset(offset(poly(t),-(M/2)-r,kind=Kind.INTERSECTION),r,kind=Kind.ARC)
        res=res-hole
    if edge>0: res=res+(outer-offset(outer,-edge,kind=Kind.INTERSECTION))
    return res

# side walls in the YZ plane (local x = Z, local y = Y)
A=(ZR,0);B=(ZF,0);C=(ZF_BOT,YT);D=(ZR,YT)
sf=truss_face([A,B,C,D],[(A,B,C),(A,C,D)],edge=M)
def to_x(face,x0):
    # map local (u,v) -> global (x0, v, u)
    pl=Plane(origin=(x0,0,0),x_dir=(0,0,1),z_dir=(1,0,0))
    return extrude(face.mirror(Plane.XZ).moved(Location(pl)),amount=T)
wallL=to_x(sf,0); wallR=to_x(sf,50-T)

# rear X-brace in the XY plane at Z=ZR
P1=(0,0);P2=(50,0);P3=(50,YT);P4=(0,YT);O=(25,YT/2)
rf=truss_face([P1,P2,P3,P4],[(P1,P2,O),(P2,P3,O),(P3,P4,O),(P4,P1,O)],edge=0)
rear=extrude(rf.moved(Location(Plane(origin=(0,0,ZR),x_dir=(1,0,0),z_dir=(0,0,1)))),amount=T)

# base ring with four countersunk M3 holes
outer=Box(XR-XL,BASE,ZB1-ZB0,align=Align.MIN).moved(Location((XL,YB,ZB0)))
inner=Box(XR-XL-2*RING,BASE+2,ZB1-ZB0-2*RING,align=Align.MIN).moved(Location((XL+RING,YB-1,ZB0+RING)))
base=fillet((outer-inner).edges().filter_by(Axis.Y),radius=3)
HOLES=[(XL+RING/2,ZB0+RING/2),(XR-RING/2,ZB0+RING/2),(XL+RING/2,ZB1-RING/2),(XR-RING/2,ZB1-RING/2)]
for x,z in HOLES:
    base-=Cylinder(SCREW/2,BASE+2,rotation=(90,0,0)).moved(Location((x,YB+BASE/2,z)))
    d=(CSK-SCREW)/2
    base-=Cone(SCREW/2,CSK/2,d,rotation=(-90,0,0),align=(Align.CENTER,Align.CENTER,Align.MIN)).moved(Location((x,YT-d,z)))

legs=(wallL+wallR+rear+base).clean()
part=(bracket+legs).clean()
print("solids",len(part.solids()),"valid",part.is_valid,"part vol",round(part.volume),"legs vol",round(legs.volume-0),"bracket",round(bracket.volume))
print("bb",part.bounding_box().min,part.bounding_box().max)
export_step(part,OUT)
