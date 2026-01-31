#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Generating STL files..."
openscad -o part_1_top_left.stl -D "cli_quadrant=0" foundation.scad
openscad -o part_2_top_right.stl -D "cli_quadrant=1" foundation.scad
openscad -o part_3_bottom_left.stl -D "cli_quadrant=2" foundation.scad
openscad -o part_4_bottom_right.stl -D "cli_quadrant=3" foundation.scad

echo "Done. Created:"
ls -lh *.stl
