# Blink Lens Application Setup

This guide covers installing and configuring the Blink Lens software on both Raspberry Pi Zero 2 W boards. For hardware setup and OS installation, see the [Pi Zero Setup Guide](pi-zero-setup.md).

## Prerequisites

- Raspberry Pi OS Lite 64-bit on both Pis (see [Pi Zero Setup Guide](pi-zero-setup.md))
- SSH enabled and network configured
- Python 3.8+ on both Pis

## Pi #1: Drive (USB Gadget) Setup

Pi #1 emulates a USB flash drive for the Blink Sync Module. It runs in "Storage Mode" permanently — Blink always has its drive. A background file watcher detects new clips and pushes them to Pi #2 automatically over SSH, so no mode switching is required.

### Step 1: Clone the Repository

```bash
ssh pi@blink-usb.local

sudo apt update && sudo apt upgrade -y
sudo apt install -y git

sudo mkdir -p /opt/blink-lens
sudo chown pi:pi /opt/blink-lens
git clone https://github.com/highhair20/blink-lens.git /opt/blink-lens
```

### Step 2: Enable USB Gadget Mode

```bash
sudo /opt/blink-lens/scripts/drive/enable-usb-gadget.sh
sudo reboot
```

The script adds `dtoverlay=dwc2,dr_mode=peripheral` under the `[all]` section in `/boot/firmware/config.txt` and `dwc2` to `/etc/modules` (idempotently — safe to run twice). The `dr_mode=peripheral` is required for the Pi to act as a USB device rather than a USB host.

**Note:** Do NOT add `g_mass_storage` to `/etc/modules`. It must be loaded with the `file=` parameter by the startup script, not at boot.

### Step 3: Install System Dependencies

After reboot, SSH back in:

```bash
ssh pi@blink-usb.local

sudo /opt/blink-lens/scripts/drive/install-deps.sh
```

### Step 4: Create the Virtual Storage

Creates a 32 GB FAT32 disk image that acts as the flash drive's storage. This takes a while — running in `screen` is recommended.

```bash
screen
sudo /opt/blink-lens/scripts/drive/create-virtual-storage.sh
```

### Step 5: Install the Application

```bash
screen
/opt/blink-lens/scripts/drive/install-app.sh
```

### Step 6: Test Storage Mode

```bash
sudo /opt/blink-lens/scripts/drive/start_storage_mode.sh

# Verify
lsmod | grep g_mass_storage
dmesg | tail -10
lsusb
```

The defaults in `configs/drive.yaml` match a standard setup (32 GB drive at `/var/blink_storage/virtual_drive.img`). To override them, pass a config file:

```bash
blink-drive start --config /path/to/config.yaml
```

### Step 7: Configure the File Watcher

The file watcher runs on Pi #1 and pushes new clips to Pi #2 automatically. It shadow-mounts the virtual drive image read-only (alongside `g_mass_storage`) to detect new files without interrupting Blink's write access.

**7a. Set Pi #2's address in the config:**

```bash
nano /opt/blink-lens/configs/drive.yaml
```

Set `processor_host` to Pi #2's IP or hostname:

```yaml
watcher:
  processor_host: "192.168.1.201"   # Pi #2 IP or hostname
  processor_user: "pi"
  processor_video_path: "/var/blink_storage/videos"
  ssh_key_path: "/home/pi/.ssh/id_rsa"
```

**7b. Set up SSH key access from Pi #1 to Pi #2:**

Pi #1 needs to rsync to Pi #2 without a password prompt. Run this on Pi #1:

```bash
ssh-keygen -t rsa -f /home/pi/.ssh/id_rsa -N ""
ssh-copy-id -i /home/pi/.ssh/id_rsa.pub pi@192.168.1.201
```

Verify it works:

```bash
ssh pi@192.168.1.201 "echo SSH OK"
```

### Step 8: Create Systemd Services

Install both service files — the drive service (Storage Mode at boot) and the watcher service (automatic clip transfer):

```bash
sudo /opt/blink-lens/scripts/drive/install-service.sh

sudo cp /opt/blink-lens/scripts/drive/systemd/blink-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blink-watcher
sudo reboot
```

