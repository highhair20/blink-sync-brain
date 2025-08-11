#!/bin/bash

# USB Gadget Configuration for Blink Sync Brain

set -euo pipefail

mkdir -p /sys/kernel/config/usb_gadget/blink_storage
cd /sys/kernel/config/usb_gadget/blink_storage

echo 0x1d6b > idVendor
echo 0x0104 > idProduct
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

mkdir -p strings/0x409
echo "BLINK_STORAGE_001" > strings/0x409/serialnumber
echo "Blink Storage Device" > strings/0x409/product
echo "Blink Sync Brain" > strings/0x409/manufacturer

mkdir -p configs/c.1/strings/0x409
echo "Blink Storage Configuration" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

mkdir -p functions/mass_storage.usb0
echo 1 > functions/mass_storage.usb0/stall
echo 0 > functions/mass_storage.usb0/lun.0/cdrom
echo 0 > functions/mass_storage.usb0/lun.0/ro
echo 0 > functions/mass_storage.usb0/lun.0/nofua
echo 1 > functions/mass_storage.usb0/lun.0/removable

DRIVE_IMG=${1:-/var/blink_storage/virtual_drive.img}
echo "$DRIVE_IMG" > functions/mass_storage.usb0/lun.0/file

ln -s functions/mass_storage.usb0 configs/c.1/

echo "20980000.usb" > UDC

