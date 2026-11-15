# case (WP6)

Parametric 3D-printed bottom tray and switch plate for one half of the reversible Corne-layout board, MX first, 42-key and 36-key variants, plus MX test plates. Only the MX tolerance test plate has been printed (14.0 mm holds firmly); see [Unverified](#unverified).

**Tool: OpenSCAD 2021.01** (installed here, imports the Ergogen DXF outlines natively, headless STL export, fast: all parts render in about 15 s). CadQuery was not needed. Newer OpenSCAD versions should work too.

## Contents

| Path | What |
| --- | --- |
| `corne_case.scad` | All parts and parameters. Select a part with `-D 'part="..."'` |
| `geometry.scad` | **Generated** key centres, mounting holes, controller/reset/switch/JST positions and the DXF path. Do not edit |
| `tools/gen_geometry.py` | Regenerates `geometry.scad` from `pcb/ergogen/preview/points.yaml` and `config.yaml` (PyYAML) |
| `tools/check.py` | Self-check (OpenSCAD, PyYAML, shapely): alignment and clearance |
| `tools/export_all.sh` | Renders every STL into `stl/` |
| `stl/` | Exported parts, about 0.5 MB each (ASCII STL from OpenSCAD 2021.01) |

## Regenerate

```sh
cd pcb/ergogen && npx -y ergogen@4.2.1 . -o output --clean --debug --svg && cd ../..   # only if the layout changed
python3 case/tools/gen_geometry.py          # add --src pcb/ergogen/output to use a fresh Ergogen run
sh case/tools/export_all.sh                 # STLs
python3 case/tools/check.py                 # verification
```

A single part: `openscad -D 'part="tray_42_left"' -o stl/tray_42_left.stl case/corne_case.scad`. Any parameter can be overridden the same way, for example `-D cutout_tol=0.1 -D batt_t=4.3 -D 'switch_type="choc"'`.

## How alignment with the PCB is ensured

- The Ergogen DXF outlines (`plate_*`, `tray_*`, `board_*`) are **not** normalised to their own bounding boxes. WP4's README says they are; the DXF files are not (the SVGs were not checked). They are written in the Ergogen frame (y up, origin = centre of the outer-column bottom key), the same frame as `points.yaml`: the mounting-hole circles in `plate_42.dxf` sit exactly at H1..H5 and the reset circle in `tray_42_left.dxf` exactly at the reset centre (0.0000 mm deviation, checked by `check.py`). So no offset is applied anywhere.
- `corne_case.scad` imports `tray_<n>.dxf` directly from `pcb/ergogen/preview/` (the committed copy of the Ergogen output; identical to a fresh `output/` run at the time of writing) for the outer outline of both tray and plate. Key centres, rotations and hole centres come from `points.yaml` and the `config.yaml` anchors through `gen_geometry.py`, so they cannot drift from the PCB. Re-run Ergogen and the two generators after any layout change.
- The tray's `wall` (2.0 mm) must match `wall` in `config.yaml`; the plate is the tray outline (PCB plus 2.0 mm) so plate and tray edges are flush.

## Parts

All coordinates are the left half seen from above (KiCad F side up). Sizes are for the 42-key variant; 36-key is 21.05 mm narrower in x.

| STL | Print | Size (mm) | Notes |
| --- | --- | --- | --- |
| `plate_42.stl`, `plate_36.stl` | left half plate | 150.28 x 88.01 x 5.0, 129.22 x 88.01 x 5.0 | 21 / 18 cutouts, 5 screw posts, controller/display window, USB notch |
| `plate_42_right.stl`, `plate_36_right.stl` | right half plate | same | already mirrored, plus the reset-button window |
| `tray_42_left.stl`, `tray_36_left.stl` | left half tray | 150.28 x 88.01 x 11.4, 129.22 x 88.01 x 11.4 | reset press hole and guide tube |
| `tray_42_right.stl`, `tray_36_right.stl` | right half tray | same | already mirrored, no press hole, socket keep-outs mirrored differently |
| `test_plate_mx.stl` | MX fit test | 60.1 x 22.0 x 1.5 | three 14.0 mm cutouts (`cutout_tol` shifts all three) |
| `test_plate_mx_tolerance.stl` | tolerance test | 60.1 x 27.0 x 1.5 | 13.9 / 14.0 / 14.1 mm cutouts, marked with 1 / 2 / 3 small holes below each |

### Mirroring rules for the right half

Plain mirroring in the slicer is **not** enough, because the halves differ in three ways, so the right-half STLs are exported separately and are **already mirrored: print them as exported, do not mirror them again**. (If you ever need another symmetric part, mirror it in the slicer.)

1. **Reset button (TS-1187A, face A, KiCad B).** Left half: it faces down, the tray has a 3.0 mm press hole under it plus a guide tube so a pin or bent paper clip reaches it, and the plate covers it. Right half: it faces up beside the controller, there is no press hole, and the plate has a window over it (`plate_*_right`).
2. **Socket pads are not mirrored.** The switch pins are fixed in the world, so on the right half the underside pads sit at the same offsets from the key as on the left, not mirrored. The bosses are shaped around the socket pads (keep-out of pad plus 0.25 mm, MX and Choc pads both), so the right tray's bosses differ from a mirrored left tray. Everything fixed to the board (outline, holes, controller, power switch, JST, USB) is mirrored.
3. **Diodes (face A)** face down on the left and up on the right. For MX this does not matter (plate 3.5 mm above the PCB, diodes 1.1 mm). For a later Choc plate, `plate_*_right` gets shallow diode pockets in its underside (parameters `diode_h`, `diode_pocket`).

## Parameters (top of `corne_case.scad`)

| Parameter | Default | Meaning |
| --- | --- | --- |
| `switch_type` | `"mx"` | `"choc"` switches to 13.8 mm cutouts, 1.2 mm plate, 2.2 mm above PCB, diode pockets on the right half. Untested, not exported |
| `mx_cutout`, `mx_plate_t`, `mx_above_pcb` | 14.0, 1.5, 5.0 | From the plan |
| `choc_cutout`, `choc_plate_t`, `choc_above_pcb` | 13.8, 1.2, 2.2 | From the plan |
| `cutout_tol` | 0.0 | Added to the cutout size. Confirmed 2026-11-15: 14.0 mm holds an MX switch firmly on the owner's printer |
| `pcb_t` | 1.6 | PCB thickness |
| `wall`, `fit` | 2.0, 0.3 | Tray wall (= Ergogen `wall`); cavity is PCB plus `fit` per side, so the wall is 1.7 mm thick |
| `floor_t`, `under_pcb` | 2.0, 3.0 | Floor and the clearance below the PCB (the plan requires at least 2.5) |
| `batt_w`, `batt_l`, `batt_t` | 20, 30, 5.0 | Battery. `docs/bom.md` cells with a JST PH lead measure about 20 x 27-28 x 4.2-4.3 mm, so they fit; a 401230 cell (12 mm wide) would too. Set `batt_t = 4.3` to lower the whole tray by 0.7 mm |
| `batt_clear`, `batt_top`, `batt_skin` | 0.5, 0.5, 0.8 | Pocket clearance in xy; clearance between battery top and PCB underside (trim socket tails); floor left under the pocket |
| `pcb_bottom` | derived | `max(floor_t + under_pcb, batt_skin + batt_t + batt_top)` = 6.3 mm. So the general under-PCB clearance is 4.3 mm, not 3.0 mm, because the battery pocket sets the PCB height |
| `boss_od`, `insert_d`, `insert_len` | 6.0, 3.2, 4.0 | Insert bosses at the 5 mounting holes. Insert hole 3.2 mm for an M2 insert of 3.5 mm OD, 3 to 4 mm long; hole is 0.5 mm deeper than the insert |
| `h4_insert`, `h4_pilot_d` | false, 1.8 | H4 gets a 1.8 mm pilot hole for a self-tapping M2 screw instead of an insert (see Unverified 2) |
| `pad_margin` | 0.25 | Bosses keep this far from the socket copper |
| `screw_clear`, `post_od`, `csk` | 2.4, 4.4, false | Plate screw hole, plate posts that press the PCB on the bosses (3.5 mm long for MX), optional countersink |
| `usb_w`, `usb_z0` | 13, 1.0 | USB-C slot width; slot bottom above the PCB top |
| `pwr_w`, `pwr_h`, `jst_w`, `jst_h` | 10, 4.0, 10, 6.0 | Right-wall openings for the power switch and the JST housing (assumed sizes) |
| `reset_hole_d`, `reset_pillar*` | 3.0, on | Press hole and the guide tube (OD 4.6) ending 0.3 mm below the button actuator |
| `win_w`, `win_bottom`, `win_top`, `reset_win_margin` | 21, header y - 3.25, controller y + 16, 1.2 | Plate window over controller and nice!view; reset window margin on the right half |

## Design summary

- **Stack (left half, bottom to top):** floor 2.0, air and sockets, PCB bottom at z = 6.3, PCB 1.6, 3.5 mm gap, plate 1.5 mm. PCB top to plate top is 5.0 mm. Total height 12.9 mm including the plate (tray 11.4 mm).
- **Plate support:** plate underside rests on the tray walls (wall top at z = 11.4) and on 5 posts (OD 4.4, 3.5 mm) that press the PCB onto the bosses around the M2 holes. The posts sit in the 5 mm webs between the switch cutouts (0.32 mm minimum gap to a cutout), checked.
- **Tray:** floor, 2 mm walls following the Ergogen tray outline, bosses, battery pocket (21 x 31 mm, floor 0.8 mm) under the controller, reset guide tube, right-edge openings.
- **Edge openings:** USB-C at the top edge over the controller (13 mm wide, open at the top, with a matching notch in the plate); power switch and JST openings in the right wall at the Ergogen y of each part. The JST opening runs through the floor in the wall zone, because a 6 mm housing plus the battery pocket needs more depth than the floor provides.
- **Plate window:** one 21 mm wide opening from below the nice!view header up past the USB end of the controller; on the right half it is joined by the reset window.

## Print settings

- **Tray:** PETG, 0.2 mm layers, 4 perimeters, 20 to 30 % infill, floor on the bed, no supports (slots are open at the top or bottom, the reset hole and insert holes are vertical).
- **Plate:** PLA or PETG, 0.2 mm layers, 4 perimeters, 100 % or 5 solid top/bottom layers (it is only 1.5 mm thick). **Exported upside down: top face on the bed, screw posts pointing up**, so no supports and a clean visible face. Tune `cutout_tol` for the elephant foot of the first layer.
- **Test plates:** print first, same material and settings as the plate. Press an MX switch in from the top: it must click in and not fall out when the plate is turned over, and must not need force. If it is loose, use the next smaller cutout; if tight, the next larger; then set `cutout_tol` (for example `-0.1`) and re-export.
- Print the halves with the correct file each: left set `*_left`/`plate_42`, right set `*_right`.

## Assembly order

1. Solder sockets, controller sockets, power switch, battery connector and display header to the PCB underside as in WP5/WP7 (the underside is KiCad B on the left half, KiCad F on the right). Trim the socket and header tails flush so the battery clears them. For 36 keys, break off the outer column and tab first.
2. Press the 4 M2 heat-set inserts into the bosses (H1, H2, H3, H5) from above with a soldering iron at about 220 to 240 C (PETG), until flush with the boss top. H4 takes no insert (self-tapping, see Unverified).
3. Place the battery in the pocket (foam tape under it), plug the JST connector, check polarity against the board marking, and route the lead through the JST opening or the gap between pocket and connector.
4. Lay the PCB on the bosses (its holes over the inserts), fit the controller and display on their sockets.
5. Place the plate on top (posts through the gap onto the PCB, plate on the wall tops), fit the 5 screws: M2 x 10 mm pan or cheese head (3.4 mm into the insert). M2 x 12 would bottom out. Do not overtighten.
6. Press the switches in (MX into the plate cutouts; they click into the hot-swap sockets).

## Self-check output

`python3 case/tools/check.py` renders sections of the real model (plate mid-plane, tray at boss height and in the floor) to DXF and compares them with `points.yaml`, the `config.yaml` anchors and the Ergogen DXFs; tolerance 0.05 mm. Output at the time of commit (the last two lines need a fresh Ergogen `output/`, otherwise they are skipped):

```text
PASS  Ergogen plate_42.dxf cutouts vs points.yaml: 21 expected, 21 found, max deviation 0.0000 mm
PASS  Ergogen plate_42.dxf holes vs config anchors: 5 expected, 5 found, max deviation 0.0000 mm
PASS  Ergogen plate_36.dxf cutouts vs points.yaml: 18 expected, 18 found, max deviation 0.0000 mm
PASS  Ergogen plate_36.dxf holes vs config anchors: 5 expected, 5 found, max deviation 0.0000 mm
PASS  Ergogen tray_42_left.dxf reset hole vs config anchor: 1 expected, 1 found, max deviation 0.0000 mm
PASS  slice_plate_42 cutout centres vs Ergogen key centres: 21 expected, 21 found, max deviation 0.0000 mm
PASS  slice_plate_42 screw holes vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_plate_36 cutout centres vs Ergogen key centres: 18 expected, 18 found, max deviation 0.0000 mm
PASS  slice_plate_36 screw holes vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_plate_42_right cutout centres vs Ergogen key centres: 21 expected, 21 found, max deviation 0.0000 mm
PASS  slice_plate_42_right screw holes vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_plate_42: screw posts (OD 4.4) clear of every switch cutout, smallest gap 0.32 mm
PASS  slice_plate_36: screw posts (OD 4.4) clear of every switch cutout, smallest gap 0.32 mm
PASS  plate_42 (left) open over the controller
PASS  plate_42 (left) covers the reset button (button faces down)
PASS  plate_42_right open over the reset button (faces up)
PASS  plate_42_right open over the controller
PASS  slice_tray_42_left insert/pilot holes (3.2 mm, H4 1.8 mm) vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_tray_42_left reset press hole vs Ergogen: 1 expected, 1 found, max deviation 0.0000 mm
PASS  slice_tray_36_left insert/pilot holes (3.2 mm, H4 1.8 mm) vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_tray_36_left reset press hole vs Ergogen: 1 expected, 1 found, max deviation 0.0000 mm
PASS  slice_tray_42_right insert/pilot holes (3.2 mm, H4 1.8 mm) vs mounting holes: 5 expected, 5 found, max deviation 0.0000 mm
PASS  slice_tray_42_right has no reset press hole
INFO  slice_tray_42_left: boss wall around the insert hole (H1..H5), thinnest per boss: 1.39, 0.80, 1.39, 0.82, 1.39 mm
PASS  slice_tray_42_left: every boss keeps at least 0.6 mm of wall around its hole (min 0.80)
INFO  slice_tray_42_right: boss wall around the insert hole (H1..H5), thinnest per boss: 0.60, 1.39, 0.60, 0.82, 1.39 mm
PASS  slice_tray_42_right: every boss keeps at least 0.6 mm of wall around its hole (min 0.60)
PASS  slice_tray_42_left: bosses clear of B.Cu socket/diode pads from the PCB file, smallest gap 0.25 mm
PASS  slice_tray_42_right: bosses clear of F.Cu socket/diode pads from the PCB file, smallest gap 0.25 mm

ALL CHECKS PASSED
```

## Unverified

1. **Only the tolerance test plate is printed.** WP6 acceptance check passed 2026-11-15: the owner's print of `test_plate_mx_tolerance.stl` holds an MX switch firmly at the 14.0 mm cutout, so `cutout_tol` stays 0.0. Screw posts, heat-set inserts and all other clearances are still by calculation only.
2. **H4 mounting hole is squeezed by sockets.** H4 (85.725, -22.645) sits 2.1 mm from the corner of one socket pad and 2.4 mm from another. A 3.2 mm insert would leave a 0.1 mm wall, so H4 uses a 1.8 mm pilot hole for a self-tapping M2 screw (boss wall 0.82 mm) instead of an insert, which departs from "5 inserts". Alternatives: move H4 about 2 mm down in WP4/WP7, or set `h4_insert = true` and accept a paper-thin boss. Also the thinnest remaining boss walls around 3.2 mm inserts are 0.8 mm (left H2) and 0.6 mm (right H1 and H3): marginal for heat-set inserts. This is a layout issue to look at before the PCB order.
3. **Socket pad keep-outs** use only the copper pads of the B-side hot-swap footprint plus 0.25 mm. The real Kailh socket bodies and solder joints may reach further; the clearance is unverified.
4. **Insert dimensions** (M2, 3.5 mm OD, 3 to 4 mm long, 3.2 mm hole) are the common values, not a specific product. Check the datasheet of the inserts you buy and set `insert_d` / `insert_len`.
5. **Battery size**: 20 x 30 x 5 mm assumed (task default); no 401230 pack with a PH lead was found in WP3. The pocket sets the PCB height (`pcb_bottom` 6.3 mm); with a 4.3 mm cell set `batt_t = 4.3`.
6. **Controller height and USB-C**: the USB slot (13 mm wide, 1.0 mm above the PCB top, open at the top) assumes the module sits on pin sockets and the connector is above the PCB top; the real USB-C overhang and height were not measured (WP4 also did not measure it). Check cable plug fit.
7. **Power switch and JST openings** (10 mm wide, 4.0 and 6.0 mm tall) are assumptions from the footprints; the MSK12C02 actuator direction and the JST housing height (6.0 mm assumed, 6.4 mm needed with clearance) were not measured. With the default `pcb_bottom` the JST opening cuts through the floor in the wall zone. Mind the polarity caveat in `docs/bom.md`.
8. **Plate window over the nice!view**: the window width 21 mm and extent are by eye. The module is expected to sit above the plate on its header; its real size (WP4 note: about 40 mm wide) and height were not checked. No controller cover or tenting feet were made (optional in the plan).
9. **Reset guide tube**: the TS-1187A actuator height 1.5 mm, 0.3 mm gap and a 3.0 mm hole are assumed; a bent paper clip is expected, not a finger.
10. **PCB thickness 1.6 mm** assumed; a thicker board would make the screws pull the plate off the walls by the difference, a thinner one leave the posts short of the PCB. `pcb_t` shifts the wall height only; post length is fixed by `above_pcb - plate_t`.
11. **Choc parameter set** compiles (`-D 'switch_type="choc"'`) but is untested and not exported. MX plate cutouts have no side notches for switch removal.
12. **STL files** are ASCII and use 40-segment circles; DXF arcs are imported at OpenSCAD's default resolution.
13. Plate hole positions are the same Ergogen centres as the PCB, but PCB fab tolerance (about 0.1 mm) and print shrinkage are not compensated beyond `cutout_tol`.
