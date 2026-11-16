#!/usr/bin/python3
"""Build the routed KiCad board for corne-reversible from the WP4 Ergogen output.

Run from the repository root with the system Python that ships KiCad's pcbnew module:

    (cd pcb/ergogen && npx -y ergogen@4.2.1 . -o output --clean --debug --svg)
    /usr/bin/python3 pcb/kicad/tools/build_board.py

Deterministic: the same Ergogen output gives the same board. See pcb/kicad/README.md.
"""
import argparse
import json
import math
import os
import re
import shutil
import sys
import time

import pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kutil import (add_track, add_via, board_outline, drawings, fp_transform, items, mm,  # noqa: E402
                   pad_polys, pt, tracks)
import router as rt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "pcb", "ergogen", "output", "pcbs", "corne_reversible.kicad_pcb")
OUT_DIR = os.path.join(ROOT, "pcb", "kicad")
OUT = os.path.join(OUT_DIR, "corne_reversible.kicad_pcb")

F, B = pcbnew.F_Cu, pcbnew.B_Cu
LAYER = {0: F, 1: B}

# ---------------------------------------------------------------------------- widths (mm)
W_SIG = 0.25
W_PWR = 0.5    # BAT_P, RAW
W_GND = 0.4
W_VCC = 0.3
W_NECK = 0.3   # power/GND inside the controller hole rows (0.84 mm gaps between hole pads)

POWER_NETS = {"BAT_P": W_PWR, "RAW": W_PWR, "GND": W_GND, "VCC": W_VCC}

REVISION = "v1.0"
DATE = "2026-11-15"


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------- per-key template
# Key frame: footprint-local mm of SW_MX_Choc_Hotswap_Reversible (KiCad y down). The diode is at
# (0, 9.525) on B.Cu with the cathode (pad 1) at x = -1.65. Pads:
#   column  (pad 1): B MX (7.085, 2.54), B Choc (8.275, -3.75), F MX (-7.085, 2.54), F Choc (-8.275, -3.75)
#   anode   (pad 2): B MX (-5.842, 5.08), B Choc (-3.275, -5.95), F MX (5.842, 5.08), F Choc (3.275, -5.95)
# Each net is on one face on the left of the key and on the other face on the right, so each
# key carries its own face-to-face links:
KEY_TEMPLATE = {
    "col": {
        "tracks": [
            (0, [(-8.275, -3.75), (-7.085, 2.54)]),                          # F Choc - F MX
            (0, [(-8.275, -3.75), (-7.0, -6.4), (-2.2, -8.2), (6.4, -8.2)]),  # F over the top of the key
            (1, [(6.4, -8.2), (8.275, -3.75)]),                              # B to B Choc
            (1, [(8.275, -3.75), (7.085, 2.54)]),                            # B Choc - B MX
        ],
        "vias": [(6.4, -8.2)],
    },
    "anode": {
        "tracks": [
            (1, [(-3.275, -5.95), (-4.0, -6.6), (-7.2, -6.6), (-7.2, 3.6), (-5.842, 5.08)]),  # B Choc - B MX
            (0, [(3.275, -5.95), (4.0, -6.6), (7.2, -6.6), (7.2, 3.6), (5.842, 5.08)]),       # F Choc - F MX
            (1, [(-5.842, 5.08), (-3.6, 7.4), (4.4, 7.4)]),                                   # B MX - via
            (0, [(5.842, 5.08), (4.4, 7.4)]),                                                 # F MX - via
            (1, [(1.65, 7.4), (1.65, 9.525)]),                                                # to diode anode
        ],
        "vias": [(4.4, 7.4)],
    },
    "row": {
        "tracks": [(1, [(-1.65, 9.525), (-3.4, 9.525)])],  # diode cathode - row via
        "vias": [(-3.4, 9.525)],
    },
}

# ---------------------------------------------------------------------------- controller fan-out
# Controller via-pads sit at x = 0, y = y0 -/+ 0.75 for hole row y0 (local frame). Each via can be
# reached from outside the hole columns through the gap above or below its row; see README.
# (net, via local y, side -1 left/+1 right, layer 0 F/1 B, gap midline local y)
ROWS_Y = [-12.7 + 2.54 * k for k in range(12)]


