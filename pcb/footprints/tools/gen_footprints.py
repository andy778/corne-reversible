#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Single source of truth for the corne-reversible footprints.

Generates, from the same geometry:
  * KiCad 8/9 footprints in ../corne_reversible.pretty/
  * Ergogen v4 footprint modules in ../ergogen/

Run from anywhere:  python3 pcb/footprints/tools/gen_footprints.py

Coordinate convention (KiCad): x to the right, y DOWN, seen from the KiCad
front (F) side. Board-face convention used by the silkscreen (see README):
the LEFT half is used with KiCad F up, the RIGHT half with KiCad B up. Set
LEFT_FACE = "B" below to swap every LEFT/RIGHT label if WP7 decides otherwise.

Geometry provenance is documented in ../THIRD_PARTY.md.
"""

import math
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRETTY = os.path.join(ROOT, "corne_reversible.pretty")
ERGO = os.path.join(ROOT, "ergogen")

LEFT_FACE = "F"  # KiCad side that points up on the LEFT half
RIGHT_FACE = "B" if LEFT_FACE == "F" else "F"
LIB = "corne_reversible"


def fmt(v):
    """Format a number without trailing zeros (stable diffs)."""
    if isinstance(v, str):
        return v
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# --------------------------------------------------------------------------
# Tiny footprint model
# --------------------------------------------------------------------------
class Pad:
    def __init__(self, num, kind, shape, at, size, layers, drill=None,
                 rratio=None, chamfer=None, prims=None, net=None, angle=0,
                 anchor="circle"):
        self.num, self.kind, self.shape = num, kind, shape
        self.at, self.size, self.layers = at, size, layers
        self.drill, self.rratio, self.chamfer = drill, rratio, chamfer
        self.prims = prims or []
        # net: None (no net), ("param", NAME) or ("local", NAME)
        self.net, self.angle, self.anchor = net, angle, anchor


class Gr:
    def __init__(self, kind, layer, **kw):
        self.kind, self.layer, self.kw = kind, layer, kw


class Footprint:
    def __init__(self, name, descr, tags, ergo_name, params, attr="through_hole"):
        self.name, self.descr, self.tags = name, descr, tags
        self.ergo_name, self.params = ergo_name, params  # params: {name: default}
        self.attr = attr
        self.layer = "F"          # KiCad side the footprint itself sits on
        self.assembled = False    # True: JLCPCB places it (in BOM and position files)
        self.pads, self.grs = [], []
        self.ref = ("REF**", (0, 0), "F.SilkS")
        self.extra_ergo_doc = ""

    # helpers ---------------------------------------------------------------
    def pad(self, *a, **kw):
        p = Pad(*a, **kw)
        self.pads.append(p)
        return p

    def line(self, layer, a, b, w=0.12):
        self.grs.append(Gr("line", layer, a=a, b=b, w=w))

    def rect(self, layer, a, b, w=0.12):
        self.grs.append(Gr("rect", layer, a=a, b=b, w=w))

    def circle(self, layer, c, r, w=0.12):
        self.grs.append(Gr("circle", layer, c=c, r=r, w=w))

    def text(self, layer, s, at, size=0.8, th=None, rot=0, justify=None):
        mirror = layer.startswith("B.")
        if layer.endswith("SilkS"):          # JLCPCB legibility: >= 0.9 mm high, 0.15 mm stroke
            size, th = max(size, 0.9), max(th or 0, 0.15)
        self.grs.append(Gr("text", layer, s=s, at=at, size=size,
                           th=th or round(size * 0.15, 3), rot=rot,
                           mirror=mirror, justify=justify))


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "corne-reversible/" + "/".join(map(str, parts))))


# --------------------------------------------------------------------------
# Emitters
# --------------------------------------------------------------------------
def _pad_sexpr(fp, i, p, ergo):
    rot = (lambda a: f"${{{a} + p.r}}" if a else "${p.r}") if ergo else (lambda a: fmt(a) if a else None)
    r = rot(p.angle)
    at = f"(at {fmt(p.at[0])} {fmt(p.at[1])}{' ' + r if r else ''})"
    s = [f'(pad "{p.num}" {p.kind} {p.shape} {at} (size {fmt(p.size[0])} {fmt(p.size[1])})']
    if p.drill is not None:
        if isinstance(p.drill, tuple):
            s.append(f"(drill oval {fmt(p.drill[0])} {fmt(p.drill[1])})")
        else:
            s.append(f"(drill {fmt(p.drill)})")
    s.append("(layers " + " ".join(f'"{l}"' for l in p.layers) + ")")
    if p.rratio is not None or p.chamfer:
        s.append(f"(roundrect_rratio {fmt(p.rratio or 0)})")
    if p.chamfer:
        ratio, corners = p.chamfer
        s.append(f"(chamfer_ratio {fmt(ratio)}) (chamfer {' '.join(corners)})")
    if p.net is not None:
        if ergo:
            kind, name = p.net
            s.append("${p.%s.str}" % name if kind == "param" else "${p.local_net('%s').str}" % name)
    if p.shape == "custom":
        s.append(f"(options (clearance outline) (anchor {p.anchor}))")
        pr = []
        for prim in p.prims:
            if prim[0] == "poly":
                pts = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in prim[1])
                pr.append(f"(gr_poly (pts {pts}) (width 0) (fill yes))")
            elif prim[0] == "line":
                (x1, y1), (x2, y2), w = prim[1], prim[2], prim[3]
                pr.append(f"(gr_line (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)}) (width {fmt(w)}))")
        s.append("(primitives " + " ".join(pr) + ")")
    if not ergo:
        s.append(f'(uuid "{uid(fp.name, "pad", i)}")')
    return " ".join(s) + ")"


def _gr_sexpr(fp, i, g, ergo):
    st = lambda w: f"(stroke (width {fmt(w)}) (type solid))"
    u = "" if ergo else f' (uuid "{uid(fp.name, "gr", i)}")'
    k = g.kw
    if g.kind == "line":
        return (f"(fp_line (start {fmt(k['a'][0])} {fmt(k['a'][1])}) (end {fmt(k['b'][0])} {fmt(k['b'][1])}) "
                f"{st(k['w'])} (layer \"{g.layer}\"){u})")
    if g.kind == "rect":
        return (f"(fp_rect (start {fmt(k['a'][0])} {fmt(k['a'][1])}) (end {fmt(k['b'][0])} {fmt(k['b'][1])}) "
                f"{st(k['w'])} (fill none) (layer \"{g.layer}\"){u})")
    if g.kind == "circle":
        c, r = k["c"], k["r"]
        return (f"(fp_circle (center {fmt(c[0])} {fmt(c[1])}) (end {fmt(c[0] + r)} {fmt(c[1])}) "
                f"{st(k['w'])} (fill none) (layer \"{g.layer}\"){u})")
    if g.kind == "text":
        rot = f"${{{k['rot']} + p.r}}" if ergo else fmt(k["rot"])
        just = []
        if k["justify"]:
            just.append(k["justify"])
        if k["mirror"]:
            just.append("mirror")
        js = f" (justify {' '.join(just)})" if just else ""
        txt = k["s"].replace('"', '\\"')
        return (f'(fp_text user "{txt}" (at {fmt(k["at"][0])} {fmt(k["at"][1])} {rot}) (layer "{g.layer}"){u} '
                f"(effects (font (size {fmt(k['size'])} {fmt(k['size'])}) (thickness {fmt(k['th'])})){js}))")
    raise ValueError(g.kind)


def attr_flags(fp):
    if fp.assembled:
        return fp.attr
    return f"{fp.attr} exclude_from_pos_files exclude_from_bom allow_soldermask_bridges"


def to_kicad_mod(fp):
    ref, rat, rlayer = fp.ref
    out = [f'(footprint "{fp.name}"',
           "\t(version 20240108)",
           '\t(generator "corne_reversible_gen")',
           '\t(generator_version "1.0")',
           f'\t(layer "{fp.layer}.Cu")',
           f'\t(descr "{fp.descr}")',
           f'\t(tags "{fp.tags}")',
           f'\t(property "Reference" "{ref}" (at {fmt(rat[0])} {fmt(rat[1])} 0) (layer "{rlayer}") '
           f'(uuid "{uid(fp.name, "ref")}") (effects (font (size 1 1) (thickness 0.15))'
           f'{" (justify mirror)" if rlayer.startswith("B.") else ""}))',
           f'\t(property "Value" "{fp.name}" (at 0 0 0) (layer "F.Fab") (uuid "{uid(fp.name, "val")}") '
           "(effects (font (size 1 1) (thickness 0.15))))",
           f"\t(attr {attr_flags(fp)})"]
    for i, g in enumerate(fp.grs):
        out.append("\t" + _gr_sexpr(fp, i, g, False))
    for i, p in enumerate(fp.pads):
        out.append("\t" + _pad_sexpr(fp, i, p, False))
    out.append(")")
    return "\n".join(out) + "\n"


def to_ergogen(fp):
    params = ",\n".join(
        f"    {k}: {v}" for k, v in
        [("designator", f"'{fp.ref[0].rstrip('*')}'")] +
        [(k, "undefined" if v is None else "{ type: 'net', value: '%s' }" % v) for k, v in fp.params.items()])
    ref, rat, rlayer = fp.ref
    lines = []
    lines.append(f'  (footprint "{LIB}:{fp.name}"')
    lines.append(f'    (layer "{fp.layer}.Cu")')
    lines.append("    ${p.at}")
    lines.append(f'    (property "Reference" "${{p.ref}}" (at {fmt(rat[0])} {fmt(rat[1])} ${{p.r}}) (layer "{rlayer}") ${{p.ref_hide}} '
                 f'(effects (font (size 1 1) (thickness 0.15)){" (justify mirror)" if rlayer.startswith("B.") else ""}))')
    lines.append(f"    (attr {attr_flags(fp)})")
    for i, g in enumerate(fp.grs):
        lines.append("    " + _gr_sexpr(fp, i, g, True))
    for i, p in enumerate(fp.pads):
        lines.append("    " + _pad_sexpr(fp, i, p, True))
    lines.append("  )")
    body = "\n".join(lines)
    nets_doc = "\n".join(f"//   {k}" + (f" (default net '{v}')" if v else " (required)") for k, v in fp.params.items())
    return f"""// SPDX-License-Identifier: MIT
