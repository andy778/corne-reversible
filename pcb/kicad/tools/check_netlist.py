#!/usr/bin/python3
"""Electrical check of the routed board, from copper geometry (not from net labels).

    /usr/bin/python3 pcb/kicad/tools/check_netlist.py [board.kicad_pcb]

1. Builds connectivity islands from the actual copper: pads, tracks and vias that touch on a
   layer are joined; plated holes and vias join F.Cu and B.Cu.
2. Simulates each half by bridging the solder jumpers of one face only
   (LEFT half: KiCad F jumpers, RIGHT half: KiCad B jumpers) and maps every controller hole to
   the Pro Micro pin that lands in it on that half (the right half sees the footprint mirrored).
3. Asserts, per key, column pin -> switch pad 1 (all four socket pads), switch pad 2 -> diode
   anode, diode cathode -> row pin, and the Corne pin map for both halves; power, reset and
   nice!view wiring; that no two controller pins share an island; that the 36-key break leaves
   the main board intact; and that bridging both faces would short (documents the hazard).
4. Cross-checks that every island carries exactly one KiCad net name.
Exit status 1 on any failure.
"""
import math
import os
import sys

import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kutil import fp_transform, mm, pad_polys, tracks  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "pcb", "kicad", "corne_reversible.kicad_pcb")
F, B = pcbnew.F_Cu, pcbnew.B_Cu

# Pro Micro pins by hole position, seen from the component side, USB up (SparkFun Pro Micro / nice!nano).
LEFT_COL = ["D1", "D0", "GND", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
RIGHT_COL = ["RAW", "GND", "RST", "VCC", "D21", "D20", "D19", "D18", "D15", "D14", "D16", "D10"]
# ZMK corne: rows D4..D7 (top, home, bottom, thumb); columns outer->inner D21 D20 D19 D18 D15 D14, both halves
ROW_PIN = {"top": "D4", "home": "D5", "bottom": "D6", "thumb": "D7"}
COL_PIN = ["D21", "D20", "D19", "D18", "D15", "D14"]
THUMB_PIN = ["D18", "D15", "D14"]  # near, mid, far
NV_ORDER = ["MOSI", "SCK", "VCC", "GND", "CS"]  # nice!view header, left to right seen from the top
NV_PIN = {"MOSI": "D2", "SCK": "D3", "CS": "D1", "VCC": "VCC", "GND": "GND"}
BREAK_X = 9.525

fails = []


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def poly(rings):
    return unary_union([Polygon(r).buffer(0) for r in rings if len(r) >= 3])


class Copper:
    def __init__(self, board):
        self.items = []  # (layerset, geom per layer dict, netname, tag)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                g = {}
                for L in (F, B):
                    if p.IsOnLayer(L):
                        pg = poly(pad_polys(p, L))
                        if not pg.is_empty:
                            g[L] = pg
                if g:
                    self.items.append((g, p.GetNetname(), ("pad", fp.GetReference(), p.GetNumber(), p, p.m_Uuid.AsString())))
        for t in tracks(board):
            if t.GetClass() == "PCB_VIA":
                c = t.GetPosition()
                pg = Point(mm(c.x), mm(c.y)).buffer(mm(t.GetWidth(F)) / 2, 16)
                self.items.append(({F: pg, B: pg}, t.GetNetname(), ("via",)))
            else:
                a, b = t.GetStart(), t.GetEnd()
                pg = LineString([(mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))]).buffer(mm(t.GetWidth()) / 2, 8)
                self.items.append(({t.GetLayer(): pg}, t.GetNetname(), ("track",)))
        self.edges = []
        for L in (F, B):
            idx = [k for k, it in enumerate(self.items) if L in it[0]]
            geoms = [self.items[k][0][L] for k in idx]
            tree = STRtree(geoms)
            for a, gg in enumerate(geoms):
                for b in tree.query(gg, predicate="intersects"):
                    if b > a:
                        self.edges.append((idx[a], idx[b]))

    def islands(self, extra_edges=(), drop=None):
        n = len(self.items)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for a, b in list(self.edges) + list(extra_edges):
            if drop and (a in drop or b in drop):
                continue
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        return [find(k) for k in range(n)]