def fanout_plan():
    up = lambda r: ROWS_Y[r] - 0.75   # noqa: E731  upper via of row r (0-based)
    lo = lambda r: ROWS_Y[r] + 0.75   # noqa: E731
    gap = lambda r: ROWS_Y[r] + 1.27  # noqa: E731  gap below row r
    return [
        # right side
        ("DISP_CS", up(0), +1, 0, ROWS_Y[0] - 1.27),
        ("RAW", lo(0), +1, 1, gap(0)),
        ("GND", lo(1), +1, 1, gap(1)),
        ("RST", lo(2), +1, 1, gap(2)),
        ("VCC", lo(3), +1, 1, gap(3)),
        ("DISP_MOSI", up(4), +1, 0, gap(3)),
        ("DISP_SCK", up(5), +1, 0, gap(4)),
        # left side
        ("COL_D21", lo(4), -1, 0, gap(4)),
        ("COL_D20", lo(5), -1, 0, gap(5)),
        ("ROW0", up(6), -1, 1, gap(5)),
        ("COL_D19", lo(6), -1, 0, gap(6)),
        ("ROW1", up(7), -1, 1, gap(6)),
        ("COL_D18", lo(7), -1, 0, gap(7)),
        ("ROW2", up(8), -1, 1, gap(7)),
        ("COL_D15", lo(8), -1, 0, gap(8)),
        ("ROW3", up(9), -1, 1, gap(8)),
        ("COL_D14", lo(9), -1, 0, gap(9)),
    ]


FANOUT_X = 9.0
MOUNT_KEEPOUT_R = 2.6  # no routed copper within this radius of a mounting hole centre (M2 head is 3.8 mm)  # stub end, just outside the hole pads (edge at 8.47)


# ---------------------------------------------------------------------------- helpers
def net_of(board, name):
    n = board.FindNet(name)
    if n is None:
        raise SystemExit(f"net {name} missing")
    return n


def poly_from_rings(rings):
    ps = [Polygon(r) for r in rings if len(r) >= 3]
    ps = [p if p.is_valid else p.buffer(0) for p in ps]
    return unary_union(ps)


def collect_items(board):
    """Copper items of the board for the router."""
    its = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetCode()
            geoms = {}
            for L, lay in LAYER.items():
                if p.IsOnLayer(lay) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    g = poly_from_rings(pad_polys(p, lay))
                    if not g.is_empty:
                        geoms[L] = g
            drill = None
            if p.GetDrillSizeX() > 0:
                c = p.GetPosition()
                dx, dy = mm(p.GetDrillSizeX()), mm(p.GetDrillSizeY())
                if abs(dx - dy) < 1e-6:
                    drill = (Point(mm(c.x), mm(c.y)), dx / 2)
                else:
                    # oval slot: approximate by a capsule; router uses its circumscribed circle
                    drill = (Point(mm(c.x), mm(c.y)), max(dx, dy) / 2)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                net = -1
                geoms = {}
            if net == 0 and geoms:
                net = -2  # netless copper: obstacle for everyone
            its.append(rt.Item(net, geoms, drill, kind=f"pad {fp.GetReference()}.{p.GetNumber()}", is_pad=bool(geoms)))
    for t in tracks(board):
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            g = Point(mm(c.x), mm(c.y)).buffer(mm(t.GetWidth(F)) / 2, 16)
            its.append(rt.Item(t.GetNetCode(), {0: g, 1: g}, (Point(mm(c.x), mm(c.y)), mm(t.GetDrillValue()) / 2), kind="via"))
        else:
            L = 0 if t.GetLayer() == F else 1
            a, b = t.GetStart(), t.GetEnd()
            g = LineString([(mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))]).buffer(mm(t.GetWidth()) / 2, 8)
            its.append(rt.Item(t.GetNetCode(), {L: g}, kind="track"))
    return its


def apertures(board):
    """Solder-mask apertures of the hand-solder jumpers (mask-only pads)."""
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and not (p.IsOnLayer(F) or p.IsOnLayer(B)):
                for lay, L in ((pcbnew.F_Mask, 0), (pcbnew.B_Mask, 1)):
                    if p.IsOnLayer(lay):
                        out.append((L, poly_from_rings(pad_polys(p, lay)), fp.GetReference()))
    return out


# ---------------------------------------------------------------------------- stages
def load_and_prepare():
    board = pcbnew.LoadBoard(SRC)
    # Local footprints that are not in corne_reversible.pretty live in corne_kicad_local.pretty
    for fp in board.GetFootprints():
        lib = fp.GetFPID()
        name = lib.GetLibItemName().wx_str()
        if name in ("D_SOD-123_Back", "MountingHole_2.2mm_M2"):
            fp.SetFPID(pcbnew.LIB_ID("corne_kicad_local", name))
    # Placeholder battery jumpers and the switch's unused pin: no net (see README, power section)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in ("MCU_BATP_UNUSED", "MCU_BATN_UNUSED", "PWR1_NC"):
                p.SetNetCode(0)
    # JLCPCB metadata on the two assembled footprints
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r.startswith("D") and fp.GetFPID().GetLibItemName().wx_str() == "D_SOD-123_Back":
            fp.SetValue("1N4148W")
            set_field(fp, "LCSC", "C81598")
            fp.SetAttributes(pcbnew.FP_SMD)
        elif fp.GetFPID().GetLibItemName().wx_str() == "SW_Reset_TS-1187A_FaceA":
            fp.SetValue("TS-1187A-B-A-B")
            set_field(fp, "LCSC", "C318884")
    return board


