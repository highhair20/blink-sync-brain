#!/bin/bash
set -euo pipefail

# Usage: sudo ./uninstall.sh [--purge]
#   --purge  Also delete all video clips, results, and face database in /var/blink_storage

PURGE=false
for arg in "$@"; do
    [[ "$arg" == "--purge" ]] && PURGE=true
done

echo "Uninstalling Blink Processor (Pi #2)..."

# ── Stop and disable service ──────────────────────────────────────────────────
if systemctl is-active --quiet blink-processor 2>/dev/null; then
    echo "Stopping blink-processor..."
    systemctl stop blink-processor
fi
if systemctl is-enabled --quiet blink-processor 2>/dev/null; then
    echo "Disabling blink-processor..."
    systemctl disable blink-processor
fi

# ── Remove service file ───────────────────────────────────────────────────────
SVC_FILE="/etc/systemd/system/blink-processor.service"
if [[ -f "${SVC_FILE}" ]]; then
    echo "Removing ${SVC_FILE}..."
    rm "${SVC_FILE}"
fi

systemctl daemon-reload

# ── Remove Python virtualenv ──────────────────────────────────────────────────
VENV="/opt/blink-lens/env"
if [[ -d "${VENV}" ]]; then
    echo "Removing virtualenv at ${VENV}..."
    rm -rf "${VENV}"
fi

# ── Purge data (opt-in) ───────────────────────────────────────────────────────
if [[ "${PURGE}" == true ]]; then
    echo "Purging video clips, results, and face database..."
    rm -rf /var/blink_storage/videos
    rm -rf /var/blink_storage/results
    rm -f  /var/blink_storage/face_database.pkl
    rmdir --ignore-fail-on-non-empty /var/blink_storage 2>/dev/null || true
else
    echo "Data preserved. Run with --purge to also delete videos, results, and face database."
fi

echo "Done."
