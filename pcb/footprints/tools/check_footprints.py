#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Geometry checks for the corne_reversible footprints against JLCPCB 2-layer rules.

Usage:  python3 pcb/footprints/tools/check_footprints.py [--markdown]
Needs:  shapely >= 2  (pip install shapely)

What it checks, per .kicad_mod in ../corne_reversible.pretty/:
  * copper-to-copper clearance between pads of DIFFERENT pad numbers on each copper
    layer (pads with the same number are the same net by KiCad convention; unnamed
    mechanical pads count as their own net)
  * drill-to-copper clearance (any hole vs copper of another net)
  * hole-to-hole spacing (edge to edge; negative = holes overlap)
  * annular ring of plated holes, minimum drill
  * for the switch: overlap of MX socket pads with Choc socket pads/holes on the same face
  * diode clearance: KiCad stock D_SOD-123 (courtyard 4.7 x 2.3 mm) placed on KiCad B
    (face A) midway between two vertically adjacent keys, long axis across the column.

Rule values (assumed JLCPCB 2-layer standard capabilities; verify on jlcpcb.com
before ordering): see RULES below.
"""

import glob
import math
import os
import re
import sys

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(os.path.dirname(HERE), "corne_reversible.pretty")

RULES = {
    "copper_clearance": 0.127,   # trace/space, pad-to-pad
    "hole_to_copper": 0.2,       # drill edge to copper of another net (assumed)
    "hole_to_hole": 0.5,         # drill edge to drill edge, different nets (JLC: 0.5 PTH; NPTH 0.5 recommended)
    "min_drill": 0.3,
    "annular_ring": 0.15,
}

# ---------------------------------------------------------------- s-expr ---
TOK = re.compile(r'\s*(\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+)')


def parse(text):
    stack, cur = [], []
    for m in TOK.finditer(text):
        t = m.group(1)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur[0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


# ------------------------------------------------------------- geometry ---
def chamfered_rect(w, h, ratio, corners):
    c = ratio * min(w, h)
    hw, hh = w / 2, h / 2
    # corner order: top_left(-,-) top_right(+,-) bottom_right(+,+) bottom_left(-,+)
    pts = []
    spec = [("top_left", (-hw, -hh), (0, c), (c, 0)),
            ("top_right", (hw, -hh), (-c, 0), (0, c)),
            ("bottom_right", (hw, hh), (0, -c), (-c, 0)),
            ("bottom_left", (-hw, hh), (c, 0), (0, -c))]
    for name, (x, y), d1, d2 in spec:
        if name in corners and c > 0:
            pts.append((x + d1[0], y + d1[1]))
            pts.append((x + d2[0], y + d2[1]))
        else:
            pts.append((x, y))
    return Polygon(pts)


def pad_shape(pad):
    shape = pad[3]
    at = first(pad, "at")
    x, y = float(at[1]), float(at[2])
    ang = float(at[3]) if len(at) > 3 else 0.0
    size = first(pad, "size")
    w, h = float(size[1]), float(size[2])
    if shape == "circle":
        g = Point(0, 0).buffer(w / 2, 64)
    elif shape == "oval":
        r = min(w, h) / 2
        if w >= h:
            g = LineString([(-(w / 2 - r), 0), (w / 2 - r, 0)]).buffer(r, 64)
        else:
            g = LineString([(0, -(h / 2 - r)), (0, h / 2 - r)]).buffer(r, 64)
    elif shape == "rect":
        g = box(-w / 2, -h / 2, w / 2, h / 2)
    elif shape == "roundrect":
        ch = first(pad, "chamfer")
        ratio = first(pad, "chamfer_ratio")
        rr = float(first(pad, "roundrect_rratio")[1]) if first(pad, "roundrect_rratio") else 0
        if ch and ratio:
            g = chamfered_rect(w, h, float(ratio[1]), ch[1:])
        else:
            rad = rr * min(w, h)
            g = box(-w / 2 + rad, -h / 2 + rad, w / 2 - rad, h / 2 - rad).buffer(rad, 32) if rad else box(-w / 2, -h / 2, w / 2, h / 2)
    elif shape == "custom":
        parts = [Point(0, 0).buffer(min(w, h) / 2, 32)]
        prims = first(pad, "primitives") or []
        for pr in prims[1:]:
            if pr[0] == "gr_poly":
                pts = [(float(p[1]), float(p[2])) for p in first(pr, "pts")[1:]]
                parts.append(Polygon(pts))
            elif pr[0] == "gr_line":
                s, e = first(pr, "start"), first(pr, "end")
                wd = float(first(pr, "width")[1])
                parts.append(LineString([(float(s[1]), float(s[2])), (float(e[1]), float(e[2]))]).buffer(wd / 2, 16))
        g = unary_union(parts)
    else:
        raise ValueError(shape)
    if ang:
        g = rotate(g, -ang, origin=(0, 0))  # KiCad angles are CCW with y down
    return translate(g, x, y)


def hole_shape(pad):
    d = first(pad, "drill")
    if d is None:
        return None
    at = first(pad, "at")
    x, y = float(at[1]), float(at[2])
    if d[1] == "oval":
        w, h = float(d[2]), float(d[3])
        r = min(w, h) / 2
        g = (LineString([(-(w / 2 - r), 0), (w / 2 - r, 0)]) if w >= h else
             LineString([(0, -(h / 2 - r)), (0, h / 2 - r)])).buffer(r, 64)
        return translate(g, x, y), min(w, h)
    dia = float(d[1])
    return Point(x, y).buffer(dia / 2, 64), dia


def load(path):
    fp = parse(open(path).read())
    pads = []
    for i, p in enumerate(find(fp, "pad")):
        num, kind = p[1], p[2]
        layers = first(p, "layers")[1:]
        cu = set()
        for l in layers:
            if l in ("*.Cu", "F&B.Cu"):
                cu |= {"F.Cu", "B.Cu"}
            elif l.endswith(".Cu"):
                cu.add(l)
        if kind == "np_thru_hole":
            cu = set()   # NPTH carries no copper
        net = num if num else f"<mech{i}>"
        geom = pad_shape(p) if cu else None
        hole = hole_shape(p)
        size = first(p, "size")
        at = first(p, "at")
        pads.append(dict(i=i, num=num, net=net, kind=kind, cu=cu, geom=geom, hole=hole,
                         size=(float(size[1]), float(size[2])), at=(float(at[1]), float(at[2]))))
    courtyards = {"F": [], "B": []}
    for g in find(fp, "fp_rect"):
        layer = first(g, "layer")[1]
        if layer.endswith("CrtYd"):
            s, e = first(g, "start"), first(g, "end")
            x1, y1, x2, y2 = float(s[1]), float(s[2]), float(e[1]), float(e[2])
            courtyards[layer[0]].append(box(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return fp[1], pads, courtyards


def desc(p):
    kind = "NPTH" if p["kind"] == "np_thru_hole" else ("PTH" if p["kind"] == "thru_hole" else "SMD")
    return f"{kind} '{p['num'] or '-'}' @({p['at'][0]:.3f},{p['at'][1]:.3f})"


def check(path):
    name, pads, _ = load(path)
    res = {"name": name, "violations": [], "min": {}, "notes": []}

    def track(key, val, a, b):
        cur = res["min"].get(key)
        if cur is None or val < cur[0]:
            res["min"][key] = (val, f"{desc(a)} vs {desc(b)}")

    # copper-copper per layer
    for layer in ("F.Cu", "B.Cu"):
        on = [p for p in pads if layer in p["cu"]]
        for i in range(len(on)):
            for j in range(i + 1, len(on)):
                a, b = on[i], on[j]
                if a["net"] == b["net"]:
                    continue
                d = a["geom"].distance(b["geom"])
                track(f"copper clearance {layer}", d, a, b)
                if d < RULES["copper_clearance"] - 1e-6:
                    res["violations"].append(f"{layer}: copper {d:.3f} < {RULES['copper_clearance']} : {desc(a)} vs {desc(b)}")
    # hole to copper
    holes = [p for p in pads if p["hole"]]
    for h in holes:
        hg, dia = h["hole"]
        for layer in ("F.Cu", "B.Cu"):
            for c in pads:
                if layer not in c["cu"] or c is h:
                    continue
                if h["kind"] == "thru_hole" and c["net"] == h["net"]:
                    continue
                d = hg.distance(c["geom"])
                track("hole to copper (other net)", d, h, c)
                if d < RULES["hole_to_copper"] - 1e-6:
                    res["violations"].append(f"{layer}: hole-to-copper {d:.3f} < {RULES['hole_to_copper']} : {desc(h)} vs {desc(c)}")
    # hole to hole
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            a, b = holes[i], holes[j]
            ga, gb = a["hole"][0], b["hole"][0]
            d = ga.distance(gb)
            if ga.intersects(gb):
                # signed overlap: how far the edges overlap along the centre line
                ca, cb = ga.centroid, gb.centroid
                d = ca.distance(cb) - (a["hole"][1] + b["hole"][1]) / 2
            track("hole to hole (edge-edge)", d, a, b)
            if d < RULES["hole_to_hole"] - 1e-6:
                res["violations"].append(f"hole-to-hole {d:.3f} < {RULES['hole_to_hole']} : {desc(a)} vs {desc(b)}")
    # annular ring and drill
    for p in pads:
        if p["hole"]:
            dia = p["hole"][1]
            track("drill diameter", dia, p, p)
            if dia < RULES["min_drill"] - 1e-6:
                res["violations"].append(f"drill {dia:.3f} < {RULES['min_drill']} : {desc(p)}")
            if p["kind"] == "thru_hole":
                ring = (min(p["size"]) - dia) / 2
                track("annular ring", ring, p, p)
                if ring < RULES["annular_ring"] - 1e-6:
                    res["violations"].append(f"annular ring {ring:.3f} < {RULES['annular_ring']} : {desc(p)}")
    return res, pads


def switch_specific(pads):
    """MX vs Choc socket interaction on each face (switch footprint only)."""
    out = []
    smd = [p for p in pads if p["kind"] == "smd"]
    holes = [p for p in pads if p["hole"]]
    for layer in ("F.Cu", "B.Cu"):
        mx = [p for p in smd if layer in p["cu"] and p["at"][1] > 0]
        ch = [p for p in smd if layer in p["cu"] and p["at"][1] < 0]
        dmin = min(a["geom"].distance(b["geom"]) for a in mx for b in ch)
        hm = min(a["geom"].distance(h["hole"][0]) for a in mx for h in holes)
        hc = min(a["geom"].distance(h["hole"][0]) for a in ch for h in holes)
        out.append(f"{layer}: MX pads vs Choc pads min gap {dmin:.3f} mm; MX pads vs any hole {hm:.3f} mm; "
                   f"Choc pads vs any hole {hc:.3f} mm")
    return out


def diode_check(switch_path):
    """SOD-123 (KiCad stock geometry) on KiCad B between keys at (0,0) and (0,19.05)."""
    name, pads, crt = load(switch_path)
    pitch = 19.05
    dy = pitch / 2
    diode_crt = box(-2.35, dy - 1.15, 2.35, dy + 1.15)
    diode_pads = unary_union([box(-1.65 - 0.45, dy - 0.6, -1.65 + 0.45, dy + 0.6),
                              box(1.65 - 0.45, dy - 0.6, 1.65 + 0.45, dy + 0.6)])
    diode_body = box(-1.4, dy - 0.9, 1.4, dy + 0.9)
    lines = []
    for off, label in ((0, "key above"), (pitch, "key below")):
        cu = [translate(p["geom"], 0, off) for p in pads if "B.Cu" in p["cu"]]
        hl = [translate(p["hole"][0], 0, off) for p in pads if p["hole"]]
        cy = [translate(c, 0, off) for c in crt["B"]]
        lines.append(f"{label}: diode pads to switch copper (B.Cu) {min(diode_pads.distance(g) for g in cu):.3f} mm; "
                     f"diode pads to nearest hole {min(diode_pads.distance(g) for g in hl):.3f} mm; "
                     f"diode courtyard to socket courtyards {min(diode_crt.distance(g) for g in cy):.3f} mm "
                     f"(overlap if 0)")
    # top-side (right half): diode body vs switch housings, plan figures
    for sw, half in (("MX housing bottom 15.6 mm", 15.6), ("MX housing top 14.0 mm (plan's 3.4 mm gap uses ~15.6)", 14.0),
                     ("Choc V1 housing 15.0 mm", 15.0)):
        gap = pitch - half
        margin = (gap - 1.8) / 2   # 1.8 mm = SOD-123 body incl. tolerance (datasheet 1.6 +- 0.1, rounded up)
        lines.append(f"top side, {sw}: gap between housings {gap:.2f} mm, SOD-123 body 1.6-1.8 mm -> "
                     f"{margin:.2f} mm each side")
    return lines


def main():
    md = "--markdown" in sys.argv
    files = sorted(glob.glob(os.path.join(PRETTY, "*.kicad_mod")))
    total = 0
    print("# Footprint check report\n" if md else "", end="")
    print(f"Rules: {RULES}\n")
    for f in files:
        res, pads = check(f)
        print(f"{'## ' if md else '== '}{res['name']}\n")
        for k, (v, where) in sorted(res["min"].items()):
            print(f"{'- ' if md else '  '}min {k}: {v:.3f} mm  ({where})")
        if "SW_MX_Choc" in res["name"]:
            for l in switch_specific(pads):
                print(f"{'- ' if md else '  '}{l}")
            for l in diode_check(f):
                print(f"{'- ' if md else '  '}diode: {l}")
        if res["violations"]:
            print(f"\n{'' if md else '  '}{len(res['violations'])} rule violation(s):\n")
            for v in res["violations"]:
                print(f"{'- ' if md else '    '}{v}")
        else:
            print(f"\n{'' if md else '  '}no rule violations")
        print()
        total += len(res["violations"])
    print(f"TOTAL violations: {total}")


if __name__ == "__main__":
    main()
