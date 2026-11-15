# corne-reversible

A wireless Corne-layout split keyboard built on one reversible PCB: the same board is used face-up for the left half and flipped for the right, so a single JLCPCB order of 5 boards covers two keyboards and a spare.

- 3x6+3 (42 keys), with a break-off outer column for 36 keys
- Hot-swap sockets for Kailh MX or Kailh Choc on the same footprint
- Pro Micro-footprint nRF52840 controller (nice!nano v2 or clone), ZMK firmware
- JLCPCB fits the diodes; everything else is hand-soldered
- 3D printed case and plate

Status: planning. Nothing has been fabricated or tested yet.

## Documents

- [Design and build plan](docs/plan.md)
- [Work packages](docs/work-packages.md)

## Layout

| Folder | Contents |
| --- | --- |
| `docs/` | Plan, work packages, build notes |
| `pcb/` | Ergogen config, KiCad project, fabrication outputs |
| `firmware/` | ZMK config and keymap |
| `case/` | Parametric case and plate sources, printable files |
