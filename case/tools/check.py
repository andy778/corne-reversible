#!/usr/bin/env python3
"""Self-check for the case (WP6).

Renders 2D sections of the real OpenSCAD model (plate mid-plane, tray at insert-boss height) to DXF,
extracts the contours and compares them with the Ergogen data, which is read independently of
geometry.scad (points.yaml, config.yaml anchors, and the Ergogen DXFs).

Checks (tolerance 0.05 mm):
  1. plate cutout centres == key centres (42, 36, and the mirrored right half), and the cutouts in the Ergogen plate_*.dxf
  2. plate screw holes == mounting holes H1..H5 (config anchors) == circles in the Ergogen plate DXF
  3. tray insert holes == mounting holes
  4. tray reset press hole == circle in Ergogen tray_*_left.dxf (left), absent on the right
  5. plate is open over the reset button on the right half, closed on the left; always open over the controller
  6. optional: clearance of the insert bosses to B-side socket copper (needs pcb/ergogen/output)

Usage: python3 case/tools/check.py        (needs openscad, PyYAML, shapely)
"""
import math
import os
import re
import subprocess
import sys
import tempfile

import yaml
from shapely.geometry import Point, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(CASE, ".."))
ERG = os.path.join(ROOT, "pcb", "ergogen")
TOL = 0.05
sys.path.insert(0, HERE)
import gen_geometry as gg  # noqa: E402  (anchor evaluation shared with the generator, but run on the raw YAML)

fails = []


def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        fails.append(msg)


# ---------------------------------------------------------------- DXF helpers
def dxf_entities(path):
    t = [x.strip() for x in open(path).read().split("\n")]
    i = t.index("ENTITIES")
    out, j, cur = [], i + 1, None
    while not (t[j] == "0" and t[j + 1] == "ENDSEC"):
        if t[j] == "0":
            cur = {"type": t[j + 1]}
            out.append(cur)
            j += 2
            continue
        cur.setdefault(t[j], []).append(t[j + 1])
        j += 2
    return out


def f(e, k):
    return float(e[k][0])


def contours(path, arc_step=3.0):
    """Chain LINE / ARC entities into closed rings (lists of points)."""
    segs = []
    for e in dxf_entities(path):
        if e["type"] == "LINE":
            segs.append([(f(e, "10"), f(e, "20")), (f(e, "11"), f(e, "21"))])
        elif e["type"] == "ARC":
            a0, a1 = f(e, "50"), f(e, "51")
            if a1 <= a0:
                a1 += 360
            n = max(2, int((a1 - a0) / arc_step))
            segs.append([(f(e, "10") + f(e, "40") * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                          f(e, "20") + f(e, "40") * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)])
    rings, used = [], [False] * len(segs)
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    ends = {}
    for i, s in enumerate(segs):
        ends.setdefault(key(s[0]), []).append((i, False))
        ends.setdefault(key(s[-1]), []).append((i, True))
    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        ring = list(segs[i])
        while key(ring[-1]) != key(ring[0]):
            nxt = None
            for (j, rev) in ends.get(key(ring[-1]), []):
                if not used[j]:
                    nxt = (j, rev)
                    break
            if nxt is None:
                break
            used[nxt[0]] = True
            s = segs[nxt[0]]
            ring += (s[::-1] if nxt[1] else s)[1:]
        rings.append(ring[:-1] if key(ring[-1]) == key(ring[0]) else ring)
    return rings


def circles(path):
    return [(f(e, "10"), f(e, "20"), f(e, "40")) for e in dxf_entities(path) if e["type"] == "CIRCLE"]


def centroid_bbox(r):
    xs, ys = [p[0] for p in r], [p[1] for p in r]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys))


def squares(rings, side):
    """Rings that are squares of the given side (rotation allowed): returns their centres."""
    out = []
    for r in rings:
        if len(r) < 4 or len(r) > 40:
            continue
        P = Polygon(r)
        if abs(P.area - side * side) < 0.02 * side * side and abs(P.length - 4 * side) < 0.1:
            c = P.centroid
            out.append((c.x, c.y))
    return out


def discs(rings, d, dtol=0.25):
    out = []
    for r in rings:
        cx, cy, w, h = centroid_bbox(r)
        if abs(w - d) < dtol and abs(h - d) < dtol and len(r) >= 8:
            out.append((cx, cy))
    return out


