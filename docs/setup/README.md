# Setup Instructions

This guide covers installing and operating the two-role layout: Pi #1 Drive (USB Gadget) and Pi #2 Processor (video/face).

## 🍓 Raspberry Pi Zero 2 W Setup

Two Raspberry Pi Zero 2 W boards:
- Pi #1 Drive: USB Gadget exposed to Blink Sync Module
- Pi #2 Processor: Video processing and face recognition

See: **[Pi Zero Setup Guide](pi-zero-setup.md)** and **[Pi Quick Reference](pi-quick-reference.md)**.

### Quick Pi Setup Overview

**Pi #1 Drive:**
- Virtual USB storage for Blink Sync Module
- Configure USB gadget, Samba optional

**Pi #2 Processor:**
- Video analysis, face recognition
- Installs OpenCV/face-recognition and runs watcher

## 📋 Prerequisites

- Raspberry Pi OS Lite 64-bit on both Pis
- SSH enabled and network configured
- Python 3.8+ on both

## 🚀 Install by Role

### Pi #1 Drive
```bash
pip install .[drive]
sudo mkdir -p /etc/blink-sync-brain && sudo cp configs/drive.yaml /etc/blink-sync-brain/config.yaml
sudo cp scripts/drive/usb-gadget.sh /opt/blink-sync-brain/usb-gadget.sh && sudo chmod +x /opt/blink-sync-brain/usb-gadget.sh
sudo cp scripts/systemd/blink-drive.service /etc/systemd/system/
sudo systemctl enable --now blink-drive
```

### Pi #2 Processor
```bash
sudo apt update && sudo apt install -y ffmpeg
pip install .[processor]
sudo mkdir -p /etc/blink-sync-brain && sudo cp configs/processor.yaml /etc/blink-sync-brain/config.yaml
sudo cp scripts/systemd/blink-processor.service /etc/systemd/system/
sudo systemctl enable --now blink-processor
```

### Step 3: Database Configuration

![Database Setup](./images/database-setup.png)

*Figure 5: Database configuration and connection setup*

**Database Configuration:**
1. **Install Database**: Install PostgreSQL or MongoDB
2. **Create Database**: Create a new database for the application
3. **Configure Connection**: Update connection settings in config files
4. **Run Migrations**: Execute database migration scripts
5. **Verify Connection**: Test database connectivity

### Step 4: API Server Setup

![API Server Setup](./images/api-server-setup.png)

*Figure 6: API server configuration and startup process*

**Server Configuration:**
```bash
# Navigate to server directory
cd server

# Install Node.js dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env file with your settings

# Start the server
npm start
```

### Step 5: Frontend Setup

![Frontend Setup](./images/frontend-setup.png)

*Figure 7: Frontend application setup and configuration*

**Frontend Configuration:**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure API endpoints
# Edit src/config/api.js with server URL

# Start development server
npm run dev
```

### Step 6: Signal Processing Setup

![Signal Processing Setup](./images/signal-processing-setup.png)

*Figure 8: Signal processing module configuration*

**Processing Configuration:**
1. **Install Dependencies**: Install signal processing libraries
2. **Configure Parameters**: Set up processing parameters
3. **Test Connections**: Verify sensor connections
4. **Calibrate System**: Run calibration procedures
5. **Validate Setup**: Test signal processing pipeline

## 🔧 Configuration

- Pi #1: edit `/etc/blink-sync-brain/config.yaml` based on `configs/drive.yaml`
- Pi #2: edit `/etc/blink-sync-brain/config.yaml` based on `configs/processor.yaml`

### System Configuration

![System Configuration](./images/system-configuration.png)

*Figure 10: System-wide configuration settings*

**Configuration Options:**
- **Performance Settings**: Processing parameters and optimization
- **Security Settings**: Authentication and encryption
- **Network Settings**: Communication protocols and ports
- **Storage Settings**: Data retention and backup policies
- **Notification Settings**: Alert preferences and delivery methods

## 🔌 Blink Integration

1. Connect Pi #1’s USB data port to the Blink Sync Module
2. In the Blink app, choose Local Storage and select the presented drive

## 🧪 Quick checks

```bash
# Pi #1
blink-drive status

# Pi #2
blink-processor status
blink-processor process-video /path/to/test.mp4 --output-dir /var/blink_storage/results
```

## 🚨 Troubleshooting

See the role-specific sections in `pi-zero-setup.md` for USB gadget and processing notes.

## 📊 Post-Installation

### Performance Optimization

![Performance Optimization](./images/performance-optimization.png)

*Figure 17: Post-installation performance optimization*

**Optimization Steps:**
1. **Resource Allocation**: Optimize CPU and memory usage
2. **Database Tuning**: Optimize database performance
3. **Network Optimization**: Optimize network communication
4. **Caching Setup**: Configure caching for better performance
5. **Monitoring Setup**: Set up performance monitoring

### Security Hardening

![Security Hardening](./images/security-hardening.png)

*Figure 18: Security hardening and best practices*

**Security Measures:**
- **Firewall Configuration**: Set up network firewalls
- **SSL/TLS Setup**: Configure secure communication
- **Access Control**: Implement proper access controls
- **Audit Logging**: Enable comprehensive audit logging
- **Regular Updates**: Set up automatic security updates

## 📚 Additional Resources

### Documentation Links

![Documentation Resources](./images/documentation-resources.png)

*Figure 19: Additional documentation and support resources*

**Available Resources:**
- **API Documentation**: [API Guide](../api/README.md)
- **Architecture Guide**: [Architecture Documentation](../architecture/README.md)
- **User Interface Guide**: [UI Documentation](../ui/README.md)
- **Troubleshooting Guide**: [Troubleshooting Documentation](../troubleshooting/README.md)
- **Community Support**: Online forums and support channels

---

*For detailed troubleshooting, see the [Troubleshooting Guide](../troubleshooting/README.md).* 