# pcb

Reversible split PCB sources and fabrication outputs. Design rationale is in [the plan](../docs/plan.md#reversible-pcb-architecture).

- `ergogen/`: Ergogen config (key positions, outline, break-off tab, mounting holes, case outlines); see `ergogen/README.md`. Generated output goes to `ergogen/output/` and is not committed.
- `footprints/`: combined MX/Choc reversible socket, solder-jumper controller, nice!view header. Third-party footprints keep their own licences, recorded in `footprints/THIRD_PARTY.md`.
- `kicad/`: KiCad project, routed board, DRC report and netlist check; see `kicad/README.md`.
- `fab/`: JLCPCB Gerbers, drill, BOM and placement files and previews (assemble the bottom side); see `fab/README.md` for the pre-order checklist.