### Manual Drive Access Scripts

The scripts in `scripts/drive/` are available for manual use or diagnostics. Under normal operation the watcher handles transfers automatically — only use these to inspect or recover the drive.

- **`start_storage_mode.sh`** — Loads `g_mass_storage`, making the virtual drive visible to Blink.
- **`start_server_mode.sh`** — Unloads `g_mass_storage` and loop-mounts the drive at `/mnt/blink_drive` for direct read access.
- **`status.sh`** — Shows whether `g_mass_storage` is loaded.

```bash
# Check current status
/opt/blink-lens/scripts/drive/status.sh

# Manual clip transfer (stop watcher first — for diagnostics only)
sudo systemctl stop blink-watcher
sudo /opt/blink-lens/scripts/drive/start_server_mode.sh
rsync -av /mnt/blink_drive/ pi@192.168.1.201:/var/blink_storage/videos/
sudo /opt/blink-lens/scripts/drive/start_storage_mode.sh
sudo systemctl start blink-watcher
```

### Step 9: Verify Services After Reboot

After reboot, SSH back in and confirm both services are running:

```bash
ssh pi@blink-usb.local

# Storage Mode should be active
/opt/blink-lens/scripts/drive/status.sh
# Expected: Storage Mode (Blink can write)

# Watcher service should be running
sudo systemctl status blink-watcher
sudo journalctl -u blink-watcher -f
```

### Step 10: Connect to Blink Sync Module

1. Connect the Pi's **USB** (data) port to the Blink Sync Module using a USB-A to Micro USB cable
2. Make sure the Pi is also powered via the **PWR** port — don't rely on power from the Sync Module
3. In the Blink app, go to **Sync Module > Local Storage** — it should show a USB drive detected
4. If prompted to format the drive, allow it — Blink needs its own filesystem structure
5. Enable local storage if not already enabled

Once configured, Blink will save clips to the virtual drive.

## Pi #2: Processor (Video & Face Recognition) Setup

### Step 1: Clone the Repository

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git

sudo mkdir -p /opt/blink-lens
sudo chown pi:pi /opt/blink-lens
git clone https://github.com/highhair20/blink-lens.git /opt/blink-lens
```

### Step 2: Install System Dependencies

```bash
sudo /opt/blink-lens/scripts/processor/install-deps.sh
```

### Step 3: Install the Application

```bash
screen
/opt/blink-lens/scripts/processor/install-app.sh
```

### Step 4: Configure the Processor

The repo includes `configs/processor.yaml` with Pi Zero 2 W–tuned defaults (lower concurrency, higher face confidence). Review and edit it if needed:

```bash
nano /opt/blink-lens/configs/processor.yaml
```

Pass it when starting the processor:
```bash
blink-processor start --config /opt/blink-lens/configs/processor.yaml
```

### Step 5: Setup Storage Directories

```bash
sudo /opt/blink-lens/scripts/processor/setup-storage.sh
```

### Step 6: Setup Face Recognition Database

```bash
# Create directory for face images
mkdir -p ~/face_images

# Add known faces (place face images in the directory)
# Image names should be: person_name.jpg

# TODO: Face database setup command is not yet implemented.
```

### Step 7: Create Systemd Service

```bash
sudo /opt/blink-lens/scripts/processor/install-service.sh
```

## System Integration & Networking

### Connect Pi #1 to Blink Sync Module

1. Connect Pi #1 to Blink Sync Module using USB-A to Micro USB cable
2. Power on Pi #1 and wait for USB gadget to initialize
3. In Blink app, go to Sync Module settings > Local Storage > select the USB drive

### Configure Static IPs

```bash
# On either Pi, configure static IP using NetworkManager
sudo nmcli connection modify "Wi-Fi" ipv4.addresses "192.168.1.200/24"  # .200 for Drive, .201 for Processor
sudo nmcli connection modify "Wi-Fi" ipv4.gateway "192.168.1.1"
sudo nmcli connection modify "Wi-Fi" ipv4.dns "192.168.1.1,8.8.8.8"
sudo nmcli connection modify "Wi-Fi" ipv4.method "manual"