def set_field(fp, name, value):
    f = fp.GetField(name) if fp.HasField(name) else None
    if f is None:
        f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), name)
        fp.Add(f)
    f.SetText(value)
    f.SetVisible(False)
    f.SetLayer(pcbnew.B_Fab if fp.GetLayer() == B else pcbnew.F_Fab)


def key_pairs(board):
    sws = {fp.GetReference(): fp for fp in board.GetFootprints()
           if fp.GetFPID().GetLibItemName().wx_str() == "SW_MX_Choc_Hotswap_Reversible"}
    dds = {fp.GetReference(): fp for fp in board.GetFootprints()
           if fp.GetFPID().GetLibItemName().wx_str() == "D_SOD-123_Back"}
    pairs = []
    for ref, sw in sorted(sws.items(), key=lambda kv: int(kv[0][2:])):
        d = dds["D" + ref[2:]]
        pairs.append((sw, d))
    return pairs


def add_templates(board):
    for sw, d in key_pairs(board):
        f = fp_transform(sw)
        nets = {}
        for p in sw.Pads():
            if p.GetNumber() == "1":
                nets["col"] = p.GetNet()
            elif p.GetNumber() == "2":
                nets["anode"] = p.GetNet()
        for p in d.Pads():
            if p.GetNumber() == "1":
                nets["row"] = p.GetNet()
            else:
                assert p.GetNetname() == nets["anode"].GetNetname(), (sw.GetReference(), p.GetNetname())
        # sanity: diode really is at key frame (0, 9.525)
        dp = d.GetPosition()
        ex = f(0, 9.525)
        assert math.hypot(mm(dp.x) - ex[0], mm(dp.y) - ex[1]) < 1e-3, sw.GetReference()
        for key, tpl in KEY_TEMPLATE.items():
            net = nets[key]
            for L, pts in tpl["tracks"]:
                bp = [f(*q) for q in pts]
                for a, b in zip(bp, bp[1:]):
                    add_track(board, net, LAYER[L], a, b, W_SIG)
            for q in tpl["vias"]:
                add_via(board, net, f(*q))


def add_fanout(board):
    mcu = [fp for fp in board.GetFootprints() if fp.GetReference() == "MCU1"][0]
    f = fp_transform(mcu)
    ends = []
    for name, vy, side, L, ym in fanout_plan():
        net = net_of(board, name)
        w = W_NECK if name in POWER_NETS else W_SIG
        pts = [(0.0, vy), (side * 1.4, ym), (side * FANOUT_X, ym)]
        bp = [f(*q) for q in pts]
        for a, b in zip(bp, bp[1:]):
            add_track(board, net, LAYER[L], a, b, w)
        ends.append((name, L, bp[-1]))
    # GND: the three GND via-pads are tied inside the footprint:
    #  rows 2 and 3: lower via of row 2 and upper via of row 3 are adjacent (B, x = 0);
    #  rows 3 and 4: both left KiCad-F jumper pads are GND-side pads, joined on F through the gap.
    g = net_of(board, "GND")
    add_track(board, g, B, f(0, ROWS_Y[1] + 0.75), f(0, ROWS_Y[2] - 0.75), W_NECK)
    add_track(board, g, F, f(-4.25, ROWS_Y[2]), f(-4.25, ROWS_Y[3]), W_NECK)
    return ends


