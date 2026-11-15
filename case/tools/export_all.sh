#!/bin/sh
# Render every printable part to case/stl/ (OpenSCAD 2021.01 or newer).
# Usage: sh case/tools/export_all.sh   (from anywhere)
set -e
cd "$(dirname "$0")/.."
mkdir -p stl
for p in plate_42 plate_36 plate_42_right plate_36_right \
         tray_42_left tray_36_left tray_42_right tray_36_right \
         test_plate_mx test_plate_mx_tolerance; do
  echo "== $p"
  openscad -q -D "part=\"$p\"" -o "stl/$p.stl" corne_case.scad
done
ls -l stl
