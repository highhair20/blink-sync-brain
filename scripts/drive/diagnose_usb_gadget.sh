#!/bin/bash

echo "=== USB Gadget Diagnostic Script ==="
echo "Date: $(date)"
echo

echo "1. Checking USB gadget modules..."
echo "dwc2 module:"
lsmod | grep dwc2 || echo "❌ dwc2 module not loaded"
echo "g_mass_storage module:"
lsmod | grep g_mass_storage || echo "❌ g_mass_storage module not loaded"
echo

echo "2. Checking virtual drive file..."
if [ -f "/var/blink_storage/virtual_drive.img" ]; then
    echo "✅ Virtual drive file exists"
    ls -la /var/blink_storage/virtual_drive.img
    echo "File type:"
    sudo file /var/blink_storage/virtual_drive.img
else
    echo "❌ Virtual drive file missing: /var/blink_storage/virtual_drive.img"
fi
echo

echo "3. Checking USB gadget configuration..."
if [ -d "/sys/kernel/config/usb_gadget" ]; then
    echo "✅ USB gadget configfs available"
    ls /sys/kernel/config/usb_gadget/ 2>/dev/null || echo "No active gadgets"
else
    echo "❌ USB gadget configfs not available"
fi
echo

echo "4. Checking USB devices..."
echo "USB devices detected:"
lsusb
echo

echo "5. Checking recent kernel messages..."
echo "Recent USB-related messages:"
dmesg | grep -i usb | tail -10
echo

echo "6. Testing manual module loading..."
echo "Attempting to load g_mass_storage module..."
sudo modprobe -r g_mass_storage 2>/dev/null || true
if sudo modprobe g_mass_storage file=/var/blink_storage/virtual_drive.img removable=1 stall=0; then
    echo "✅ Module loaded successfully"
    lsmod | grep g_mass_storage
else
    echo "❌ Failed to load module"
fi
echo

echo "7. Checking service status..."
systemctl is-active blink-drive
systemctl is-enabled blink-drive
echo

echo "=== Diagnostic Complete ==="
