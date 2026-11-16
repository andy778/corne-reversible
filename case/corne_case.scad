// Parametric case for the reversible Corne-layout board (WP6).
// OpenSCAD 2021.01 or newer.  Everything is in the Ergogen frame of WP4 (mm, y up, origin = centre of
// the outer-column bottom key), viewed from ABOVE the LEFT half (KiCad F side up).
//
//   openscad -D 'part="plate_42"' -o stl/plate_42.stl corne_case.scad
//
// part = plate_42 | plate_36 | plate_42_right | plate_36_right
//        tray_42_left | tray_36_left | tray_42_right | tray_36_right
//        test_plate_mx | test_plate_mx_tolerance
//        slice_* parts are 2D debug sections used by tools/check.py
//
// Outlines come from the WP4 Ergogen DXFs (../pcb/ergogen/preview/*.dxf, same frame as points.yaml, so no
// re-alignment is needed); key and hole positions come from geometry.scad (generated from points.yaml
// and config.yaml by tools/gen_geometry.py).

include <geometry.scad>

part = "plate_42";

// ---------------------------------------------------------------- switch type
switch_type = "mx";            // "mx" (deliverable) or "choc" (parameter set only, untested)

// MX
mx_cutout      = 14.0;         // square cutout
mx_plate_t     = 1.5;          // thickness at the clip
mx_above_pcb   = 5.0;          // PCB top to plate top
// Choc V1 (not exported, kept for a later plate)
choc_cutout    = 13.8;
choc_plate_t   = 1.2;          // 1.2 to 1.3
choc_above_pcb = 2.2;
diode_h        = 1.1;          // SOD-123 height; diode pockets only on the half where diodes face up (right)
diode_pocket   = [5.4, 3.2];   // pocket size, centred 9.525 mm below the key in the key frame

cutout_tol  = 0.0;             // added to the cutout size; tune after printing the test plate

is_mx       = switch_type == "mx";
cutout      = (is_mx ? mx_cutout : choc_cutout) + cutout_tol;
plate_t     = is_mx ? mx_plate_t : choc_plate_t;
above_pcb   = is_mx ? mx_above_pcb : choc_above_pcb;
post_h      = above_pcb - plate_t;       // plate underside to PCB top = length of the screw posts

// ---------------------------------------------------------------- PCB / tray
pcb_t       = 1.6;
wall        = 2.0;                       // must equal `wall` in pcb/ergogen/config.yaml (tray outline = PCB + wall)
fit         = 0.3;                       // cavity is the PCB outline + fit on every side
floor_t     = 2.0;                       // floor thickness
under_pcb   = 3.0;                       // floor top to PCB bottom, general area (>= 2.5 required)

// battery (task default 20 x 30 x 5; docs/bom.md cells are about 20 x 27-28 x 4.2-4.3)
batt_w = 20;  batt_l = 30;  batt_t = 5.0;
batt_clear  = 0.5;                       // on each side in xy
batt_top    = 0.5;                       // between battery top and PCB underside (socket tails, trim them)
batt_skin   = 0.8;                       // floor left under the battery pocket
batt_cy     = ctrl_pos[1] - 2;           // pocket centre y (under the controller)

// PCB underside level: either the general clearance or whatever the battery needs, whichever is larger
pcb_bottom  = max(floor_t + under_pcb, batt_skin + batt_t + batt_top);
wall_h      = pcb_bottom + pcb_t + post_h;   // wall top = plate underside
if (pcb_bottom - jst_h - 0.4 < batt_skin) echo("WARNING: JST housing is deeper than the floor pocket; check jst_h");

// M2 heat-set inserts and screws
boss_od     = 6.0;
pad_margin  = 0.25;                      // boss keeps this far from the socket pads (copper)
insert_d    = 3.2;                       // hole for an M2 insert of 3.5 mm OD (check your inserts)
insert_len  = 4.0;                       // insert length 3 to 4 mm
insert_deep = insert_len + 0.5;          // blind hole depth below the boss top
// WP7 moved H4 to 3.24 mm from the nearest socket pad, so it now takes an insert like H1-H3/H5.
// Set h4_insert = false to fall back to a 1.8 mm pilot hole for a self-tapping M2 screw.
h4_insert   = true;
h4_pilot_d  = 1.8;
hole_d      = [insert_d, insert_d, insert_d, h4_insert ? insert_d : h4_pilot_d, insert_d];
screw_clear = 2.4;                       // M2 clearance in plate and posts
post_od     = 4.4;                       // plate posts press the PCB onto the bosses
csk         = false;                     // true: countersink the plate screw holes (90 deg, 3.9 mm head)

// edge openings (all assumptions, see README)
usb_w       = 13.0;                      // USB-C plug overmould 12 plus clearance
usb_z0      = 1.0;                       // slot bottom above the PCB top
pwr_w       = 10.0;                      // MSK12C02 slide travel
pwr_h       = 4.0;                       // below the PCB
jst_w       = 10.0;                      // JST PH S2B-PH-K housing 8 wide plus clearance
jst_h       = 6.0;                       // housing height (unmeasured)

