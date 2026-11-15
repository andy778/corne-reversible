# KiCad board (WP7)

Routed KiCad 10 project for one reversible Corne half. LEFT half = KiCad F side up, RIGHT half = the same board flipped (KiCad B up). JLCPCB assembles KiCad B (face A): 21 diodes and the reset button. Fabrication outputs are in [`../fab/`](../fab/README.md).

**Status:** routed, KiCad DRC 0 errors, geometric netlist check passing for both halves. **Not reviewed:** WP8 does the independent pre-order review. Nothing here has been sent to JLCPCB.

## Contents

| Path | What |
| --- | --- |
| `corne_reversible.kicad_pcb` / `.kicad_pro` | The board and its design rules (generated, do not hand-edit without re-running the checks) |
| `fp-lib-table` | Project libraries: `corne_reversible` = `../footprints/corne_reversible.pretty` (WP5), `corne_kicad_local` = `corne_kicad_local.pretty` |
| `corne_kicad_local.pretty/` | The two Ergogen-local footprints (SOD-123 diode on face A, M2 hole), exported in front form so KiCad can check board copies against them |
| `tools/build_board.py` | Builds the routed board from the Ergogen output (see Regenerate) |
| `tools/router.py` | The small grid maze router `build_board.py` uses for the inter-key nets |
| `tools/check_netlist.py` | Electrical check from copper geometry, both halves; output in `netlist-check.txt` |
| `tools/make_fab.py` | Gerbers, drill, JLCPCB BOM/CPL, previews into `../fab/` |
| `tools/kutil.py` | pcbnew helpers |
| `drc-report.txt` | `kicad-cli pcb drc --severity-all` of the committed board |
| `netlist-check.txt` | Output of `check_netlist.py` on the committed board |

## Regenerate

Tools used: Ergogen **4.2.1** (`npx`), KiCad **10.0.6** (`kicad-cli`, and the `pcbnew` Python module of the system Python, `/usr/bin/python3`, 3.14 on the build machine), `shapely` 2.1, `numpy`, `scipy`, `Pillow`. Freerouting was not installed and not used.

```sh
cd pcb/ergogen && npx -y ergogen@4.2.1 . -o output --clean --debug --svg && python3 check.py && cd ../..
/usr/bin/python3 pcb/kicad/tools/build_board.py          # about 5 minutes; deterministic
(cd pcb/kicad && kicad-cli pcb drc --severity-all -o drc-report.txt corne_reversible.kicad_pcb)
/usr/bin/python3 pcb/kicad/tools/check_netlist.py > pcb/kicad/netlist-check.txt
/usr/bin/python3 pcb/kicad/tools/make_fab.py
```

`build_board.py` reads `pcb/ergogen/output/pcbs/corne_reversible.kicad_pcb` (KiCad 5 format from Ergogen), and:

1. assigns the JLCPCB data (value, `LCSC` field) to the diodes (C81598) and the TS-1187A (C318884), and points the two Ergogen-local footprints at `corne_kicad_local`;
2. removes the net from the placeholder battery jumper pads (`BAT+`/`BAT-`) and from the power switch's unused pin 3 (see Power);
3. places a fixed per-key template (identical for all 21 keys, rotated with the key): it joins the four column socket pads, the four anode socket pads and the diode anode, and puts a via on the diode cathode;
4. places the controller fan-out stubs (see Controller) and the nice!view jumper stubs and lanes;
5. routes everything else with `router.py` (0.05 mm grid, two layers, then pulled straight with exact clearance checks), in a fixed order with per-net layer preferences: power and display nets first on the right of the controller, then rows (F preferred) and columns (B preferred) inside the key field, then the long column and row runs into the controller;
6. removes router leftovers (dead-end stubs, single-layer vias) and trims overhangs at T-junctions;
7. moves the controller's jumper instruction text clear of the nice!view labels and adds the version and half labels.

## Board

| | |
| --- | --- |
| Size | **146.28 x 84.01 mm** (outline bounding box, 42-key), 100.9 cm2. 2 layers, 1.6 mm |
| Origin | KiCad (0, 0) = centre of the outer-column bottom key; Ergogen coordinates are the same with y negated |
| Copper | 669 track segments (3.15 m), 106 vias (0.6/0.3 mm) |
| Mounting holes | M2, 2.2 mm NPTH, Ergogen frame: H1 (30.075, 32.65), H2 (65.675, 34.54), H3 (30.075, 13.6), H4 (85.725, -25.645), H5 (115.75, 3.855). H1-H4 moved in this WP for the case inserts (see `pcb/ergogen/README.md`) |
| Break line | x = 9.525 (KiCad), 38 holes of 0.6 mm in Edge.Cuts |

