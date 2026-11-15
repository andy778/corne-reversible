#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the 1:1 paper test sheet and a DRC test board from corne_reversible.pretty.

    python3 pcb/footprints/tools/make_test_sheet.py            # board + project only
    python3 pcb/footprints/tools/make_test_sheet.py --pdf      # also plot PDFs (needs kicad-cli, pdfunite)
    python3 pcb/footprints/tools/make_test_sheet.py --drc      # also run kicad-cli DRC

Writes into ../test-print/:
  test-sheet.kicad_pcb / .kicad_pro   A4 board: 2x2 keys (with SOD-123 diodes on KiCad B
                                      between the rows), controller, nice!view header,
                                      power switch, reset, JST, 50 mm scale bars.
  test-sheet.pdf                      page 1: KiCad F side as seen from F
                                      page 2: KiCad B side as seen from B (plotted mirrored)
  drc-report.txt                      KiCad DRC against the JLCPCB rule set in the .kicad_pro

Pad nets on the test board: every footprint pad number becomes its own net
("<REF>-<pad>"), switch pads use per-key nets, so DRC sees the same "same number =
same net" logic KiCad uses in a real design.
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRETTY = os.path.join(ROOT, "corne_reversible.pretty")
OUT = os.path.join(ROOT, "test-print")
KICAD_STOCK_SOD123 = "/usr/share/kicad/footprints/Diode_SMD.pretty/D_SOD-123.kicad_mod"

PITCH = 19.05
nets = {"": 0}


def net(name):
    if name not in nets:
        nets[name] = len(nets)
    return nets[name]


def place(fp_file, ref, x, y, netfn, lib="corne_reversible"):
    txt = open(fp_file).read()
    name = re.search(r'\(footprint "([^"]+)"', txt).group(1)
    txt = re.sub(r'\(footprint "[^"]+"', f'(footprint "{lib}:{name}"', txt, count=1)
    txt = re.sub(r'\n\s*\((?:version|generator|generator_version) [^\n]*\)', "", txt)
    txt = txt.replace('(layer "F.Cu")', f'(layer "F.Cu")\n\t(at {x} {y})', 1)
    txt = re.sub(r'\(property "Reference" "[^"]*"', f'(property "Reference" "{ref}"', txt, count=1)
    # drop uuids so repeated placements do not clash (KiCad regenerates them)
    txt = re.sub(r'\s*\(uuid "?[0-9a-fA-F-]+"?\)', "", txt)
    txt = re.sub(r'\s*\(tstamp [0-9a-fA-F-]+\)', "", txt)

    def addnet(m):
        num = m.group(1)
        n = netfn(num)
        return m.group(0) + (f' (net {net(n)} "{n}")' if n else "")
    txt = re.sub(r'\(pad "([^"]*)" \w+ \w+', addnet, txt)
    return txt


def gr_line(layer, a, b, w=0.2):
    return f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}"))'


def gr_text(layer, s, at, size=1.5, th=0.25, justify="left"):
    mirror = " mirror" if layer.startswith("B.") else ""
    justify = "" if justify == "center" else justify
    just = f" (justify {justify}{mirror})" if (justify or mirror) else ""
    return (f'(gr_text "{s}" (at {at[0]} {at[1]} 0) (layer "{layer}") '
            f'(effects (font (size {size} {size}) (thickness {th})){just}))')


def scale_bars(x0, y0):
    out = []
    for layer in ("F.SilkS", "B.SilkS"):
        # horizontal 50 mm
        out.append(gr_line(layer, (x0, y0), (x0 + 50, y0), 0.3))
        for k in range(0, 51, 10):
            out.append(gr_line(layer, (x0 + k, y0 - (2.5 if k % 50 == 0 else 1.5)), (x0 + k, y0), 0.2))
        out.append(gr_text(layer, "50 mm (check with a ruler: 50.0 mm)", (x0 + 25, y0 + 2.5), 1.3, 0.2, "center"))
        # vertical 50 mm
        vx = x0 + 150
        out.append(gr_line(layer, (vx, y0 - 50), (vx, y0), 0.3))
        for k in range(0, 51, 10):
            out.append(gr_line(layer, (vx, y0 - k), (vx + (2.5 if k % 50 == 0 else 1.5), y0 - k), 0.2))
        out.append(gr_text(layer, "50 mm", (vx + 3, y0 - 25), 1.3, 0.2))
    return out


