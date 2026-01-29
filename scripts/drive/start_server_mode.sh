#!/bin/bash
echo "Switching to Server Mode for Pi-Guard..."
# Unload the kernel module to stop USB drive emulation
modprobe -r g_mass_storage
# Mount the storage file locally so Samba can see it
mount -o loop /var/blink_storage/virtual_drive.img /var/blink_storage/share
echo "Server Mode is LIVE. Share is accessible."