def add_display_stubs(board):
    """nice!view: every jumper target pad gets a stub out of its mask aperture, away from the gap.

    B pads: straight stub down to y = +4.65 (local). F pads: dog-leg to a via 0.9 mm to the left,
    so both faces can be reached from below. Under the header, four lanes per face run to a port
    1.47 mm right of the header (x = +6.55 local); the router joins the ports to the controller.
    Lane order (top to bottom) F: CS, GND, SCK, MOSI; B: MOSI, SCK, GND, CS (nested so that no
    lane crosses another net's riser on the same face).
    """
    disp = [fp for fp in board.GetFootprints() if fp.GetReference() == "DISP1"][0]
    f = fp_transform(disp)
    W = 0.2
    VY = 4.85          # via row, local y (pads at 3.05)
    LANES = [4.85, 5.5, 5.95, 6.4]
    XPORT = 6.55
    lane_f = {"CS": 0, "GND": 1, "SCK": 2, "MOSI": 3}
    lane_b = {"MOSI": 0, "SCK": 1, "GND": 2, "CS": 3}
    for p in disp.Pads():
        name = p.GetNumber()
        if name not in ("MOSI", "SCK", "GND", "CS") or not (p.IsOnLayer(F) or p.IsOnLayer(B)):
            continue
        net = p.GetNet()
        lx = round(mm(p.GetFPRelativePosition().x), 3)
        ly = round(mm(p.GetFPRelativePosition().y), 3)
        if p.IsOnLayer(F):
            vx = lx - 0.9
            pts = [(lx, ly), (lx, ly + 0.9), (vx, VY)]
            for a, b in zip(pts, pts[1:]):
                add_track(board, net, F, f(*a), f(*b), W)
            add_via(board, net, f(vx, VY))
            y = LANES[lane_f[name]]
            pts = [(vx, VY), (vx, y), (XPORT, y)] if y != VY else [(vx, VY), (XPORT, VY)]
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    add_track(board, net, F, f(*a), f(*b), W)
        else:
            y = LANES[lane_b[name]]
            pts = [(lx, ly), (lx, y), (XPORT, y)]
            for a, b in zip(pts, pts[1:]):
                add_track(board, net, B, f(*a), f(*b), W)


# ---------------------------------------------------------------------------- routing
def make_router(board):
    outline = board_outline(board)
    polys = [Polygon(ext, holes) for ext, holes in outline]
    poly = unary_union(polys)
    r = rt.Router(poly.bounds, poly, res=0.05)
    for it in collect_items(board):
        r.add_item(it)
    for L, g, ref in apertures(board):
        r.add_keepout(L, g.buffer(0.05))
    # Nothing but the hand-placed fan-out stubs inside the controller footprint (between its hole columns).
    mcu = [fp for fp in board.GetFootprints() if fp.GetReference() == "MCU1"][0]
    f = fp_transform(mcu)
    (x0, y0), (x1, y1) = f(-7.0, -16.5), f(7.0, 16.6)
    for L in (0, 1):
        r.add_keepout(L, box(x0, y0, x1, y1))
    # Mounting holes: keep routed copper outside the M2 screw head / insert boss footprint
    for fp in board.GetFootprints():
        if fp.GetFPID().GetLibItemName().wx_str() == "MountingHole_2.2mm_M2":
            c = fp.GetPosition()
            for L in (0, 1):
                r.add_keepout(L, Point(mm(c.x), mm(c.y)).buffer(MOUNT_KEEPOUT_R, 32))
    return r


def commit(board, r, net, segs, vias, w):
    netinfo = board.FindNet(r.netname[net])
    for L, a, b in segs:
        add_track(board, netinfo, LAYER[L], a, b, w)
        r.add_item(r.segment_item(net, L, a, b, w))
    for p in vias:
        add_via(board, netinfo, p)
        r.add_item(r.via_item(net, p))


