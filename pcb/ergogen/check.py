#!/usr/bin/env python3
"""Geometry and net checks for the generated board. Run after:
    npx ergogen@4.2.1 . -o output --clean --debug --svg
Usage: python3 check.py            (from pcb/ergogen)
Needs PyYAML only for output/points/points.yaml.
"""
import math, re, sys, yaml

PITCH = 19.05
TOL = 0.001
fails = []

def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)

pts = yaml.safe_load(open("output/points/points.yaml"))
cols = {}
for name, p in pts.items():
    z, c, r = name.split("_")
    if z == "matrix":
        cols.setdefault(c, {})[r] = p
order = ["outer", "pinky", "ring", "middle", "index", "inner"]
rows = ["top", "home", "bottom"]

# 1. vertical spacing in each matrix column
for c in order:
    for a, b in zip(rows, rows[1:]):
        d = cols[c][a]["y"] - cols[c][b]["y"]
        dx = cols[c][a]["x"] - cols[c][b]["x"]
        check(abs(d - PITCH) < TOL and abs(dx) < TOL,
              f"column {c}: {a}->{b} dy={d:.4f} mm dx={dx:.4f}")
# 2. horizontal spacing between columns
for a, b in zip(order, order[1:]):
    d = cols[b]["home"]["x"] - cols[a]["home"]["x"]
    check(abs(d - PITCH) < TOL, f"columns {a}->{b}: dx={d:.4f} mm")
# 3. stagger relative to the middle column, in units of 19.05 mm (crkbd: 0.3 .3 .1 0 .1 .2 down)
exp = dict(zip(order, [0.3, 0.3, 0.1, 0.0, 0.1, 0.2]))
for c in order:
    down = (cols["middle"]["home"]["y"] - cols[c]["home"]["y"]) / PITCH + 0.0
    check(abs(down - (exp[c] - exp["middle"])) < 0.001,
          f"stagger {c}: {down:+.3f} u below middle, expected {exp[c]-exp['middle']:+.3f}")

# 4. PCB file: footprint list, diode offsets, nets
txt = open("output/pcbs/corne_reversible.kicad_pcb").read()
fps = re.split(r"\n  \(footprint ", txt)[1:]
info = []
for f in fps:
    m = re.match(r'"([^"]+)"', f)
    a = re.search(r"\(at ([-0-9.e]+) ([-0-9.e]+)(?: ([-0-9.e]+))?\)", f)
    info.append((m.group(1), float(a.group(1)), float(a.group(2)), float(a.group(3) or 0), f))
sw = [i for i in info if "SW_MX_Choc" in i[0]]
dd = [i for i in info if "D_SOD-123_Back" in i[0]]
check(len(sw) == 21 and len(dd) == 21, f"21 switches and 21 diodes (got {len(sw)}, {len(dd)})")
# each diode must be 9.525 mm from exactly one switch, below it in the key frame
ok = 0
for d in dd:
    best = None
    for s in sw:
        dist = math.hypot(d[1] - s[1], d[2] - s[2])
        if best is None or dist < best[0]:
            best = (dist, s)
    if abs(best[0] - PITCH / 2) < 0.01 and abs(d[3] - best[1][3]) < 0.01:
        ok += 1
check(ok == 21, f"every diode is 9.525 mm from its key with the key's rotation ({ok}/21)")
check(all('layer "B.Cu"' in d[4].split("\n")[1] for d in dd), "all diodes on B.Cu (face A, left-half underside)")
# nets: each diode anode net == its switch pad 2 net; cathode in ROWn
def pad_nets(f, num):
    return set(re.findall(r'\(pad "%s"[^\n]*\(net \d+ "([^"]+)"\)' % num, f))
def pad_nets2(f, num):
    return set(re.findall(r'\(pad "%s".*?\(net "?\d*"? ?"?([A-Za-z0-9_]+)"?\)' % num, f))
bad = 0
for d in dd:
    a = pad_nets(d[4], 2) or pad_nets2(d[4], 2)
    k = pad_nets(d[4], 1) or pad_nets2(d[4], 1)
    if not (len(a) == 1 and len(k) == 1 and list(k)[0].startswith("ROW") and list(a)[0].startswith("SW_")):
        bad += 1
check(bad == 0, f"diode anode on SW_* net, cathode on ROWn ({21-bad}/21)")
cn = set()
for s in sw:
    cn |= pad_nets(s[4], 1) or pad_nets2(s[4], 1)
check(cn == {"COL_D21", "COL_D20", "COL_D19", "COL_D18", "COL_D15", "COL_D14"}, f"switch pad 1 nets: {sorted(cn)}")
mcu = [i for i in info if "MCU_" in i[0]][0][4]
for pin, net in [("D4", "ROW0"), ("D5", "ROW1"), ("D6", "ROW2"), ("D7", "ROW3"), ("D21", "COL_D21"),
                 ("D20", "COL_D20"), ("D19", "COL_D19"), ("D18", "COL_D18"), ("D15", "COL_D15"),
                 ("D14", "COL_D14"), ("D1", "DISP_CS"), ("D2", "DISP_MOSI"), ("D3", "DISP_SCK")]:
    check(net in (pad_nets(mcu, pin) or pad_nets2(mcu, pin)), f"controller {pin} -> {net}")

# 5. mounting holes survive removal of the outer-column tab (break line x = outer + 9.525)
bx = cols["outer"]["home"]["x"] + PITCH / 2
holes = [i for i in info if "MountingHole" in i[0]]
check(len(holes) == 5, f"5 mounting holes (got {len(holes)})")
check(all(h[1] > bx + 2.0 for h in holes), "all mounting holes are right of the break line by > 2 mm")
for i in info:
    if any(k in i[0] for k in ("MountingHole", "Reset", "SPDT", "JST", "MCU_", "Display")):
        print(f"      {i[0].split(':')[1]:48s} KiCad x={i[1]:8.3f} y={i[2]:8.3f} rot={i[3]:g}")

print("\nRESULT:", "ALL PASS" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