def match(found, expected, label):
    """Every expected point has exactly one found point within TOL, and no extra points exist."""
    worst = 0.0
    ok = True
    left = list(found)
    for e in expected:
        best = min(left, key=lambda p: math.hypot(p[0] - e[0], p[1] - e[1]), default=None)
        if best is None or math.hypot(best[0] - e[0], best[1] - e[1]) > TOL:
            ok = False
            continue
        worst = max(worst, math.hypot(best[0] - e[0], best[1] - e[1]))
        left.remove(best)
    ok = ok and not left
    check(ok, "%s: %d expected, %d found, max deviation %.4f mm" % (label, len(expected), len(found), worst))


def render(part, out):
    subprocess.run(["openscad", "-q", "-D", 'part="%s"' % part, "-o", out, os.path.join(CASE, "corne_case.scad")], check=True)


def outline_with_holes(rings):
    rings = sorted(rings, key=lambda r: -Polygon(r).area)
    outer = Polygon(rings[0])
    holes = [r for r in rings[1:] if outer.contains(Polygon(r).representative_point())]
    return Polygon(rings[0], holes)


def main():
    cfg = yaml.safe_load(open(os.path.join(ERG, "config.yaml")))
    pts = yaml.safe_load(open(os.path.join(ERG, "preview", "points.yaml")))
    units = {"kp": 19.05, "ks": 19.05}
    for k, v in cfg["units"].items():
        units[k] = gg.evaluate(v, units)

    def anchor(n):
        a = cfg["anchors"][n]
        r = pts[a["ref"]]
        sx, sy = (gg.evaluate(v, units) for v in a.get("shift", [0, 0]))
        return (r["x"] + sx, r["y"] + sy)

    keys42 = [(p["x"], p["y"]) for n, p in pts.items()]
    keys36 = [(p["x"], p["y"]) for n, p in pts.items() if not n.startswith("matrix_outer_")]
    holes = [anchor(h) for h in ("h1", "h2", "h3", "h4", "h5")]
    rst, ctrl = anchor("rst"), anchor("ctrl")
    mir = lambda L: [(-x, y) for x, y in L]
    cut = 14.0
    tmp = tempfile.mkdtemp(prefix="corne_case_check_")

    # ---- Ergogen DXF self-consistency (frame shared with points.yaml)
    for n, keys in (("42", keys42), ("36", keys36)):
        rings = contours(os.path.join(ERG, "preview", "plate_%s.dxf" % n))
        match(squares(rings, cut), keys, "Ergogen plate_%s.dxf cutouts vs points.yaml" % n)
        match([(x, y) for x, y, r in circles(os.path.join(ERG, "preview", "plate_%s.dxf" % n))], holes,
              "Ergogen plate_%s.dxf holes vs config anchors" % n)
    rc = circles(os.path.join(ERG, "preview", "tray_42_left.dxf"))
    match([(x, y) for x, y, r in rc], [rst], "Ergogen tray_42_left.dxf reset hole vs config anchor")

    # ---- plates
    plates = {}
    for part, keys, right in (("slice_plate_42", keys42, False), ("slice_plate_36", keys36, False),
                              ("slice_plate_42_right", mir(keys42), True)):
        out = os.path.join(tmp, part + ".dxf")
        render(part, out)
        rings = contours(out)
        plates[part] = outline_with_holes(rings)
        match(squares(rings, cut), keys, "%s cutout centres vs Ergogen key centres" % part)
        match(discs(rings, 2.4), mir(holes) if right else holes, "%s screw holes vs mounting holes" % part)
    # ---- screw posts (OD 4.4, plate underside) must not run into a switch cutout or the windows
    for part in ("slice_plate_42", "slice_plate_36"):
        P = plates[part]
        hs = holes
        gap = min(Point(h).buffer(2.2).distance(Polygon(r)) for h in hs for r in
                  [q for q in contours(os.path.join(tmp, part + ".dxf")) if len(q) < 40 and Polygon(q).area > 150])
        check(gap > 0.2, "%s: screw posts (OD 4.4) clear of every switch cutout, smallest gap %.2f mm" % (part, gap))
    # ---- windows
    ctrl_pt = Point(ctrl)
    check(not plates["slice_plate_42"].contains(ctrl_pt), "plate_42 (left) open over the controller")
    check(plates["slice_plate_42"].contains(Point(rst)), "plate_42 (left) covers the reset button (button faces down)")
    check(not plates["slice_plate_42_right"].contains(Point(-rst[0], rst[1])), "plate_42_right open over the reset button (faces up)")
    check(not plates["slice_plate_42_right"].contains(Point(-ctrl[0], ctrl[1])), "plate_42_right open over the controller")

    # ---- trays
    bosses = {}
    for part, right in (("slice_tray_42_left", False), ("slice_tray_36_left", False), ("slice_tray_42_right", True)):
        out = os.path.join(tmp, part + ".dxf")
        render(part, out)
        rings = contours(out)
        match(discs(rings, 3.2) + discs(rings, 1.8, 0.1), mir(holes) if right else holes,
              "%s insert/pilot holes (3.2 mm, H4 1.8 mm) vs mounting holes" % part)
        bosses[part] = [Polygon(r) for r in rings]
        fl = os.path.join(tmp, part + "_floor.dxf")
        render(part + "_floor", fl)
        red = discs(contours(fl), 3.0, 0.1)
        if right:
            check(not any(math.hypot(x + rst[0], y - rst[1]) < 1 for x, y in red), "%s has no reset press hole" % part)
        else:
            match(red, [rst], "%s reset press hole vs Ergogen" % part)

    # ---- boss geometry and clearance to the real socket pads (needs a fresh Ergogen run in pcb/ergogen/output)
    pcb = os.path.join(ERG, "output", "pcbs", "corne_reversible.kicad_pcb")
    for part, right in (("slice_tray_42_left", False), ("slice_tray_42_right", True)):
        hs = mir(holes) if right else holes
        polys = bosses[part]
        walls = []
        for h in hs:
            outer = [P for P in polys if P.contains(Point(h)) and P.area < 80 and P.area > 12]
            if not outer:
                check(False, "%s: no boss around hole %s" % (part, h))
                continue
            inner = min((P for P in polys if P.contains(Point(h)) and P.area < 12), key=lambda P: P.area)
            walls.append(outer[0].exterior.distance(Point(h)) - math.sqrt(4 * inner.area / math.pi) / 2)
        print("INFO  %s: boss wall around the insert hole (H1..H5), thinnest per boss: %s mm" % (part, ", ".join("%.2f" % w for w in walls)))
        check(min(walls) >= 0.6, "%s: every boss keeps at least 0.6 mm of wall around its hole (min %.2f)" % (part, min(walls)))
    if os.path.exists(pcb):
        from shapely import affinity
        from shapely.geometry import box
        txt = open(pcb).read()
        for part, right in (("slice_tray_42_left", False), ("slice_tray_42_right", True)):
            layer = '"F.Cu"' if right else '"B.Cu"'
            pads = []
            for fp in re.split(r"\n  \(footprint ", txt)[1:]:
                m = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", fp)
                fx, fy, fr = float(m.group(1)), float(m.group(2)), math.radians(float(m.group(3) or 0))
                for pad in re.finditer(r'\(pad "[^"]*" smd \w+ \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\) \(size ([-\d.]+) ([-\d.]+)\) \(layers ([^)]*)\)', fp):
                    if layer not in pad.group(6):
                        continue
                    px, py = float(pad.group(1)), float(pad.group(2))
                    bx = fx + px * math.cos(fr) + py * math.sin(fr)
                    by = fy - px * math.sin(fr) + py * math.cos(fr)
                    shp = box(-float(pad.group(4)) / 2, -float(pad.group(5)) / 2, float(pad.group(4)) / 2, float(pad.group(5)) / 2)
                    shp = affinity.rotate(shp, float(pad.group(3) or 0), origin=(0, 0))
                    x, y = (-bx, -by) if right else (bx, -by)   # Ergogen frame, flipped for the right half
                    pads.append(affinity.translate(shp, x, y))
            gaps = []
            for P in bosses[part]:
                if 12 < P.area < 80:
                    gaps.append(min(P.distance(q) for q in pads))
            check(min(gaps) > 0.0, "%s: bosses clear of %s socket/diode pads from the PCB file, smallest gap %.2f mm" % (part, layer.strip('"'), min(gaps)))
    else:
        print("INFO  pcb/ergogen/output not present, boss-to-pad clearance skipped (run Ergogen first)")

    print("\n%s" % ("ALL CHECKS PASSED" if not fails else "%d CHECK(S) FAILED" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