## Design rules (JLCPCB 2-layer, from docs/bom.md)

Conservative values where space allows; the absolute JLCPCB minimum is in brackets.

| Rule | Board setting | JLCPCB |
| --- | --- | --- |
| Clearance, copper to copper | 0.20 mm | 0.10 (0.15 recommended) |
| Track width, minimum | 0.20 mm (only the nice!view lanes use 0.20) | 0.10 |
| Signal tracks | 0.25 mm | |
| Power tracks | BAT_P 0.50, RAW 0.50, GND 0.40 (JST, reset, controller), VCC 0.30 mm; 0.30 mm where they pass between the controller hole rows (0.84 mm gaps). nice!view GND 0.25 | |
| Vias | 0.6 mm pad / 0.3 mm drill (ring 0.15) | 0.15 / 0.25 min, 0.2 hole preferred |
| Minimum via annular ring | 0.15 mm (the controller's 0.7/0.3 via-pads have 0.20) | |
| Minimum through hole | 0.30 mm | 0.15 (via), 0.2 preferred |
| Copper to drill hole | 0.25 mm | |
| Hole to hole | 0.50 mm | 0.20 via, 0.45 pad |
| Copper to board edge (incl. mouse-bite holes) | 0.30 mm | 0.20 |
| Text height / thickness | 0.8 / 0.15 mm (footprint silk is 0.9 mm) | 1.0 mm recommended, 0.15 line |

Net classes: Default 0.25, Power (BAT_P, RAW) 0.5, Ground (GND) 0.4, Logic3V3 (VCC) 0.3, all 0.2 mm clearance.

## Routing decisions

**Per key** (template, key frame; B = KiCad B.Cu, F = KiCad F.Cu): column pads 1 are on B on the right of the key and on F on the left; anode pads 2 the other way round. Column: F Choc - F MX, an F track over the top of the key to a via, B to the B Choc pad, B Choc - B MX. Anode: B Choc - B MX down the left side, F Choc - F MX down the right side, both into a via below the MX pads, B to the diode anode. Row: diode cathode on B to a via left of the diode. Column trunks run vertically on B, rows horizontally on F, so the key field is close to a Manhattan grid.

**Matrix to controller.** The long column runs (the outer columns in particular) go along the top edge of the key field or through the gaps between key rows, then down the strip left of the controller; rows enter the same strip from the key field and the thumb cluster. The router chose these paths; see the previews. Thumb keys connect to their column nets (near = D18 under the index column, mid = D15, far = D14).

**Controller** (`MCU1`, socketed, face-up on both halves). The board net goes to the centre via-pad of each pin exactly as `pcb/footprints/README.md` describes; the jumpers select the half. Each used via-pad is reached by a hand-placed stub through the gap between two hole rows (0.84 mm between hole pads), on the face and side where the via-pad has no link of another net. Left side: columns on F (D21 ... D14), rows on B (D4 ... D7). Right side: RAW, GND, RST, VCC on B; D1 (CS), D2 (MOSI), D3 (SCK) on F. The three controller GND via-pads are tied inside the footprint: the adjacent pair of rows 2/3 with a short B track, rows 3/4 through their two F-side GND jumper pads (both are GND-side pads, so this is plain GND copper on both halves). Nothing else is routed between the hole columns.

**nice!view.** Each jumper target pad gets a stub out of its mask aperture, away from the jumper gap. F pads dog-leg to a via 0.9 mm to their left; B pads go straight down. Under the header four nested lanes per face (0.20 mm) run to the right, where the router joins them to the controller. CS = D1, MOSI = D2, SCK = D3, plus VCC and GND, both halves (checked).

**Power.** JST pin 2 (BAT_P, both hole pairs) -> MSK12C02 pin 1 (both faces) ; MSK12C02 common pin 2 (both faces) -> controller RAW. JST pin 1 and the reset button go to GND. Decision on the WP5 battery placeholder holes `HB1`/`HB2` (B+/B-): **kept, but their jumper target pads have no net and nothing is routed to them.** The plan asked for the holes, and on a socketed nice!nano or SuperMini the battery reaches the controller through RAW. With no copper on the target pads, bridging a B+/B- jumper on either or both faces connects the hole to an isolated pad, so the CRITICAL battery short in the WP5 hazard table cannot happen on this board. If a future controller needs B+ there, that is a board change.

**Mounting holes.** The router keeps its copper at least 2.6 mm (copper edge) from every mounting-hole centre, outside an M2 screw head (3.8 mm). Measured nearest copper edge from the centre: H1 2.60, H2 2.35 (fixed key-template copper), H3 2.60, H4 2.61, H5 1.50 mm. H5's 1.50 mm is the nice!view MOSI lane on F (and the CS lane on B, under the plastic boss); a single net under the screw head cannot short to anything even if the mask is scratched, but a nylon washer at H5 costs nothing.\n\n**Reset.** TS-1187A pin 1 (both pads) -> RST, pin 2 (both pads) -> GND.

**Break-off tab.** Only COL_D21, ROW0, ROW1 and ROW2 cross x = 9.525 (checked); they cross in the three gaps of the perforation, at least 0.30 mm from every bite hole (DRC copper-to-edge). No other copper is in the tab. With the tab removed the remaining 18 keys and everything else stay connected (checked).

**No ground pour.** GND only has to connect the JST, the reset button, three controller via-pads and the display, all within 30 mm of each other on the right of the controller; tracks do that. A pour on both faces would sit against the hand-bridged jumper pads (a solder blob could reach it), wick heat from the socket pads, need a keep-out along the break line, and put copper under the controller module's antenna end. So none.

**Silkscreen.** From WP5: `LEFT HALF: BRIDGE 24 PIN / JUMPERS ON THIS FACE ONLY / USB / CONTROLLER FACE UP` on F and the `RIGHT HALF` version on B (moved below the nice!view header so it no longer overlaps the display pin labels), pin names at every controller hole and nice!view hole on both faces, `LEFT: bridge 4` / `RIGHT: bridge 4` at the display, B+/B- marked. Added: `corne-reversible v1.0 2026-11-15` on both faces and `LEFT HALF: THIS FACE UP` (F) / `RIGHT HALF: THIS FACE UP` (B). Polarity: every diode has a cathode bar on B silk at the cathode pad; the JST has `+`/`-` and `USE THIS PAIR` on each face.

## DRC result

`drc-report.txt`, KiCad 10.0.6, all severities: **0 errors, 0 unconnected items, 60 warnings**, none excluded. Accepted warnings:

| Count | Type | Why accepted |
| --- | --- | --- |
| 42 | `hole_to_hole` | The two overlapping 3.0 mm MX socket holes per key (2 per key), inherent to the reversible MX footprint (WP5). The fab drills a figure-8; JLCPCB's DFM may ask, answer "intended". Left as warnings rather than DRC exclusions so they stay visible on every run |
| 12 | `silk_over_copper` | Controller pin labels next to the JST/reset pads and the `USE THIS PAIR` text over controller hole pads; JLCPCB clips silk on pads. Legibility of a few right-half pin labels (B face, D2-D8) is reduced; the pin map is printed on the F face and in the WP5 README |
| 5 | `silk_overlap` | The same labels touching the reset and JST outlines |
| 1 | `lib_footprint_mismatch` | `SW22` (TS-1187A): value and the `LCSC` field were set on the board copy |

All other footprints match their library copies, which also confirms that the Ergogen modules and the WP5 `.kicad_mod` files are the same footprints.

## Netlist check

`tools/check_netlist.py` builds connectivity from the copper itself (pads, tracks, vias, plated holes), bridges the jumpers of one face (LEFT: F, RIGHT: B), maps each controller hole to the Pro Micro pin that lands in it on that half (mirrored on the right half) and asserts per key: column pin -> all four pad-1 socket pads, pad 2 -> diode anode, diode cathode -> row pin, for both halves against the stock ZMK Corne pin map; power, reset and nice!view wiring; no two controller pins sharing copper; unused pins isolated; the 36-key break; the break-line crossings; that bridging both faces does short pins (the documented hazard); and that every copper island carries one net name. Result on the committed board: `netlist-check.txt`, **271 checks, ALL PASS**.

## Known limits

- The router is mine and simple; routes are valid (DRC) but not pretty in places, notably around the nice!view and on the right of the controller. Open the board in KiCad before ordering.
- The right edge layout (power switch, reset, JST next to the controller) is WP4's and is tight; see the silk warnings above.
- Everything listed under "Unverified" in `pcb/footprints/README.md` and `pcb/ergogen/README.md` still applies.
