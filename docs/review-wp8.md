# WP8 pre-order review

Reviewed 15 Nov 2026 on branch `wp7-kicad` at commit `cdb7dbb`. Coordinates are KiCad board coordinates in mm (y down) unless stated.

## Verdict: DO NOT ORDER

One blocker: the placement file would have JLCPCB fit all 21 diodes backwards. The fix is one line in `pcb/kicad/tools/make_fab.py` and a regenerated CPL; no copper changes.

The board itself passes: the Gerbers and drill files match the board, the copper matches the stock ZMK `corne` pin map on both halves, and DRC has no errors. Once the CPL is corrected the order can go ahead under these conditions:

1. Regenerate the CPL with diode rotation 180 (D1 to D20) and 195 (D21), and confirm in JLCPCB's bottom-side placement preview that every diode's cathode band sits at the silkscreen bar.
2. Decide on the three should-fix items below. None of them stops a 42-key MX build from working.

## Blocker

### B1. CPL diode rotation is 180 degrees off

- **Evidence.** `pcb/fab/corne_reversible_cpl_jlcpcb.csv` gives rotation 0 for D1 to D20 and 15 for D21, all `Bottom`. On the board each diode is on B.Cu with orientation 0 (D21: -15), cathode pad 1 at local x = -1.65, on a `ROW` net. Example: D16 at (95.25, 7.62), pad 1 at (93.6, 7.62) on `ROW2`.
- **Why it is wrong.** JLCPCB's part C81598 (EasyEDA footprint `SOD-123F_L2.7-W1.6-LS3.8-RD`, read from the EasyEDA component API) has pad 1 = K at -x. For bottom-side parts the three tools I checked all use JLCPCB rotation = (180 - KiCad orientation) mod 360: [kicad-jlcpcb-tools](https://github.com/Bouni/kicad-jlcpcb-tools) `fabrication.py`, [Fabrication Toolkit](https://github.com/bennymeg/Fabrication-Toolkit) `process.py`, and KiBot's [`mirror_bottom`](https://kibot.readthedocs.io/en/latest/configuration/filters/rot_footprint.html) option ("used by JLCPCB"). That gives 180 and 195.
- **Where the error came from.** `make_fab.py` argues that the board's diode footprint "has the cathode at +x in its front-side form", so it adds 180. That is not how KiCad stores flipped footprints. I flipped KiCad's stock `D_SOD-123` to the back with `pcbnew`: it reports orientation 0 with pad 1 still at x = -1.65, identical to the diodes on this board. So the plain rule applies unchanged. The script's own polarity check uses the same formula, so it cannot catch this.
- **Effect if ordered as is.** Every diode has its anode on the row. With `col2row` no key registers on either half. A custom shield with `row2col` would rescue the boards, but the plan requires the stock shield.
- **Fix.** In `ref_angle`/`bom_cpl`, mirror the measured direction before subtracting the library angle: `rot = (180.0 - theta - phi) % 360.0` (and the same in `polarity`). Expected output: D1 to D20 = 180.0, D21 = 195.0, SW22 = 90.0 or 270.0 (equivalent). Then check the preview: JLCPCB has changed its bottom-side convention before, so the preview is the final authority.

## Should-fix

### S1. Break-line holes are drawn as outline circles, not drills

- **Evidence.** 38 circles of 0.6 mm diameter on Edge.Cuts at x = 9.525, y = -47.575 to 10.025 (`corne_reversible-Edge_Cuts.gm1`); none are in `corne_reversible-NPTH.drl`.
- **Risk.** JLCPCB mills outline features with a tool of about 1 mm; its [capabilities page](https://jlcpcb.com/capabilities/pcb-capabilities) lists non-plated slots from 1.0 mm and non-plated drills from 0.5 mm. A 0.6 mm circle in the outline file will be converted by hand, ignored, or queried. This is the most likely cause of a DFM hold.
- **Fix.** Replace the circles with 0.6 mm NPTH pads so they land in the NPTH drill file. Routing does not change (copper is already 0.31 mm clear).
- **Related, 36-key build only.** The perforation leaves three solid bridges of 4.2 to 5.4 mm (y = -43.7 to -39.5, -25.7 to -20.3, -6.5 to -1.1), and 0.6 mm of board between holes, against the 0.2 to 0.3 mm JLCPCB recommends. The Choc pads of the pinky column (F.Cu, x from 9.475) and of the outer column (B.Cu, x to 9.575) each cross the line by 0.05 mm. The tab will need a saw or deep scoring, not a snap. Four nets cross (`COL_D21`, `ROW0`, `ROW1`, `ROW2`), not the single trace the plan describes; this is unavoidable with the diodes on the tab. With the tab removed every remaining net stays whole (checked).

### S2. Battery connector markings on the B face are unreadable

- **Evidence.** DRC warnings at (124.75, -24.505) and (126.3 to 126.75, -21.8 to -26.9): the B.SilkS text `USE THIS PAIR` lies over controller hole pads H14 to H17, `+` is printed on top of the `D8` pin label and `-` on top of `D6`. Confirmed in a render of the B face.
- **Risk.** The JST has two hole pairs with opposite polarity, one per face. On the right half (B up) the only cue for the correct pair and for polarity is this text. The wrong pair reverses the battery into the controller.
- **Fix.** Move the B-face `USE THIS PAIR`, `+` and `-` clear of the pads and pin labels (silk only). If not fixed, write the rule into the build notes: on face B use the pair at x = 126.75, `+` is the hole at y = -23.505.

### S3. Battery plug points out of the board edge

- **Evidence.** `BT1` at (129.75, -24.505), rotation 90. The S2B-PH-K housing outline runs x = 128.4 to 136.0 for the F-face pair and 125.4 to 133.0 for the B-face pair; the board edge is at x = 134.75. The plug enters from +x on both.
- **Risk.** The F-face connector overhangs the edge by 1.25 mm and the lead must leave the housing outside the board outline on both halves, then turn back to the battery under the controller. In the WP6 tray (wall inner face at x = 135.05) the lead loops through the wall opening, outside the case on the half that uses the F pair.
- **Fix.** Either rotate `BT1` so the plug faces the controller (needs re-routing of `BAT_P` and GND), or for v1 leave the housing off and solder the battery lead to the marked holes.

## Notes

- **Jumper mistakes.** Bridging both faces of one hole ties two nets: row 4 from the USB end shorts VCC to GND, row 1 puts the battery on P0.06. Bridging the wrong face only mirrors the whole pinout: battery + lands on the D1 pin and battery - on the VCC pin, which destroys the controller. No single hole ties RAW to GND. The `BAT+`/`BAT-` jumper pads are isolated copper, so bridging them does nothing. Before fitting the controller or battery, check with a multimeter: RAW to GND open, VCC to GND open, and each socket pin connected to the net named beside it.
- **Battery placeholder holes** `HB1`/`HB2` at (114.48, -49.745) and (117.02, -49.745) are not wired. On the nice!nano v2 the B+/B- holes are in line with the pin rows, not here, and the footprint's `B+`/`B-` labels are on the opposite sides to the module's. Ignore them. The battery reaches the controller through RAW, which the nice!nano v2 pinout labels BATTERY+.
- **No protection on the board.** There is no fuse, reverse-polarity or under-voltage protection. Use a cell with a built-in protection circuit. JST PH polarity differs between battery vendors: check against the `+` mark before plugging in. Charging only works with the power switch on.
- **Battery under the controller.** The WP6 tray leaves 0.5 mm between the cell and the trimmed socket pins. Put Kapton or fish paper between them.
- **Expected DFM questions.** 42 pairs of overlapping 3.0 mm socket holes (centres 2.84 mm apart, normal for reversible MX footprints); 42 short slots of 2.32 x 1.9 mm; a 0.39 mm web between each slot and the nearest socket hole. Answer "intended".
- **Order form.** Assemble Bottom side only. Seven diodes (D1, D4, D7, D10, D19, D20, D21) have pads 1.4 mm from the board edge, so let JLCPCB add edge rails and fiducials.
- **Silkscreen.** Text is 0.9 mm high, under JLCPCB's recommended 1.0 mm. On the B face the pin labels D2 to D8 sit under the reset button and the JST pads. The F face is clean.
- **Switch footprint.** The centre hole is 5.0 mm (MX post is 4.0 mm), so MX switches are located by the plate and the socket only. There is no hole for the Choc V2 corner leg; clip it. A Choc socket on the diode face clears the diode body by about 0.5 mm.
- **Power switch.** The MSK12C02 actuator ends at x = 134.4, 0.35 mm inside the board edge, so it is recessed behind the tray wall.
- **Antenna.** No copper pour. About a third of the area under the last 6 mm of the controller is signal copper (jumper pads and links), which the jumper scheme makes unavoidable.
- **Part package.** JLCPCB's footprint for C81598 is SOD-123F (flat lead, 3.8 mm span). The board's pads (0.9 x 1.2 mm at +-1.65) cover it.

## What I verified and how

| Item | Method | Result |
| --- | --- | --- |
| Fab files match the board | Re-exported Gerbers and drill with `kicad-cli` 10.0.6 using the same options, compared with `pcb/fab/gerbers` ignoring date lines; unzipped the archive and compared | 11 of 11 identical; zip equals folder |
| Copper connectivity | Own script: parsed the `.kicad_pcb`, built pad, track and via shapes with shapely, joined touching copper per layer and through plated holes, ignoring net names | 88 copper islands, none carrying two net names; no net split; nothing closer than 0.2 mm |
| Pin map, left half | Same script, joining all copper exposed in each F-face jumper mask window, then tracing each controller hole by its Pro Micro position (module face up, USB at -y) | Columns outer to inner on D21, D20, D19, D18, D15, D14; rows top to thumb on D4, D5, D6, D7; thumbs on D18, D15, D14 |
| Pin map, right half | Same with the B-face windows and the view mirrored | Identical pins per physical column, which is what `corne_right.overlay` expects (14, 15, 18, 19, 20, 21 from the inner column) |
| ZMK source | Read `corne.dtsi`, `corne_left.overlay`, `corne_right.overlay`, the nice!nano pin map and the `nice_view_adapter` overlay at the pinned revision `4de3133` (same as `main` today) | `col2row`, pins as above, display CS on D1, MOSI D2, SCK D3 |
| Diode direction on the board | Each switch pad 2 island holds exactly one diode pad 2; that diode's pad 1 island reaches a row pin | 21 of 21, cathode to row |
| Power, reset, display | Traced islands | JST pin 2 to switch pin 1; switch pin 2 to RAW; JST pin 1, reset pads 2 and three controller GND pins on GND; reset pads 1 on RST; header reads MOSI, SCK, VCC, GND, CS from the left on each half's top face |
| Controller and display pinouts | nice!nano v2 and nice!view pinout images from nicekeyboards.com | Match, including RAW = BATTERY+ and the header order with the display over the controller |
| Jumper hazards | Bridged both faces in the script and listed the tied nets | As in the notes above |
| Switch footprint | Compared pads and holes with daprice `Kailh_socket_PG1350_reversible` and `Kailh_socket_MX` | Choc pads and holes identical (rotated 180); MX holes identical, MX pads 0.45 mm closer to the holes (the other common land pattern) |
| Controller footprint | Pad coordinates | 2 x 12 holes, 2.54 mm pitch, rows 15.24 mm apart, 1.0 mm drill |
| TS-1187A | XKB datasheet rev A2 and the EasyEDA footprint for C318884 | Pads match (+-3.0, +-1.875); the internally joined pins are the pair along the lead direction, as wired; rotation 90 is right |
| JST, power switch | Compared with KiCad's stock `JST_PH_S2B-PH-K` footprint; pad pattern of MSK12C02 | Each face's pair has pin 1 = GND with the housing on that face; switch pads mirrored per face |
| BOM and CPL contents | Parsed both CSVs against the board | 22 parts, all on B.Cu, positions equal the pad centroids with y negated; no other part listed; B paste has 46 openings, F paste none |
| DRC | `kicad-cli pcb drc --severity-all` | 0 errors, 0 unconnected, 60 warnings: 42 overlapping socket holes, 17 silkscreen (S2 and the notes), 1 library mismatch on SW22 (fields only) |
| Outline | Polygonised Edge.Cuts | One closed outline, 146.28 x 84.01 mm; copper at least 0.34 mm from it; mounting holes at least 1.9 mm from it |
| Case fit | Compared `case/geometry.scad` with the board | Five M2 holes, controller, display, reset, switch and JST positions and the outline bounding box agree exactly |

## What I could not verify

- JLCPCB's live behaviour for bottom-side rotation. The rule in B1 comes from three independent tools, not from a JLCPCB document. Only the placement preview settles it.
- Stock and Basic status of C81598 and C318884 on the day of ordering.
- Physical fit of sockets, switches, controller and display. I compared coordinates with published footprints; I did not handle parts, and I did not open the Kailh socket datasheets.
- The pinout of the SuperMini clones. Only the nice!nano v2 was checked.
- MSK12C02 pin numbering and actuator side (taken from the footprint, not a datasheet).
- That the firmware builds, and that the Ergogen config regenerates this board. Neither was run.
- Printed case parts.
