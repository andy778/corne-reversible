# Fabrication outputs (WP7)

JLCPCB files for the corne-reversible board, generated from `pcb/kicad/corne_reversible.kicad_pcb` by `pcb/kicad/tools/make_fab.py` (KiCad 10.0.6 `kicad-cli`). **Not ordered, not uploaded.** WP8 reviews these before any money is spent.

Regenerate: `/usr/bin/python3 pcb/kicad/tools/make_fab.py` (exits non-zero if the BOM/CPL or the polarity check fails).

## Files

| File | What |
| --- | --- |
| `corne_reversible_gerbers.zip` | Upload this for the PCB. Gerbers with Protel extensions (F/B copper, mask, paste, silk, Edge.Cuts) and Excellon drill in mm, plated and non-plated holes in separate files. No job file. Coordinates are absolute (KiCad origin) |
| `gerbers/` | The same files unzipped |
| `corne_reversible_bom_jlcpcb.csv` | JLCPCB BOM: Comment, Designator, Footprint, LCSC Part # |
| `corne_reversible_cpl_jlcpcb.csv` | JLCPCB CPL: Designator, Mid X, Mid Y, Layer, Rotation |
| `preview/corne_reversible_render_top.png`, `_bottom.png` | 3D renders of KiCad F and B (no part models: they show pads, silk and the empty land patterns) |
| `preview/corne_reversible_F_face.svg` | F copper, mask, silk: the top of the LEFT half |
| `preview/corne_reversible_B_face_mirrored.svg` | B copper, mask, silk seen from below: the top of the RIGHT half, and the face JLCPCB assembles |
| `preview/corne_reversible_B_assembly_mirrored.svg` | B fab, silk and paste seen from below: the assembled parts' outlines and cathode bars |

## Order form (for WP8 and the owner)

- Board: 2 layers, 1.6 mm, **146.28 x 84.01 mm**, 5 pieces. Single board, no panel. The perforated break-off line is part of the outline (38 holes of 0.6 mm in Edge.Cuts), not a V-cut.
- Assembly: **Economic PCBA, assemble the Bottom side only.** All JLCPCB parts are on KiCad B (face A): the CPL says `Bottom` for every row. Nothing is assembled on the top.
- Parts (per board): 21 x 1N4148W SOD-123, **C81598** (Basic) and 1 x TS-1187A-B-A-B reset button, **C318884** (Basic). No other line in the BOM. Every other part is hand-soldered and is excluded from BOM and CPL.

## BOM and CPL

BOM: 2 lines.

| Comment | Designator | Footprint | LCSC |
| --- | --- | --- | --- |
| 1N4148W | D1-D21 | D_SOD-123_Back | C81598 |
| TS-1187A-B-A-B | SW22 | SW_Reset_TS-1187A_FaceA | C318884 |

CPL: 22 rows, all `Bottom`. Mid X / Mid Y are the KiCad footprint origins in mm with Y negated, i.e. the Gerber coordinates. D1-D20 have rotation 0.0, D21 (under the rotated thumb key) 15.0, SW22 90.0.

### Rotation, and the correction applied

JLCPCB places from its own (EasyEDA) footprints. Read from the EasyEDA component data on 2026-11-15:

- C81598: footprint `SOD-123F_L2.7-W1.6-LS3.8-RD`, pad 1 = cathode at -x, cathode bar silk on the pad 1 side, symbol pin 1 = K.
- C318884: four pads at (+-3.0, +-1.85) mm, leads along x, pins 1 and 2 on one row, 3 and 4 on the other. Same land pattern and orientation as KiCad's `SW_Push_1P1T_XKB_TS-1187A`, whose pad 1 / pad 2 rows match the internal pairing.

For bottom-side parts, the convention used by the kicad-jlcpcb-tools plugin is JLCPCB rotation = (180 - KiCad orientation) mod 360, for a KiCad footprint whose front-side form matches the EasyEDA footprint. **This board's diode footprint does not**: Ergogen draws it directly on B.Cu with the cathode at -x, so its front-side form has the cathode at +x. The plain rule would put every diode in backwards. `make_fab.py` therefore computes the rotation from the copper instead: it measures, seen from the top, the direction from the part centre to the cathode pad (diode) or from the pad-1 row to the pad-2 row (TS-1187A), and converts it with the same convention (R = 360 - measured angle - library angle). Net effect versus the plain plugin rule: **diodes +180 degrees** (0 instead of 180), TS-1187A no change in effect (90; 270 would be equivalent, its pin pairs are symmetric under 180 degrees; 0 or 180 would put the leads across the pads and is wrong).

`make_fab.py` also checks, for every diode, that pad 1 (cathode) is on a `ROW` net and pad 2 (anode) on the key's switch net, i.e. cathode toward the row as required by `col2row`. All 21 pass.

**The rotation convention is the single most expensive thing to get wrong on this order** (a reversed diode set kills every key on both halves). It is derived, not observed: confirm it in JLCPCB's placement preview before paying (see the checklist).

## Before ordering (WP8 checklist)

1. **Diode polarity in JLCPCB's preview.** In the assembly preview of the bottom side, every diode's cathode band must sit on the side of the silkscreen bar printed next to it (the bar is at the cathode pad, the pad nearer the row via). If they are all reversed, the rotation convention is off by 180 degrees: fix it in `make_fab.py` and regenerate, or rotate all 21 in the preview. D21 is the rotated one; check it separately.
2. **Reset button** lands with its four leads on the four pads (leads pointing along the board's Y axis in the preview).
3. **Part stock and Basic status on the day**: C81598 (needs 105 + spare) and C318884 (5). If either has become Extended, the feeder fee applies; if out of stock, stop and pick a replacement with the same land pattern and polarity.
4. **No other parts in the BOM**: exactly two lines, 22 placements per board, all Bottom. The controller, sockets, power switch, JST, nice!view header and jumpers must not appear.
5. **Assembly side = Bottom**; "Top" would place nothing (or JLCPCB will complain that the parts are on the other side).
6. **Jumper silkscreen readable**: in the Gerber viewer, F silk shows `LEFT HALF: BRIDGE 24 PIN / JUMPERS ON THIS FACE ONLY`, B silk (mirrored view) shows `RIGHT HALF: ...`, and the pin names at every controller hole are legible on both faces. Some right-half (B) labels next to the JST and reset are partly clipped by pads (DRC silk warnings); check they are still readable.
7. **Outline and break line**: the board outline is closed, the 38 perforation holes are present, and JLCPCB does not treat them as an error. Their DFM may also query the 42 overlapping MX socket holes (intended, figure-8 drills).
8. **No paste on the jumpers or hand-solder pads**: F paste is empty; B paste has exactly the 21 diodes (2 pads each) and the reset button (4 pads), 46 openings.
9. Re-run DRC and `check_netlist.py` on the exact files being ordered if anything was changed.
