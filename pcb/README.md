# pcb

Reversible split PCB sources and fabrication outputs. Design rationale is in [the plan](../docs/plan.md#reversible-pcb-architecture).

- `ergogen/`: Ergogen config (key positions, outline, break-off tab, mounting holes, case outlines); see `ergogen/README.md`. Generated output goes to `ergogen/output/` and is not committed.
- `footprints/`: combined MX/Choc reversible socket, solder-jumper controller, nice!view header. Third-party footprints keep their own licences, recorded in `footprints/THIRD_PARTY.md`.
- `kicad/`: KiCad project, routed board, DRC.
- `fab/`: JLCPCB Gerbers, BOM and placement files.
