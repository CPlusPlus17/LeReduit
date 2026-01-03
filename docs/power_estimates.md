# Power Consumption & Battery Runtime Estimates

## Component Breakdown

| Component | Status | Current @ 5V | Power (Watts) | Note |
| :--- | :--- | :--- | :--- | :--- |
| **Raspberry Pi 4** | Idle | 0.7A | 3.5W | Base system, WiFi/BT off (internal) |
| **Raspberry Pi 4** | Load (4 Cores) | 1.4A | 7.0W | Heavy K3s/Map rendering |
| **SSD (NVMe USB)** | Avg | 0.4A | 2.0W | Varies heavily by R/W ops |
| **Alfa WiFi (AR9271)** | TX Mode | 0.5A | 2.5W | High power dongle |
| **Heltec LoRa V3** | RX/Idle | 0.1A | 0.5W | Peaks 0.2A during TX |
| **GPS (BE-880)** | Active | 0.07A | 0.35W | Continuous tracking |
| **Sensors** | All Active | 0.05A | 0.25W | Negligible combined |
| **Fan (5V)** | Active | 0.15A | 0.75W | If installed |

### Total Scenarios

1.  **Eco Mode (Idle)**
    *   Pi Idle, SSD idle, Network listen only.
    *   **~7 Watts** (1.4A @ 5V)

2.  **Tactical Mode (Active)**
    *   Pi Load, Map Server busy, High Power WiFi TX, LoRa TX.
    *   **~13 Watts** (2.6A @ 5V)

## Battery Runtime (100Ah AGM)

*   **Nominal Capacity**: 100Ah @ 12V = 1200Wh
*   **Usable Capacity (AGM)**: 50% Depth of Discharge = **600Wh**
*   **DC-DC Efficiency**: ~90% (12V to 5V conversion)
*   **Effective Energy**: **~540Wh**

| Scenario | Power | Runtime (hrs) | Runtime (Days) |
| :--- | :--- | :--- | :--- |
| **Eco (7W)** | 7W | 77h | **3.2 Days** |
| **Active (13W)** | 13W | 41h | **1.7 Days** |

## Solar Replenishment (100W Panel)

*   **Summer (Sunny)**: ~400-500Wh / day.
    *   **Result**: Fully self-sustaining in Eco mode. Positive energy balance.
*   **Winter (Overcast)**: ~50-100Wh / day.
    *   **Result**: Extends runtime by +10-20%, but **battery will deplete after ~4-5 days**.

### Recommendations
1.  **Disable High Power WiFi** (AR9271) when not needed. It consumes ~2.5W just to be ready.
2.  **Shutdown Strategy**: Use the **11.5V** cutoff to protect the battery cycle life.
