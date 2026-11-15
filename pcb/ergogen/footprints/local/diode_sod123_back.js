// SOD-123 diode, SMD, placed on KiCad B.Cu (face A: JLCPCB assembles the bottom side).
// Pad geometry from KiCad stock D_SOD-123 (pads 0.9 x 1.2 mm at +-1.65 mm).
// Pad 1 = cathode (band, towards -x), pad 2 = anode (towards +x).
// Long axis along local x: placed between vertically adjacent keys, across the column.
// Params: from = anode net (switch pad 2), to = cathode net (row).
module.exports = {
  params: {
    designator: 'D',
    from: undefined,
    to: undefined
  },
  body: p => `
  (footprint "corne_reversible:D_SOD-123_Back"
    (layer "B.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 1.6 ${p.r}) (layer "B.SilkS") ${p.ref_hide} (effects (font (size 0.9 0.9) (thickness 0.15)) (justify mirror)))
    (attr smd)
    (fp_line (start -2.25 1.1) (end -2.25 -1.1) (stroke (width 0.12) (type solid)) (layer "B.SilkS"))
    (fp_rect (start -2.35 -1.15) (end 2.35 1.15) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (fp_rect (start -1.4 -0.85) (end 1.4 0.85) (stroke (width 0.1) (type solid)) (fill none) (layer "B.Fab"))
    (pad "1" smd roundrect (at -1.65 0 ${p.r}) (size 0.9 1.2) (layers "B.Cu" "B.Mask" "B.Paste") (roundrect_rratio 0.25) ${p.to.str})
    (pad "2" smd roundrect (at 1.65 0 ${p.r}) (size 0.9 1.2) (layers "B.Cu" "B.Mask" "B.Paste") (roundrect_rratio 0.25) ${p.from.str})
  )
  `
}
