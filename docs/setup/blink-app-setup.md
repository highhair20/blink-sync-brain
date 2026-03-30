# Blink Lens Application Setup

This guide covers installing and configuring the Blink Lens software on both Raspberry Pi Zero 2 W boards. For hardware setup and OS installation, see the [Pi Zero Setup Guide](pi-zero-setup.md).

## Prerequisites

- Raspberry Pi OS Lite 64-bit on both Pis (see [Pi Zero Setup Guide](pi-zero-setup.md))
- SSH enabled and network configured

---

## Step 1: Pi #1 — Clone, Enable USB Gadget, and Reboot

```bash
ssh pi@blink-drive.local

sudo apt update && sudo apt upgrade -y
sudo apt install -y git screen
sudo mkdir -p /opt/blink-lens
sudo git clone https://github.com/highhair20/blink-lens.git /opt/blink-lens
sudo chown -R pi:pi /opt/blink-lens
sudo /opt/blink-lens/scripts/drive/enable-usb-gadget.sh
sudo reboot
```

## Step 2: Pi #2 — Clone and Install

While Pi #1 is rebooting, set up Pi #2. dlib/face-recognition compilation takes a long time — run in `screen` so it survives a disconnection:

```bash
ssh pi@blink-processor.local

sudo apt update && sudo apt upgrade -y
sudo apt install -y git screen
sudo mkdir -p /opt/blink-lens
sudo git clone https://github.com/highhair20/blink-lens.git /opt/blink-lens
sudo chown -R pi:pi /opt/blink-lens
screen -S install
sudo /opt/blink-lens/scripts/processor/install.sh
```

## Step 3: Pi #1 — Configure

Once Pi #2 is reachable on the network, SSH back into Pi #1 and run:

```bash
ssh pi@blink-drive.local
/opt/blink-lens/scripts/drive/configure.sh 192.168.1.201
```

You will be prompted for Pi #2's password once to copy the SSH key.

## Step 4: Pi #1 — Install and Reboot

Virtual drive image creation (32 GB) takes several minutes — run in `screen` so it survives a disconnection:

```bash
screen -S install
sudo /opt/blink-lens/scripts/drive/install.sh
sudo reboot
```

## Step 5: Configure Static IPs

Run on each Pi. Your SSH session will drop when the connection restarts — reconnect using the static IP.

```bash
# Pi #1 (blink-drive)
sudo /opt/blink-lens/scripts/configure-static-ip.sh 192.168.1.200

# Pi #2 (blink-processor)
sudo /opt/blink-lens/scripts/configure-static-ip.sh 192.168.1.201
```

## Step 6: Connect Pi #1 to Blink Sync Module

1. Connect the Pi's **USB** (data) port to the Blink Sync Module using a USB-A to Micro USB cable
2. Power the Pi via the **PWR** port — do not rely on power from the Sync Module
3. In the Blink app, go to **Sync Module > Local Storage** — it should show a USB drive detected
4. If prompted to format the drive, allow it
5. Enable local storage if not already enabled

## Step 7: Test Video Transfer

Trigger motion in front of a Blink camera, then watch the watcher log on Pi #1:

```bash
sudo journalctl -u blink-watcher -f
```

You should see:
```
Drive image changed, waiting to settle
Scanning virtual drive for new clips
New clips found count=1
Pushing clip to processor file=clip.mp4
Clip pushed successfully file=clip.mp4
```

Confirm the clip arrived on Pi #2:

```bash
ls -lt /var/blink_storage/videos/
```

---

## Troubleshooting

### USB Gadget Issues

Run the diagnostic script first:

```bash
sudo /opt/blink-lens/scripts/drive/diagnose_usb_gadget.sh
```

**Gadget not recognized:**
```bash
lsmod | grep dwc2
lsmod | grep g_mass_storage
dmesg | grep -i usb | tail -20
sudo modprobe -r g_mass_storage 2>/dev/null || true
sudo modprobe g_mass_storage file=/var/blink_storage/virtual_drive.img removable=1 stall=0
```

**Virtual drive not created:**
```bash
sudo /opt/blink-lens/scripts/drive/create-virtual-storage.sh
```

**Systemd service issues:**
```bash
sudo systemctl status blink-drive
sudo journalctl -u blink-drive -f
sudo systemctl daemon-reload && sudo systemctl restart blink-drive
```

### File Watcher Issues

**Watcher not starting** (requires `blink-drive` to be active first):
```bash
sudo systemctl status blink-drive
sudo systemctl status blink-watcher
sudo journalctl -u blink-watcher -b
```

**Clips not being pushed to Pi #2:**
```bash
ssh pi@192.168.1.201 "echo SSH OK"
sudo journalctl -u blink-watcher -f
```

**Shadow mount failing:**
```bash
sudo losetup -j /var/blink_storage/virtual_drive.img
mount | grep blink_shadow
sudo losetup -D
```

**Clips re-pushed after restart (corrupt state file):**
```bash
sudo rm /var/blink_storage/watcher_state.json
```

### Video Processing Issues

**OpenCV:**
```bash
sudo apt install -y python3-opencv
```

**dlib / face_recognition:**
```bash
python3 -c "import dlib; print('dlib OK')"
```

### Network Issues

**Pi not accessible:**
```bash
nmcli device status
ip addr show wlan0
```

**SSH not working:**
```bash
sudo systemctl status ssh
sudo systemctl restart ssh
```

---

*For hardware and OS setup, see the [Pi Zero Setup Guide](pi-zero-setup.md).*
