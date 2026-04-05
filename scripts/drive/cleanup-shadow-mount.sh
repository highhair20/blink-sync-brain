#!/bin/bash
# Unmount the shadow mount and detach loop devices after blink-watcher stops.
# Reads paths from drive.yaml so it works even if defaults have been changed.

CONFIG="/opt/blink-lens/configs/drive.yaml"

SHADOW=$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('${CONFIG}'))
    print(d.get('watcher', {}).get('shadow_mount_point', '/mnt/blink_shadow'))
except Exception:
    print('/mnt/blink_shadow')
" 2>/dev/null || echo "/mnt/blink_shadow")

DRIVE=$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('${CONFIG}'))
    print(d.get('storage', {}).get('virtual_drive_path', '/var/blink_storage/virtual_drive.img'))
except Exception:
    print('/var/blink_storage/virtual_drive.img')
" 2>/dev/null || echo "/var/blink_storage/virtual_drive.img")

umount "${SHADOW}" 2>/dev/null || true
losetup -j "${DRIVE}" 2>/dev/null | cut -d: -f1 | xargs -r losetup -d
