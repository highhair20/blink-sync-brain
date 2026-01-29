# ✨ Configure USB Gadget Mode for Brain Drive

Brain Drive emulates a USB Flash Drive for the Blink Module. It is controlled by Brain Processor and switches between "Storage Mode" (for Blink) and "Server Mode" (for Brain Processor).

## ✨ Prepare Pi Brain Drive

1. **Connect to the Pi**

   SSH into the Brain Drive that will be used as a USB drive.
   ```bash
   ssh pi@braindrive.local
   ```

1. **Update the System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git python3 python3-pip screen cmake libboost-all-dev
   ```

1. **Install the Blink Sync Brain application**
   ```bash
   cd /opt
   sudo git clone https://github.com/highhair20/blink-sync-brain.git
   # Install minimal dependencies for Brain Drive functionality
   # Install may take some time. I recommend running this in screen.
   screen
   cd blink-sync-brain
   sudo python -m venv env
   source env/bin/activate
   sudo ./env/bin/pip install -r requirements-drive.txt
   ```

1. **Create the Virtual Storage**

   Create the large file that will act as the flash drive's storage. This will take some time so running it in a ```screen``` will help in case your ssh session gets interupted.
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

1. **Install & Configure Samba (for Server Mode)**
   ```bash
   sudo apt install samba -y
   # Create the directory that will be shared
   sudo mkdir -p /var/blink_storage/share
   sudo chown pi:pi /var/blink_storage/share
   # Edit the Samba config file
   sudo nano /etc/samba/smb.conf
   ```

   Add this share definition to the very bottom of the file:
   ```bash
   [BlinkClips]
   comment = Blink Video Clips
   path = /var/blink_storage/share
   read only = no
   browsable = yes
   guest ok = yes
   ```

   Save the file and restart Samba: ```sudo systemctl restart smbd```.


1. **Enable USB Gadget Mode**
   ```bash
   # Edit config.txt
   sudo nano /boot/firmware/config.txt
   ```
   Append the following to the bottom of the file:
   ```bash
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
   # Edit modules file
   sudo nano /etc/modules
   ```
   Add this line to the end of the file:
   ```bash
   dwc2
   ```
   **Note:** Do NOT add `g_mass_storage` here. It must be loaded with the `file=` parameter by the startup script, not at boot.

4. **Reboot to Apply Changes**
   ```bash
   sudo reboot
   ```
--- 
1. **Initial State**
   
   Run the script to put the Brain Drive into storage mode for the first time.

1. **Install Storage Mode Script**
   After the reboot you'll need to ssh into the Pi
   ```bash
   ssh pi@braindrive.local
   ```
   
   Copy the storage mode script to the correct location:
   ```bash
   sudo cp /opt/blink-sync-brain/scripts/drive/start_storage_mode.sh /opt/blink-sync-brain/start_storage_mode.sh
   sudo chmod +x /opt/blink-sync-brain/start_storage_mode.sh
   ```

2. **Create Configuration File**
   ```bash
   # Copy the drive-specific configuration
   sudo cp /opt/blink-sync-brain/configs/drive.yaml /etc/blink-sync-brain/config.yaml
   
   # Edit the configuration if needed
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

   **Important**: Update the `virtual_drive_path` and `virtual_drive_size_gb` to match your setup.

3. **Test Storage Mode**
   ```bash
   # Simple storage mode activation
   sudo /opt/blink-sync-brain/start_storage_mode.sh

   # Check if it's working
   lsmod | grep g_mass_storage
   dmesg | tail -10
   
   # Check if USB gadget is recognized
   lsusb
   ```

4. **Create Systemd Service**

   You have two options for the systemd service:

   **Option A: Simple Shell Script Service (Recommended)**
   ```bash
   sudo cp /opt/blink-sync-brain/scripts/systemd/blink-drive-simple.service /etc/systemd/system/blink-drive.service
   ```
   This service uses the `start_storage_mode.sh` script directly.

   **Option B: Python Application Service**
   ```bash
   sudo cp /opt/blink-sync-brain/scripts/systemd/blink-drive.service /etc/systemd/system/
   ```
   This service uses the full Python application with `blink-sync-brain start --mode usb-gadget`.

   **Note**: Option A is simpler and more reliable for basic USB gadget functionality.

5. **Enable and Start the Service**
   ```bash
   sudo systemctl enable --now blink-drive
   ```