//
// {LIB}:{fp.name} for Ergogen v4.
// GENERATED by pcb/footprints/tools/gen_footprints.py -- do not edit by hand;
// change the generator and re-run it so KiCad and Ergogen stay identical.
//
// {fp.descr}
//
// Provenance and licences: pcb/footprints/THIRD_PARTY.md
// Pad names, nets and the jumper scheme: pcb/footprints/README.md
//
// Net params:
{nets_doc}
{fp.extra_ergo_doc}
module.exports = {{
  params: {{
{params}
  }},
  body: p => `
{body}
  `
}}
"""


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def mirror_x(pt):
    return (-pt[0], pt[1])


def mirror_corner(c):
    return {"top_left": "top_right", "top_right": "top_left",
            "bottom_left": "bottom_right", "bottom_right": "bottom_left"}[c]


def face_layers(face, mask=True, paste=False):
    l = [f"{face}.Cu"]
    if paste:
        l.append(f"{face}.Paste")
    if mask:
        l.append(f"{face}.Mask")
    return l


def other(face):
    return "B" if face == "F" else "F"


# --------------------------------------------------------------------------
# 1. Combined reversible MX + Choc hot-swap switch
# --------------------------------------------------------------------------
SW = dict(
    center_d=5.0,            # Choc V2 centre post needs 5.0; MX post is 4.0
    slot_c=5.29, slot_len=2.32, slot_w=1.9,   # covers MX pegs (+-5.08, 1.75) and Choc V1 pegs (+-5.5, 1.9)
    hs_d=3.0,                # socket / switch-pin holes (Kailh datasheets)
    mx_pad=(2.55, 2.5), mx_chamfer=0.2,
    choc_pad=(2.6, 2.6), choc_chamfer=0.5,
)


def switch_fp():
    fp = Footprint(
        "SW_MX_Choc_Hotswap_Reversible",
        "Reversible hot-swap footprint for Kailh MX (CPG151101S11) OR Kailh Choc (CPG135001S30) sockets on either "
        "face. MX pins on the +y half (MX switch rotated 180 deg, south-facing), Choc pins on the -y half. "
        "5.0 mm centre hole for Choc V2. Pad 1 = column side, pad 2 = diode side. MX pads adapted from "
        "ceoloide/ergogen-footprints switch_mx (c) 2023 Marco Massarelli, MIT; see THIRD_PARTY.md.",
        "keyboard switch hotswap MX Choc reversible kailh",
        "switch_mx_choc_reversible",
        {"from": None, "to": None})
    fp.ref = ("SW**", (0, -8.6), "F.SilkS")
    s = SW
    npth = ["*.Cu", "*.Mask"]
    fp.pad("", "np_thru_hole", "circle", (0, 0), (s["center_d"],) * 2, npth, drill=s["center_d"])
    for sx in (1, -1):
        fp.pad("", "np_thru_hole", "oval", (sx * s["slot_c"], 0), (s["slot_len"], s["slot_w"]), npth,
               drill=(s["slot_len"], s["slot_w"]))
    # Shared Choc pin-1 hole
    fp.pad("", "np_thru_hole", "circle", (0, -5.95), (s["hs_d"],) * 2, npth, drill=s["hs_d"])

    # sx=+1: switch on F, socket on B.   sx=-1: switch on B, socket on F.
    for sx, face in ((1, "B"), (-1, "F")):
        lay = face_layers(face)
        # --- MX (rotated 180 deg so its pins sit at +y) ---
        fp.pad("", "np_thru_hole", "circle", (3.81 * sx, 2.54), (s["hs_d"],) * 2, npth, drill=s["hs_d"])
        fp.pad("", "np_thru_hole", "circle", (-2.54 * sx, 5.08), (s["hs_d"],) * 2, npth, drill=s["hs_d"])
        fp.pad("1", "smd", "rect", (7.085 * sx, 2.54), s["mx_pad"], lay, net=("param", "from"))
        fp.pad("2", "smd", "roundrect", (-5.842 * sx, 5.08), s["mx_pad"], lay, rratio=0,
               chamfer=(s["mx_chamfer"], ["top_right" if sx == 1 else "top_left"]), net=("param", "to"))
        # --- Choc (standard orientation, pins at -y) ---
        fp.pad("", "np_thru_hole", "circle", (5 * sx, -3.75), (s["hs_d"],) * 2, npth, drill=s["hs_d"])
        fp.pad("1", "smd", "rect", (8.275 * sx, -3.75), s["choc_pad"], lay, net=("param", "from"))
        fp.pad("2", "smd", "roundrect", (-3.275 * sx, -5.95), s["choc_pad"], lay, rratio=0,
               chamfer=(s["choc_chamfer"], ["bottom_left" if sx == 1 else "bottom_right"]), net=("param", "to"))
        # Fab / courtyard: approximate socket bodies (bounding boxes of pads, holes and datasheet outline)
        mx_box = ((-7.3 * sx, 0.8), (8.55 * sx, 6.75))
        choc_box = ((-4.8 * sx, -8.35), (9.8 * sx, -1.35))
        for (a, b), label, ly in ((mx_box, "MX", 3.25), (choc_box, "CHOC", -3.25)):
            fp.rect(f"{face}.Fab", a, b, 0.1)
            fp.rect(f"{face}.CrtYd", a, b, 0.05)
            fp.text(f"{face}.SilkS", label, (0, ly), size=0.8, th=0.12)
    # switch housing and keycap references
    fp.rect("Dwgs.User", (-7, -7), (7, 7), 0.1)
    fp.rect("Dwgs.User", (-9.025, -9.025), (9.025, 9.025), 0.1)
    fp.extra_ergo_doc = """//
