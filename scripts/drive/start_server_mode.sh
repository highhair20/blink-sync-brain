#!/bin/bash
echo "Switching to Server Mode for Pi-Guard..."
# Unload the kernel module to stop USB drive emulation
sudo modprobe -r g_mass_storage
# Mount the storage file locally so Samba can see it
sudo mount -o loop /home/pi/blink_storage.img /home/pi/blink_share
echo "Server Mode is LIVE. Share is accessible."