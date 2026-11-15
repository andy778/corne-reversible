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
