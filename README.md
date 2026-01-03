# 🏔️ Le Réduit

> **Autarker Server: Solar, LoRa, WLAN & SSD. Deine digitale Festung für Kommunikation & Lagebild im Notfall.**

![Project Status](https://img.shields.io/badge/Status-In%20Construction-orange)
![License](https://img.shields.io/badge/License-MIT-blue)
![Solar Power](https://img.shields.io/badge/Power-Solar%20%2B%20100Ah-green)
![Orchestration](https://img.shields.io/badge/Orchestration-k3s%20%2F%20Helm-blueviolet)

## 📖 Über das Projekt

**Le Réduit** ist eine Hommage an die Schweizer Réduit-Strategie: Eine letzte, sichere Bastion, wenn rundherum alles ausfällt.

Dieses Projekt dokumentiert den Bau einer tragbaren, energieautarken IT-Infrastruktur in einer genormten Eurobox (Rako-Kiste). Das System transformiert einen Raspberry Pi 4 in ein **taktisches Operationszentrum (TOC)** für:
1.  **Lagebild & Führung:** Echtzeit-Tracking und Kartenmaterial via TAK (Team Awareness Kit).
2.  **Sichere Kommunikation:** Verschlüsselter Chat und VoIP ohne Internet.
3.  **Funk-Brücke:** Integration von LoRa (Meshtastic) in IP-Netzwerke.
4.  **Notstrom-Versorgung:** Massive 100Ah Batteriekapazität für tagelangen Betrieb ohne Sonne.

## ✨ Features

* **🔋 Energie-Autarkie:** 100W faltbares Solarpanel + 30A MPPT Regler + 100Ah AGM Deep Cycle Batterie.
* **📡 Off-Grid Kommunikation:**
    * **LoRa:** Meshtastic Node (868 MHz) für Kommunikation über Kilometer ohne Mobilfunknetz.
    * **WLAN:** High-Power Access Point (Atheros AR9271) für lokale Team-Geräte.
* **🛡️ Edge Cluster:** Betrieb als Single-Node Kubernetes Cluster (k3s) für maximale Stabilität und "Infrastructure as Code".
* **💾 Hardware:** Passiv gekühltes Aluminium-Gehäuse ("Armor Case"), isoliertes Rako-Case, IP-zertifizierte Durchführungen.

---

## 🛠️ Hardware (Bill of Materials)

Eine detaillierte Einkaufsliste befindet sich in [BOM.md](BOM.md). Hier sind die Hauptkomponenten:

### ⚡ Energie
* **Batterie:** 12V AGM Deep Cycle (100Ah)
* **Solar:** 200W Faltbares Panel & Victron/MPPT 30A Laderegler
* **Ladung:** SAE-Aussenanschluss & PACO 10A Netzladegerät (Backup)
* **Überwachung:** Digitales Voltmeter & Sicherungshalter (16AWG)

### 🖥️ Compute & Network
* **SBC:** Raspberry Pi 4 Model B (8GB RAM)
* **Storage:** Intenso TOP SSD (256GB) + USB 3.0 SATA Adapter (UASP)
* **LoRa:** Heltec WiFi LoRa 32 V3 (ESP32)
* **WiFi:** Atheros AR9271 USB Adapter (mit externer Antenne)
* **RTC:** DS3231 Real Time Clock (für Zeitstempel ohne Internet)

### 📦 Gehäuse
* **Kiste:** Rako Behälter 600x400mm (60 Liter)
* **Struktur:** Pappel-Sperrholz "Technik-Deck" & Buchenleisten-Fixierung
* **Isolierung:** XPS Jackodur (20mm) für Winterbetrieb

---

## 🔌 Verkabelung & Architektur

Das System folgt einer sternförmigen 12V-Topologie mit zentraler Absicherung.

See the [Detailed Wiring Schema](docs/wiring_schema.md) for the complete Mermaid diagram and pinout.

**Wichtige Verbindungen:**
* **Solar Input:** SAE Buchse -> MPPT Regler
* **Last:** MPPT Load -> Hauptschalter -> Verteiler -> DC-DC Wandler -> Pi 4
* **Daten:** SSD an USB 3.0 (Blau), Funk-Module an USB 2.0 (Interferenz-Vermeidung).

---

## 💻 Software Stack: "Edge Kubernetes Cluster"

Das System läuft als **Single-Node Kubernetes Cluster** basierend auf **k3s**. Dies ermöglicht "Self-Healing" Capabilities (stürzt ein Service ab, wird er neu gestartet) und ein professionelles Deployment via **Helm Charts**.

### 🏗️ Orchestrierung & Core
* **OS:** Raspberry Pi OS Lite (64-bit)
* **Cluster:** [k3s](https://k3s.io/) (Lightweight Kubernetes, optimiert für Edge/IoT).
* **Package Management:** **Helm**. Alle Services sind als Charts definiert.
* **Ingress:** **Traefik** oder **Nginx Ingress** für das Routing interner Domains (z.B. `tak.reduit.local`).
* **Cert-Manager:** Verwaltet interne Self-Signed Zertifikate für TLS-Verschlüsselung.

### 🗺️ Situational Awareness (Lagebild)
* **[OpenTAKServer](https://github.com/TakServer/OpenTakServer):**
    * Deployed via Helm Chart.
    * Zentraler Server für **ATAK** (Android Team Awareness Kit) Clients.
    * Liefert Positionsdaten, Marker, Chat und "Data Packages" an alle verbundenen Endgeräte.
    * Hostet Offline-Kartenkacheln für das Einsatzgebiet.

### 💬 Secure Comms
* **[Matrix](https://matrix.org/):**
    * High-Performance Matrix Server (in Rust geschrieben).
    * Bietet E2EE (End-to-End Encrypted) Chats und Filesharing.
    * Extrem ressourcensparend im Vergleich zu Synapse.
* **[Mumble](https://www.mumble.info/):**
    * VoIP-Server für taktische Sprachkommunikation mit niedriger Latenz.
    * Funktioniert auch bei instabilen Verbindungen zuverlässig.

### 📡 Funk-Brücke & Tools
* **[Meshtastic-Bridge](https://meshtastic.org/):**
    * Custom Pod, der via Python-API Nachrichten vom LoRa-USB-Stick in einen Matrix-Raum spiegelt.
    * Ermöglicht Kommunikation zwischen WLAN-Nutzern (ATAK/Matrix) und weit entfernten LoRa-Nodes.

---

## ⚠️ Sicherheitshinweis

Dieses Projekt verwendet grosse Energiespeicher (Blei-Säure/AGM Batterien) und LiPo-Akkus.
* **Kurzschlussgefahr:** Eine 100Ah Batterie kann bei Kurzschluss Kabel zum Schmelzen bringen und Brände verursachen. Sicherungen sind Pflicht!
* **Ausgasung:** AGM-Batterien sind sicher, sollten aber dennoch nicht in luftdichten Behältern ohne Druckausgleich geladen werden (Vent Plug verbaut).

## 🤝 Mitwirken

Pull Requests für Helm Charts, 3D-Druck-Teile (Halterungen) oder Konfigurations-Tipps sind willkommen!

## 📄 Lizenz

Dieses Projekt ist unter der MIT Lizenz veröffentlicht - siehe [LICENSE](LICENSE) Datei für Details.

---
*Gebaut in der Schweiz 🇨🇭 für den Fall der Fälle.*