def build():
    os.makedirs(OUT, exist_ok=True)
    fps = []
    pre = lambda n: os.path.join(PRETTY, n + ".kicad_mod")

    # 2x2 keys, column pitch 19.05, rows 19.05, diode between the rows on KiCad B (= face A)
    kx, ky = 35.0, 60.0
    k = 0
    for c in range(2):
        for r in range(2):
            k += 1
            x, y = kx + c * PITCH, ky + r * PITCH
            fps.append(place(pre("SW_MX_Choc_Hotswap_Reversible"), f"SW{k}", x, y,
                             lambda num, k=k, c=c: {"1": f"COL{c}", "2": f"SW{k}-D"}.get(num)))
        dx, dy = kx + c * PITCH, ky + PITCH / 2
        d = place(KICAD_STOCK_SOD123, f"D{c + 1}", dx, dy,
                  lambda num, c=c: {"1": "ROW1", "2": f"SW{c * 2 + 2}-D"}.get(num), lib="Diode_SMD")
        fps.append(flip_to_back(d))

    fps.append(place(pre("MCU_ProMicro_nRF52840_Reversible_Jumpers"), "MCU1", 105.0, 75.0,
                     lambda num: (f"MCU1-{num}" if num.startswith("H") else (num if num else None))))
    fps.append(place(pre("Display_niceview_Header_Reversible_Jumpers"), "DISP1", 150.0, 50.0,
                     lambda num: (f"DISP1-{num}" if num.startswith("H") else (num if num else None))))
    fps.append(place(pre("SW_SPDT_MSK12C02_Reversible"), "PWR1", 150.0, 70.0,
                     lambda num: {"1": "BAT_P", "2": "RAW", "3": "PWR1-NC"}.get(num)))
    fps.append(place(pre("SW_Reset_TS-1186F_Side_Reversible"), "RST1", 150.0, 85.0,
                     lambda num: {"1": "RST", "2": "GND"}.get(num)))
    fps.append(place(pre("JST_PH_S2B-PH-K_Reversible"), "BT1", 175.0, 70.0,
                     lambda num: {"1": "GND", "2": "BAT_P"}.get(num)))

    graphics = scale_bars(25, 150)
    # board outline
    x1, y1, x2, y2 = 15, 14, 195, 162
    for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        graphics.append(gr_line("Edge.Cuts", a, b, 0.1))
    graphics.append(gr_text("F.SilkS", "corne-reversible WP5 footprint test sheet - KiCad F side, seen from F", (18, 20), 2, 0.3))
    graphics.append(gr_text("F.SilkS", "= TOP of LEFT half / UNDERSIDE of RIGHT half. Print at 100% (actual size).", (18, 24), 1.6, 0.25))
    graphics.append(gr_text("F.SilkS", "Keys 19.05 mm pitch. Diodes are on the other side.", (18, 27.5), 1.6, 0.25))
    graphics.append(gr_text("B.SilkS", "corne-reversible WP5 footprint test sheet - KiCad B side, seen from B", (192, 20), 2, 0.3, "left"))
    graphics.append(gr_text("B.SilkS", "= UNDERSIDE of LEFT half / TOP of RIGHT half (face A). Print at 100%.", (192, 24), 1.6, 0.25, "left"))
    graphics.append(gr_text("B.SilkS", "SOD-123 diodes (JLCPCB-placed) shown between the key rows.", (192, 27.5), 1.6, 0.25, "left"))

    net_lines = "\n".join(f'  (net {i} "{n}")' for n, i in sorted(nets.items(), key=lambda kv: kv[1]))
    board = f"""(kicad_pcb (version 20240108) (generator "corne_reversible_gen") (generator_version "8.0")
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A4")
  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
  )
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints yes))
{net_lines}
{chr(10).join(fps)}
{chr(10).join('  ' + g for g in graphics)}
)
"""
    path = os.path.join(OUT, "test-sheet.kicad_pcb")
    open(path, "w").write(board)
    pro = {
        "board": {"design_settings": {
            "rules": {"min_clearance": 0.127, "min_track_width": 0.127, "min_via_annular_width": 0.15,
                      "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3, "min_hole_to_hole": 0.5,
                      "min_hole_clearance": 0.2, "min_copper_edge_clearance": 0.3, "min_silk_clearance": 0.0,
                      "min_text_height": 0.6, "min_text_thickness": 0.1, "solder_mask_to_copper_clearance": 0.0,
                      "allow_blind_buried_vias": False, "allow_microvias": False},
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore"}}},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.127, "track_width": 0.2,
                                      "via_diameter": 0.6, "via_drill": 0.3, "microvia_diameter": 0.3,
                                      "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
                                      "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0,0,0,0)",
                                      "schematic_color": "rgba(0,0,0,0)", "priority": 2147483647}],
                         "meta": {"version": 3}},
        "meta": {"filename": "test-sheet.kicad_pro", "version": 1},
    }
    open(os.path.join(OUT, "test-sheet.kicad_pro"), "w").write(json.dumps(pro, indent=2) + "\n")
    print("wrote", path)
    return path


