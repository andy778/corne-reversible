# Ergogen layout (WP4)

One half of the reversible Corne-layout board: 3x6 matrix plus 3 thumb keys at 19.05 mm pitch, controller, nice!view header, power switch, reset button, JST connector, 5 M2 holes, a break-off tab for the outer column, and the case outlines for WP6. The right half is the same board flipped.

**Ergogen version:** 4.2.1 (`npx ergogen@4.2.1`, same as WP5).

## Run

```sh
cd pcb/ergogen
npx -y ergogen@4.2.1 . -o output --clean --debug --svg   # --debug writes points/points.yaml, --svg writes the outline SVGs
python3 check.py                                          # spacing, stagger, net and hole checks (needs PyYAML)
```

`output/` is not committed. `preview/` holds a copy of the outline SVG/DXF files, `points.yaml`, a plot of the generated board and the output of `check.py`.

Layout of this folder:

| Path | What |
| --- | --- |
| `config.yaml` | The Ergogen config (points, footprints, outlines) |
| `footprints/corne` | Symlink to `../../footprints/ergogen` (WP5 modules). Do not edit through it |
| `footprints/local/diode_sod123_back.js` | SOD-123 diode on KiCad B.Cu (WP5 has no diode module) |
| `footprints/local/mounting_hole_m2.js` | 2.2 mm NPTH, no copper |
| `check.py` | Acceptance checks |
| `preview/` | Small committed copy of results |

## Layout