// reset button TS-1187A (face A, KiCad B)
reset_h       = 1.5;
reset_hole_d  = 3.0;                     // WP4 press hole diameter
reset_body    = [5.6, 7.5];              // courtyard in the world frame after the 90 degree rotation
reset_pillar  = true;                    // printed guide tube under the button so a pin can reach it
reset_pillar_od = 4.6;
reset_gap     = 0.3;                     // pillar top to button actuator

// plate windows
win_w       = 21.0;                      // controller / display window width, centred on the controller
win_bottom  = display_pos[1] - 3.25;     // below the nice!view header
win_top     = ctrl_pos[1] + 16.0;        // above the USB end of the module
reset_win_margin = 1.2;                  // added to the reset courtyard (right half only)

// test plates
test_pitch  = 19.05;
test_margin = 4.0;

$fn = 40;

function outline_file(kind, n) = str(dxf_dir, kind, "_", n, ".dxf");
module outline2d(kind, n) { import(outline_file(kind, n)); }

// ================================================================ plate
module cut_square(sz) { square(sz, center = true); }

module plate_windows(right) {
  // controller and nice!view
  translate([ctrl_pos[0] - win_w / 2, win_bottom]) square([win_w, win_top - win_bottom]);
  // USB-C notch through the top edge
  translate([ctrl_pos[0] - usb_w / 2, win_top - 0.1]) square([usb_w, 20]);
  // reset button faces UP on the right half: keep it uncovered
  if (right)
    translate([reset_pos[0], reset_pos[1]])
      square([reset_body[0] + 2 * reset_win_margin, reset_body[1] + 2 * reset_win_margin], center = true);
}

module plate2d(n, keys, right) {
  difference() {
    outline2d("tray", n);                                  // PCB outline + wall, as the tray
    for (k = keys) translate([k[1], k[2]]) rotate(k[3]) cut_square(cutout);
    for (h = holes) translate(h) circle(d = screw_clear);
    plate_windows(right);
  }
}

module screw_post() {
  difference() {
    translate([0, 0, 0]) cylinder(d = post_od, h = post_h + 0.01);
    translate([0, 0, -1]) cylinder(d = screw_clear, h = post_h + 2);
  }
}

// plate in ASSEMBLY orientation: top face at z = plate_t, posts below (z < 0), left-half view
module plate_assembly(n, keys, right) {
  difference() {
    union() {
      linear_extrude(plate_t) plate2d(n, keys, right);
      for (h = holes) translate([h[0], h[1], -post_h]) screw_post();
    }
    if (csk)
      for (h = holes) translate([h[0], h[1], plate_t - 1.0]) cylinder(d1 = screw_clear, d2 = 3.9 + 0.2, h = 1.01);
    // Choc only: diode pockets in the plate underside, right half (diodes face up)
    if (!is_mx && right)
      for (k = keys)
        translate([k[1], k[2], -0.01]) rotate(k[3]) translate([0, -9.525, 0])
          translate([-diode_pocket[0] / 2, -diode_pocket[1] / 2, 0])
            cube([diode_pocket[0], diode_pocket[1], max(0, diode_h + 0.2 - post_h) + 0.01]);
  }
}

// printed with the top face on the bed, posts up. The right half is the mirror image plus its reset window.
module plate_print(n, keys, right) {
  rotate([180, 0, 0]) translate([0, 0, -plate_t])
    if (right) mirror([1, 0, 0]) plate_assembly(n, keys, true);
    else plate_assembly(n, keys, false);
}

// ================================================================ tray
module tray_cavity2d(n) { offset(r = -(wall - fit)) outline2d("tray", n); }

// Sockets solder to the underside. Their pads are NOT mirrored between the halves (the switch pins are
// fixed in the world), so in the left-coordinate frame the right half's pads are the pattern mirrored in x.
module socket_keepout2d(keys, right) {
  for (k = keys) translate([k[1], k[2]]) rotate(k[3])
    if (right) mirror([1, 0]) socket_pads2d(); else socket_pads2d();
}
module socket_pads2d() {
  for (p = socket_pads_b) translate([p[0], p[1]]) offset(delta = pad_margin) square([p[2], p[3]], center = true);
}

// boss footprint: a disc with the socket pads (plus margin) bitten out of it
module boss2d(h, keys, right) {
  intersection() {
    translate(h) circle(d = boss_od);
    difference() {
      translate(h) square(boss_od + 2, center = true);
      socket_keepout2d(keys, right);
    }
  }
}