def flip_to_back(txt):
    """Move a stock (front) footprint to the back: mirror x of everything, swap F./B. layers."""
    txt = txt.replace('(layer "F.Cu")', '(layer "B.Cu")', 1)

    def mirror_at(m):
        parts = m.group(1).split()
        x = float(parts[0])
        parts[0] = f"{-x:g}"
        return f"({m.group(0).split()[0][1:]} {' '.join(parts)})"
    out = []
    for line in txt.split("\n"):
        out.append(line)
    t = "\n".join(out)
    # mirror coordinates inside the footprint (not the footprint's own (at X Y))
    head, body = t.split("\n", 1)
    first_at = re.search(r"\(at [^)]*\)", body)
    keep = first_at.group(0)
    body = body.replace(keep, "@@AT@@", 1)
    body = re.sub(r"\((start|end|at|xy|center|mid) (-?[\d.]+) (-?[\d.]+)",
                  lambda m: f"({m.group(1)} {-float(m.group(2)):g} {m.group(3)}", body)
    body = body.replace("@@AT@@", keep, 1)
    body = re.sub(r'"F\.(Cu|Paste|Mask|SilkS|Fab|CrtYd)"', lambda m: f'"B.{m.group(1)}"', body)
    body = re.sub(r'(\(thickness [\d.]+\)\s*\))', r'\1 (justify mirror)', body)
    return head + "\n" + body


def run(cmd):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True)


def pdf(path):
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    common = ["--drill-shape-opt", "2", "--black-and-white", "--mode-single", "--exclude-value"]
    f = os.path.join(tmp, "f.pdf")
    b = os.path.join(tmp, "b.pdf")
    r1 = run(["kicad-cli", "pcb", "export", "pdf", path, "-o", f, "--layers",
              "F.Cu,F.Silkscreen,F.Fab,Edge.Cuts,User.Drawings"] + common)
    r2 = run(["kicad-cli", "pcb", "export", "pdf", path, "-o", b, "--mirror", "--layers",
              "B.Cu,B.Silkscreen,B.Fab,Edge.Cuts,User.Drawings"] + common)
    for r in (r1, r2):
        if r.returncode:
            print(r.stdout, r.stderr)
            sys.exit(1)
    out = os.path.join(OUT, "test-sheet.pdf")
    subprocess.run(["pdfunite", f, b, out], check=True)
    shutil.rmtree(tmp)
    print("wrote", out)


def drc(path):
    rep = os.path.join(OUT, "drc-report.txt")
    r = run(["kicad-cli", "pcb", "drc", "--severity-all", "--units", "mm", "-o", rep, path])
    print(r.stdout[-2000:], r.stderr[-2000:])
    print("wrote", rep)


if __name__ == "__main__":
    p = build()
    if "--pdf" in sys.argv:
        pdf(p)
    if "--drc" in sys.argv:
        drc(p)
