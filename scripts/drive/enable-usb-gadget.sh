#!/bin/bash
set -euo pipefail

echo "Enabling USB gadget mode..."

# Add dwc2 overlay to config.txt if not already present
if ! grep -q "^dtoverlay=dwc2" /boot/firmware/config.txt; then
    printf '\n# Enable USB gadget mode\ndtoverlay=dwc2\n' >> /boot/firmware/config.txt
    echo "Added dtoverlay=dwc2 to /boot/firmware/config.txt"
else
    echo "dtoverlay=dwc2 already present in /boot/firmware/config.txt"
fi

# Add dwc2 module to /etc/modules if not already present
if ! grep -q "^dwc2" /etc/modules; then
    printf 'dwc2\n' >> /etc/modules
    echo "Added dwc2 to /etc/modules"
else
    echo "dwc2 already present in /etc/modules"
fi

echo "Done. Reboot to apply changes: sudo reboot"