def route_net(board, r, name, w=W_SIG, layer_cost=(1.0, 1.0), via_cost=1.5, order=None, max_tries=1,
              exclude=None, cost_maps=(), forbid=()):
    net = board.FindNet(name).GetNetCode()
    done = 0
    while True:
        comps = r.components(net)
        if exclude:
            comps = [c for c in comps if not exclude(c)]
        if len(comps) <= 1:
            return done
        # grow from the component chosen by `order` (default: largest)
        comps.sort(key=lambda c: -len(c))
        tree = comps[0] if order is None else order(comps)
        others = [c for c in comps if c is not tree]
        tg = unary_union([g for it in tree for g in it.geoms.values()])
        dist = sorted(((unary_union([g for it in c for g in it.geoms.values()]).distance(tg), k)
                       for k, c in enumerate(others)))
        d0, k = dist[0]
        target = others[k]
        tgeom = unary_union([g for it in target for g in it.geoms.values()])
        # sources: tree items within reach of the target
        src = [it for it in tree if any(g.distance(tgeom) < d0 + 12 for g in it.geoms.values())]
        t0 = time.time()
        kw = dict(layer_cost=layer_cost, via_cost=via_cost, cost_maps=cost_maps, forbid=forbid)
        path, msg = r.route_connection(net, src, target, w / 2, window_margin=6.0 + min(d0 * 0.3, 10), **kw)
        if path is None:
            path, msg = r.route_connection(net, src, target, w / 2, window_margin=25.0, **kw)
        if path is None:
            log(f"  FAIL {name}: {msg} (gap {d0:.2f} mm, target {[it.kind for it in target][:3]})")
            return -1
        segs, vias = r.path_to_segments(path, net, w / 2, forbid)
        commit(board, r, net, segs, vias, w)
        done += 1
        log(f"  {name}: +{len(segs)} segs {len(vias)} vias ({time.time() - t0:.1f}s, gap {d0:.1f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["prep", "template", "all"])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=None, help="debug: stop after N routing steps")
    ap.add_argument("--finish-only", default=None, help="debug: load a routed board and only run the finishing step")
    args = ap.parse_args()
    if args.finish_only:
        board = pcbnew.LoadBoard(args.finish_only)
        finish(board)
        pcbnew.SaveBoard(args.out, board)
        drop_items_from_file(args.out, DOOMED)
        bites_to_npth(args.out, os.path.dirname(args.out))
        write_project(os.path.splitext(args.out)[0] + ".kicad_pro")
        write_lib_table(os.path.dirname(args.out))
        return
    board = load_and_prepare()
    export_local_lib(board, os.path.dirname(args.out))
    if args.stage != "prep":
        add_templates(board)
        add_fanout(board)
        add_display_stubs(board)
    if args.stage == "all":
        route_all(board, args.limit)
    finish(board)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    pcbnew.SaveBoard(args.out, board)
    drop_items_from_file(args.out, DOOMED)
    bites_to_npth(args.out, os.path.dirname(args.out))
    write_project(os.path.splitext(args.out)[0] + ".kicad_pro")
    write_lib_table(os.path.dirname(args.out))
    log("saved", args.out)


# ---------------------------------------------------------------------------- project settings
RULES = {
    "min_clearance": 0.2,
    "min_connection": 0.0,
    "min_copper_edge_clearance": 0.3,
    "min_hole_clearance": 0.25,
    "min_hole_to_hole": 0.5,
    "min_through_hole_diameter": 0.3,
    "min_track_width": 0.2,
    "min_via_annular_width": 0.15,
    "min_via_diameter": 0.6,
    "min_silk_clearance": 0.0,
    "min_text_height": 0.8,
    "min_text_thickness": 0.15,
    "solder_mask_to_copper_clearance": 0.0,
}

NETCLASSES = [
    ("Default", W_SIG, 0.2, ""),
    ("Power", W_PWR, 0.2, "BAT_P|RAW"),
    ("Ground", W_GND, 0.2, "GND"),
    ("Logic3V3", W_VCC, 0.2, "VCC"),
]


def write_project(path):
    d = json.load(open(path))
    ds = d["board"]["design_settings"]
    ds["rules"].update(RULES)
    ds["track_widths"] = [0.0, 0.25, 0.3, 0.4, 0.5]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}]
    sev = ds["rule_severities"]
    # see README "Accepted DRC findings"
    sev["hole_to_hole"] = "warning"
    sev["npth_inside_courtyard"] = "warning"  # break-line NPTH on the key-tile boundary (WP8 S1)
    sev["lib_footprint_mismatch"] = "warning"
    sev["lib_footprint_issues"] = "warning"
    base = d["net_settings"]["classes"][0]
    classes = []
    for name, w, clr, _ in NETCLASSES:
        c = dict(base)
        c.update({"name": name, "track_width": w, "clearance": clr, "via_diameter": 0.6, "via_drill": 0.3,
                  "priority": -1 if name == "Default" else 1})
        classes.append(c)
    d["net_settings"]["classes"] = classes
    pats = [{"netclass": "Default", "pattern": ""}]
    for name, _, _, pat in NETCLASSES[1:]:
        for n in pat.split("|"):
            pats.append({"netclass": name, "pattern": n})
    d["net_settings"]["netclass_patterns"] = pats
    d["net_settings"]["netclass_assignments"] = None
    d["meta"]["filename"] = os.path.basename(path)
    json.dump(d, open(path, "w"), indent=2, sort_keys=True)
    open(path, "a").write("\n")


