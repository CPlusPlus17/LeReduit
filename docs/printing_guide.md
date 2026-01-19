# 🖨️ Printing Guide for Le Réduit Platform

This guide describes how to manufacture the internal mounting platform using 3D printing. This replaces the traditional plywood approach with a modular, technical design.

## 🧵 Material Selection

### ✅ Recommended: ASA (Acrylonitrile Styrene Acrylate)
*   **Why**: UV resistant, high heat resistance (~95°C), chemically resistant. Perfect for outdoor/enclosed electronics.
*   **Finish**: Matte Black looks professional and hides layer lines.

### ⚠️ Acceptable: PETG (Polyethylene Terephthalate Glycol)
*   **Why**: Good heat resistance (~75°C), easy to print, flexible.
*   **Warning**: If the Rako box sits in direct blistering sunlight, internal temps *might* soften PETG under load. For shaded deployment, it is fine.

### ⛔️ Avoid: PLA (Polylactic Acid)
*   **Why**: Softens at ~55-60°C. A closed black box in the sun will exceed this. Your platform will warp and fail.

## 📐 Segmentation & Printing Strategy

The total size is **550mm x 350mm**, which exceeds most hobbyist build volumes.

### Option A: Large Format (Voron 2.4 350 / Modix)
*   If you have a 350x350mm bed, you can print it in **2 segments** (Left/Right).
*   Join method: M3 bolts + Nuts or dovetail slide.

### Option B: Standard Format (Prusa MK3/4 / Bambu X1C)
*   Standard bed (~250x210mm).
*   Requires printing in **4-6 Segments**.
*   **Assembly**: The CAD design features 'Puzzle' connectors or bolt flanges. Use Superglue (Cyanoacrylate) for permanent bonds or M3 bolts for modularity.

## ⚙️ Print Settings

*   **Nozzle**: 0.4mm or 0.6mm (0.6mm recommended for speed and strength).
*   **Perimeters (Walls)**: 4 to 5 (Crucial for screw holding strength).
*   **Top/Bottom Layers**: 4.
*   **Infill**: 20-30% Grid or Gyroid (Structural rigidity).
*   **Supports**: Minimal. Design should be chamfered to avoid supports.

## 🔧 Post-Processing

### Heat-Set Inserts
*   The design relies on **M2.5 and M3 Heat-Set Inserts** (Short type).
*   **Process**:
    1.  Set soldering iron to ~250°C (for ASA/PETG).
    2.  Place insert on the hole.
    3.  Gently press down with the iron until flush.
    4.  Use a flat object to hold it flush while cooling.

### Assembly
1.  Assemble the plate segments.
2.  Install all heat-set inserts.
3.  Perform a "Dry Fit" in the Rako box to ensure tolerances.

## 🔩 Hardware Reference (Heat-Set Inserts)

Based on the **OD 3.5mm** (M2.5) and **OD 4.0mm** (M3) kit:

| Screw Size | Insert OD | Recommended CAD Hole Ø | Depth | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **M2.5** | 3.5 mm | **3.2 - 3.3 mm** | 4-5 mm | Raspberry Pi, HATs |
| **M3** | 4.0 mm | **3.6 - 3.7 mm** | 5-6 mm | Mounts, Clips, SSD |
| **M2** | 3.5 mm | **3.2 - 3.3 mm** | 3-4 mm | Small Sensors (Optional) |

> [!TIP]
> **Hole Sizing**: For 3D printing, holes often shrink slightly. Designing the hole at **OD - 0.3mm** usually provides a perfect interference fit for heat setting.

---
**Happy Printing!**