6. **Reboot**
   ```bash
   sudo reboot
   ```

<!--
### Step 4: Install Blink Sync Brain

3. **Create Configuration**
   ```bash
   sudo cp config.yaml.example /etc/blink-sync-brain/config.yaml
   sudo nano /etc/blink-sync-brain/config.yaml
   ```
-->

<!--
5. **Install Python role and Test Storage Mode**
   ```bash
   # Install minimal role
   pip install .[drive]
   sudo mkdir -p /etc/blink-sync-brain
   sudo cp configs/drive.yaml /etc/blink-sync-brain/config.yaml

   # Test storage mode script
   sudo ./opt/blink-sync-brain/start_storage_mode.sh
   
   # Check if the mass storage module is loaded
   lsmod | grep g_mass_storage
   
   # Check if the virtual drive exists
   ls -la /var/blink_storage/
   ```
-->

## ✨ Pi Zero 2 W #2: Video Processing Setup

### Step 1: Install Video Processing Dependencies

1. **Update the System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git python3 python3-pip
   ```

2. **Install System Dependencies**
   ```bash
   # Install video processing dependencies
   sudo apt install -y ffmpeg libsm6 libxext6 libxrender-dev libgomp1
   
   # Install OpenCV dependencies
   sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
   sudo apt install -y libjasper-dev libqtcore4 libqtgui4 libqt4-test
   sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
   sudo apt install -y libv4l-dev libxvidcore-dev libx264-dev
   sudo apt install -y libgtk-3-dev libtiff5-dev libjpeg-dev libpng-dev
   sudo apt install -y libtiff-dev libdc1394-22-dev
   ```

3. **Install Python Dependencies**
   ```bash
   # Install face recognition dependencies
   sudo apt install -y cmake build-essential
   sudo apt install -y libdlib-dev libblas-dev liblapack-dev
   sudo apt install -y libjpeg-dev libpng-dev libtiff-dev
   sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
   sudo apt install -y libv4l-dev libxvidcore-dev libx264-dev
   sudo apt install -y libgtk-3-dev libatlas-base-dev gfortran
   ```

### Step 4: Install Blink Sync Brain (Pi #2 Processor)

1. **Clone the Repository**
   ```bash
   cd /opt
   sudo git clone https://github.com/yourusername/blink-sync-brain.git
   cd blink-sync-brain
   ```

2. **Install Python Dependencies**
   ```bash
   # Install full dependencies for video processing and face recognition
   pip install -r requirements-processor.txt
   
   # Alternative: Install as package with processor extras
   # pip install .[processor]
   ```

3. **Create Configuration**
   ```bash
   sudo cp config.yaml.example /etc/blink-sync-brain/config.yaml
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

4. **Setup Storage Directory**
   ```bash
   sudo mkdir -p /var/blink_storage/videos
   sudo mkdir -p /var/blink_storage/results
   sudo chown pi:pi /var/blink_storage
   ```

### Step 5: Configure Network Access

1. **Setup Static IP using NetworkManager**
   ```bash
   # Connect to the Pi via SSH first
   ssh pi@192.168.1.XXX
   
   # Configure static IP using NetworkManager
   sudo nmcli connection modify "Wi-Fi" ipv4.addresses "192.168.1.201/24"
   sudo nmcli connection modify "Wi-Fi" ipv4.gateway "192.168.1.1"
   sudo nmcli connection modify "Wi-Fi" ipv4.dns "192.168.1.1,8.8.8.8"
   sudo nmcli connection modify "Wi-Fi" ipv4.method "manual"
   
   # Restart the connection
   sudo nmcli connection down "Wi-Fi"
   sudo nmcli connection up "Wi-Fi"
   ```

2. **Enable SSH Access from Pi #1**
   ```bash
   # On Pi #2, generate SSH key
   ssh-keygen -t rsa -b 4096
   
   # Copy public key to Pi #1
   ssh-copy-id pi@192.168.1.200
   ```

### Step 6: Setup Face Recognition Database

1. **Create Face Database**
   ```bash
   # Create directory for face images
   mkdir -p ~/face_images
   
   # Add known faces (place face images in the directory)
   # Image names should be: person_name.jpg
   
   # Setup the face database
   blink-sync-brain setup face-database
   ```

