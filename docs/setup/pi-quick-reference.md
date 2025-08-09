# Raspberry Pi Quick Reference Guide

Quick commands and tips for setting up and managing your Raspberry Pi Zero 2 W boards.

## 🍎 Mac-Specific Setup

### SD Card Preparation on macOS
```bash
# List all disk devices
diskutil list

# Unmount the SD card (replace diskX with your card)
diskutil unmountDisk /dev/diskX

# Flash the image (WARNING: This will erase the card)
sudo dd if=raspios-lite.img of=/dev/rdiskX bs=1m

# Eject the card when done
diskutil eject /dev/diskX

# Re-insert and mount for configuration
# The boot partition should auto-mount to /Volumes/boot
# For newer Pi OS versions, use /Volumes/boot/firmware/
```

### Network Scanning on macOS
```bash
# Install network scanning tools
brew install nmap
brew install arp-scan

# Scan for Pi devices
nmap -sn 192.168.1.0/24
sudo arp-scan --localnet | grep -i raspberry

# Find Pi's IP address
ping -c 1 raspberrypi.local
```

### Initial Pi Configuration Files
```bash
# Enable SSH (newer Pi OS: /boot/firmware/, older: /boot/)
touch /Volumes/boot/firmware/ssh

# Configure WiFi (newer Pi OS: /boot/firmware/, older: /boot/)
nano /Volumes/boot/firmware/wpa_supplicant.conf

# Check if files exist
ls -la /Volumes/boot/firmware/
```

## 🔧 Essential Commands

### System Configuration
```bash
# Set keyboard layout
sudo raspi-config nonint do_configure_keyboard us          # US English
sudo raspi-config nonint do_configure_keyboard gb          # UK English
sudo raspi-config nonint do_configure_keyboard de          # German
sudo raspi-config nonint do_configure_keyboard fr          # French
sudo raspi-config nonint do_configure_keyboard es          # Spanish

# Set timezone
sudo timedatectl set-timezone America/New_York             # US Eastern
sudo timedatectl set-timezone America/Chicago              # US Central
sudo timedatectl set-timezone America/Denver               # US Mountain
sudo timedatectl set-timezone America/Los_Angeles          # US Pacific
sudo timedatectl set-timezone Europe/London                # UK
sudo timedatectl set-timezone Europe/Berlin                # Germany
sudo timedatectl set-timezone Asia/Tokyo                   # Japan
sudo timedatectl set-timezone Australia/Sydney             # Australia

# Set locale
sudo raspi-config nonint do_change_locale en_US.UTF-8      # US English
sudo raspi-config nonint do_change_locale en_GB.UTF-8      # UK English
sudo raspi-config nonint do_change_locale de_DE.UTF-8      # German

# Check current settings
timedatectl status
locale
```

### System Information
```bash
# Check Pi model and version
cat /proc/device-tree/model

# Check CPU temperature
vcgencmd measure_temp

# Check memory usage
free -h

# Check disk usage
df -h

# Check network interfaces
ip addr show

# Check running services
sudo systemctl list-units --type=service --state=running
```

### Network Configuration
```bash
# Find Pi's IP address
hostname -I

# Test network connectivity
ping 8.8.8.8

# Check NetworkManager status
nmcli device status
nmcli connection show

# Check WiFi signal strength
nmcli device wifi list

# Scan for WiFi networks
nmcli device wifi rescan
nmcli device wifi list
```

### Package Management
```bash
# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade

# Install a package
sudo apt install package_name

# Remove a package
sudo apt remove package_name

# Clean package cache
sudo apt autoremove
sudo apt autoclean
```

## 🍓 Pi Zero 2 W Specific

### Enable USB Gadget Mode
```bash
# Edit boot configuration
sudo nano /boot/config.txt

# Add these lines:
dtoverlay=dwc2
dtparam=usb_con=1

# Edit modules
sudo nano /etc/modules

# Add these lines:
dwc2
g_mass_storage

# Reboot to apply changes
sudo reboot
```

### Check USB Gadget Status
```bash
# Check if modules are loaded
lsmod | grep dwc2
lsmod | grep g_mass_storage

# Check gadget directory
ls /sys/kernel/config/usb_gadget/

# Check USB device info
lsusb
```

### Performance Optimization
```bash
# Enable GPU memory split (for video processing)
sudo nano /boot/config.txt

# Add or modify:
gpu_mem=128

# Overclock (use with caution)
sudo nano /boot/config.txt

# Add:
arm_freq=1000
over_voltage=2
```

## 📱 Blink Sync Brain Commands

### Installation
```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/blink-sync-brain.git
cd blink-sync-brain

# Install dependencies
sudo pip3 install -r requirements.txt

# Copy configuration
sudo cp config.yaml.example /etc/blink-sync-brain/config.yaml
```

### Service Management
```bash
# Start USB gadget service
sudo systemctl start blink-usb-gadget.service

# Enable auto-start
sudo systemctl enable blink-usb-gadget.service

# Check service status
sudo systemctl status blink-usb-gadget.service

# View service logs
sudo journalctl -u blink-usb-gadget.service -f
```

