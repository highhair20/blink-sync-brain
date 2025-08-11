#!/bin/bash
echo "Switching to Storage Mode for Blink..."
# Ensure the share is unmounted before starting the gadget
sudo umount /home/pi/blink_share &>/dev/null || true
# Load the kernel module to start USB drive emulation
sudo modprobe g_mass_storage file=/home/pi/blink_storage.img removable=1 stall=0
echo "Storage Mode is LIVE."