2. **Test Face Recognition**
   ```bash
   # Test with a sample video
   blink-processor process-video /path/to/test_video.mp4 --output-dir /var/blink_storage/results
   ```

## 🔧 System Integration

### Step 1: Connect Pi #1 to Blink Sync Module

1. **Connect USB Cable**
   - Connect Pi #1 to Blink Sync Module using USB-A to USB-A cable
   - Power on Pi #1
   - Wait for USB gadget to initialize

2. **Configure Blink Sync Module**
   - In Blink app, go to Sync Module settings
   - Select "Local Storage"
   - Choose the USB drive (should appear as "Blink Storage Device")

### Step 2: Setup Network Communication

1. **Configure Pi #1 to Access Pi #2**
   ```bash
   # On Pi #1, test connection to Pi #2
   ping 192.168.1.201
   
   # Setup SSH key for passwordless access
   ssh-keygen -t rsa -b 4096
   ssh-copy-id pi@192.168.1.201
   ```

2. **Test Video Transfer**
   ```bash
   # On Pi #2, create a test script
   nano ~/test_transfer.sh
   ```

   Add this script:
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

## 🚨 Troubleshooting

### USB Gadget Issues

1. **Gadget Not Recognized - Complete Diagnostic**
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
   # Check if dwc2 module is available
   modinfo dwc2
   
   # Check if g_mass_storage module is available
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
   which blink-sync-brain
   which start_storage_mode.sh
   
   # Test the command manually
   sudo /opt/blink-sync-brain/start_storage_mode.sh
   
   # Reload systemd and restart service
   sudo systemctl daemon-reload
   sudo systemctl restart blink-drive
   ```

2. **Virtual Drive Not Created**
   ```bash
   # Check if the drive file exists
   ls -la /var/blink_storage/
   
   # Create manually if needed
   sudo dd if=/dev/zero of=/var/blink_storage/virtual_drive.img bs=1G count=32
   sudo mkfs.exfat /var/blink_storage/virtual_drive.img
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
   
   # Reduce processing load
   # Edit config.yaml and increase frame_skip
   ```

### Network Issues

1. **Pi #2 Not Accessible**
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

2. **SSH Connection Issues**
   ```bash
   # Check SSH service
   sudo systemctl status ssh
   
   # Restart SSH if needed
   sudo systemctl restart ssh
   
   # Check NetworkManager connection
   nmcli connection show "Wi-Fi"
   nmcli device wifi list
   ```

## 📊 Monitoring and Maintenance

### System Monitoring

1. **Create Monitoring Script**
   ```bash
   nano ~/monitor_system.sh
   ```

   Add this script:
   ```bash
   #!/bin/bash
   
   echo "=== Blink Sync Brain System Status ==="
   echo "Date: $(date)"
   echo
   
   echo "Pi #1 (USB Gadget):"
   ssh pi@192.168.1.200 "blink-sync-brain status"
   echo
   
   echo "Pi #2 (Video Processing):"
   blink-sync-brain status
   echo
   
   echo "Storage Usage:"
   df -h /var/blink_storage
   echo
   
   echo "Temperature:"
   vcgencmd measure_temp
   ```

2. **Setup Cron Job for Monitoring**
   ```bash
   crontab -e
   ```

   Add this line:
   ```cron
   */30 * * * * /home/pi/monitor_system.sh >> /var/log/blink_monitor.log 2>&1
   ```

### Regular Maintenance

1. **Weekly Tasks**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade
   
   # Clean old logs
   sudo journalctl --vacuum-time=7d
   
   # Check disk usage
   df -h
   ```

2. **Monthly Tasks**
   ```bash
   # Backup face database
   cp /var/blink_storage/face_database.pkl /backup/
   
   # Clean old videos
   blink-sync-brain cleanup --dry-run
   blink-sync-brain cleanup
   ```

## 🔒 Security Considerations

1. **Change Default Passwords**
   ```bash
   # Change pi user password
   passwd
   
   # Create new user (optional)
   sudo adduser blinkuser
   sudo usermod -aG sudo blinkuser
   ```

2. **Firewall Configuration**
   ```bash
   # Install and configure firewall
   sudo apt install -y ufw
   sudo ufw allow ssh
   sudo ufw allow 8080  # If using web interface
   sudo ufw enable
   ```

3. **Regular Updates**
   ```bash
   # Setup automatic security updates
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```