### Application Commands
```bash
# Check system status
blink-sync-brain status

# Process a video
blink-sync-brain process-video /path/to/video.mp4

# Setup face database
blink-sync-brain setup face-database

# Clean old files
blink-sync-brain cleanup

# Run tests
blink-sync-brain test
```

## 🔒 Security Commands

### User Management
```bash
# Change pi user password
passwd

# Create new user
sudo adduser newuser

# Add user to sudo group
sudo usermod -aG sudo newuser

# Switch to new user
su - newuser
```

### SSH Configuration
```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096

# Copy key to another Pi
ssh-copy-id pi@192.168.1.201

# Test SSH connection
ssh pi@192.168.1.201

# Disable password authentication (after key setup)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### Firewall Setup
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow specific port
sudo ufw allow 8080

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status
```

## 📊 Monitoring Commands

### System Monitoring
```bash
# Real-time system monitor
htop

# Check system load
uptime

# Monitor disk I/O
iotop

# Check network connections
netstat -tuln

# Monitor USB devices
lsusb -v
```

### Log Monitoring
```bash
# View system logs
sudo journalctl -f

# View specific service logs
sudo journalctl -u service_name -f

# View recent boot logs
sudo journalctl -b

# Clean old logs
sudo journalctl --vacuum-time=7d
```

### Storage Monitoring
```bash
# Check storage usage
df -h

# Find large files
sudo find / -type f -size +100M -exec ls -lh {} \;

# Check inode usage
df -i

# Monitor directory size
du -sh /var/blink_storage/*
```

## 🔧 Troubleshooting Commands

### Network Issues
```bash
# Restart NetworkManager
sudo systemctl restart NetworkManager

# Restart WiFi connection
sudo nmcli connection down "Wi-Fi" && sudo nmcli connection up "Wi-Fi"

# Check NetworkManager configuration
nmcli connection show "Wi-Fi"

# Check WiFi configuration
sudo cat /etc/wpa_supplicant/wpa_supplicant.conf

# Test DNS resolution
nslookup google.com
```

### USB Issues
```bash
# Check USB devices
lsusb

# Check USB gadget status
ls /sys/kernel/config/usb_gadget/

# Reload USB modules
sudo modprobe -r dwc2 g_mass_storage
sudo modprobe dwc2 g_mass_storage

# Check USB gadget logs
dmesg | grep -i usb
```

### Performance Issues
```bash
# Check CPU frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Check memory pressure
cat /proc/pressure/memory

# Check temperature
vcgencmd measure_temp

# Check throttling
vcgencmd get_throttled
```

## 📝 Configuration Files

### Important Files
```bash
# Boot configuration
/boot/config.txt

# Network configuration
/etc/network/interfaces
/etc/wpa_supplicant/wpa_supplicant.conf

# SSH configuration
/etc/ssh/sshd_config

# System modules
/etc/modules

# Blink Sync Brain config
/etc/blink-sync-brain/config.yaml
```

### Common Configurations

#### Static IP Setup
```bash
# Using NetworkManager (recommended)
sudo nmcli connection modify "Wi-Fi" ipv4.addresses "192.168.1.200/24"
sudo nmcli connection modify "Wi-Fi" ipv4.gateway "192.168.1.1"
sudo nmcli connection modify "Wi-Fi" ipv4.dns "192.168.1.1,8.8.8.8"
sudo nmcli connection modify "Wi-Fi" ipv4.method "manual"
sudo nmcli connection down "Wi-Fi" && sudo nmcli connection up "Wi-Fi"

# Legacy dhcpcd method
sudo nano /etc/dhcpcd.conf
```

#### WiFi Configuration
```bash
# Using NetworkManager (recommended)
sudo nmcli device wifi connect "YOUR_WIFI_SSID" password "YOUR_WIFI_PASSWORD"

# Or create a connection profile
sudo nmcli connection add type wifi con-name "MyWiFi" ifname wlan0 ssid "YOUR_WIFI_SSID"
sudo nmcli connection modify "MyWiFi" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "YOUR_WIFI_PASSWORD"
sudo nmcli connection up "MyWiFi"

# Legacy wpa_supplicant method (for initial setup)
# Note: In newer Pi OS versions, place in /boot/firmware/ on SD card
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

## 🚀 Performance Tips

### For Pi Zero 2 W
```bash
# Reduce GPU memory usage
sudo nano /boot/config.txt
# Set: gpu_mem=64

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Use swap file for memory
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### For Video Processing
```bash
# Increase process priority
sudo nice -n -10 blink-sync-brain process-video video.mp4

# Use tmpfs for temporary files
sudo mount -t tmpfs -o size=512M tmpfs /tmp

# Monitor during processing
watch -n 1 'ps aux | grep blink-sync-brain'
```

## 📚 Useful Scripts

### System Status Script
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

### Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp /etc/blink-sync-brain/config.yaml $BACKUP_DIR/

# Backup face database
cp /var/blink_storage/face_database.pkl $BACKUP_DIR/

# Backup logs
cp /var/log/blink_monitor.log $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

---

*For detailed setup instructions, see the [Pi Zero Setup Guide](pi-zero-setup.md).* 