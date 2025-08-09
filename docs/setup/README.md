# Setup Instructions

This guide provides detailed step-by-step instructions for setting up the Blink Sync Brain system, including annotated screenshots for each stage of the installation process.

## 🍓 Raspberry Pi Zero 2 W Setup

The Blink Sync Brain system is designed to run on two Raspberry Pi Zero 2 W boards. For detailed Pi-specific setup instructions, see:

- **[Complete Pi Zero Setup Guide](pi-zero-setup.md)** - Comprehensive instructions for setting up both Pi boards
- **[Pi Quick Reference](pi-quick-reference.md)** - Quick commands and troubleshooting for Pi management

### Quick Pi Setup Overview

**Pi Zero 2 W #1 (USB Gadget Mode):**
- Acts as virtual USB storage for Blink Sync Module
- Requires USB gadget mode configuration
- Minimal processing requirements

**Pi Zero 2 W #2 (Video Processing Hub):**
- Handles video analysis and face recognition
- Requires video processing dependencies
- Higher performance configuration needed

## 📋 Prerequisites

Before beginning the installation, ensure you have the following requirements:

### System Requirements

![System Requirements](./images/system-requirements.png)

*Figure 1: System requirements checklist and compatibility matrix*

**Minimum Requirements:**
- **Operating System**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- **Processor**: Intel i5 or AMD Ryzen 5 (4 cores minimum)
- **Memory**: 8GB RAM (16GB recommended)
- **Storage**: 50GB available space
- **Network**: Stable internet connection
- **Display**: 1920x1080 resolution minimum

### Software Dependencies

![Software Dependencies](./images/software-dependencies.png)

*Figure 2: Required software dependencies and versions*

**Required Software:**
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **Docker**: 20.10 or higher
- **Git**: 2.30 or higher
- **Database**: PostgreSQL 13+ or MongoDB 5+

## 🚀 Installation Process

### Step 1: Download and Extract

![Download Process](./images/download-process.png)

*Figure 3: Download and extraction process with progress indicators*

**Instructions:**
1. Navigate to the project repository
2. Click the "Download" button or clone the repository
3. Extract the downloaded files to your desired location
4. Verify all files are present in the extraction directory

### Step 2: Environment Setup

![Environment Setup](./images/environment-setup.png)

*Figure 4: Environment configuration and setup process*

**Setup Commands:**
```bash
# Create virtual environment
python -m venv blink-sync-env

# Activate virtual environment
# Windows:
blink-sync-env\Scripts\activate
# macOS/Linux:
source blink-sync-env/bin/activate

# Install Python dependencies
pip install -r requirements.txt
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

### Environment Variables

![Environment Configuration](./images/environment-configuration.png)

*Figure 9: Environment variable configuration panel*

**Key Configuration Variables:**
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=blink_sync_brain
DB_USER=username
DB_PASSWORD=password

# API Configuration
API_PORT=3000
API_SECRET=your-secret-key
CORS_ORIGIN=http://localhost:3001

# Signal Processing
SIGNAL_SAMPLE_RATE=1000
SIGNAL_CHANNELS=8
PROCESSING_BUFFER_SIZE=1024
```

### System Configuration

![System Configuration](./images/system-configuration.png)

*Figure 10: System-wide configuration settings*

**Configuration Options:**
- **Performance Settings**: Processing parameters and optimization
- **Security Settings**: Authentication and encryption
- **Network Settings**: Communication protocols and ports
- **Storage Settings**: Data retention and backup policies
- **Notification Settings**: Alert preferences and delivery methods

## 🔌 Hardware Setup

### Sensor Connection

![Sensor Connection](./images/sensor-connection.png)

*Figure 11: Brain signal sensor connection and setup*

**Connection Process:**
1. **Connect Sensors**: Attach brain signal sensors to the interface
2. **Verify Connections**: Check signal quality and connectivity
3. **Calibrate Sensors**: Run calibration procedures
4. **Test Signal Quality**: Validate signal acquisition
5. **Configure Channels**: Set up channel mapping

### Device Configuration

![Device Configuration](./images/device-configuration.png)

*Figure 12: Device-specific configuration and settings*

**Device Setup:**
- **Driver Installation**: Install necessary device drivers
- **Port Configuration**: Configure communication ports
- **Protocol Settings**: Set up communication protocols
- **Test Connectivity**: Verify device communication
- **Save Configuration**: Store device settings

## 🧪 Testing and Validation

### System Testing

![System Testing](./images/system-testing.png)

*Figure 13: Comprehensive system testing and validation*

**Test Procedures:**
1. **Unit Tests**: Run individual component tests
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete system workflow
4. **Performance Tests**: Validate system performance
5. **Security Tests**: Verify security measures

### Signal Validation

![Signal Validation](./images/signal-validation.png)

*Figure 14: Signal quality validation and testing*

**Validation Steps:**
- **Signal Quality Check**: Verify signal-to-noise ratio
- **Processing Accuracy**: Test signal processing algorithms
- **Classification Testing**: Validate brain state classification
- **Synchronization Test**: Test multi-interface sync
- **Error Handling**: Test error scenarios and recovery

## 🚨 Troubleshooting

### Common Issues

![Common Issues](./images/common-issues.png)

*Figure 15: Common installation issues and solutions*

**Frequent Problems:**
- **Dependency Conflicts**: Resolve package version conflicts
- **Database Connection**: Fix database connectivity issues
- **Port Conflicts**: Resolve port binding conflicts
- **Permission Errors**: Fix file and directory permissions
- **Network Issues**: Troubleshoot network connectivity

### Diagnostic Tools

![Diagnostic Tools](./images/diagnostic-tools-setup.png)

*Figure 16: Built-in diagnostic tools for troubleshooting*

**Diagnostic Features:**
- **System Health Check**: Comprehensive system diagnostics
- **Connection Tester**: Test all system connections
- **Performance Monitor**: Monitor system performance
- **Log Analyzer**: Analyze system logs for errors
- **Configuration Validator**: Validate configuration settings

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