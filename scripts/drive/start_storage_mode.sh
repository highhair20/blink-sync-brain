#!/bin/bash
echo "Switching to Storage Mode for Blink..."
# Ensure the share is unmounted before starting the gadget
umount /var/blink_storage/share &>/dev/null || true
# Unload the module first in case it was loaded without parameters
modprobe -r g_mass_storage &>/dev/null || true
# Load the kernel module to start USB drive emulation
modprobe g_mass_storage file=/var/blink_storage/virtual_drive.img removable=1 stall=0
echo "Storage Mode is LIVE."