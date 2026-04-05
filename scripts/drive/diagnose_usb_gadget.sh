#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0"
    exit 1
fi

echo "=== USB Gadget Diagnostic Script ==="
echo "Date: $(date)"
echo

echo "1. Checking USB gadget modules..."
echo "dwc2 module:"
lsmod | grep dwc2 || echo "❌ dwc2 module not loaded"
echo "dwc2 dr_mode:"
if [[ -f /sys/module/dwc2/parameters/dr_mode ]]; then
    DR_MODE=$(cat /sys/module/dwc2/parameters/dr_mode)
    if [[ "${DR_MODE}" == "peripheral" ]]; then
        echo "✅ peripheral (correct for USB gadget mode)"
    else
        echo "❌ ${DR_MODE} (should be 'peripheral' — run enable-usb-gadget.sh and reboot)"
    fi
else
    echo "  (not readable — dwc2 may not be loaded)"
fi
echo "g_mass_storage module:"
lsmod | grep g_mass_storage || echo "❌ g_mass_storage module not loaded"
echo

echo "2. Checking virtual drive file..."
if [ -f "/var/blink_storage/virtual_drive.img" ]; then
    echo "✅ Virtual drive file exists"
    ls -la /var/blink_storage/virtual_drive.img
    echo "File type:"
    file /var/blink_storage/virtual_drive.img
else
    echo "❌ Virtual drive file missing: /var/blink_storage/virtual_drive.img"
fi
echo

echo "3. Checking g_mass_storage backing file..."
# g_mass_storage is a legacy gadget module — it does not use configfs.
# The backing file parameter tells us what image it is serving to the host.
if lsmod | grep -q g_mass_storage; then
    BACKING=$(cat /sys/module/g_mass_storage/parameters/file 2>/dev/null || echo "")
    if [[ -n "${BACKING}" ]]; then
        echo "✅ g_mass_storage backing file: ${BACKING}"
        if [[ -f "${BACKING}" ]]; then
            echo "✅ Backing file exists"
        else
            echo "❌ Backing file not found — virtual drive image may have been deleted"
        fi
    else
        echo "⚠️  g_mass_storage is loaded but backing file parameter is not readable"
    fi
else
    echo "⚠️  g_mass_storage is not loaded — skipping backing file check"
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

echo "6. Checking blink-drive service status..."
systemctl is-active blink-drive
systemctl is-enabled blink-drive
echo

echo "7. Checking blink-watcher service status..."
systemctl is-active blink-watcher 2>/dev/null || echo "blink-watcher: inactive or not installed"
echo "Recent blink-watcher log (last 20 lines):"
journalctl -u blink-watcher -n 20 --no-pager 2>/dev/null || echo "  (no journal entries found)"
echo

echo "=== Diagnostic Complete ==="