- **Pitch:** `kp = ks = 19.05`, both axes. `check.py` asserts adjacent keys in every column are 19.05 mm apart (dx = 0), and adjacent columns 19.05 mm apart.
- **Stagger source:** QMK `keyboards/crkbd/info.json`, layout `LAYOUT_split_3x6_3` (qmk/qmk_firmware, `master`). Key y per column, in units of 19.05 mm, measured down: outer 0.3, pinky 0.3, ring 0.1, middle 0.0, index 0.1, inner 0.2. Thumbs at x = 4, 5, 6 (columns index, inner, and one beyond), with the third key drawn 0.5 u higher and 1.5 u tall (the rotated key). Ergogen stagger is relative to the previous column: pinky 0, ring +0.2 u, middle +0.1 u, index -0.1 u, inner -0.1 u (y up).
- **Thumb cluster:** the first two thumb keys are straight, directly under the index and inner columns, 1.1 u below the index bottom key (so the inner column keeps a full 19.05 mm to its thumb). The third (outer) thumb is rotated -15 degrees (clockwise), 21.05 mm to the right of the second and 0.25 u higher. This follows the QMK drawing in spirit, not the crkbd PCB measurements; see the unverified list.
- **Rows / columns (col2row):** rows top to bottom `ROW0`, `ROW1`, `ROW2`; thumb row `ROW3`. Columns outer to inner: `COL_D21`, `COL_D20`, `COL_D19`, `COL_D18`, `COL_D15`, `COL_D14`. Thumbs, outer to inner: `COL_D18`, `COL_D15`, `COL_D14`. Matches `pcb/footprints/README.md` (Corne pin map).
- **Per key:** switch pad 1 = column net, switch pad 2 = net `SW_<column>_<row>` (named `SW_<column>_<row>`, for example `SW_ring_home` or `SW_near_thumb`, taken from Ergogen's point names), diode anode on that net, diode cathode on the row net.
- **Controller:** `MCU_ProMicro_nRF52840_Reversible_Jumpers` at the crkbd position (inner side, top), USB end towards the top edge. Board nets on its signal pads: D4..D7 = ROW0..ROW3, D21/D20/D19/D18/D15/D14 = the column nets, D1 = `DISP_CS`, D2 = `DISP_MOSI`, D3 = `DISP_SCK`. GND, VCC, RAW, RST keep their default nets. The placeholder B+/B- holes are tied to unique nets `MCU_BATP_UNUSED` and `MCU_BATN_UNUSED` so they cannot join the battery net by accident.
- **nice!view header:** directly below the controller, centred on it. MOSI, SCK, CS go to D2, D3, D1 as `nice_view_adapter` expects.
- **Edge parts, right edge (inner side) beside the controller:** MSK12C02 power switch (BAT_P to RAW), reset button, JST PH (BAT_N = GND, BAT_P). The switch and JST point their actuator and plug towards the edge.

## Face convention

As in `pcb/footprints/README.md`. LEFT half = KiCad F side up. **All diodes and the reset button are on KiCad B.Cu (face A)**: they are the underside on the left half and the top on the right half. Each diode sits 9.525 mm from its key in the key's own frame (directly below it, between vertically adjacent keys), long axis across the column, pad 1 (cathode, to the row) on the key's -x side. The 3 bottom-row diodes of the outer columns and thumb diodes sit below their keys, at the board edge or inside the thumb cluster. `check.py` verifies every diode is exactly 9.525 mm from a key with the key's rotation.

## Outputs

`output/pcbs/corne_reversible.kicad_pcb`: the board (52 footprints, nets assigned, **no tracks, no zones**). `output/outlines/*.dxf` / `*.svg`:

| File | What | Overall size (mm) |
| --- | --- | --- |
| `board_42` | PCB outline, 42-key, with the break-off perforation | 146.275 x 84.01 |
| `board_36` | PCB after the tab is removed (ideal cut at the break line, nubs not drawn) | 125.225 x 84.01 |
| `plate_42` / `plate_36` | Switch plate outline = PCB outline, 21 / 18 cutouts of 14.0 x 14.0 mm, 5 holes of 2.2 mm | as board |
| `tray_42` / `tray_36` | PCB outline offset by 2.0 mm (`wall`) | 150.275 x 88.01 / 129.225 x 88.01 |
| `tray_42_left` / `tray_36_left` | Same plus a 3.0 mm press hole under the reset button (LEFT half only) | as tray |

The 36-key plate and tray remove the outer column, its cutouts, and the tab area; all 5 mounting holes are in the remaining board, so all 5 are in the 36-key plate too. Each exported file is normalised to its own bounding box (its own origin), so the outline files cannot be overlaid by coordinate. The shared frame is the Ergogen one (below), also in `preview/points.yaml`.

**Coordinates (Ergogen frame, mm, y up; origin = centre of the outer-column bottom key; KiCad coordinates are the same with y negated):**

| Item | x | y |
| --- | --- | --- |
| Reset button centre (TS-1187A, rotated 90) | 128.35 | 33.505 |
| Controller origin (centre of the 24 holes) | 115.75 | 34.505 |
| nice!view header origin | 115.75 | 11.855 |
| Power switch origin | 131.55 | 42.505 |
| JST origin | 129.75 | 24.505 |
| Mount holes H1..H5 | (28.575, 31.1), (66.675, 34.29), (28.575, 12.05), (85.725, -22.645), (115.75, 3.855) | |

The reset press hole in `tray_*_left` is at the reset centre. The reset button is **top actuated, 1.5 mm tall, courtyard 7.5 x 5.6 mm**, in the strip right of the controller, outside the key area. On the right half it faces up: WP6 must leave the plate open (or notch it) over that spot or the plate will press on the button. On the left half it faces down into the tray press hole.

Mounting holes: M2 (2.2 mm). H1 to H4 are on key-tile corners, columns 1 to 5 and the thumb cluster; H5 is in the controller strip below the nice!view header. They are NPTH with no copper on either face, so they work on both faces. None is in the outer column or the tab, so all five survive the 36-key break.

## Break-off tab (outer column)

- The break line is `x = outer column + 9.525 mm`, the tile boundary between the outer and pinky columns. It is a **perforation, not a slot**: 38 holes of 0.6 mm at 1.2 mm pitch (0.6 mm webs), running the full height. WP7 routes the 4 crossing nets between the holes.
- Holes are skipped (3 gaps of about 4 mm per row) where the Choc pad-1 copper tips on the two adjacent keys reach the line (9.575 mm from the outer key centre on KiCad B, 9.475 mm from the pinky key centre on KiCad F). MX copper stays at least 0.85 mm from the hole edges.
- **Plan conflict, not reopened:** the plan says only the column trace crosses the break line. That cannot be: the 3 tab diodes connect each outer-column key to ROW0..ROW2, so **COL_D21 and ROW0, ROW1, ROW2 all cross** (4 nets). Breaking the tab leaves 3 harmless row stubs. Moving the diodes to the main board would instead make 3 anode nets cross plus the column.
- `docs/bom.md` does not exist on this branch, so JLCPCB's mouse-bite guidance was not read. The design uses holes of 0.6 mm (0.5 to 0.8 mm range given in the task) and a continuous tab (the whole 57 mm side), so the 4 to 5 mm tab minimum is met trivially. A plain perforated line is fragile in transit; if JLCPCB wants routed slots with bridges, the Choc pad tips would have to be trimmed (see the next section).

## Results (KiCad 10 `kicad-cli`)

The generated `.kicad_pcb` opens, plots (SVG in `preview/`) and runs DRC. DRC findings with default KiCad rules (0.5 mm edge, 0.25 mm hole): 214 unconnected items (expected, no routing) and, from the WP5 footprints, 42 hole-to-hole and 42 pad-to-peg-slot "edge clearance" hits (peg slot NPTH to the socket pad 0.377 mm; WP5 accepted these against JLCPCB rules of 0.2 mm), plus library and silkscreen warnings. The layout adds **no copper, hole or edge clearance violation** of its own. The remaining layout findings are about 17 `courtyards_overlap` / `npth_inside_courtyard` hits between a mounting hole's courtyard and the approximate socket courtyard rectangles (the hole copper clearance itself passes).

## Unverified / risks

1. **Stagger and thumb numbers** come from QMK's `info.json` fetched through a summariser, not diffed against the crkbd KiCad PCB. The QMK drawing has a surprising 1.6 u gap from the bottom row to the thumb row; I used 1.1 u (needed so a straight thumb key clears the inner column) and a -15 degree third thumb. Compare with the physical Corne (or foostan/crkbd PCB) before ordering.
2. **Thumb keycap clearance**: the third thumb is rotated and 21.05 mm from the second (a spacing I chose: 19.05 mm would make keycap corners touch). Not checked with real keycaps.
3. **Break line and the Choc pad tips** (above): the perforation nibbles the tip of the Choc pad 1 at 3 places per side. For an MX-only build there is no issue. The WP5 pad could be shortened by 0.2 mm to clear the line; **a WP5 footprint change if Choc on a 36-key build matters**.
4. **No JLCPCB mouse-bite check** (docs/bom.md absent). Only 4 nets cross, between 0.6 mm webs; a perforation line over 57 mm may be fragile.
5. **Mounting hole courtyard overlaps** (see Results). A hole sits 0.04 mm to 1.2 mm from socket copper in places; DRC hole clearance passes at 0.25 mm. Check by eye in KiCad.
6. **Edge parts positions** (power switch, reset, JST at the right edge) are placed by eye. The JST courtyard (plug and lead) extends past the right edge by design (up to 8 mm beyond the pads on the B face); WP6 needs an opening. The controller is placed so the footprint's USB end sits at the top edge; the real USB-C overhang was not measured.
7. **nice!view fit**: only the 5-hole header is placed. The 1.3 inch display module's own board outline (about 40 mm wide) was not checked against keys and the controller; it is placed where the crkbd OLED header sits by intent, not verified.
8. **Ergogen outline fillet** is 1 mm on the union; the `expand` tray offset gives rounded outside corners.
9. Net names `SW_<col>_<row>` for the diode junction are mine; WP7's netlist check should use the net class "pad 2 of switch = anode".
10. The symlink `footprints/corne` assumes a filesystem that preserves symlinks (fine on Linux/macOS git).
