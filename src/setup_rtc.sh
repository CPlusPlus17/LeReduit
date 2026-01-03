#!/bin/bash

# Check if run as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "🔧 Configuring DS3231 RTC..."

CONFIG_FILE="/boot/config.txt"
# Check if /boot/firmware/config.txt exists (Bookworm/Newer OS)
if [ -f "/boot/firmware/config.txt" ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
fi

echo "Using config file: $CONFIG_FILE"

# 1. Enable I2C
if ! grep -q "dtparam=i2c_arm=on" "$CONFIG_FILE"; then
    echo "Enabling I2C in config..."
    echo "dtparam=i2c_arm=on" >> "$CONFIG_FILE"
fi

# 2. Add RTC Overlay
if ! grep -q "dtoverlay=i2c-rtc,ds3231" "$CONFIG_FILE"; then
    echo "Adding DS3231 overlay..."
    echo "dtoverlay=i2c-rtc,ds3231" >> "$CONFIG_FILE"
else
    echo "RTC overlay already present."
fi

# 3. Disable Fake HW Clock
echo "Disabling fake-hwclock..."
apt-get -y remove fake-hwclock
update-rc.d -f fake-hwclock remove
systemctl disable fake-hwclock

# 4. Modify hwclock-set
# Comment out lines that prevent hwclock from working on systemd
if [ -f "/lib/udev/hwclock-set" ]; then
    sed -i '/if \[ -e \/run\/systemd\/system \] ; then/,+2 s/^/#/' /lib/udev/hwclock-set
    echo "Modified /lib/udev/hwclock-set"
fi

echo "✅ Configuration complete. Please REBOOT the Pi."
echo "After reboot, run 'sudo i2cdetect -y 1' to verify device at 0x68 (should show UU)."
