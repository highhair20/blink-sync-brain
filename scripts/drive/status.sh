#!/bin/bash

if lsmod | grep -q g_mass_storage; then
    echo "Storage Mode: ACTIVE (Blink can write clips)"
else
    echo "Storage Mode: INACTIVE (g_mass_storage not loaded)"
fi

if systemctl is-active --quiet blink-watcher 2>/dev/null; then
    echo "Watcher:      RUNNING (clips will be pushed to Pi #2)"
else
    echo "Watcher:      STOPPED"
fi
