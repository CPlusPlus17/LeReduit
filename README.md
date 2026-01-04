# 🏔️ Le Réduit

> **Autonomous Server: Solar, LoRa, WLAN & SSD. Your digital fortress for communication & situational awareness in emergencies.**

![Project Status](https://img.shields.io/badge/Status-In%20Construction-orange)
![License](https://img.shields.io/badge/License-MIT-blue)
![Solar Power](https://img.shields.io/badge/Power-Solar%20%2B%20100Ah-green)
![Orchestration](https://img.shields.io/badge/Orchestration-k3s%20%2F%20Helm-blueviolet)

## 📖 About the Project

**Le Réduit** is a tribute to the Swiss National Redoubt strategy: A final, secure bastion when everything else fails.

This project documents the construction of a portable, energy-autonomous IT infrastructure inside a standardized Eurobox (Rako case). The system transforms a Raspberry Pi 4 into a **Tactical Operations Center (TOC)** for:
1.  **Situational Awareness & Command:** Real-time tracking and maps via TAK (Team Awareness Kit).
2.  **Secure Communication:** Encrypted chat and VoIP without the internet.
3.  **Radio Bridge:** Integration of LoRa (Meshtastic) into IP networks.
4.  **Emergency Power Supply:** Massive 100Ah battery capacity for days of operation without sun.

## ✨ Features

* **🔋 Energy Autonomy:** 100W/200W foldable solar panel + 30A MPPT controller + 100Ah AGM Deep Cycle battery.
* **📡 Off-Grid Communication:**
    * **LoRa:** Meshtastic Node (868 MHz) for communication over kilometers without mobile networks.
    * **LTE:** 4G/Cat-1 Bridge for hybrid connectivity when mobile networks are available.
    * **WLAN:** High-Power Access Point (Atheros AR9271) for local team devices.
* **🛡️ Edge Cluster:** Operates as a Single-Node Kubernetes Cluster (k3s) for maximum stability and "Infrastructure as Code".
* **💾 Hardware:** Passively cooled aluminum housing ("Armor Case"), insulated Rako case, IP-certified feedthroughs.

---

## 🛠️ Hardware (Bill of Materials)

A detailed shopping list can be found in [BOM.md](BOM.md). Here are the main components:

### ⚡ Energy
* **Battery:** 12V AGM Deep Cycle (100Ah)
* **Solar:** 100W/200W Foldable Panel & Victron/MPPT 30A Charge Controller
* **Charging:** SAE External Port & PACO 10A Mains Charger (Backup)
* **Monitoring:** Digital Voltmeter & Fuse Holder (16AWG)

### 🖥️ Compute & Network
* **SBC:** Raspberry Pi 4 Model B (8GB RAM)
* **Storage:** Intenso TOP SSD (256GB, SATA III) + USB 3.0 Adapter
* **LoRa:** Heltec WiFi LoRa 32 V3 (ESP32)
* **WiFi:** Atheros AR9271 USB Adapter (with external antenna)
* **LTE:** USB A7670G LTE Cat 1 Dongle (Global Bands)
* **RTC:** DS3231 Real Time Clock (for timestamps without internet)

### 📦 Enclosure
* **Box:** Rako Container 600x400mm (60 Liters)
* **Structure:** Poplar plywood "Tech Deck" & Beechwood slat fixation
* **Insulation:** XPS Jackodur (20mm) for winter operation

---

## 🔌 Wiring & Architecture

The system follows a star-shaped 12V topology with central fusing.

See the [Detailed Wiring Schema](docs/wiring_schema.md) for the complete Mermaid diagram and pinout.

**Key Connections:**
* **Solar Input:** SAE Socket -> MPPT Controller
* **Load:** MPPT Load -> Main Switch -> Distributor -> DC-DC Converter -> Pi 4
* **Data:** SSD on USB 3.0 (Blue), Radio Modules on USB 2.0 (Interference Avoidance).

---

## 💻 Software Stack: "Edge Kubernetes Cluster"

The system runs as a **Single-Node Kubernetes Cluster** based on **k3s**. This enables "Self-Healing" capabilities (if a service crashes, it is restarted) and professional deployment via **Helm Charts**.

### 🏗️ Orchestration & Core
* **OS:** Raspberry Pi OS Lite (64-bit)
* **Cluster:** [k3s](https://k3s.io/) (Lightweight Kubernetes, optimized for Edge/IoT).
* **Package Management:** **Helm**. All services are defined as charts.
* **Ingress:** **Traefik** or **Nginx Ingress** for routing internal domains (e.g., `tak.reduit.local`).
* **Cert-Manager:** Manages internal self-signed certificates for TLS encryption.

### 🗺️ Situational Awareness
* **[OpenTAKServer](https://github.com/TakServer/OpenTakServer):**
    * Deployed via Helm Chart.
    * Central server for **ATAK** (Android Team Awareness Kit) clients.
    * Provides position data, markers, chat, and "Data Packages" to all connected end devices.
    * Hosts offline map tiles for the operational area.

### 💬 Secure Comms
* **[Matrix](https://matrix.org/):**
    * High-Performance Matrix Server (written in Rust).
    * Offers E2EE (End-to-End Encrypted) chats and file sharing.
    * Extremely resource-efficient compared to Synapse.
* **[Mumble](https://www.mumble.info/):**
    * VoIP server for tactical voice communication with low latency.
    * Works reliably even with unstable connections.

### 📡 Radio Bridge & Tools
* **[Meshtastic-Bridge](https://meshtastic.org/):**
    * Custom Pod that mirrors messages from the LoRa USB stick into a Matrix room via Python API.
    * Enables communication between WLAN users (ATAK/Matrix) and distant LoRa nodes.

---

## ⚠️ Safety Warning

This project uses large energy storage (Lead-Acid/AGM batteries) and LiPo batteries.
* **Short Circuit Hazard:** A 100Ah battery can melt cables and cause fires in case of a short circuit. Fuses are mandatory!
* **Outgassing:** AGM batteries are safe but should still not be charged in airtight containers without pressure equalization (Vent Plug installed).

## 🤝 Contributing

Pull Requests for Helm Charts, 3D printed parts (mounts), or configuration tips are welcome!

## 📄 License

This project is published under the MIT License - see [LICENSE](LICENSE) file for details.

---
*Built in Switzerland 🇨🇭 for when it matters.*