# Restart the connection
sudo nmcli connection down "Wi-Fi"
sudo nmcli connection up "Wi-Fi"
```

### Setup SSH Key Access Between Pis

Pi #1 pushes clips to Pi #2 via rsync, so Pi #1 needs passwordless SSH access to Pi #2. Run this on Pi #1:

```bash
ssh-keygen -t rsa -f /home/pi/.ssh/id_rsa -N ""
ssh-copy-id -i /home/pi/.ssh/id_rsa.pub pi@192.168.1.201
```

For general management access from your workstation, also copy your own key to both Pis:

```bash
ssh-copy-id pi@192.168.1.200   # Pi #1
ssh-copy-id pi@192.168.1.201   # Pi #2
```

### Test Video Transfer

Trigger a test by causing motion in front of a Blink camera. Watch the watcher log on Pi #1 to confirm the clip is detected and pushed:

```bash
# On Pi #1 — watch for clip detection and push
sudo journalctl -u blink-watcher -f
```

You should see log lines like:
```
Drive image changed, waiting to settle
Scanning virtual drive for new clips
New clips found count=1
Pushing clip to processor file=clip.mp4
Clip pushed successfully file=clip.mp4
```

Then confirm the clip arrived on Pi #2:

```bash
# On Pi #2
ls -lt /var/blink_storage/videos/
```

## Troubleshooting

### USB Gadget Issues

As a first step, run the built-in diagnostic script. It checks modules, the virtual drive file, USB gadget configfs, kernel messages, and the systemd service:

```bash
sudo /opt/blink-lens/scripts/drive/diagnose_usb_gadget.sh
```

1. **Gadget Not Recognized — Complete Diagnostic**
   ```bash
   # Check if modules are loaded
   lsmod | grep dwc2
   lsmod | grep g_mass_storage

   # Check if USB gadget is active
   ls /sys/kernel/config/usb_gadget/ 2>/dev/null || echo "No USB gadgets found"

   # Check kernel messages for USB errors
   dmesg | grep -i usb | tail -20
   dmesg | grep -i gadget | tail -20

   # Check if virtual drive exists and is accessible
   ls -la /var/blink_storage/virtual_drive.img

   # Test manual module loading
   sudo modprobe -r g_mass_storage 2>/dev/null || true
   sudo modprobe g_mass_storage file=/var/blink_storage/virtual_drive.img removable=1 stall=0

   # Check if it appears in lsusb
   lsusb
   ```

2. **USB Gadget Not Appearing on Host Computer**
   ```bash
   # Verify the virtual drive file is properly formatted
   sudo file /var/blink_storage/virtual_drive.img

   # Check file permissions
   ls -la /var/blink_storage/virtual_drive.img

   # Ensure the file is not mounted elsewhere
   mount | grep virtual_drive

   # Test with a smaller test file
   sudo dd if=/dev/zero of=/tmp/test.img bs=1M count=100
   sudo mkfs.vfat /tmp/test.img
   sudo modprobe -r g_mass_storage
   sudo modprobe g_mass_storage file=/tmp/test.img removable=1 stall=0
   ```

3. **Module Loading Issues**
   ```bash
   # Check if modules are available
   modinfo dwc2
   modinfo g_mass_storage

   # Check kernel version compatibility
   uname -r

   # Reload modules if needed
   sudo modprobe -r g_mass_storage dwc2
   sudo modprobe dwc2
   sudo modprobe g_mass_storage
   ```

4. **Systemd Service Issues**
   ```bash
   # Check service status
   sudo systemctl status blink-drive

   # Check service logs
   sudo journalctl -u blink-drive -f

   # Check if the command exists
   which blink-drive

   # Test the command manually
   sudo /opt/blink-lens/scripts/drive/start_storage_mode.sh

   # Reload systemd and restart service
   sudo systemctl daemon-reload
   sudo systemctl restart blink-drive
   ```

5. **Virtual Drive Not Created**
   ```bash
   ls -la /var/blink_storage/

   # Create manually if needed (preferred — handles partitioning correctly)
   sudo /opt/blink-lens/scripts/drive/create-virtual-storage.sh
   ```

### File Watcher Issues

1. **Watcher service not starting**
   ```bash
   sudo systemctl status blink-watcher
   sudo journalctl -u blink-watcher -b
   # blink-watcher requires blink-drive — confirm blink-drive is active first
   sudo systemctl status blink-drive
   ```

2. **Clips not being pushed to Pi #2**
   ```bash
   # Check watcher logs for errors
   sudo journalctl -u blink-watcher -f

   # Test SSH access from Pi #1 to Pi #2 manually
   ssh pi@192.168.1.201 "echo SSH OK"

   # Test rsync manually (replace clip.mp4 with an actual file from the shadow mount)
   rsync -az -e "ssh -i /home/pi/.ssh/id_rsa" \
     /mnt/blink_shadow/clip.mp4 \
     pi@192.168.1.201:/var/blink_storage/videos/
   ```

3. **Shadow mount failing**
   ```bash
   # Check if loop device can be created
   sudo losetup -fP /var/blink_storage/virtual_drive.img
   sudo losetup -j /var/blink_storage/virtual_drive.img

   # Check mount point
   ls /mnt/blink_shadow
   mount | grep blink_shadow

   # Clean up stale loop devices if needed
   sudo losetup -D   # detach all unused loop devices
   ```

4. **Watcher state file issue (clips being re-pushed after restart)**
   ```bash
   cat /var/blink_storage/watcher_state.json
   # If corrupt, remove it — the watcher will rebuild state on next scan
   sudo rm /var/blink_storage/watcher_state.json
   ```

### Video Processing Issues

1. **OpenCV Installation Problems**
   ```bash
   # Install OpenCV from source if pip fails
   sudo apt install -y python3-opencv
   ```

2. **Face Recognition Issues**
   ```bash
   # Check dlib installation
   python3 -c "import dlib; print('dlib OK')"

   # Reinstall if needed
   sudo pip3 uninstall dlib face_recognition
   sudo pip3 install dlib face_recognition
   ```

3. **Performance Issues**
   ```bash
   # Monitor system resources
   htop

   # Check temperature
   vcgencmd measure_temp

   # Reduce processing load — increase frame_skip in config.yaml
   ```

### Network Issues

1. **Pi Not Accessible**
   ```bash
   # Check network configuration using NetworkManager
   nmcli device status
   nmcli connection show

   # Check IP address
   ip addr show wlan0

   # Test connectivity
   ping 192.168.1.1
   ping 8.8.8.8
   ```

2. **NetworkManager Configuration Issues**
   ```bash
   # Check NetworkManager service status
   sudo systemctl status NetworkManager

   # Restart NetworkManager
   sudo systemctl restart NetworkManager

   # List available WiFi networks
   nmcli device wifi list

   # Connect to a specific network
   sudo nmcli device wifi connect "SSID_NAME" password "PASSWORD"

   # Check connection details
   nmcli connection show "Wi-Fi"
   ```

3. **SSH Connection Issues**
   ```bash
   # Check SSH service
   sudo systemctl status ssh

   # Restart SSH if needed
   sudo systemctl restart ssh

   # Check NetworkManager connection
   nmcli connection show "Wi-Fi"
   nmcli device wifi list
   ```

## Monitoring & Maintenance

### System Monitoring Script

```bash
#!/bin/bash

