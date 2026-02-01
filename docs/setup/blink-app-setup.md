# Blink Sync Brain Application Setup

This guide covers installing and configuring the Blink Sync Brain software on both Raspberry Pi Zero 2 W boards. For hardware setup and OS installation, see the [Pi Zero Setup Guide](pi-zero-setup.md).

## Prerequisites

- Raspberry Pi OS Lite 64-bit on both Pis (see [Pi Zero Setup Guide](pi-zero-setup.md))
- SSH enabled and network configured
- Python 3.8+ on both Pis

## Pi #1: Drive (USB Gadget) Setup

Pi #1 emulates a USB flash drive for the Blink Sync Module. It switches between "Storage Mode" (for Blink) and "Server Mode" (for Pi #2 to pull clips).

### Step 1: Enable USB Gadget Mode

```bash
ssh pi@blink-usb.local
```

1. **Edit config.txt**
   ```bash
   sudo nano /boot/firmware/config.txt
   ```
   Append the following to the bottom of the file:
   ```
   # Enable USB gadget mode
   dtoverlay=dwc2
   ```

2. **Add dwc2 to the kernel command line**
   ```bash
   # Edit cmdline.txt — this file is a SINGLE line, append to the END of the existing line
   sudo nano /boot/firmware/cmdline.txt
   ```
   Append `modules-load=dwc2` to the **end** of the existing line (do NOT create a new line):
   ```
   ... rootwait modules-load=dwc2
   ```

3. **Enable USB Gadget Module**
   ```bash
   sudo nano /etc/modules
   ```
   Add this line to the end of the file:
   ```
   dwc2
   ```
   **Note:** Do NOT add `g_mass_storage` here. It must be loaded with the `file=` parameter by the startup script, not at boot.

4. **Reboot to Apply Changes**
   ```bash
   sudo reboot
   ```

### Step 2: System Dependencies

After reboot, SSH back in:

```bash
ssh pi@blink-usb.local

sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip screen cmake libboost-all-dev
```

### Step 3: Install the Application

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/blink-sync-brain.git
# Install may take some time. Running in screen is recommended.
screen
cd blink-sync-brain
sudo python -m venv env
source env/bin/activate
pip install .[drive]
```

### Step 4: Create the Virtual Storage

Create the large file that will act as the flash drive's storage. Running in `screen` is recommended in case your SSH session is interrupted.

```bash
# Create storage directory
sudo mkdir -p /var/blink_storage
sudo chown pi:pi /var/blink_storage
sudo chmod 755 /var/blink_storage

# Create virtual drive image
screen
cd /var/blink_storage
dd if=/dev/zero of=virtual_drive.img bs=1M count=32768 status=progress
sudo chown pi:pi virtual_drive.img

# Format the file with the FAT32 filesystem
sudo mkfs.vfat virtual_drive.img
```

### Step 5: Install & Configure Samba (for Server Mode)

```bash
sudo apt install samba -y
# Create the directory that will be shared
sudo mkdir -p /var/blink_storage/share
sudo chown pi:pi /var/blink_storage/share
# Edit the Samba config file
sudo nano /etc/samba/smb.conf
```

Add this share definition to the very bottom of the file:
```ini
[BlinkClips]
comment = Blink Video Clips
path = /var/blink_storage/share
read only = no
browsable = yes
guest ok = yes
```

Save the file and restart Samba: `sudo systemctl restart smbd`.

### Step 6: Configure and Test Storage Mode

1. **Install Storage Mode Script**
   ```bash
   sudo cp /opt/blink-sync-brain/scripts/drive/start_storage_mode.sh /opt/blink-sync-brain/start_storage_mode.sh
   sudo chmod +x /opt/blink-sync-brain/start_storage_mode.sh
   ```

2. **Create Configuration File**
   ```bash
   sudo mkdir -p /etc/blink-sync-brain
   sudo cp /opt/blink-sync-brain/configs/drive.yaml /etc/blink-sync-brain/config.yaml
   sudo nano /etc/blink-sync-brain/config.yaml
   ```

   The configuration should look like this:
   ```yaml
   storage:
     virtual_drive_path: "/var/blink_storage/virtual_drive.img"
     virtual_drive_size_gb: 32
     cleanup_threshold: 85.0
     retention_days: 30
     monitor_interval: 300

   logging:
     level: "INFO"
   ```

   **Important**: Update `virtual_drive_path` and `virtual_drive_size_gb` to match your setup.

3. **Test Storage Mode**
   ```bash
   sudo /opt/blink-sync-brain/start_storage_mode.sh

   # Verify
   lsmod | grep g_mass_storage
   dmesg | tail -10
   lsusb
   ```

### Mode Switching Scripts

Pi #1 has two mode scripts in `scripts/drive/`:

- **`start_storage_mode.sh`** — Loads the `g_mass_storage` kernel module, making the virtual drive visible to the Blink Sync Module as a USB flash drive.
- **`start_server_mode.sh`** — Unloads `g_mass_storage` and loop-mounts the virtual drive locally so Samba can share it with Pi #2 for clip retrieval.

Install both scripts:
```bash
sudo cp /opt/blink-sync-brain/scripts/drive/start_server_mode.sh /opt/blink-sync-brain/start_server_mode.sh
sudo chmod +x /opt/blink-sync-brain/start_server_mode.sh
```

To switch modes manually:
```bash
# Switch to Server Mode (Pi #2 can pull clips)
sudo /opt/blink-sync-brain/start_server_mode.sh

