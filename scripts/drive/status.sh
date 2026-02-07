#!/bin/bash

if lsmod | grep -q g_mass_storage; then
    echo "Storage Mode (Blink can write)"
elif mount | grep -q blink_drive; then
    echo "Server Mode (drive mounted locally)"
else
    echo "Unknown (neither gadget loaded nor drive mounted)"
fi