module tray_body(n, keys, right) {
  difference() {
    union() {
      linear_extrude(floor_t) outline2d("tray", n);
      linear_extrude(wall_h) difference() { outline2d("tray", n); tray_cavity2d(n); }
      for (h = holes) translate([0, 0, floor_t - 0.01]) linear_extrude(pcb_bottom - floor_t + 0.01) boss2d(h, keys, right);
      if (!right && reset_pillar)
        translate([reset_pos[0], reset_pos[1], floor_t - 0.01])
          cylinder(d = reset_pillar_od, h = pcb_bottom - reset_h - reset_gap - floor_t + 0.01);
    }
    // heat-set insert holes (open at the boss top)
    for (i = [0 : len(holes) - 1])
      translate([holes[i][0], holes[i][1], pcb_bottom - insert_deep]) cylinder(d = hole_d[i], h = insert_deep + 1);
    // battery pocket in the floor
    translate([ctrl_pos[0] - (batt_w + 2 * batt_clear) / 2, batt_cy - (batt_l + 2 * batt_clear) / 2, batt_skin])
      cube([batt_w + 2 * batt_clear, batt_l + 2 * batt_clear, floor_t]);
    // reset press hole (left half only: the button faces down)
    if (!right)
      translate([reset_pos[0], reset_pos[1], -1]) cylinder(d = reset_hole_d, h = pcb_bottom + 2);
    // USB-C: open at the top, towards +y
    translate([ctrl_pos[0] - usb_w / 2, ctrl_pos[1] + 12, pcb_bottom + pcb_t + usb_z0])
      cube([usb_w, 30, wall_h]);
    // power switch (right edge, underside of the PCB)
    translate([board_bbox[1] - 0.5, pwr_pos[1] - pwr_w / 2, pcb_bottom - pwr_h])
      cube([wall + 2, pwr_w, pwr_h + 0.2]);
    // JST connector (underside): pocket in the floor under the housing, then an opening in the right wall.
    // The wall opening runs through the floor if the housing is deeper than the floor allows (see README).
    translate([jst_pos[0] - 3.5, jst_pos[1] - jst_w / 2, max(batt_skin, pcb_bottom - jst_h - 0.4)])
      cube([board_bbox[1] - jst_pos[0] + 3.5, jst_w, pcb_bottom + 0.2 - max(batt_skin, pcb_bottom - jst_h - 0.4)]);
    translate([board_bbox[1] - 0.5, jst_pos[1] - jst_w / 2, max(-1, pcb_bottom - jst_h - 0.4)])
      cube([wall + 2, jst_w, pcb_bottom + 0.2 - max(-1, pcb_bottom - jst_h - 0.4)]);
  }
}

module tray_print(n, right) {
  keys = n == 42 ? keys_42 : keys_36;
  if (right) mirror([1, 0, 0]) tray_body(n, keys, true);
  else tray_body(n, keys, false);
}

// ================================================================ test plates
module test_plate(sizes, marks = false) {
  n = len(sizes);
  w = (n - 1) * test_pitch + 14 + 2 * test_margin;
  h = 14 + 2 * test_margin + (marks ? 5 : 0);
  y0 = -7 - test_margin - (marks ? 5 : 0);
  linear_extrude(plate_t) difference() {
    translate([-7 - test_margin, y0]) square([w, h]);
    for (i = [0 : n - 1]) {
      translate([i * test_pitch, 0]) square(sizes[i], center = true);
      // i + 1 small holes under cutout i identify the size (1 = smallest)
      if (marks)
        for (j = [0 : i]) translate([i * test_pitch + (j - i / 2) * 2.4, -7 - test_margin - 1]) circle(d = 1.2, $fn = 16);
    }
  }
}

// ================================================================ slices (2D debug sections for check.py)
module slice_plate(n, keys, right) {
  projection(cut = true) translate([0, 0, -plate_t / 2])
    if (right) mirror([1, 0, 0]) plate_assembly(n, keys, true);
    else plate_assembly(n, keys, false);
}
module slice_tray(n, right, z) {
  projection(cut = true) translate([0, 0, -z]) tray_print(n, right);
}

// ================================================================ dispatch
if (part == "plate_42")              plate_print(42, keys_42, false);
else if (part == "plate_36")         plate_print(36, keys_36, false);
else if (part == "plate_42_right")   plate_print(42, keys_42, true);
else if (part == "plate_36_right")   plate_print(36, keys_36, true);
else if (part == "tray_42_left")     tray_print(42, false);
else if (part == "tray_36_left")     tray_print(36, false);
else if (part == "tray_42_right")    tray_print(42, true);
else if (part == "tray_36_right")    tray_print(36, true);
else if (part == "test_plate_mx")           test_plate([mx_cutout + cutout_tol, mx_cutout + cutout_tol, mx_cutout + cutout_tol]);
else if (part == "test_plate_mx_tolerance") test_plate([13.9, 14.0, 14.1], true);
else if (part == "slice_plate_42")        slice_plate(42, keys_42, false);
else if (part == "slice_plate_36")        slice_plate(36, keys_36, false);
else if (part == "slice_plate_42_right")  slice_plate(42, keys_42, true);
else if (part == "slice_tray_42_left")    slice_tray(42, false, pcb_bottom - 1.0);   // through bosses and inserts
else if (part == "slice_tray_36_left")    slice_tray(36, false, pcb_bottom - 1.0);
else if (part == "slice_tray_42_right")   slice_tray(42, true, pcb_bottom - 1.0);
else if (part == "slice_tray_42_left_floor")  slice_tray(42, false, 1.2);            // through the floor
else if (part == "slice_tray_36_left_floor")  slice_tray(36, false, 1.2);
else if (part == "slice_tray_42_right_floor") slice_tray(42, true, 1.2);
else echo("unknown part", part);