// MX hot-swap pad positions, sizes and the inner-pad chamfer are adapted from
// ceoloide/ergogen-footprints switch_mx.js, Copyright (c) 2023 Marco Massarelli,
// MIT licence (full notice in pcb/footprints/THIRD_PARTY.md).
//
// Notes:
// - Always reversible: MX and Choc socket pads on both faces. Solder one socket per
//   key, on the face that is the underside of that half.
// - Overlapping MX socket holes (2.84 mm apart, 3.0 mm drills) are inherent to
//   reversible MX hot-swap footprints; see README.
// - Choc V2 corner leg (if your switch has one) has no hole; see README."""
    return fp


# --------------------------------------------------------------------------
# Jumper helper (two pads, one shared mask opening, no paste)
# --------------------------------------------------------------------------
JMP = dict(w=0.9, h=1.25, gap=0.3, link_w=0.4, trace_w=0.3, via_size=0.7, via_drill=0.3)


def jumper(fp, face, hole_num, hole_net, hole_xy, inner_c, outer_c, horizontal, tgt_num, tgt_net,
           tgt_link_to=None):
    """Add a solder jumper on `face`.

    inner pad (number hole_num) is linked by copper to the hole at hole_xy;
    outer pad (number tgt_num) optionally linked to tgt_link_to (a via pad).
    Pads are w x h (horizontal jumpers: pads side by side along x).
    """
    w, h = (JMP["w"], JMP["h"]) if horizontal else (JMP["h"], JMP["w"])
    hw, hh = w / 2, h / 2
    rectp = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    lay = [f"{face}.Cu"]
    link = ("line", (0, 0), (hole_xy[0] - inner_c[0], hole_xy[1] - inner_c[1]), JMP["link_w"])
    fp.pad(hole_num, "smd", "custom", inner_c, (0.4, 0.4), lay, prims=[("poly", rectp), link], net=hole_net)
    prims = [("poly", rectp)]
    if tgt_link_to is not None:
        prims.append(("line", (0, 0), (tgt_link_to[0] - outer_c[0], tgt_link_to[1] - outer_c[1]), JMP["trace_w"]))
    fp.pad(tgt_num, "smd", "custom", outer_c, (0.4, 0.4), lay, prims=prims, net=tgt_net)
    # one mask opening across both halves and the gap
    cx, cy = (inner_c[0] + outer_c[0]) / 2, (inner_c[1] + outer_c[1]) / 2
    mw = abs(inner_c[0] - outer_c[0]) + w + 0.1
    mh = abs(inner_c[1] - outer_c[1]) + h + 0.1
    fp.pad("", "smd", "rect", (cx, cy), (mw, mh), [f"{face}.Mask"])


