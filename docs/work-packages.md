# Work packages

Each package lands as its own branch and pull request. The model column is the cheapest model expected to do the package well; the hard, expensive-to-get-wrong work is kept for the stronger models.

| ID | Package | Output | Model | Depends on |
| --- | --- | --- | --- | --- |
| WP1 | Repo scaffold | Folder READMEs, licence, CI skeleton | Haiku | none |
| WP2 | ZMK config | `firmware/` with `build.yaml`, stock Corne shield, starter keymap, GitHub Actions build | Haiku | none |
| WP3 | BOM verification | `docs/bom.md` with current JLCPCB and LCSC part numbers, stock, basic or extended status, hand-solder part choices | Sonnet | none |
| WP4 | Ergogen layout | `pcb/ergogen/` config: key positions, outline, break-off tab, mounting holes, case outlines | Sonnet | WP5 footprints for final output |
| WP5 | Footprints | Combined reversible MX and Choc socket footprint, solder-jumper controller footprint, nice!view header | Opus | none |
| WP6 | Case and plate | `case/` parametric source for tray and plate, MX first, 42-key and 36-key variants | Sonnet | WP4 outlines |
| WP7 | KiCad routing and fabrication outputs | Routed board, DRC clean, Gerbers, BOM and placement files | Opus | WP3, WP4, WP5 |
| WP8 | Pre-order review | Independent check of footprints, netlist against the Corne pin map, diode polarity and placement | Fable | WP7 |

## Acceptance checks

- **WP2:** GitHub Actions produces left and right `.uf2` files.
- **WP3:** every part has a link to its source page and the date it was checked.
- **WP4:** Ergogen runs without errors and the outline matches MX spacing of 19.05 mm.
- **WP5:** footprints pass a 1:1 paper test-fit with real sockets, switches and controller on both faces.
- **WP6:** a three-cutout test plate holds an MX switch firmly.
- **WP7:** KiCad DRC is clean against JLCPCB 2-layer rules.
- **WP8:** written sign-off before any money is spent.

## Status

Updated 2026-11-16. All eight packages are merged to `main`.

| ID | Pull request | Acceptance check | Status |
| --- | --- | --- | --- |
| WP1 | #1 | No check defined | Merged 2026-11-15 |
| WP2 | #2 | Left and right `.uf2` built in GitHub Actions | Passed. CI builds `corne_left.uf2` and `corne_right.uf2` (ZMK pinned to main at 4de3133 for `nice_nano//zmk`) |
| WP3 | #3, #5 | Every part has a source link and a check date | Passed. Every part in `docs/bom.md` has a link and was checked on 2026-11-15. #5 added the TS-1187A reset button to the JLCPCB-assembled parts |
| WP4 | #6 | Ergogen runs cleanly at 19.05 mm spacing | Passed. Ergogen 4.2.1 runs without errors, and `pcb/ergogen/check.py` confirms the 19.05 mm pitch. WP7 later moved mounting holes H1 to H4 |
| WP5 | #4 | 1:1 paper test-fit on both faces | Passed. The owner's paper test passed on 2026-11-15 |
| WP6 | #7 | Three-cutout test plate holds an MX switch | Passed. Holds firmly at a 14.0 mm cutout (`cutout_tol = 0`). The case was regenerated in #8 for the moved holes |
| WP7 | #8 | DRC clean against JLCPCB 2-layer rules | Passed. 0 errors, 0 unconnected, 69 reviewed warnings (see `pcb/kicad/README.md`). The netlist check passes |
| WP8 | #9 | Written sign-off before any money is spent | Review written (`docs/review-wp8.md`) with the verdict "do not order" over one blocker. That blocker (diode placement rotation) and two of the three should-fix items are fixed in #8. Sign-off is conditional on one more check: the JLCPCB bottom-side placement preview must show every diode's cathode band at its silk bar |

Open after WP8: the battery plug overhangs the board edge (WP8 S3; solder the lead directly for v1). Also not yet verified: the SuperMini clone pinout and the MSK12C02 pin numbering.