# Switch back to Storage Mode (Blink can write clips)
sudo /opt/blink-sync-brain/start_storage_mode.sh
```

### Step 7: Create Systemd Service

Install the service file that runs `start_storage_mode.sh` at boot:

```bash
sudo cp /opt/blink-sync-brain/scripts/systemd/blink-drive.service /etc/systemd/system/
```

Enable and start the service, then reboot:
```bash
sudo systemctl enable --now blink-drive
sudo reboot
```

## Pi #2: Processor (Video & Face Recognition) Setup

### Step 1: System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip
```

### Step 2: Install Video Processing Dependencies

```bash
# Video processing
sudo apt install -y ffmpeg libsm6 libxext6 libxrender-dev libgomp1

# OpenCV dependencies
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libjasper-dev libqtcore4 libqtgui4 libqt4-test
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libv4l-dev libxvidcore-dev libx264-dev
sudo apt install -y libgtk-3-dev libtiff5-dev libjpeg-dev libpng-dev
sudo apt install -y libtiff-dev libdc1394-22-dev

# Face recognition / dlib dependencies
sudo apt install -y cmake build-essential
sudo apt install -y libdlib-dev libblas-dev liblapack-dev
sudo apt install -y libatlas-base-dev gfortran
```

### Step 3: Install the Application

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/blink-sync-brain.git
cd blink-sync-brain

# Install full dependencies for video processing and face recognition
pip install .[processor]
```

### Step 4: Configure the Processor

```bash
sudo mkdir -p /etc/blink-sync-brain
sudo cp configs/processor.yaml /etc/blink-sync-brain/config.yaml
sudo nano /etc/blink-sync-brain/config.yaml
```

Update the configuration for video processing:
```yaml
storage:
  video_directory: "/var/blink_storage/videos"
  results_directory: "/var/blink_storage/results"

processing:
  frame_skip: 3  # Lower for better accuracy
  max_concurrent_videos: 1  # Lower for Pi Zero 2 W

face_recognition:
  database_path: "/var/blink_storage/face_database.pkl"
  confidence_threshold: 0.7  # Higher for better accuracy
```

### Step 5: Setup Storage Directories

```bash
sudo mkdir -p /var/blink_storage/videos
sudo mkdir -p /var/blink_storage/results
sudo chown pi:pi /var/blink_storage
```

### Step 6: Setup Face Recognition Database

```bash
# Create directory for face images
mkdir -p ~/face_images

# Add known faces (place face images in the directory)
# Image names should be: person_name.jpg

# TODO: Face database setup command is not yet implemented.
# For now, manage face images manually in the face_images directory.
```

Test face recognition:
```bash
blink-processor process-video /path/to/test_video.mp4 --output-dir /var/blink_storage/results
```

### Step 7: Create Systemd Service

```bash
sudo cp /opt/blink-sync-brain/scripts/systemd/blink-processor.service /etc/systemd/system/
sudo systemctl enable --now blink-processor
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

```bash
# On each Pi, generate SSH key and copy to the other
ssh-keygen -t rsa -b 4096
ssh-copy-id pi@192.168.1.201  # or .200 from Pi #2
```

### Test Video Transfer

Create a transfer test script on Pi #2:

```bash
#!/bin/bash

# Monitor for new videos and process them
while true; do
    for video in /var/blink_storage/videos/*.mp4; do
        if [ -f "$video" ]; then
            echo "Processing: $video"
            blink-processor process-video "$video"
            mv "$video" /var/blink_storage/processed/
        fi
    done
    sleep 10
done
```

## Troubleshooting

### USB Gadget Issues

As a first step, run the built-in diagnostic script. It checks modules, the virtual drive file, USB gadget configfs, kernel messages, and the systemd service:

```bash
sudo /opt/blink-sync-brain/scripts/drive/diagnose_usb_gadget.sh
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
   which start_storage_mode.sh

   # Test the command manually
   sudo /opt/blink-sync-brain/start_storage_mode.sh

   # Reload systemd and restart service
   sudo systemctl daemon-reload
   sudo systemctl restart blink-drive
   ```

5. **Virtual Drive Not Created**
   ```bash
   ls -la /var/blink_storage/

   # Create manually if needed
   sudo dd if=/dev/zero of=/var/blink_storage/virtual_drive.img bs=1G count=32
   sudo mkfs.vfat /var/blink_storage/virtual_drive.img
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

echo "=== Blink Sync Brain System Status ==="
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
blink-drive setup
blink-drive start
blink-drive stop
blink-drive status

# Pi #2 (Processor)
blink-processor start
blink-processor status
blink-processor process-video /path/to/video.mp4 --output-dir /var/blink_storage/results
```

### Service Management

```bash
sudo systemctl start blink-drive.service
sudo systemctl enable blink-drive.service
sudo systemctl status blink-drive.service
sudo journalctl -u blink-drive.service -f
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
cp /etc/blink-sync-brain/config.yaml $BACKUP_DIR/
cp /var/blink_storage/face_database.pkl $BACKUP_DIR/
cp /var/log/blink_monitor.log $BACKUP_DIR/
echo "Backup completed: $BACKUP_DIR"
```

### Important Configuration Files

```
/boot/firmware/config.txt          # Boot configuration
/etc/modules                       # System modules
/etc/ssh/sshd_config               # SSH configuration
/etc/blink-sync-brain/config.yaml  # Blink Sync Brain config
```

---

*For hardware and OS setup, see the [Pi Zero Setup Guide](pi-zero-setup.md).*