# --------------------------------------------------------------------------
# 2. Pro Micro / nice!nano jumper-reversible controller
# --------------------------------------------------------------------------
# Pin names as seen with the controller COMPONENT SIDE UP, USB towards -y,
# viewed from above (standard Pro Micro / nice!nano pinout).
PM_LEFT = ["D1", "D0", "GND", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
PM_RIGHT = ["RAW", "GND", "RST", "VCC", "D21", "D20", "D19", "D18", "D15", "D14", "D16", "D10"]
PM = dict(row_x=7.62, y0=-12.7, pitch=2.54, hole_d=1.0, hole_pad=1.7,
          j_inner=5.45, j_outer=4.25, via_dy=0.75,
          bat_y=-15.24, bat_x=1.27)


def controller_fp():
    sig_names = sorted(set(PM_LEFT + PM_RIGHT), key=lambda n: (n[0] != "D", int(n[1:]) if n[0] == "D" else 0, n))
    params = {n: n for n in sig_names}
    params.update({"BAT_P": "BAT_P", "BAT_N": "GND"})
    fp = Footprint(
        "MCU_ProMicro_nRF52840_Reversible_Jumpers",
        "Pro Micro footprint nRF52840 controller (nice!nano v2 / SuperMini), socketed, component side UP on both halves. "
        "Every hole has a solder jumper on each face: bridge ONLY the face pointing up (LEFT half: "
        f"{LEFT_FACE}.Cu, RIGHT half: {RIGHT_FACE}.Cu). Pads named after the controller pin they reach.",
        "pro micro nice nano supermini nrf52840 reversible jumper",
        "mcu_promicro_reversible_jumpers", params)
    fp.ref = ("MCU**", (0, -19.3), "F.SilkS")
    m = PM
    left_face = LEFT_FACE
    right_face = RIGHT_FACE

    def pnet(name):
        return ("param", "BAT_P" if name == "BAT+" else "BAT_N" if name == "BAT-" else name)

    for i in range(12):
        y = m["y0"] + m["pitch"] * i
        hl, hr = f"H{i + 1}", f"H{24 - i}"           # Pro Micro pin numbers in left-half view
        nl, nr = PM_LEFT[i], PM_RIGHT[i]             # pin seated in that hole on the LEFT half
        xl, xr = -m["row_x"], m["row_x"]
        for hn, x in ((hl, xl), (hr, xr)):
            fp.pad(hn, "thru_hole", "circle", (x, y), (m["hole_pad"],) * 2, ["*.Cu", "*.Mask"],
                   drill=m["hole_d"], net=("local", hn))
        via_l = (0, y - m["via_dy"])   # net nl
        via_r = (0, y + m["via_dy"])   # net nr
        fp.pad(nl, "thru_hole", "circle", via_l, (JMP["via_size"],) * 2, ["*.Cu"], drill=JMP["via_drill"], net=pnet(nl))
        fp.pad(nr, "thru_hole", "circle", via_r, (JMP["via_size"],) * 2, ["*.Cu"], drill=JMP["via_drill"], net=pnet(nr))
        # LEFT face: hole -> the pin the LEFT half seats there.
        jumper(fp, left_face, hl, ("local", hl), (xl, y), (-m["j_inner"], y), (-m["j_outer"], y), True,
               nl, pnet(nl), via_l)
        jumper(fp, left_face, hr, ("local", hr), (xr, y), (m["j_inner"], y), (m["j_outer"], y), True,
               nr, pnet(nr), via_r)
        # RIGHT face: the board is flipped, so the hole at -x holds the pin that sits at +x on the left half.
        jumper(fp, right_face, hl, ("local", hl), (xl, y), (-m["j_inner"], y), (-m["j_outer"], y), True,
               nr, pnet(nr), via_r)
        jumper(fp, right_face, hr, ("local", hr), (xr, y), (m["j_inner"], y), (m["j_outer"], y), True,
               nl, pnet(nl), via_l)
        # pin labels (what is seated in each hole on that half)
        for face, lab_l, lab_r in ((left_face, nl, nr), (right_face, nr, nl)):
            fp.text(f"{face}.SilkS", lab_l, (-10.55, y), size=0.75, th=0.12)
            fp.text(f"{face}.SilkS", lab_r, (10.55, y), size=0.75, th=0.12)

    # Battery holes next to the USB end (placeholder positions, see README).
    # LEFT half view: B+ on the left, B- on the right.
    by, bx = m["bat_y"], m["bat_x"]
    for hn, x, nleft, nright in (("HB1", -bx, "BAT+", "BAT-"), ("HB2", bx, "BAT-", "BAT+")):
        fp.pad(hn, "thru_hole", "circle", (x, by), (m["hole_pad"],) * 2, ["*.Cu", "*.Mask"], drill=m["hole_d"],
               net=("local", hn))
        sx = -1 if x < 0 else 1
        inner = (sx * (bx + 1.95), by)
        outer = (sx * (bx + 3.15), by)
        jumper(fp, left_face, hn, ("local", hn), (x, by), inner, outer, True, nleft, pnet(nleft))
        jumper(fp, right_face, hn, ("local", hn), (x, by), inner, outer, True, nright, pnet(nright))
    for face, a, b in ((left_face, "B+", "B-"), (right_face, "B-", "B+")):
        fp.text(f"{face}.SilkS", a, (-bx - 5.3, by), size=0.75, th=0.12)
        fp.text(f"{face}.SilkS", b, (bx + 5.3, by), size=0.75, th=0.12)

    # Outline of the controller board + USB, on both fab layers; silk box
    for face in ("F", "B"):
        fp.rect(f"{face}.Fab", (-8.89, -16.51), (8.89, 16.57), 0.1)
        fp.rect(f"{face}.Fab", (-3.81, -18.03), (3.81, -16.51), 0.1)
        fp.rect(f"{face}.CrtYd", (-9.15, -18.3), (9.15, 16.85), 0.05)
        fp.text(f"{face}.Fab", "USB", (0, -17.3), size=0.8)
        fp.line(f"{face}.SilkS", (-9.0, 16.75), (9.0, 16.75), 0.15)
        fp.line(f"{face}.SilkS", (-9.0, -16.75), (-4.0, -16.75), 0.15)
        fp.line(f"{face}.SilkS", (4.0, -16.75), (9.0, -16.75), 0.15)
    for face, half in ((left_face, "LEFT"), (right_face, "RIGHT")):
        fp.text(f"{face}.SilkS", f"{half} HALF: BRIDGE 24 PIN", (0, 18.1), size=0.9, th=0.15)
        fp.text(f"{face}.SilkS", "JUMPERS ON THIS FACE ONLY", (0, 19.4), size=0.9, th=0.15)
        fp.text(f"{face}.SilkS", "USB / CONTROLLER FACE UP", (0, 20.7), size=0.7, th=0.12)
    fp.extra_ergo_doc = """//
// Notes:
// - Place with the USB end towards -y (same as the KiCad footprint), component
//   side up on both halves. Holes H1..H24 are local nets, only joined to a
//   signal through a bridged jumper. Each signal has one tented 0.3 mm via-pad in
//   the centre column that both of its jumpers are already tied to; route the
//   board net to that via.
// - BAT_P / BAT_N jumpers are a PLACEHOLDER for controllers with B+/B- holes at
//   the USB end. Bridging both faces there shorts the battery. See README."""
    return fp


# --------------------------------------------------------------------------
# 3. nice!view 5-pin header with jumpers
# --------------------------------------------------------------------------
NV_LEFT = ["MOSI", "SCK", "VCC", "GND", "CS"]   # left-half view, x = -5.08 .. +5.08


def niceview_fp():
    fp = Footprint(
        "Display_niceview_Header_Reversible_Jumpers",
        "nice!view 5-pin 2.54 mm header (MOSI, SCK, VCC, GND, CS in LEFT-half view). VCC is the centre pin and "
        "mirrors onto itself; the other four have a solder jumper per face. Bridge ONLY the face pointing up.",
        "nice!view display header reversible jumper",
        "display_niceview_reversible_jumpers",
        {"MOSI": "MOSI", "SCK": "SCK", "VCC": "VCC", "GND": "GND", "CS": "CS"})
    fp.ref = ("DISP**", (0, -6.3), "F.SilkS")
    n = len(NV_LEFT)
    for k in range(n):
        x = -5.08 + 2.54 * k
        left_fn, right_fn = NV_LEFT[k], NV_LEFT[n - 1 - k]
        if left_fn == right_fn:   # VCC
            fp.pad(left_fn, "thru_hole", "circle", (x, 0), (1.7, 1.7), ["*.Cu", "*.Mask"], drill=1.0,
                   net=("param", left_fn))
        else:
            hn = f"H{k + 1}"
            fp.pad(hn, "thru_hole", "circle", (x, 0), (1.7, 1.7), ["*.Cu", "*.Mask"], drill=1.0, net=("local", hn))
            for face, fn in ((LEFT_FACE, left_fn), (RIGHT_FACE, right_fn)):
                jumper(fp, face, hn, ("local", hn), (x, 0), (x, 1.85), (x, 3.05), False, fn, ("param", fn))
        for face, fn in ((LEFT_FACE, left_fn), (RIGHT_FACE, right_fn)):
            fp.text(f"{face}.SilkS", fn, (x, -3.1), size=0.9, th=0.15, rot=90)
    for face, half in ((LEFT_FACE, "LEFT"), (RIGHT_FACE, "RIGHT")):
        fp.text(f"{face}.SilkS", f"{half}: bridge 4", (0, 4.7), size=0.7, th=0.12)
    for face in ("F", "B"):
        fp.rect(f"{face}.SilkS", (-6.45, -1.35), (6.45, 1.1), 0.12)
        fp.rect(f"{face}.CrtYd", (-6.7, -5.0), (6.7, 5.3), 0.05)
        fp.rect(f"{face}.Fab", (-6.35, -1.27), (6.35, 1.27), 0.1)
    return fp


# --------------------------------------------------------------------------
# 4. Hand-soldered edge parts: per-face SMD pads (no jumpers needed)
# --------------------------------------------------------------------------
def per_face(fp, pads, enlarge=None):
    """pads: list of (num, at, size, net) for the KiCad-front copy; B copy is mirrored."""
    for face in ("F", "B"):
        for num, at, size, net in pads:
            at2 = at if face == "F" else mirror_x(at)
            fp.pad(num, "smd", "rect", at2, size, face_layers(face), net=net)


def power_switch_fp():
    fp = Footprint(
        "SW_SPDT_MSK12C02_Reversible",
        "Shou Han MSK-12C02 side-actuated SPDT slide switch, SMD pads on both faces (hand-soldered on the "
        "underside). Pin 2 = common. Actuator towards +y (board edge). Pads lengthened 0.4 mm for hand soldering. "
        "Pad geometry from the MSK-12C02 datasheet / KiCad SW_SPDT_Shouhan_MSK12C02.",
        "slide switch power SPDT MSK-12C02 reversible side",
        "power_switch_msk12c02_reversible", {"from": "BAT_P", "to": "RAW"}, attr="smd")
    fp.ref = ("PWR**", (0, -4.2), "F.SilkS")
    pads = [("1", (-2.25, -2.15), (0.6, 1.7), ("param", "from")),
            ("2", (0.75, -2.15), (0.6, 1.7), ("param", "to")),
            ("3", (2.25, -2.15), (0.6, 1.7), ("local", "NC")),
            ("", (-3.675, -1.1), (1.05, 0.7), None), ("", (-3.675, 1.1), (1.05, 0.7), None),
            ("", (3.675, -1.1), (1.05, 0.7), None), ("", (3.675, 1.1), (1.05, 0.7), None)]
    per_face(fp, pads)
    for x in (-1.5, 1.5):
        fp.pad("", "np_thru_hole", "circle", (x, 0), (0.85, 0.85), ["*.Cu", "*.Mask"], drill=0.85)
    for face in ("F", "B"):
        sx = 1 if face == "F" else -1
        fp.rect(f"{face}.Fab", (-3.35, -1.4), (3.35, 1.4), 0.1)
        fp.rect(f"{face}.Fab", (0.15 * sx, 1.4), (1.45 * sx, 2.85), 0.1)
        fp.rect(f"{face}.CrtYd", (-4.45, -3.25), (4.45, 3.1), 0.05)
        fp.line(f"{face}.SilkS", (-3.0, 1.55), (3.0, 1.55), 0.12)
        fp.text(f"{face}.SilkS", "PWR", (0, 2.4), size=0.7, th=0.12)
    return fp


def reset_fp():
    fp = Footprint(
        "SW_Reset_TS-1186F_Side_Reversible",
        "PROVISIONAL (reset part not final, WP3). XKB TS-1186F-B-A (LCSC C908470) right-angle SMD tactile switch, "
        "3.5 x 2.9 mm body, actuator towards +y (board edge), 2 x 0.8 mm holes for the locating pegs. Pads on both "
        "faces (hand-soldered on the underside). Land pattern from the XKB TS-1186F-X-X drawing (pads 1.2 x 0.6 at "
        "x +-2.0, y +-0.9), pads lengthened 0.4 mm outward for hand soldering. Pins 1+2 (y<0) and 3+4 (y>0) are "
        "internally joined, so the footprint uses pad numbers 1 and 2 only.",
        "reset tactile side switch TS-1186F right angle reversible",
        "reset_switch_ts1186f_reversible", {"from": "RST", "to": "GND"}, attr="smd")
    fp.ref = ("RST**", (0, -2.6), "F.SilkS")
    pads = [("1", (-2.2, -0.9), (1.6, 0.6), ("param", "from")), ("1", (2.2, -0.9), (1.6, 0.6), ("param", "from")),
            ("2", (-2.2, 0.9), (1.6, 0.6), ("param", "to")), ("2", (2.2, 0.9), (1.6, 0.6), ("param", "to"))]
    per_face(fp, pads)
    for y in (-0.9, 0.9):
        fp.pad("", "np_thru_hole", "circle", (0, y), (0.8, 0.8), ["*.Cu", "*.Mask"], drill=0.8)
    for face in ("F", "B"):
        fp.rect(f"{face}.Fab", (-1.75, -1.45), (1.75, 1.45), 0.1)
        fp.rect(f"{face}.Fab", (-0.8, 1.45), (0.8, 2.15), 0.1)
        fp.rect(f"{face}.CrtYd", (-3.25, -1.7), (3.25, 2.4), 0.05)
        fp.text(f"{face}.SilkS", "RST", (0, 3.1), size=0.7, th=0.12)
    return fp


FACE_A = RIGHT_FACE   # underside of the LEFT half: the one face JLCPCB assembles


def reset_1187a_fp(face="F"):
    """XKB TS-1187A-B-A-B, JLCPCB Basic part C318884, factory-placed on face A only.

    The KiCad library copy is a normal front-side footprint (flip it onto face A in KiCad). The Ergogen
    module is emitted already flipped onto FACE_A, so Ergogen boards get it on the assembled side with
    correct position-file side and rotation.
    """
    sx = 1 if face == "F" else -1
    fp = Footprint(
        "SW_Reset_TS-1187A_FaceA",
        "XKB TS-1187A-B-A-B (JLCPCB/LCSC C318884, Basic) 5.1 x 5.1 x 1.5 mm top-actuated SMD tactile switch. "
        "JLCPCB-assembled on face A only (KiCad " + FACE_A + "): on the LEFT half it faces down (press through "
        "the tray), on the RIGHT half it faces up (keep it outside the plate). Land pattern = KiCad "
        "SW_Push_1P1T_XKB_TS-1187A (pads 1.0 x 0.75 at x +-3.0, y +-1.875). Pins 1 and 2 pairs are joined inside.",
        "reset tactile switch TS-1187A SMD JLCPCB basic face A",
        "reset_switch_ts1187a_face_a", {"from": "RST", "to": "GND"}, attr="smd")
    fp.layer = face
    fp.assembled = True
    fp.ref = ("SW**", (0, -3.6 * 1), f"{face}.SilkS")
    for num, y in (("1", -1.875), ("2", 1.875)):
        for x in (-3.0, 3.0):
            fp.pad(num, "smd", "rect", (x * sx, y), (1.0, 0.75), face_layers(face, paste=True),
                   net=("param", "from" if num == "1" else "to"))
    fp.rect(f"{face}.Fab", (-2.55, -2.55), (2.55, 2.55), 0.1)
    fp.circle(f"{face}.Fab", (0, 0), 1.2, 0.1)
    fp.rect(f"{face}.CrtYd", (-3.75, -2.8), (3.75, 2.8), 0.05)
    for a, b in (((-2.75, -1.0), (-2.75, 1.0)), ((2.75, -1.0), (2.75, 1.0)),
                 ((-1.3, -2.75), (1.3, -2.75)), ((-1.3, 2.75), (1.3, 2.75))):
        fp.line(f"{face}.SilkS", a, b, 0.12)
    fp.text(f"{face}.SilkS", "RST", (0, 3.6), size=0.7, th=0.12)
    return fp


JST_DY = 3.0   # offset of the second (other-face) hole pair


def jst_fp():
    fp = Footprint(
        "JST_PH_S2B-PH-K_Reversible",
        "JST PH 2-pin side-entry THT connector S2B-PH-K-S (LCSC C173752), plug from +y. Two hole pairs: y=0 for a "
        "connector fitted on KiCad F, y=-3.0 for one fitted on KiCad B. The pairs are wired mirror-image so pin 1 keeps "
        "its net on both faces without jumpers (no double-bridge battery short possible). Default pin 1 = BAT_N (GND), "
        "pin 2 = BAT_P: CHECK YOUR BATTERY LEAD POLARITY. Hole/pad sizes from the JST PH datasheet / KiCad "
        "JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal.",
        "JST PH battery connector THT side entry S2B-PH-K reversible",
        "battery_jst_ph_tht_reversible", {"BAT_P": "BAT_P", "BAT_N": "GND"}, attr="through_hole")
    fp.ref = ("BT**", (0, -6.6), "F.SilkS")
    th = ["*.Cu", "*.Mask"]
    # pair for a connector on F: pin 1 at -x (seen from F)
    fp.pad("1", "thru_hole", "roundrect", (-1, 0), (1.2, 1.75), th, drill=0.75, rratio=0.2, net=("param", "BAT_N"))
    fp.pad("2", "thru_hole", "oval", (1, 0), (1.2, 1.75), th, drill=0.75, net=("param", "BAT_P"))
    # pair for a connector on B: seen from F its pin 1 is at +x
    fp.pad("1", "thru_hole", "roundrect", (1, -JST_DY), (1.2, 1.75), th, drill=0.75, rratio=0.2, net=("param", "BAT_N"))
    fp.pad("2", "thru_hole", "oval", (-1, -JST_DY), (1.2, 1.75), th, drill=0.75, net=("param", "BAT_P"))
    for face, py in (("F", 0.0), ("B", -JST_DY)):
        sx = 1 if face == "F" else -1
        fp.rect(f"{face}.Fab", (-2.95, py - 1.35), (2.95, py + 6.25), 0.1)
        fp.rect(f"{face}.CrtYd", (-3.45, py - 1.85), (3.45, py + 11.0), 0.05)   # incl. plug and lead
        fp.text(f"{face}.Fab", "plug", (0, py + 4.5), size=0.7)
        # silk: bracket around this face's pair, polarity marks outside the pads
        fp.line(f"{face}.SilkS", (-3.1, py - 1.2), (-3.1, py + 1.2), 0.15)
        fp.line(f"{face}.SilkS", (3.1, py - 1.2), (3.1, py + 1.2), 0.15)
        fp.text(f"{face}.SilkS", "-", (-2.35 * sx, py), size=0.9, th=0.15)
        fp.text(f"{face}.SilkS", "+", (2.35 * sx, py), size=0.9, th=0.15)
    fp.text("F.SilkS", "USE THIS PAIR", (0, 2.2), size=0.6, th=0.1)
    fp.text("B.SilkS", "USE THIS PAIR", (0, -JST_DY - 2.0), size=0.6, th=0.1)
    return fp


ALL = [switch_fp, controller_fp, niceview_fp, power_switch_fp, reset_fp, reset_1187a_fp, jst_fp]


def main():
    os.makedirs(PRETTY, exist_ok=True)
    os.makedirs(ERGO, exist_ok=True)
    for f in ALL:
        fp = f()
        with open(os.path.join(PRETTY, fp.name + ".kicad_mod"), "w") as fh:
            fh.write(to_kicad_mod(fp))
        efp = f(FACE_A) if f is reset_1187a_fp else fp
        with open(os.path.join(ERGO, fp.ergo_name + ".js"), "w") as fh:
            fh.write(to_ergogen(efp))
        print(f"wrote {fp.name}.kicad_mod and ergogen/{fp.ergo_name}.js ({len(fp.pads)} pads)")


if __name__ == "__main__":
    main()
