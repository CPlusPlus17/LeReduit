# 📐 Mechanical Layout Plan

**Plate Size**: 550mm x 350mm (8mm Plywood)
**Orientation**: Horizontal (Landscape) inside Rako box.

## Design Philosophy: "Clean Deck"
- All cables disappear immediately through holes near the components to the "Underdeck".
- High Power (12V) on the RIGHT side (nearer to cable glands usually).
- Logic (5V/Data) on the LEFT side.
- Airflow: Components spaced out.

## ASCII Layout Map

```text
       [   LEFT: 550mm   ]                                     [ RIGHT ]
  +-----------------------------------------------------------------------+
  |                                                                       |
  |   [ WIFI ANT  ]         [  SSD DRIVE  ]          [ MPPT CONTROLLER ]  |
  |     (Atheros)            (Velcro/Screw)             (Vertical Mount)  |
  |                                                                       |
  |                                                                       |
  |   [ RASPBERRY PI 4 ]    [  Heltec LoRa ]         [ FUSE UNIT ]        |
  |     (Armor Case)         (Stick/Case)             (Distributor)       |
  |                                                                       |
  |                         [ RTC / INA219 ]                              |
  |                          (Sensor Cluster)                             |
  |                                                                       |
  |                                                  [ MAIN SWITCH ]      |
  |                                                   (Through Plate)     |
  |                                                                       |
  +-----------------------------------------------------------------------+
```

## Drilling & Mounting Guide

### 1. The "Power Zone" (Right)
- **MPPT Controller**: Needs airflow. Mount slightly elevated or ensure space.
- **Main Switch**: Drill 20-23mm hole (measure switch diameter!) to flush mount it into the wood, or mount it on a small 3D printed L-bracket if it's not a panel mount type.
- **Cable Pass-throughs**: Drill 8mm or 10mm holes right next to the MPPT screw terminals for Solar In and Battery Out.

### 2. The "Logic Zone" (Left/Center)
- **Raspberry Pi**: Use the M2.5 standoffs. 
    - *Drill Template*: Place Pi, mark 4 holes.
    - *USB*: Orientation matters! Point USB ports towards the "Cable Highway" (center or edge depending on cable length).
- **SSD**: Velcro is best for vibration dampening.
- **Heltec LoRa**: Mount with screen visible? Or just safely attached? If screen visible, cut a small window or mount on top.

### 3. The "Cable Underworld" (Bottom side)
- Use the adhesive cable clips here.
- Run the 12V rails (Solar, Battery) along the edges to keep them away from the sensitive data lines of the Pi.
- Twist positive and negative wires together (Twisted Pair) to reduce magnetic interference.

## Dimensions Checklist
- **Pi 4**: ~88 x 58 mm
- **SSD**: ~100 x 70 mm
- **MPPT**: Checks specific model size (usually ~130 x 70 mm for small ones).