def export_local_lib(board, d):
    """corne_kicad_local.pretty: the two Ergogen-local footprints, flipped back to their front form."""
    lib = os.path.join(d, "corne_kicad_local.pretty")
    shutil.rmtree(lib, ignore_errors=True)
    os.makedirs(lib, exist_ok=True)
    io = pcbnew.PCB_IO_KICAD_SEXPR()
    done = set()
    for fp in board.GetFootprints():
        name = fp.GetFPID().GetLibItemName().wx_str()
        if name in ("D_SOD-123_Back", "MountingHole_2.2mm_M2") and name not in done:
            c = pcbnew.FOOTPRINT(fp)
            c.SetOrientationDegrees(0)
            if c.GetLayer() == B:
                c.Flip(c.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            c.SetPosition(pcbnew.VECTOR2I(0, 0))
            c.SetReference("D**" if name.startswith("D_") else "H**")
            for fn in ("LCSC",):
                if c.HasField(fn):
                    c.GetField(fn).SetText("")
            c.SetValue(name)
            io.FootprintSave(lib, c)
            done.add(name)


def write_lib_table(d):
    with open(os.path.join(d, "fp-lib-table"), "w") as fh:
        fh.write('(fp_lib_table\n  (version 7)\n'
                 '  (lib (name "corne_reversible")(type "KiCad")(uri "${KIPRJMOD}/../footprints/corne_reversible.pretty")'
                 '(options "")(descr "WP5 reversible footprints (source: pcb/footprints/tools/gen_footprints.py)"))\n'
                 '  (lib (name "corne_kicad_local")(type "KiCad")(uri "${KIPRJMOD}/corne_kicad_local.pretty")'
                 '(options "")(descr "SOD-123 diode on face A and M2 hole, from pcb/ergogen/footprints/local"))\n'
                 ')\n')


def route_all(board, limit=None):
    r = make_router(board)
    r.netname = {board.FindNet(n).GetNetCode(): n for n in board.GetNetsByName().keys()} if False else None
    names = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            names[p.GetNetCode()] = p.GetNetname()
    r.netname = names
    plan = ROUTE_PLAN[:limit]
    for name, kw in plan:
        log(f"route {name}")
        res = route_net(board, r, name, **kw)
        if res < 0:
            log(f"!! unrouted: {name}")


def is_disp(c):
    return any(it.kind.startswith("pad DISP1") for it in c)


def not_mcu(c):
    return any(it.kind.startswith("pad MCU1") for it in c)


# Left strip between the inner column and the controller hole column (absolute mm).
STRIP = box(103.9, -52.0, 107.3, -18.5)
# Area the controller-side nets (power, display) must not use: the left strip and the left hole column.
LEFT_OF_MCU = box(95.0, -60.0, 109.6, -13.5)
RIGHT_ONLY = [(LEFT_OF_MCU, None)]
ROW_COST = dict(layer_cost=(1.0, 1.8), via_cost=1.5)
COL_COST = dict(layer_cost=(1.8, 1.0), via_cost=1.5)
COL_STRIP = dict(layer_cost=(1.8, 1.0), via_cost=1.5, cost_maps=[(STRIP, 1, 4.0)])
ROW_STRIP = dict(layer_cost=(1.0, 1.8), via_cost=1.5, cost_maps=[(STRIP, 0, 4.0)])
SIDE = dict(via_cost=1.0, forbid=RIGHT_ONLY)
ROUTE_PLAN = [
    # power and controller-side nets, right of the controller only
    ("RAW", dict(w=W_PWR, **SIDE)),
    ("BAT_P", dict(w=W_PWR, **SIDE)),
    ("RST", dict(w=W_SIG, **SIDE)),
    ("VCC", dict(w=W_VCC, **SIDE)),
    ("GND", dict(w=W_GND, exclude=is_disp, **SIDE)),
    ("DISP_SCK", dict(w=W_SIG, **SIDE)),
    ("DISP_MOSI", dict(w=W_SIG, **SIDE)),
    ("DISP_CS", dict(w=W_SIG, **SIDE)),
    ("GND", dict(w=W_SIG, **SIDE)),
    # matrix, inside the key field first (controller stubs excluded)
] + [(n, dict(exclude=not_mcu, **ROW_COST)) for n in ("ROW0", "ROW1", "ROW2", "ROW3")] \
  + [(n, dict(exclude=not_mcu, **COL_COST)) for n in ("COL_D14", "COL_D15", "COL_D18", "COL_D19", "COL_D20", "COL_D21")] \
  + [(n, dict(**COL_STRIP)) for n in ("COL_D14", "COL_D15", "COL_D18", "COL_D19", "COL_D20", "COL_D21")] \
  + [(n, dict(**ROW_STRIP)) for n in ("ROW3", "ROW2", "ROW1", "ROW0")]


def finish(board):
    silkscreen(board)
    tb = board.GetTitleBlock()
    tb.SetTitle("corne-reversible")
    tb.SetRevision(REVISION)
    tb.SetDate(DATE)
    tb.SetCompany("andy778")
    tb.SetComment(0, "Reversible Corne half: LEFT = KiCad F up, RIGHT = KiCad B up. JLCPCB assembles B (face A).")
    remove_dangling(board)


BITE_R = 0.3  # break-line perforation radius drawn by Ergogen as Edge.Cuts circles


def bites_to_npth(path, libdir):
    """Replace the Ergogen break-line circles on Edge.Cuts by 0.6 mm NPTH pads (footprint BRK1), so they
    land in the NPTH drill file instead of the outline (WP8 S1). Runs on the saved file, after routing."""
    txt = open(path).read()
    pat = re.compile(r"\n\t\(gr_circle\s*\(center ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)"
                     r"(?:(?!\n\t\().)*?\(layer \"Edge\.Cuts\"\)(?:(?!\n\t\().)*?\n\t\)", re.S)
    centres = []

    def take(m):
        cx, cy, ex, ey = map(float, m.groups())
        if abs(math.hypot(ex - cx, ey - cy) - BITE_R) > 1e-3:
            return m.group(0)
        centres.append((cx, cy))
        return ""
    txt = pat.sub(take, txt)
    open(path, "w").write(txt)
    if not centres:
        return
    board = pcbnew.LoadBoard(path)
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("corne_kicad_local", "BreakLine_Perforation_NPTH"))
    fp.SetReference("BRK1")
    fp.Reference().SetVisible(False)
    fp.SetValue("BreakLine_Perforation_NPTH")
    fp.Value().SetVisible(False)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    x0, y0 = centres[0]
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
    board.Add(fp)
    for n, (cx, cy) in enumerate(sorted(centres, key=lambda c: c[1]), 1):
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        d = pcbnew.FromMM(2 * BITE_R)
        pad.SetSize(pcbnew.VECTOR2I(d, d))
        pad.SetDrillSize(pcbnew.VECTOR2I(d, d))
        pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
        pad.SetNumber("")
        fp.Add(pad)
        pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    pcbnew.SaveBoard(path, board)
    c = pcbnew.FOOTPRINT(fp)
    c.SetPosition(pcbnew.VECTOR2I(0, 0))
    c.SetReference("BRK**")
    pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(os.path.join(libdir, "corne_kicad_local.pretty"), c)
    log(f"break line: {len(centres)} Edge.Cuts circles replaced by NPTH pads")


