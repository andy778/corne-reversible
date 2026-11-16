#!/usr/bin/python3
"""JLCPCB fabrication outputs for the routed board.

    /usr/bin/python3 pcb/kicad/tools/make_fab.py

Writes to pcb/fab/:
  gerbers/                         Gerber (Protel extensions) + Excellon drill (PTH and NPTH separate)
  corne_reversible_gerbers.zip     the folder above, zipped flat (what JLCPCB's upload expects)
  corne_reversible_bom_jlcpcb.csv  Comment, Designator, Footprint, LCSC Part #
  corne_reversible_cpl_jlcpcb.csv  Designator, Mid X, Mid Y, Layer, Rotation
  preview/                         renders and SVG plots of both faces

BOM/CPL contain only footprints that carry an LCSC field and are not excluded from BOM and
position files: the 21 SOD-123 diodes and the TS-1187A reset button, all on KiCad B.Cu (face A).

Rotation (see pcb/fab/README.md) is computed from the copper, not from the KiCad orientation:
for each part a reference vector is measured on the board as seen from the top (y up):
  diode: centre -> cathode pad (pad 1); library angle phi = 180 (EasyEDA C81598: cathode pad 1 at -x)
  TS-1187A: pad-1 pair centre -> pad-2 pair centre; phi = -90 (EasyEDA C318884: pins 1,2 at the
  top row, 3,4 at the bottom row, leads along x)
and JLCPCB bottom rotation R = (180 - theta - phi) mod 360: seen from the bottom the board direction
theta becomes 180 - theta, and the library part (reference at phi) is turned by R counter-clockwise in
that view. For a footprint whose front version matches the EasyEDA one this equals the kicad-jlcpcb-tools
/ Fabrication Toolkit / KiBot rule R = 180 - orientation. (WP7 used 360 - theta - phi, which put every
diode in backwards; found in the WP8 review, B1.) Confirm in JLCPCB's bottom-side placement preview.
"""
import csv
import glob
import math
import os
import shutil
import subprocess
import sys
import zipfile

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kutil import mm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BOARD = os.path.join(ROOT, "pcb", "kicad", "corne_reversible.kicad_pcb")
FAB = os.path.join(ROOT, "pcb", "fab")
NAME = "corne_reversible"
ROT_OFFSET = {"C81598": 0.0, "C318884": 0.0}
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args):
    print("+", " ".join(args))
    subprocess.run(args, check=True)