echo "=== Blink Lens System Status ==="
echo "Date: $(date)"
echo

echo "Pi #1 (USB Gadget):"
ssh pi@192.168.1.200 "blink-drive status"
echo

echo "Pi #2 (Video Processing):"
blink-processor status
echo

echo "Storage Usage:"
df -h /var/blink_storage
echo

echo "Temperature:"
vcgencmd measure_temp
```

### Setup Cron Job for Monitoring

```bash
crontab -e
```

Add this line:
```cron
*/30 * * * * /home/pi/monitor_system.sh >> /var/log/blink_monitor.log 2>&1
```

### Weekly Maintenance

```bash
# Update system
sudo apt update && sudo apt upgrade

# Clean old logs
sudo journalctl --vacuum-time=7d

# Check disk usage
df -h
```

### Monthly Maintenance

```bash
# Backup face database
cp /var/blink_storage/face_database.pkl /backup/

# Check storage status
blink-drive status
blink-processor status
```

## Security

1. **Change Default Passwords**
   ```bash
   passwd

   # Create new user (optional)
   sudo adduser blinkuser
   sudo usermod -aG sudo blinkuser
   ```

2. **Firewall Configuration**
   ```bash
   sudo apt install -y ufw
   sudo ufw allow ssh
   sudo ufw allow 8080  # If using web interface
   sudo ufw enable
   ```

3. **Regular Updates**
   ```bash
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

