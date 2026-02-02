#!/bin/bash
echo "Switching to Server Mode for Blink Sync Brain..."
# Unload the kernel module to stop USB drive emulation
modprobe -r g_mass_storage
# Mount the storage file locally so Pi #2 can pull clips via rsync/SSH
mount -o loop /var/blink_storage/virtual_drive.img /mnt/blink_drive
echo "Server Mode is LIVE. Drive mounted at /mnt/blink_drive."