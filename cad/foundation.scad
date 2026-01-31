// Tech Stack Foundation
// Total dimensions: 340mm x 320mm

// --- Global Resolution ---
// --- Global Resolution ---
$fn = 30;

// --- Dimensions (mm) ---
total_width = 340;
total_depth = 320;
plate_thickness = 4;
wall_height = 8; 

// Component Dimensions [w, d, h_mock]
dim_solar = [130, 90, 30];
dim_hd = [100, 70, 15]; // Assumed 100x70
dim_hd_adapter = [50, 50, 10]; 
dim_pi = [92, 65, 20];
dim_heltec = [80, 45, 10];
dim_wifi = [90, 30, 10];
dim_conv_12v = [50, 30, 20];

// Spacing
margin = 10;

// --- Render Control ---
// CLI override support: pass -D cli_quadrant=X
cli_quadrant = undef;
render_quadrant = (cli_quadrant == undef) ? -1 : cli_quadrant; 
show_mocks = (render_quadrant == -1);

// --- Modules ---

module mounting_grid() {
    // Generates a grid of 4mm holes (2D circles)
    grid_spacing = 20;
    for (x = [grid_spacing : grid_spacing : total_width - grid_spacing]) {
        for (y = [grid_spacing : grid_spacing : total_depth - grid_spacing]) {
            translate([x, y])
                circle(d = 4);
        }
    }
}

module joining_tabs() {
     // Tabs to join the 4 quadrants with M3 screws
     // Vertical seam
     for (y = [total_depth/4, total_depth*0.75]) {
         translate([total_width/2, y, plate_thickness/2]) {
             difference() {
                 cube([12, 20, plate_thickness], center=true);
                 translate([3, 0, -5]) cylinder(h=20, d=3.5); // Hole right
                 translate([-3, 0, -5]) cylinder(h=20, d=3.5); // Hole left
             }
         }
     }
     // Horizontal seam
     for (x = [total_width/4, total_width*0.75]) {
         translate([x, total_depth/2, plate_thickness/2]) {
             difference() {
                 cube([20, 12, plate_thickness], center=true);
                 translate([0, 3, -5]) cylinder(h=20, d=3.5); // Hole top
                 translate([0, -3, -5]) cylinder(h=20, d=3.5); // Hole bottom
             }
         }
     }
     // Center cross
     translate([total_width/2, total_depth/2, plate_thickness/2]) {
         difference() {
             cube([20, 20, plate_thickness], center=true);
             translate([5, 5, -5]) cylinder(h=20, d=3.5);
             translate([-5, 5, -5]) cylinder(h=20, d=3.5);
             translate([5, -5, -5]) cylinder(h=20, d=3.5);
             translate([-5, -5, -5]) cylinder(h=20, d=3.5);
         }
     }
}

module base_plate() {
    color("DimGray") 
    linear_extrude(plate_thickness)
        difference() {
            square([total_width, total_depth]);
            mounting_grid();
        }
    //joining_tabs(); // To implement properly, tabs need to be part of the split logic or added to specific quadrants
}

module component_box(dim, label_text, color_code="Silver") {
    w = dim[0];
    d = dim[1];
    h = dim[2];
    
    if (show_mocks) {
        translate([0,0,plate_thickness]) {
            color(color_code) {
                difference() {
                    cube([w, d, h]);
                    translate([2, 2, 2]) cube([w-4, d-4, h]);
                }
            }
            color("Black")
            translate([w/2, d/2, h])
            linear_extrude(1)
            text(label_text, size=min(w,d)/5, halign="center", valign="center");
        }
        
        // Footprint marker retention wall
        color("Red")
        difference() {
             cube([w+4, d+4, plate_thickness + 2]);
             translate([2, 2, -1]) cube([w, d, plate_thickness + 5]);
             translate([1, 1, -1]) cube([w+2, d+2, plate_thickness + 5]); // Thin wall
        }
    }
}

// --- Layout ---

module layout() {
    // 1. Solar Converter (Top Left)
    translate([margin, total_depth - dim_solar[1] - margin, 0])
        component_box(dim_solar, "Solar Conv", "Orange");

    // 2. Raspberry Pi (Top Right)
    translate([total_width - dim_pi[0] - margin, total_depth - dim_pi[1] - margin, 0])
        component_box(dim_pi, "RPi 4", "Green");

    // 3. Hard Drive & Adapter (Left, below Solar)
    translate([margin, total_depth - dim_solar[1] - margin*2 - dim_hd[1], 0]) {
        component_box(dim_hd, "HDD", "Black");
        translate([dim_hd[0] + 5, 0, 0]) 
            component_box(dim_hd_adapter, "Adapt", "Gray");
    }

    // 4. Heltec V2 x2 (Center area)
    translate([margin + dim_hd[0] + margin + 40, margin + 40, 0]) {
        component_box(dim_heltec, "Heltec 1", "White");
        translate([0, dim_heltec[1] + margin, 0])
            component_box(dim_heltec, "Heltec 2", "White");
    }

    // 5. Wifi Stick (Bottom Right)
    translate([total_width - dim_wifi[0] - margin, margin, 0])
        component_box(dim_wifi, "WiFi", "Blue");

    // 6. Converter 12V (shifted right to avoid Adapter overlap)
    translate([total_width/2 + 20, total_depth/2, 0])
        component_box(dim_conv_12v, "12V Conv", "Yellow");
}

module full_assembly() {
    base_plate();
    layout();
}

module quadrant(q) {
    intersection() {
        full_assembly();
        if (q == 0) { // Top Left
             translate([0, total_depth/2, -10]) cube([total_width/2, total_depth/2, 100]);
        } else if (q == 1) { // Top Right
             translate([total_width/2, total_depth/2, -10]) cube([total_width/2, total_depth/2, 100]);
        } else if (q == 2) { // Bottom Left
             translate([0, 0, -10]) cube([total_width/2, total_depth/2, 100]);
        } else if (q == 3) { // Bottom Right
             translate([total_width/2, 0, -10]) cube([total_width/2, total_depth/2, 100]);
        }
    }
}

module joiner_strip() {
    linear_extrude(plate_thickness)
        difference() {
            square([40, 12], center=true);
            translate([10, 0]) circle(d=4);
            translate([-10, 0]) circle(d=4);
        }
}

module joiner_cross() {
    linear_extrude(plate_thickness)
        difference() {
            square([40, 40], center=true);
            translate([10, 10]) circle(d=4);
            translate([-10, 10]) circle(d=4);
            translate([10, -10]) circle(d=4);
            translate([-10, -10]) circle(d=4);
        }
}

// --- Main Render ---
if (render_quadrant == -1) {
    full_assembly();
} else if (render_quadrant == 10) {
    joiner_strip();
} else if (render_quadrant == 11) {
    joiner_cross();
} else {
    quadrant(render_quadrant);
}
