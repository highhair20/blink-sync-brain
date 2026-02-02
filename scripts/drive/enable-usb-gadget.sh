#!/bin/bash
set -euo pipefail

echo "Enabling USB gadget mode..."

# Add dwc2 overlay under [all] in config.txt if not already present.
# It must be under [all] so it applies regardless of board-specific sections.
CONFIG="/boot/firmware/config.txt"
if ! grep -q "^dtoverlay=dwc2$" "${CONFIG}"; then
    if grep -q "^\[all\]" "${CONFIG}"; then
        # Insert after the [all] line
        sed -i '/^\[all\]/a dtoverlay=dwc2' "${CONFIG}"
    else
        # No [all] section — append one
        printf '\n[all]\ndtoverlay=dwc2\n' >> "${CONFIG}"
    fi
    echo "Added dtoverlay=dwc2 under [all] in ${CONFIG}"
else
    echo "dtoverlay=dwc2 already present in ${CONFIG}"
fi

# Add dwc2 module to /etc/modules if not already present
if ! grep -q "^dwc2" /etc/modules; then
    printf 'dwc2\n' >> /etc/modules
    echo "Added dwc2 to /etc/modules"
else
    echo "dwc2 already present in /etc/modules"
fi

echo "Done. Reboot to apply changes: sudo reboot"