def main():
    board = pcbnew.LoadBoard(BOARD)
    cu = Copper(board)
    items = cu.items
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    mcu, disp = fps["MCU1"], fps["DISP1"]

    def pad_items(ref, num=None, layer=None):
        out = []
        for k, (g, net, tag) in enumerate(items):
            if tag[0] == "pad" and tag[1] == ref and (num is None or tag[2] == num):
                if layer is None or layer in g:
                    out.append(k)
        return out

    # ---- jumpers: pairs of copper pads inside one mask aperture of the same face
    jumpers = {F: [], B: []}
    for fp in (mcu, disp):
        for p in fp.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or p.IsOnLayer(F) or p.IsOnLayer(B):
                continue
            for cuL, mk in ((F, pcbnew.F_Mask), (B, pcbnew.B_Mask)):
                if not p.IsOnLayer(mk):
                    continue
                ap = poly(pad_polys(p, mk))
                inside = [k for k in pad_items(fp.GetReference(), layer=cuL)
                          if Point(mm(items[k][2][3].GetPosition().x), mm(items[k][2][3].GetPosition().y)).within(ap)]
                check(len(inside) == 2, f"{fp.GetReference()} aperture at {p.GetFPRelativePosition().x/1e6:.2f},"
                                        f"{p.GetFPRelativePosition().y/1e6:.2f} on {'F' if cuL == F else 'B'} holds 2 pads")
                if len(inside) == 2:
                    jumpers[cuL].append(tuple(inside))
    print(f"INFO  jumpers: {len(jumpers[F])} on KiCad F, {len(jumpers[B])} on KiCad B")
    check(len(jumpers[F]) == 26 + 4 and len(jumpers[B]) == 26 + 4,
          "26 controller (24 pins + 2 placeholder battery) and 4 nice!view jumpers per face")

    # ---- controller holes by local position
    tf_m = fp_transform(mcu)
    holes = {}
    for p in mcu.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSizeX() > 0:
            lp = p.GetFPRelativePosition()
            holes[(round(mm(lp.x), 2), round(mm(lp.y), 2))] = p
    ys = sorted({y for (x, y) in holes if abs(abs(x) - 7.62) < 0.01})

    def pin_holes(half):
        """{pin: [item index of hole]} for a half."""
        out = {}
        for (x, y), p in holes.items():
            if abs(abs(x) - 7.62) > 0.01:
                continue
            seen_x = x if half == "LEFT" else -x  # right half is seen from KiCad B: mirrored
            r = ys.index(y)
            pin = (LEFT_COL if seen_x < 0 else RIGHT_COL)[r]
            k = [k for k in pad_items("MCU1") if items[k][2][4] == p.m_Uuid.AsString()][0]
            out.setdefault(pin, []).append(k)
        return out

    # ---- keys by geometry
    sws = [fp for fp in board.GetFootprints() if fp.GetFPID().GetLibItemName().wx_str() == "SW_MX_Choc_Hotswap_Reversible"]
    dds = [fp for fp in board.GetFootprints() if fp.GetFPID().GetLibItemName().wx_str() == "D_SOD-123_Back"]
    colx = [0.0, 19.05, 38.1, 57.15, 76.2, 95.25]
    keys = []
    thumbs = sorted([s for s in sws if mm(s.GetPosition().y) > 10], key=lambda s: mm(s.GetPosition().x))
    for s in sws:
        x, y = mm(s.GetPosition().x), mm(s.GetPosition().y)
        if s in thumbs:
            keys.append((s, "thumb", THUMB_PIN[thumbs.index(s)], f"thumb{thumbs.index(s)}"))
            continue
        ci = min(range(6), key=lambda i: abs(colx[i] - x))
        same = sorted([t for t in sws if t not in thumbs and abs(mm(t.GetPosition().x) - colx[ci]) < 0.1],
                      key=lambda t: mm(t.GetPosition().y))
        row = ["top", "home", "bottom"][same.index(s)]
        keys.append((s, row, COL_PIN[ci], f"c{ci}{row}"))
    check(len(keys) == 21 and len(dds) == 21, "21 keys and 21 diodes found")

    def diode_for(s):
        f = fp_transform(s)
        ex = f(0, 9.525)
        return min(dds, key=lambda d: math.hypot(mm(d.GetPosition().x) - ex[0], mm(d.GetPosition().y) - ex[1]))

    def evaluate(half, bridged_faces, drop=None, key_filter=None, quiet=False):
        extra = [e for L in bridged_faces for e in jumpers[L]]
        isl = cu.islands(extra, drop)
        ph = pin_holes(half)
        pin_isl = {}
        for pin, ks in ph.items():
            pin_isl.setdefault(pin, set()).update(isl[k] for k in ks)
        results = []

        def ok(cond, msg):
            results.append((cond, f"[{half}] {msg}"))

        # pins: each pin name maps to one island (GND: three holes, one island)
        for pin, s in pin_isl.items():
            ok(len(s) == 1, f"pin {pin} holes form one island ({len(s)})")
        P = {pin: next(iter(s)) for pin, s in pin_isl.items()}
        distinct = {}
        for pin, i in P.items():
            distinct.setdefault(i, []).append(pin)
        shared = [v for v in distinct.values() if len(v) > 1]
        ok(not shared, f"no two controller pins on one island {shared if shared else ''}")
        # matrix
        for s, row, cpin, label in keys:
            if key_filter and not key_filter(s):
                continue
            d = diode_for(s)
            p1 = {isl[k] for k in pad_items(s.GetReference(), "1")}
            p2 = {isl[k] for k in pad_items(s.GetReference(), "2")}
            an = {isl[k] for k in pad_items(d.GetReference(), "2")}
            ca = {isl[k] for k in pad_items(d.GetReference(), "1")}
            n1 = len(pad_items(s.GetReference(), "1"))
            ok(n1 == 4 and len(p1) == 1 and p1 == {P[cpin]},
               f"{label} {s.GetReference()}: column pin {cpin} -> all 4 pad-1 socket pads")
            ok(len(p2) == 1 and p2 == an and p2 != p1, f"{label} {s.GetReference()}: pad 2 (4 pads) -> {d.GetReference()} anode")
            ok(len(ca) == 1 and ca == {P[ROW_PIN[row]]} and ca != an,
               f"{label} {d.GetReference()}: cathode -> row pin {ROW_PIN[row]}")
        if key_filter:
            return results, P, isl
        # power / reset
        sw_pwr = fps["PWR1"]
        ok({isl[k] for k in pad_items("PWR1", "2")} == {P["RAW"]}, "power switch common (pin 2, both faces) -> RAW")
        batp = {isl[k] for k in pad_items("PWR1", "1")} | {isl[k] for k in pad_items("BT1", "2")}
        ok(len(batp) == 1 and batp.isdisjoint(set(P.values())),
           "JST + (both hole pairs) -> power switch pin 1 (both faces), not directly on any controller pin")
        ok({isl[k] for k in pad_items("BT1", "1")} == {P["GND"]}, "JST - (both hole pairs) -> GND")
        ok({isl[k] for k in pad_items("SW22", "1")} == {P["RST"]}, "reset button pin 1 (both pads) -> RST")
        ok({isl[k] for k in pad_items("SW22", "2")} == {P["GND"]}, "reset button pin 2 (both pads) -> GND")
        # nice!view: header holes seen left to right from the top of this half
        tf_d = fp_transform(disp)
        dh = []
        for p in disp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSizeX() > 0:
                lx = mm(p.GetFPRelativePosition().x)
                seen = lx if half == "LEFT" else -lx
                k = [k for k in pad_items("DISP1") if items[k][2][4] == p.m_Uuid.AsString()][0]
                dh.append((seen, k))
        dh.sort()
        for (seen, k), sig in zip(dh, NV_ORDER):
            ok(isl[k] == P[NV_PIN[sig]], f"nice!view {sig} (hole {dh.index((seen, k)) + 1} from left) -> {NV_PIN[sig]}")
        # unused pins isolated: island holds nothing but the controller footprint copper
        for pin in ("D0", "D8", "D9", "D10", "D16"):
            others = {items[k][2][1] for k in range(len(items)) if isl[k] == P[pin] and items[k][2][0] == "pad"}
            ok(others == {"MCU1"}, f"unused pin {pin} not connected to anything else")
        return results, P, isl

    for half, faces in (("LEFT", [F]), ("RIGHT", [B])):
        print(f"\n== {half} half: jumpers bridged on KiCad {'F' if faces == [F] else 'B'} only")
        res, P, isl = evaluate(half, faces)
        for c, m in res:
            check(c, m)

    # ---- 36-key break: drop all copper whose geometry lies left of the break line, re-check main keys
    print("\n== 36-key variant: tab copper removed (x < 9.525)")
    drop = set()
    for k, (g, net, tag) in enumerate(items):
        if all(gg.bounds[2] < BREAK_X + 0.6 for gg in g.values()) or all(gg.centroid.x < BREAK_X for gg in g.values()):
            drop.add(k)
    for half, faces in (("LEFT", [F]), ("RIGHT", [B])):
        res, P, isl = evaluate(half, faces, drop=drop, key_filter=lambda s: mm(s.GetPosition().x) > BREAK_X)
        bad = [m for c, m in res if not c]
        check(not bad, f"[{half}] 36-key: all 18 main-board keys still wired ({len(res)} checks) {bad[:3]}")
    crossing = set()
    for k, (g, net, tag) in enumerate(items):
        if tag[0] in ("track",) and any(gg.bounds[0] < BREAK_X < gg.bounds[2] for gg in g.values()):
            crossing.add(net)
    check(crossing == {"COL_D21", "ROW0", "ROW1", "ROW2"}, f"only COL_D21, ROW0-2 cross the break line: {sorted(crossing)}")

    # ---- fault simulation: both faces bridged must short (documents the hazard; expected FAIL inside)
    print("\n== fault simulation: jumpers bridged on BOTH faces")
    res, P, isl = evaluate("LEFT", [F, B])
    shorted = [m for c, m in res if not c and "no two controller pins" in m]
    check(bool(shorted), "bridging both faces shorts controller pins (expected hazard): " + (shorted[0][-120:] if shorted else ""))

    # ---- labels vs geometry
    print("\n== net labels vs copper islands")
    isl = cu.islands()
    names = {}
    for k, (g, net, tag) in enumerate(items):
        names.setdefault(isl[k], set()).add(net)
    multi = [sorted(v) for v in names.values() if len(v) > 1]
    check(not multi, f"every copper island carries exactly one net name {multi[:3]}")
    per_net = {}
    for i, v in names.items():
        for n in v:
            per_net.setdefault(n, set()).add(i)
    split = sorted(n for n, s in per_net.items() if len(s) > 1 and n)
    check(not split, f"every named net is one copper island (fully routed) {split}")

    print(f"\nRESULT: {'ALL PASS' if not fails else f'{len(fails)} FAIL'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
