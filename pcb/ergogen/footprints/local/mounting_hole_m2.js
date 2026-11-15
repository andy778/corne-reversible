// M2 mounting hole, 2.2 mm NPTH, no copper on either face.
module.exports = {
  params: { designator: 'H' },
  body: p => `
  (footprint "corne_reversible:MountingHole_2.2mm_M2"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 -3 ${p.r}) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))))
    (attr exclude_from_pos_files exclude_from_bom)
    (fp_circle (center 0 0) (end 1.4 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
    (fp_circle (center 0 0) (end 1.4 0) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (pad "" np_thru_hole circle (at 0 0 ${p.r}) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask"))
  )
  `
}
