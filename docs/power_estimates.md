# Power Consumption & Battery Runtime Estimates

## Component Breakdown

| Component | Status | Current @ 5V | Power (Watts) | Note |
| :--- | :--- | :--- | :--- | :--- |
| **Raspberry Pi 4** | Idle | 0.6A | 3.0W | Aggressive Undervolt (-4) |
| **Raspberry Pi 4** | Load (4 Cores) | 1.2A | 6.0W | Aggressive Undervolt (-4) |
| **SSD (Intenso SATA)** | Avg | 0.3A | 1.5W | SATA III via USB adapter |
| **Alfa WiFi (AR9271)** | TX Mode | 0.5A | 2.5W | High power dongle |
| **Heltec LoRa V3** | RX/Idle | 0.1A | 0.5W | Peaks 0.2A during TX |
| **LTE Dongle (A7670G)** | Active/Data | 0.3A | 1.5W | Disabled by default |
| **GPS (BE-880)** | Active | 0.07A | 0.35W | Continuous tracking |
| **Sensors** | All Active | 0.05A | 0.25W | Negligible combined |

### Hardware Optimizations
*Optimizations configured via `setup/optimize_hardware.sh` included in estimates:*
*   **CPU Frequency**: **900MHz** (capped for power saving).
*   **Undervolting**: `over_voltage=-4` (aggressive power reduction).
*   **Peripherals**: HDMI, Audio, Bluetooth, & Internal WiFi **DISABLED**.

### Total Scenarios

1.  **Eco Mode (Idle)**
    *   Pi Idle, SSD idle, Network listen only.
    *   **~6.0 Watts** (1.2A @ 5V)

2.  **Tactical Mode (Active)**
    *   Pi Load, Map Server busy, High Power WiFi TX, LoRa TX, LTE Active.
    *   **~13.5 Watts** (2.7A @ 5V)

## Battery Runtime (100Ah AGM)

*   **Nominal Capacity**: 100Ah @ 12V = 1200Wh
*   **Usable Capacity (AGM)**: 50% Depth of Discharge = **600Wh**
*   **DC-DC Efficiency**: ~90% (12V to 5V conversion)
*   **Effective Energy**: **~540Wh**

| Scenario | Power | Runtime (hrs) | Runtime (Days) |
| :--- | :--- | :--- | :--- |
| **Eco (6W)** | 6.0W | 90h | **3.75 Days** |
| **Active (13.5W)** | 13.5W | 40h | **1.6 Days** |

## Solar Replenishment (100W Panel)

*   **Summer (Sunny)**: ~400-500Wh / day.
    *   **Result**: Fully self-sustaining in Eco mode. Positive energy balance.
*   **Winter (Overcast)**: ~50-100Wh / day.
    *   **Result**: Extends runtime by +10-20%, but **battery will deplete after ~4-5 days**.

### Recommendations
1.  **Disable High Power WiFi** (AR9271) when not needed. It consumes ~2.5W just to be ready.
2.  **Shutdown Strategy**: Use the **11.5V** cutoff to protect the battery cycle life.
