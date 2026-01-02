# 🏔️ Le Réduit

> **Autarker Rako-Server: Solar, LoRa, WLAN & SSD. Deine digitale Festung für Kommunikation & Daten im Notfall.**

![Project Status](https://img.shields.io/badge/Status-In%20Construction-orange)
![License](https://img.shields.io/badge/License-MIT-blue)
![Solar Power](https://img.shields.io/badge/Power-Solar%20%2B%20100Ah-green)

## 📖 Über das Projekt

**Le Réduit** ist eine Hommage an die Schweizer Réduit-Strategie: Eine letzte, sichere Bastion, wenn rundherum alles ausfällt.

Dieses Projekt dokumentiert den Bau einer tragbaren, energieautarken IT-Infrastruktur in einer genormten Eurobox (Rako-Kiste). Das System dient als:
1.  **Kommunikations-Knoten:** LoRa Mesh (Meshtastic) und WLAN-Access-Point.
2.  **Wissens-Arche:** Offline-Verfügbarkeit von Wikipedia, OpenStreetMap und technischen Handbüchern.
3.  **Notstrom-Versorgung:** Massive 100Ah Batteriekapazität für tagelangen Betrieb ohne Sonne.

## ✨ Features

* **🔋 Energie-Autarkie:** 200W faltbares Solarpanel + 30A MPPT Regler + 100Ah AGM Deep Cycle Batterie.
* **📡 Off-Grid Kommunikation:**
    * **LoRa:** Meshtastic Node (868 MHz) für Kommunikation über Kilometer ohne Mobilfunknetz.
    * **WLAN:** High-Power Access Point (Atheros AR9271) für lokale Geräte.
* **💾 Datensicherheit:** Raspberry Pi 4 (8GB) mit 256GB SSD für Server-Dienste und Datenspeicherung.
* **🛡️ Robustheit:** Passiv gekühltes Aluminium-Gehäuse ("Armor Case"), isoliertes Rako-Case, IP-zertifizierte Durchführungen.

---

## 🛠️ Hardware (Bill of Materials)

Eine detaillierte Einkaufsliste befindet sich in [BOM.md](BOM.md). Hier sind die Hauptkomponenten:

### ⚡ Energie
* **Batterie:** ACCONIC VDC100 Deep Cycle AGM (12V, 100Ah)
* **Solar:** 200W Faltbares Panel & Victron/MPPT 30A Laderegler
* **Ladung:** SAE-Außenanschluss & PACO 10A Netzladegerät (Backup)
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

![Wiring Diagram](docs/wiring_diagram.png)
*(Platzhalter: Lade hier das Bild hoch, das ich dir generiert habe)*

**Wichtige Verbindungen:**
* **Solar Input:** SAE Buchse -> MPPT Regler
* **Last:** MPPT Load -> Hauptschalter -> Verteiler -> DC-DC Wandler -> Pi 4
* **Daten:** SSD an USB 3.0 (Blau), Funk-Module an USB 2.0 (zur Vermeidung von Interferenzen).

---

## 💻 Software Stack

Das System läuft auf **Raspberry Pi OS Lite (64-bit)**. Geplante Services:

1.  **[Meshtastic](https://meshtastic.org/):** Firmware auf dem Heltec V3 Stick zur Teilnahme am Mesh-Netzwerk.
2.  **[Kiwix](https://www.kiwix.org/):** Zum Hosten von ZIM-Dateien (Wikipedia offline).
3.  **Hostapd & Dnsmasq:** Um den Raspberry Pi als WLAN-Hotspot zu betreiben.
4.  **Samba/NFS:** Fileserver für den Datenaustausch im Feld.

---

## ⚠️ Sicherheitshinweis

Dieses Projekt verwendet große Energiespeicher (Blei-Säure/AGM Batterien) und LiPo-Akkus.
* **Kurzschlussgefahr:** Eine 100Ah Batterie kann bei Kurzschluss Kabel zum Schmelzen bringen und Brände verursachen. Sicherungen sind Pflicht!
* **Ausgasung:** AGM-Batterien sind sicher, sollten aber dennoch nicht in luftdichten Behältern ohne Druckausgleich geladen werden (Vent Plug verbaut).

## 🤝 Mitwirken

Pull Requests für Skripte, 3D-Druck-Teile (Halterungen) oder Konfigurations-Tipps sind willkommen!

## 📄 Lizenz

Dieses Projekt ist unter der MIT Lizenz veröffentlicht - siehe [LICENSE](LICENSE) Datei für Details.

---
*Gebaut in der Schweiz 🇨🇭 für den Fall der Fälle.*