DOOMED = set()


def drop_items_from_file(path, uuids):
    """Delete top-level (segment ...)/(via ...) blocks by uuid from a saved .kicad_pcb.
    (BOARD.Remove() corrupts SWIG type data in this pcbnew build, so it is done on the file.)"""
    if not uuids:
        return
    txt = open(path).read()
    out, i, n, dropped = [], 0, len(txt), 0
    while i < n:
        j = txt.find("\n\t(", i)
        if j < 0:
            out.append(txt[i:])
            break
        out.append(txt[i:j + 1])
        # find matching paren of the block starting at j+2
        k, depth, q = j + 2, 0, False
        while k < n:
            ch = txt[k]
            if ch == '"' and txt[k - 1] != "\\":
                q = not q
            elif not q:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
            k += 1
        block = txt[j + 1:k + 1]
        head = block.lstrip()[:8]
        if (head.startswith("(segment") or head.startswith("(via")) and any(u in block for u in uuids):
            dropped += 1
        else:
            out.append(block)
        i = k + 1
    open(path, "w").write("".join(out))
    log(f"dropped {dropped} dangling tracks/vias from {os.path.basename(path)}")
    assert dropped == len(uuids), (dropped, len(uuids))


def trim_track(d, k, cu):
    """Shorten a needed track whose far end overhangs a T-junction back to the last copper it touches."""
    L = d["geoms"][0][0]
    a, b = d["ends"]
    net = d["net"]

    def touches(pnt):
        return any(o != k and LL == L and n == net and g.distance(pnt) < d["hw"] - 0.01 for LL, g, n, o in cu)
    if touches(a) and not touches(b):
        keep, free = a, b
    elif touches(b) and not touches(a):
        keep, free = b, a
    else:
        return
    line = LineString([keep, free])
    best = 0.0
    for LL, g, n, o in cu:
        if o == k or LL != L or n != net:
            continue
        inter = d["geoms"][0][1].intersection(g)
        if inter.is_empty or inter.area < 1e-4:
            continue
        for q in getattr(inter, "geoms", [inter]):
            if q.geom_type != "Polygon":
                continue
            # deepest point of the overlap along the track, kept fully inside the overlap
            c = q.representative_point()
            ext = max(line.project(Point(xy)) for xy in q.exterior.coords)
            best = max(best, min(ext, line.project(c) + 0.5 * (ext - line.project(c))))
    if best <= 0.05 or best >= line.length - 1e-3:
        return
    np_ = line.interpolate(best)
    t = d["obj"]
    if free is b:
        t.SetEnd(pt(np_.x, np_.y))
        d["ends"] = (a, np_)
    else:
        t.SetStart(pt(np_.x, np_.y))
        d["ends"] = (np_, b)
    d["geoms"] = [(L, LineString(list(d["ends"])).buffer(d["hw"], 8))]
    d["trimmed"] = True
    log(f"  trimmed a dangling end by {line.length - best:.2f} mm")