def gerbers():
    out = os.path.join(FAB, "gerbers")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    run("kicad-cli", "pcb", "export", "gerbers", "-o", out + "/", "-l", LAYERS, "--subtract-soldermask", BOARD)
    run("kicad-cli", "pcb", "export", "drill", "-o", out + "/", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-separate-th", "--excellon-oval-format", "alternate", "--drill-origin", "absolute", BOARD)
    for f in glob.glob(os.path.join(out, "*.gbrjob")):
        os.remove(f)
    z = os.path.join(FAB, f"{NAME}_gerbers.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(out)):
            zi = zipfile.ZipInfo(f, date_time=(2026, 11, 15, 0, 0, 0))  # reproducible zip
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, open(os.path.join(out, f), "rb").read())
    print("wrote", z, sorted(os.listdir(out)))


def field(fp, name):
    return fp.GetField(name).GetText() if fp.HasField(name) else ""


def ref_angle(fp):
    """(theta, phi): measured reference direction seen from the top (deg, y up) and library angle."""
    c = fp.GetPosition()
    pads = {}
    for p in fp.Pads():
        pads.setdefault(p.GetNumber(), []).append(p.GetPosition())
    if fp.GetReference().startswith("D"):
        q = pads["1"][0]
        vx, vy = mm(q.x - c.x), -mm(q.y - c.y)
        phi = 180.0
    else:
        a = [sum(mm(q.x) for q in pads["1"]) / len(pads["1"]), sum(mm(q.y) for q in pads["1"]) / len(pads["1"])]
        b = [sum(mm(q.x) for q in pads["2"]) / len(pads["2"]), sum(mm(q.y) for q in pads["2"]) / len(pads["2"])]
        vx, vy = b[0] - a[0], -(b[1] - a[1])
        phi = -90.0
    return math.degrees(math.atan2(vy, vx)), phi


def bom_cpl():
    b = pcbnew.LoadBoard(BOARD)
    parts = []
    for fp in b.GetFootprints():
        lcsc = field(fp, "LCSC")
        excluded = fp.IsExcludedFromBOM() or fp.IsExcludedFromPosFiles()
        if not lcsc or excluded:
            continue
        parts.append(fp)
    parts.sort(key=lambda f: (f.GetValue(), int("".join(c for c in f.GetReference() if c.isdigit()))))
    # BOM
    groups = {}
    for fp in parts:
        key = (fp.GetValue(), fp.GetFPID().GetLibItemName().wx_str(), field(fp, "LCSC"))
        groups.setdefault(key, []).append(fp.GetReference())
    bom = os.path.join(FAB, f"{NAME}_bom_jlcpcb.csv")
    with open(bom, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, foot, lcsc), refs in groups.items():
            w.writerow([val, ",".join(refs), foot, lcsc])
    # CPL
    cpl = os.path.join(FAB, f"{NAME}_cpl_jlcpcb.csv")
    rows = []
    for fp in parts:
        p = fp.GetPosition()
        side = "Bottom" if fp.GetLayer() == pcbnew.B_Cu else "Top"
        if side != "Bottom":
            raise SystemExit(f"{fp.GetReference()} is not on the bottom (face A)")
        theta, phi = ref_angle(fp)
        rot = (180.0 - theta - phi) % 360.0
        rot = round(rot, 1) % 360.0
        rows.append([fp.GetReference(), f"{mm(p.x):.4f}mm", f"{-mm(p.y):.4f}mm", side, f"{rot:.1f}"])
    with open(cpl, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(rows)
    print("wrote", bom, cpl)
    return b, parts, rows


def polarity(b, parts, rows):
    """Cathode pad on a ROW net, anode on the switch net, and the CPL rotation puts the library
    cathode (EasyEDA pad 1) onto that pad: re-derive the board direction from R and compare."""
    ok = True
    rot = {r[0]: float(r[4]) for r in rows}
    for fp in parts:
        theta, phi = ref_angle(fp)
        back = (180.0 - rot[fp.GetReference()] - phi) % 360.0
        d = abs((back - theta + 180) % 360 - 180)
        if fp.GetReference().startswith("D"):
            cath = [p for p in fp.Pads() if p.GetNumber() == "1"][0]
            an = [p for p in fp.Pads() if p.GetNumber() == "2"][0]
            nets_ok = cath.GetNetname().startswith("ROW") and an.GetNetname().startswith("SW_")
            good = nets_ok and d < 0.1
            print(("PASS " if good else "FAIL ") + f"{fp.GetReference()}: cathode (pad 1) on {cath.GetNetname()}, "
                  f"anode on {an.GetNetname()}, cathode points {theta:+.1f} deg seen from top, CPL rotation "
                  f"{rot[fp.GetReference()]:.1f} (KiCad orientation {fp.GetOrientationDegrees():.1f})")
        else:
            good = d < 0.1 or abs(d - 180) < 0.1
            print(("PASS " if good else "FAIL ") + f"{fp.GetReference()}: TS-1187A leads axis {theta:+.1f} deg, "
                  f"CPL rotation {rot[fp.GetReference()]:.1f} (pin pairs symmetric under 180)")
        ok &= good
    return ok


def previews():
    out = os.path.join(FAB, "preview")
    os.makedirs(out, exist_ok=True)
    for side in ("top", "bottom"):
        run("kicad-cli", "pcb", "render", "-o", os.path.join(out, f"{NAME}_render_{side}.png"), "--side", side,
            "-w", "2400", "-h", "1500", "--quality", "high", "--background", "opaque", BOARD)
    # 2D plots: copper + silk + mask per face (B face plotted mirrored, as seen from below)
    run("kicad-cli", "pcb", "export", "svg", "-o", os.path.join(out, f"{NAME}_F_face.svg"), "-l",
        "F.Cu,F.SilkS,F.Mask,Edge.Cuts", "--mode-single", "--fit-page-to-board", "--exclude-drawing-sheet", BOARD)
    run("kicad-cli", "pcb", "export", "svg", "-o", os.path.join(out, f"{NAME}_B_face_mirrored.svg"), "-l",
        "B.Cu,B.SilkS,B.Mask,Edge.Cuts", "--mode-single", "--fit-page-to-board", "--exclude-drawing-sheet",
        "--mirror", BOARD)
    run("kicad-cli", "pcb", "export", "svg", "-o", os.path.join(out, f"{NAME}_B_assembly_mirrored.svg"), "-l",
        "B.Fab,B.SilkS,B.Paste,Edge.Cuts", "--mode-single", "--fit-page-to-board", "--exclude-drawing-sheet",
        "--mirror", BOARD)


def main():
    os.makedirs(FAB, exist_ok=True)
    gerbers()
    b, parts, rows = bom_cpl()
    n_d = sum(1 for r in rows if r[0].startswith("D"))
    n_sw = sum(1 for r in rows if r[0].startswith("SW"))
    print(f"CPL: {n_d} diodes, {n_sw} reset button(s), {len(rows)} rows, layers {sorted({r[3] for r in rows})}")
    ok = n_d == 21 and n_sw == 1 and len(rows) == 22 and {r[3] for r in rows} == {"Bottom"}
    ok &= polarity(b, parts, rows)
    if "--no-preview" not in sys.argv:
        previews()
    print("RESULT:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