4. **SSH Hardening**
   ```bash
   # After setting up SSH keys, disable password authentication
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```

## Appendix: Quick Reference

### System Information

```bash
cat /proc/device-tree/model     # Pi model and version
vcgencmd measure_temp            # CPU temperature
free -h                          # Memory usage
df -h                            # Disk usage
ip addr show                     # Network interfaces
sudo systemctl list-units --type=service --state=running  # Running services
uptime                           # System load
```

### Package Management

```bash
sudo apt update                  # Update package list
sudo apt upgrade                 # Upgrade installed packages
sudo apt install package_name    # Install a package
sudo apt remove package_name     # Remove a package
sudo apt autoremove && sudo apt autoclean  # Clean cache
```

### Application Commands

```bash
# Pi #1 (Drive)
blink-drive start                                             # Start Storage Mode (load g_mass_storage)
blink-drive stop                                              # Stop Storage Mode
blink-drive status                                            # Show gadget status
blink-drive watch --config /opt/blink-lens/configs/drive.yaml  # Start file watcher (push clips to Pi #2)

# Pi #2 (Processor)
blink-processor start
blink-processor status
blink-processor process-video /path/to/video.mp4 --output-dir /var/blink_storage/results
```

### Service Management

```bash
# Drive service (Storage Mode — runs at boot)
sudo systemctl start blink-drive
sudo systemctl enable blink-drive
sudo systemctl status blink-drive
sudo journalctl -u blink-drive -f

# Watcher service (pushes clips to Pi #2 — depends on blink-drive)
sudo systemctl start blink-watcher
sudo systemctl enable blink-watcher
sudo systemctl status blink-watcher
sudo journalctl -u blink-watcher -f
```

### Performance Tips

```bash
# Reduce GPU memory (Drive Pi)
# In /boot/firmware/config.txt, set: gpu_mem=64

# Increase GPU memory (Processor Pi, for video processing)
# In /boot/firmware/config.txt, set: gpu_mem=128

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Use swap file for memory
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Increase process priority for video processing
sudo nice -n -10 blink-processor process-video video.mp4

# Use tmpfs for temporary files
sudo mount -t tmpfs -o size=512M tmpfs /tmp
```

### Log Monitoring

```bash
sudo journalctl -f                       # All system logs
sudo journalctl -u blink-drive -f        # Drive service logs
sudo journalctl -u blink-processor -f    # Processor service logs
sudo journalctl -b                       # Current boot logs
sudo journalctl --vacuum-time=7d         # Clean old logs
```

### Storage Monitoring

```bash
df -h                                    # Overall disk usage
du -sh /var/blink_storage/*              # Blink storage breakdown
df -i                                    # Inode usage
```

### Useful Scripts

**System Status:**
```bash
#!/bin/bash
echo "=== Pi Zero 2 W Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Temperature: $(vcgencmd measure_temp)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "Network: $(hostname -I)"
```

**Backup:**
```bash
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp /opt/blink-lens/configs/drive.yaml $BACKUP_DIR/
cp /var/blink_storage/face_database.pkl $BACKUP_DIR/
cp /var/log/blink_monitor.log $BACKUP_DIR/
echo "Backup completed: $BACKUP_DIR"
```

### Important Configuration Files

```
/boot/firmware/config.txt          # Boot configuration
/etc/modules                       # System modules
/etc/ssh/sshd_config               # SSH configuration
/opt/blink-lens/configs/drive.yaml      # Drive Pi config
/opt/blink-lens/configs/processor.yaml  # Processor Pi config
```

---

*For hardware and OS setup, see the [Pi Zero Setup Guide](pi-zero-setup.md).*