def remove_dangling(board):
    """Drop track stubs and vias left over by the router (dead ends that connect nothing)."""
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            for L, lay in LAYER.items():
                if p.IsOnLayer(lay) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    pads.append((L, poly_from_rings(pad_polys(p, lay)), p.GetNetCode(),
                                 f"pad:{fp.GetReference()}:{p.GetNumber()}:{p.m_Uuid.AsString()}"))
    alive = {}
    for t in tracks(board):
        k = t.m_Uuid.AsString()
        net = t.GetNetCode()
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            p = Point(mm(c.x), mm(c.y))
            r = mm(t.GetWidth(F)) / 2
            g = p.buffer(r, 16)
            alive[k] = dict(obj=t, geoms=[(0, g), (1, g)], via=(p, r), net=net)
        else:
            a, b = t.GetStart(), t.GetEnd()
            pa, pb = (mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))
            g = LineString([pa, pb]).buffer(mm(t.GetWidth()) / 2, 8)
            alive[k] = dict(obj=t, geoms=[(0 if t.GetLayer() == F else 1, g)], ends=(Point(pa), Point(pb)), net=net,
                            hw=mm(t.GetWidth()) / 2)
    removed = 0
    while True:
        cu = list(pads)
        for k, d in alive.items():
            cu += [(L, g, d["net"], k) for L, g in d["geoms"]]
        changed = False
        for k in list(alive.keys()):
            d = alive[k]
            net = d["net"]
            if "via" in d:
                c, r = d["via"]
                layers = {L for L, g, n, o in cu if o != k and n == net and g.distance(c) < r - 0.01}
                dangling = len(layers) < 2
            else:
                L = d["geoms"][0][0]
                dangling = any(not any(o != k and LL == L and n == net and g.distance(pnt) < d["hw"] - 0.01
                                       for LL, g, n, o in cu) for pnt in d["ends"])
            if not dangling:
                continue
            # only drop it if it does not join anything: everything it touches must stay connected without it
            mine = dict(d["geoms"])
            touch = sorted({o for L, g, n, o in cu if o != k and n == net and L in mine and g.intersects(mine[L])})
            if len(touch) > 1:
                same = [(L, g, o) for L, g, n, o in cu if n == net and o != k]
                parent = {o: o for _, _, o in same}

                def find(x):
                    while parent[x] != x:
                        parent[x] = parent[parent[x]]
                        x = parent[x]
                    return x
                for i1 in range(len(same)):
                    for i2 in range(i1 + 1, len(same)):
                        L1, g1, o1 = same[i1]
                        L2, g2, o2 = same[i2]
                        if o1 != o2 and L1 == L2 and g1.intersects(g2):
                            parent[find(o1)] = find(o2)
                if len({find(o) for o in touch}) > 1:
                    if "ends" in d and not d.get("trimmed"):
                        trim_track(d, k, cu)
                    continue
            del alive[k]
            DOOMED.add(k)
            removed += 1
            changed = True
            break
        if not changed:
            break
    log(f"dangling tracks/vias to drop: {removed}")


def board_text(board, text, layer, x, y, size=1.0, thick=0.15, angle=0.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(pt(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(int(size * 1e6), int(size * 1e6)))
    t.SetTextThickness(int(thick * 1e6))
    t.SetTextAngleDegrees(angle)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def silkscreen(board):
    """Move the controller jumper instructions clear of the nice!view pin labels; add version text."""
    mcu = [fp for fp in board.GetFootprints() if fp.GetReference() == "MCU1"][0]
    gi = mcu.GraphicalItems()
    ys = {"BRIDGE 24 PIN": -1.6, "JUMPERS ON THIS FACE ONLY": -0.3, "USB / CONTROLLER FACE UP": 1.0}
    for i in range(len(gi)):
        t = gi[i].Cast()
        if t.GetClass() == "PCB_TEXT":
            for key, y in ys.items():
                if key in t.GetText():
                    t.SetPosition(pt(117.0, y))
    for lay in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        board_text(board, f"corne-reversible {REVISION} {DATE}", lay, 117.0, 2.4, size=0.9)
    # half labels on the key field edge: which half this face is the TOP of
    board_text(board, "LEFT HALF: THIS FACE UP", pcbnew.F_SilkS, 117.0, 3.7, size=0.9)
    board_text(board, "RIGHT HALF: THIS FACE UP", pcbnew.B_SilkS, 117.0, 3.7, size=0.9)


if __name__ == "__main__":
    main()
