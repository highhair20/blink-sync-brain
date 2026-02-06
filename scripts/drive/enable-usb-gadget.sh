#!/bin/bash
set -euo pipefail

echo "Enabling USB gadget mode..."

# Add dwc2 overlay with peripheral mode under [all] in config.txt.
# dr_mode=peripheral is required for USB gadget mode (device, not host).
# It must be under [all] so it applies regardless of board-specific sections.
CONFIG="/boot/firmware/config.txt"
OVERLAY="dtoverlay=dwc2,dr_mode=peripheral"
if ! grep -q "^dtoverlay=dwc2,dr_mode=peripheral$" "${CONFIG}"; then
    # Remove any existing dwc2 line under [all] that doesn't have the right mode
    sed -i '/^\[all\]/,/^\[/{/^dtoverlay=dwc2$/d}' "${CONFIG}"
    if grep -q "^\[all\]" "${CONFIG}"; then
        # Insert after the [all] line
        sed -i "/^\[all\]/a ${OVERLAY}" "${CONFIG}"
    else
        # No [all] section — append one
        printf '\n[all]\n%s\n' "${OVERLAY}" >> "${CONFIG}"
    fi
    echo "Added ${OVERLAY} under [all] in ${CONFIG}"
else
    echo "${OVERLAY} already present in ${CONFIG}"
fi

# Add dwc2 module to /etc/modules if not already present
if ! grep -q "^dwc2" /etc/modules; then
    printf 'dwc2\n' >> /etc/modules
    echo "Added dwc2 to /etc/modules"
else
    echo "dwc2 already present in /etc/modules"
fi

echo "Done. Reboot to apply changes: sudo reboot"
