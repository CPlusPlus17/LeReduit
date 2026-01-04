#!/bin/bash
set -e

CONFIG_TXT="/boot/config.txt"
# Fallback for newer OS or Ubuntu
if [ ! -f "$CONFIG_TXT" ]; then
    CONFIG_TXT="/boot/firmware/config.txt"
fi

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}=== Applying Le Réduit Hardware Optimizations ===${NC}"

if [ ! -w "$CONFIG_TXT" ]; then
    echo "Error: Cannot write to $CONFIG_TXT. Are you running as root?"
    exit 1
fi

# Backup
cp "$CONFIG_TXT" "${CONFIG_TXT}.bak_$(date +%Y%m%d_%H%M%S)"
echo "Backed up config.txt."

# Create the config block
cat <<EOF >> "$CONFIG_TXT"

# --- Le Reduit Power Optimizations ---
# Limit CPU Frequency (900MHz for power saving)
arm_freq=900

# Undervolt (Aggressive -4)
over_voltage=-4

# Disable Bluetooth
dtoverlay=disable-bt

# Disable WiFi (Internal)
# Only enable this if you are exclusively using the external Atheros (wlan1) or Ethernet!
dtoverlay=disable-wifi

# Disable Audio (Onboard)
dtparam=audio=off

# Stealth Mode: Disable LEDs
# Power LED
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=off
# Activity LED
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off

# Disable HDMI Output (Headless)
hdmi_blanking=1
hdmi_ignore_hotplug=1

# -------------------------------------
EOF

echo -e "${GREEN}Optimizations added to $CONFIG_TXT.${NC}"
echo "Note: 'dtoverlay=disable-wifi' is COMMENTED OUT by default. Uncomment it manually if `wlan1` is your only interface."
echo "Please REBOOT to apply changes."
