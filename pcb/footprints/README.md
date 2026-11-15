# Footprints (WP5)

Reversible footprints for the corne-reversible board, in KiCad and Ergogen form, plus the checks and the 1:1 paper test sheet.

**Status:** generated, KiCad DRC-checked and geometry-checked. **Paper-tested:** the WP5 acceptance check, a 1:1 test fit with real parts (see [Paper test](#paper-test)), passed on 2026-11-15.

## Contents

| Path | What |
| --- | --- |
| `corne_reversible.pretty/` | KiCad 8/9/10 footprint library (file format 20240108, opens in KiCad 8 and later) |
| `ergogen/` | Ergogen v4 footprint modules with the same geometry. Copy or symlink into `<ergogen project>/footprints/corne/` and use `what: corne/<file name>` |
| `tools/gen_footprints.py` | **Source of truth.** Generates both of the above. Edit this, never the outputs |
| `tools/check_footprints.py` | Geometry and clearance checker against JLCPCB 2-layer rules (needs `shapely`) |
| `tools/make_test_sheet.py` | Builds `test-print/test-sheet.kicad_pcb` and plots the PDF; also runs KiCad DRC |
| `test-print/test-sheet.pdf` | 1:1 printable sheet. Page 1 shows the KiCad F side; page 2 shows the KiCad B side seen from B |
| `test-print/drc-report.txt` | KiCad 10 DRC of the test board against JLCPCB rules |
| `THIRD_PARTY.md` | Sources, commits and licences |

Regenerate everything:

```sh
python3 pcb/footprints/tools/gen_footprints.py
python3 pcb/footprints/tools/check_footprints.py
python3 pcb/footprints/tools/make_test_sheet.py --pdf --drc
```

## Face convention (read this first)

The plan calls the faces A and B: face A is the underside of the left half and the top of the right half. Diodes go on face A.

The footprints assume this mapping:

| | LEFT half | RIGHT half |
| --- | --- | --- |
| Board orientation | KiCad **F** side up | flipped left to right, KiCad **B** side up |
| Face A (JLCPCB diodes) | underside = KiCad **B** | top = KiCad **B** |
| Sockets, power switch, reset, JST | soldered on KiCad B | soldered on KiCad F |
| Controller and nice!view | on top (KiCad F), component side up | on top (KiCad B), component side up |
| Jumpers to bridge | the ones on **KiCad F** (silk: `LEFT HALF: BRIDGE 24 PIN JUMPERS ON THIS FACE ONLY`) | the ones on **KiCad B** (silk: `RIGHT HALF: …`) |

So **WP7 places the diodes on KiCad B.Cu**, and JLCPCB assembles the bottom side. To use the opposite mapping, set `LEFT_FACE = "B"` in `gen_footprints.py` and regenerate. Every LEFT/RIGHT label and jumper net then swaps sides.

The flip is a left-right mirror: a point at KiCad (x, y) is seen at (-x, y) from the top of the right half. The USB end stays at -y on both halves.

## Footprints

All footprints are marked `exclude_from_pos_files exclude_from_bom` because only the diodes are factory-placed. WP7 can change that if a full BOM is wanted. **No hand-soldered pad has paste.** This matters most for the jumpers: paste on face-A jumpers would let JLCPCB's stencil bridge all of them. Do not add paste.

### `SW_MX_Choc_Hotswap_Reversible` / `ergogen/switch_mx_choc_reversible.js`

One key, 19.05 mm pitch. Origin is the key centre.

- **MX** (Kailh CPG151101S11) pads and holes are on the +y half. The MX switch is rotated 180 degrees (south-facing), which is what makes room for Choc. The socket pads are on both faces. The inner pad is chamfered to clear the other face's socket hole.
- **Choc** (Kailh CPG135001S30) pads and holes are on the -y half, on both faces, sharing the pin-1 hole at (0, -5.95). The inner pad is chamfered (50 %) to clear the other face's side hole.
- Centre hole is 5.0 mm, for the Choc V2 post. Each side peg uses one oval slot, 2.32 x 1.9 mm centred at ±5.29, which takes both the MX PCB-mount pegs (±5.08) and the Choc V1 pegs (±5.5).
- Pads: `1` = column side (`from`), `2` = diode side (`to`). Each net appears on 4 pads: MX F, MX B, Choc F, Choc B. The faces are **not joined inside the footprint**, so WP7 routes both. A switch is a plain contact, so the pad-to-net choice per socket is free; it was picked so pad 1 is at the outer x edge (column traces run vertically) and pad 2 is nearest the diode below for MX.
- Fab and courtyard layers: approximate socket outlines on both faces. Dwgs.User: 14 x 14 mm switch outline and 18.05 mm keycap outline.

### `MCU_ProMicro_nRF52840_Reversible_Jumpers` / `ergogen/mcu_promicro_reversible_jumpers.js`

Pro Micro footprint for the nice!nano v2 or a SuperMini. It is socketed and mounted **component side up on both halves**, with USB towards -y. The rows are 15.24 mm apart; holes are 1.0 mm drill with 1.7 mm pads, for machine-pin sockets.

- **Holes `H1`..`H24`** use Pro Micro numbering in the LEFT-half view: H1 is top-left (D1) and the numbering runs counter-clockwise. Each hole is a local net with nothing attached except its two jumpers.
- **Per hole, one jumper on each face** (0.9 x 1.25 mm pads, 0.3 mm gap, one shared mask opening, tented copper link to the hole):
  - KiCad F jumper: connects the hole to the pin the LEFT half seats there.
  - KiCad B jumper: connects the hole to the pin the RIGHT half seats there, which is the pin at the mirrored hole.
- **Signal pads** are named after the controller pin: `D0`..`D21`, `RAW`, `GND`, `RST`, `VCC`. Each signal has a 0.7 / 0.3 mm tented via-pad in the centre column (x = 0, y = row ± 0.75). Its F jumper and its mirrored B jumper are already tied to it inside the footprint. **WP7 routes the board net to that via.** In Ergogen, pass the board net as the param, e.g. `D4: ROW0`.
- **`BAT+` / `BAT-` (holes `HB1`, `HB2`)** sit next to the USB end at y = -15.24, x = ±1.27, with jumpers as for the other pins. They are a **placeholder**: see the unverified list. With a nice!nano v2 the normal battery path is JST, then power switch, then the `RAW` pin. Leave these unbridged and unrouted unless your controller really has B+/B- holes at exactly these positions.
- Silk on each face gives the pin name at every hole as seen on that half, plus the bridging instruction.
- The nice!nano extra pins (P1.01, P1.02, P1.07) are **not** included. They sit in different places on the nice!nano and the SuperMini, and the Corne does not need them.

### `Display_niceview_Header_Reversible_Jumpers` / `ergogen/display_niceview_reversible_jumpers.js`

A 5-pin 2.54 mm header. Seen from the top of the LEFT half, x = -5.08 to +5.08: **MOSI, SCK, VCC, GND, CS**. VCC is the centre pin and mirrors onto itself, so it is a plain pad `VCC`. The other four holes (`H1`, `H2`, `H4`, `H5`) each have one jumper per face, placed below the header:

| Hole (left view) | KiCad F jumper (LEFT) | KiCad B jumper (RIGHT) |
| --- | --- | --- |
| H1 (x = -5.08) | MOSI | CS |
| H2 (x = -2.54) | SCK | GND |
| H3 (x = 0) | VCC (no jumper) | VCC |
| H4 (x = +2.54) | GND | SCK |
| H5 (x = +5.08) | CS | MOSI |

The jumper target pads are named `MOSI`, `SCK`, `GND`, `CS`. They are **not** joined inside the footprint, because the F and B copies cross each other. WP7 routes them: MOSI to D2, SCK to D3, CS to D1, plus GND and VCC.

### Edge parts (soldered by hand on whichever face is the underside)

These parts carry their own pads on each face, mirrored, with the same pad numbers. So the pin function is right on both faces **without jumpers**. The F and B copies are separate copper that WP7 joins.

| Footprint | Part (WP3, LCSC, checked 2026-11-15) | Pads / nets | Notes |
| --- | --- | --- | --- |
| `SW_SPDT_MSK12C02_Reversible` | Shou Han MSK12C02, C431540 | `1` = BAT_P (from JST), `2` = common, goes to RAW, `3` = NC; 4 unnamed shell tabs; 2 NPTH | Actuator towards +y (board edge). Signal pads lengthened 0.4 mm away from the body for hand soldering. Because the B copy is mirrored, ON is the opposite slide direction on the two halves. |
| `SW_Reset_TS-1186F_Side_Reversible` | XKB TS-1186F-B-A, C908470. **Fallback only**: the owner chose the factory-fitted TS-1187A (below) | `1` = RST (pins 1+2), `2` = GND (pins 3+4); two 0.8 mm peg holes | Land pattern read from the XKB TS-1186F-X-X drawing; pads lengthened 0.4 mm outward. Actuator assumed towards +y. |
| `JST_PH_S2B-PH-K_Reversible` | JST S2B-PH-K-S, C173752, THT side entry | `1` = BAT_N (GND), `2` = BAT_P | THT holes are shared by both faces, so a connector fitted on the other face would swap polarity. This footprint therefore has **two hole pairs**: y = 0 for a connector on KiCad F, y = -3.0 for one on KiCad B, wired as mirror images. No jumpers, so there is no double-bridge battery short. Silk on each face marks `USE THIS PAIR`. Courtyard includes the plug and lead. |

### `SW_Reset_TS-1187A_FaceA` / `ergogen/reset_switch_ts1187a_face_a.js` (JLCPCB-assembled)

- XKB TS-1187A-B-A-B, C318884, **JLCPCB Basic** (no feeder fee): the owner chose to have JLCPCB fit it with the diodes, on face A only.
- Pads, paste and courtyard are KiCad's stock `SW_Push_1P1T_XKB_TS-1187A` (1.0 x 0.75 mm at x +-3.0, y +-1.875). `1` = RST, `2` = GND. Included in BOM and position files, unlike the hand-soldered footprints.
- The KiCad library copy is front-side; flip it onto face A in KiCad. The Ergogen module is emitted already on face A (KiCad B with the default `LEFT_FACE`).
- It is top-actuated, 1.5 mm tall. Left half: it faces down, so the tray needs a press hole under it. Right half: it faces up, so place it outside the switch plate (next to the controller), not under a key.

## Corne pin map (ZMK stock `corne` shield)

Source: zmkfirmware/zmk `main` at `4de313367288aad5aeaa1243890e40dc813f7008`:
[`corne.dtsi`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/boards/shields/corne/corne.dtsi),
[`corne_left.overlay`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/boards/shields/corne/corne_left.overlay),
[`corne_right.overlay`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/boards/shields/corne/corne_right.overlay).
GPIO names are from [`nice_nano/arduino_pro_micro_pins.dtsi`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/module/boards/nicekeyboards/nice_nano/arduino_pro_micro_pins.dtsi).

**Diode direction: `col2row`.** Current flows from the column, through the switch, into the diode anode and out of the cathode to the row. So: column net goes to switch pad `1`, switch pad `2` goes to the diode **anode**, and the diode **cathode** (band) goes to the row net. Rows are inputs with pull-down.

| Matrix line | Pro Micro pin (`&pro_micro N`) | nRF52840 GPIO | Physical position |
| --- | --- | --- | --- |
| Row 0 | D4 | P0.22 | top row |
| Row 1 | D5 | P0.24 | home row |
| Row 2 | D6 | P1.00 | bottom row |
| Row 3 | D7 | P0.11 | thumb row (3 keys, under columns 3 to 5) |
| Column, outer pinky | D21 | P0.31 | left `col-gpios[0]`, right `col-gpios[5]` |
| Column, pinky | D20 | P0.29 | left [1], right [4] |
| Column, ring | D19 | P0.02 | left [2], right [3] |
| Column, middle (and outer thumb) | D18 | P1.15 | left [3], right [2] |
| Column, index (and middle thumb) | D15 | P1.13 | left [4], right [1] |
| Column, inner index (and inner thumb) | D14 | P1.11 | left [5], right [0] |

Left `col-gpios` = 21, 20, 19, 18, 15, 14 (outer to inner). Right `col-gpios` = 14, 15, 18, 19, 20, 21 (inner to outer), with `col-offset = <6>`. **The same physical column uses the same pin on both halves**: the outer pinky column is D21 on both, the inner index column is D14 on both. A flipped board gives exactly this, so the board nets are simply `ROW0..3` and `COL_D21 … COL_D14` on one copper layout. The 36-key break-off tab carries the D21 column. The 5-column ZMK transform drops RC(x,0) and RC(x,11).

Not used by the Corne matrix: D0, D1, D2, D3, D8, D9, D10, D16. D1, D2 and D3 go to the nice!view.

## nice!view mapping (stock `nice_view_adapter`)

Source: [`nice_view_adapter/boards/nice_nano_nrf52840_zmk.overlay`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/boards/shields/nice_view_adapter/boards/nice_nano_nrf52840_zmk.overlay) and [`README.md`](https://github.com/zmkfirmware/zmk/blob/4de313367288aad5aeaa1243890e40dc813f7008/app/boards/shields/nice_view_adapter/README.md) at the same commit. Confirmed by [nicekeyboards docs](https://nicekeyboards.com/docs/nice-view/pinout-schematic) and WP3.

| nice!view pin | Pro Micro pin | nRF52840 | ZMK |
| --- | --- | --- | --- |
| MOSI | D2 | P0.17 | `SPIM_MOSI` (same pin as the Corne OLED SDA) |
| SCK | D3 | P0.20 | `SPIM_SCK` (same pin as the Corne OLED SCL) |
| CS | D1 | P0.06 | `cs-gpios = <&pro_micro 1 …>` |
| VCC | VCC (3.3 V) | | |
| GND | GND | | |

The adapter also assigns MISO to P0.25, which is not a Pro Micro pin and is not connected. The adapter disables `pro_micro_i2c`. With this wiring, `corne_left nice_view_adapter nice_view` builds unmodified.

## Jumper scheme and per-pin hazards

On each half, bridge **only** the jumpers on the face pointing up: KiCad F on the left half, KiCad B on the right. Bridging a hole on both faces shorts the two nets in the table below. Bridging the **wrong** face on a half mirrors the whole pinout, which puts battery voltage on a GPIO and shorts VCC to GND, so it is **destructive**. The hazard is the same for the hole at -x and its mirror at +x.

| Row (from USB end) | Left-half pin at -x | Left-half pin at +x | If both faces are bridged | Severity |
| --- | --- | --- | --- | --- |
| 1 | D1 (nice!view CS) | RAW (battery, up to 4.2 V) | Battery on P0.06, above the nRF52840's VDD + 0.3 V limit. Can destroy the GPIO or MCU and the display input | **HIGH** |
| 2 | D0 (unused) | GND | D0 grounded | low |
| 3 | GND | RST | Held in reset, never boots | low (no damage) |
| 4 | GND | VCC (3.3 V out) | 3.3 V rail shorted: regulator overload and heat, battery drain, display dead | **HIGH** |
| 5 | D2 (MOSI) | D21 (col, outer pinky) | Display data on a column: garbage on the display, ghost keys | medium |
| 6 | D3 (SCK) | D20 (col) | as above | medium |
| 7 | D4 (row 0) | D19 (col) | Driven column into a row input: whole-row ghosting | medium (no damage) |
| 8 | D5 (row 1) | D18 (col) | as above | medium |
| 9 | D6 (row 2) | D15 (col) | as above | medium |
| 10 | D7 (row 3) | D14 (col) | as above | medium |
| 11 | D8 (unused) | D16 (unused) | none | none |
| 12 | D9 (unused) | D10 (unused) | none | none |
| USB end | BAT+ | BAT- | **Direct battery short, no fuse.** Placeholder holes: leave unbridged | **CRITICAL** |
| nice!view H1/H5 | MOSI (D2) | CS (D1) | Display garbage | low |
| nice!view H2/H4 | SCK (D3) | GND | SPI clock pin driven into ground | low to medium |

GND has to be jumpered too. The three controller GND pins are at left-view rows 2 (+x), 3 (-x) and 4 (-x); they mirror onto D0, RST and VCC, so no pin is symmetric and all 24 holes need jumpers.

**Before fitting the controller or connecting the battery**, with a multimeter:

1. RAW net to GND net: open circuit.
2. VCC net to GND net: open circuit.
3. For each bridged hole, continuity from the hole to the net named on the silk at that hole on the upward face.
4. No jumper bridged on the downward face (check visually before the case goes on).

## Diode clearance (face A, between vertically adjacent keys)

Checked with KiCad's stock `D_SOD-123` (pads 0.9 x 1.2 mm at ±1.65 mm, courtyard 4.7 x 2.3 mm). The diode is placed on KiCad B, centred between two keys (y = +9.525 from the upper key), long axis across the column.

| Check | Result |
| --- | --- |
| Diode pads to switch copper, key above / key below | 3.58 mm / 1.68 mm |
| Diode pads to nearest NPTH | 1.71 mm (Choc pin-1 hole of the key below) |
| Diode courtyard to socket courtyards, key above (MX) / key below (Choc) | 1.63 mm / **0.03 mm**, tight but not overlapping (the Choc socket outline is approximate) |
| Top side (right half), gap between MX housings at the 15.6 mm bottom flange | 3.45 mm, leaving 0.83 mm each side of a 1.8 mm diode body |
| Top side, gap between Choc V1 housings (15.0 mm) | 4.05 mm, leaving 1.13 mm each side |

This confirms the plan's 3.4 mm (MX) and 4 mm (Choc) budget. A Choc build with diodes on the top face still needs the plate pockets described in the plan.

## Validation results

**KiCad** (`kicad-cli` 10.0.6):

- All six footprints load and plot (`kicad-cli fp export svg`).
- DRC was run on `test-print/test-sheet.kicad_pcb` (4 keys, 2 diodes, every other footprint), with JLCPCB rules in `test-sheet.kicad_pcb`'s project: 0.127 mm clearance, 0.3 mm drill, 0.15 mm via ring, 0.2 mm hole clearance, 0.5 mm hole-to-hole.
- Result: **no clearance, short, annular-ring or silkscreen violations.** The only findings are 8 × `hole_to_hole`, which are the overlapping MX socket holes described below (2 per key), plus "unconnected items" (expected, because the test board is not routed).
- The Ergogen modules were run through Ergogen 4.2.1 on a small test config, with rotated keys and footprints. The output board loads in KiCad. Its DRC shows only the same MX hole overlap, edge clearance against the one-key toy outline, unconnected items and the library-not-configured notice. Ergogen's 0.8 mm minimum text height passes, because all silk text is at least 0.9 mm.

**`tools/check_footprints.py`** (rules: 0.127 mm copper, 0.2 mm hole to copper, 0.5 mm hole to hole, 0.3 mm drill, 0.15 mm ring):

| Footprint | Min copper gap | Min hole to copper | Min hole to hole | Min ring | Violations |
| --- | --- | --- | --- | --- | --- |
| Switch | 8.95 mm (same face, different net) | 0.301 mm (MX inner pad chamfer vs other face's MX hole) | **-0.16 mm** (overlap) | n/a (NPTH) | 4 hole-to-hole, see below |
| Switch, MX pads vs Choc pads, same face | 3.74 mm | MX 0.301 / Choc 0.356 mm to any hole | | | none |
| Controller | 0.30 mm (jumper gap) | 0.54 mm | 0.74 mm | 0.20 mm (via-pads) | none |
| nice!view | 0.30 mm (jumper gap) | 1.19 mm | 1.54 mm | 0.35 mm | none |
| MSK12C02 | 0.60 mm | 0.95 mm | 2.15 mm | | none |
| TS-1186F | 1.20 mm | 1.00 mm | 1.00 mm | | none |
| JST PH THT | 0.80 mm | 1.03 mm | 1.25 mm | 0.225 mm | none |

The 4 switch violations are known and accepted:

- **MX socket holes overlap by 0.16 mm** (3.0 mm drills 2.84 mm apart, at (±3.81, 2.54) and (∓2.54, 5.08)). This is inherent to every reversible MX hot-swap footprint: ceoloide `switch_mx` reversible and the mass-produced Lily58 Pro have the same overlap. The fab drills a figure-8 hole. JLCPCB's DFM check may query it; answer "intended".
- **Peg slot to MX hole web is 0.39 mm** (< 0.5 mm). ceoloide `switch_mx` has the same 0.39 mm. These are NPTH in FR4 with no copper, so the only risk is a fragile web.

## Paper test

`test-print/test-sheet.pdf`, A4 landscape, 2 pages, black and white:

- Page 1: KiCad F side seen from F, which is the top of the LEFT half and the underside of the RIGHT half.
- Page 2: KiCad B side seen from B (plotted mirrored), which is the underside of the LEFT half and the top of the RIGHT half (face A, with the SOD-123 diodes).
- Each page has a 2 x 2 block of keys at 19.05 mm pitch, the controller, the nice!view header, power switch, reset and JST, and a 50 mm horizontal and 50 mm vertical scale bar.

Print at **100 % / actual size**, no fit-to-page. Measure both 50 mm bars before trusting anything else. Then on **both pages**:

1. Lay a Kailh MX socket on the MX pads and a Kailh Choc socket on the Choc pads of each key. The socket bosses should sit on the hole circles and the solder tabs on the pads.
2. Push an MX switch (pins through the paper at the MX holes, rotated so its pins sit in the +y half, i.e. LED window facing away from the Choc pads) and a Choc V1 and a Choc V2 switch. Check the centre posts and pegs line up with the holes and slots. **Check whether your Choc V2 has a corner leg**; there is no hole for it (see below).
3. Check that a socket on one key does not cover the diode on page 2, and that switch housings clear the diode position on the top face of the right half.
4. Push the controller with its sockets or pins through the 24 holes, component side up and USB towards the top of the page. Check every hole lines up and that the pin labels on the silk match the pins printed on your controller, on both pages.
5. Lay the nice!view on its header holes and check the pin order (MOSI, SCK, VCC, GND, CS from left on page 1).
6. Check the MSK12C02, TS-1186F and JST footprints against the parts.

## Unverified / needs physical check

1. **Whole switch footprint**: socket fit on both faces for both socket types. This is the WP5 acceptance test and the main project risk.
2. **Choc V2 corner leg.** Some Choc V2 parts have a leg at (∓5.0, +5.15) mm. That spot is under the MX socket's inner pad on the same face, so there is **no hole** for it. A V2 switch with that leg may not sit flat until the leg is clipped. Check with the real switch.
3. **MX switch location.** The 5.0 mm centre hole (for the Choc V2 post) is 1 mm larger than the MX post, and the peg slots allow about 0.4 mm of x play. MX alignment therefore relies on the plate and the socket. Check that the paper fit feels right.
4. **Socket outlines** on Fab and courtyard layers are approximate bounding boxes, not datasheet drawings. The Choc-to-diode courtyard gap is 0.03 mm.
5. **nice!view header order and orientation**: MOSI, SCK, VCC, GND, CS from the left, seen from the top of the left half. This comes from ceoloide's footprint (reference only); the nicekeyboards pinout is an image. The footprint is symmetric, but if the real order is reversed, the LEFT/RIGHT jumper labels would be wrong. Check against the real display before fab.
6. **Battery holes B+/B-**: position (x = ±1.27, y = -15.24) and whether they are needed at all. The plan asked for them. The nice!nano docs say the battery pads are on the top of the module, which a socket cannot reach, and that RAW/B+ is the battery pin. Confirm on the bought controllers. Otherwise leave them unrouted and unbridged, or delete them.
7. **SuperMini pinout.** It is assumed identical to the nice!nano on the 24 Pro Micro pins (ZMK builds it as `nice_nano`), including RAW = battery+. Measure the bought boards (plan risk list).
8. **Socket hole size.** The 1.0 mm drill for machine-pin sockets, and whether low-profile socket strips (about 2.5 mm wide) clear the inner jumper pads by the assumed 0.45 mm.
9. **Jumper size.** The 0.9 x 1.25 mm pads with a 0.3 mm gap: confirm they are easy to bridge with an iron and easy to clear again.
10. **MSK12C02**: that pin 2 is the common, the actuator side, and that the lengthened pads still suit the part.
11. **TS-1186F-B-A is provisional.** The land pattern was read by eye from the scanned XKB drawing. The pin 1+2 / 3+4 pairing comes from its circuit diagram. The actuator direction relative to the pads is assumed.
12. **JST two-pair layout.** A connector pushed into the other face's pair has reversed polarity; follow the `USE THIS PAIR` silk. **Battery lead polarity varies by vendor**: check it against the `+`/`-` silk before plugging in.
13. **JLCPCB rule values** are assumed (0.2 mm hole to copper, 0.5 mm hole to hole). Confirm on jlcpcb.com on the day of ordering.
14. **Face convention** (LEFT = KiCad F up, diodes on KiCad B) must match what WP4 and WP7 do.
