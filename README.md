# NetDeviceScanner

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()

> **Enterprise-grade network device discovery and hardware inventory system**

A high-performance Python tool for automated discovery, information collection, and asset management of network devices (routers, switches) via SSH. Supports multi-vendor environments with concurrent processing capabilities for large-scale networks (400-500+ devices).

## ✨ Features

- 🔍 **Auto-Discovery**: Zero-configuration network scanning with automatic device identification
- 🏢 **Multi-Vendor Support**: Cisco, Huawei, H3C, Juniper, Arista, HP/HPE
- ⚡ **High Concurrency**: Process 400-500+ devices simultaneously (configurable thread pool)
- 📊 **Comprehensive Data**: Hostname, model, serial number, OS version, port count, uptime, module inventory
- 💾 **Flexible Storage**: SQLite database with Excel/CSV/JSON export
- 🔐 **Secure**: SSH-based authentication with environment variable credential management
- 🎯 **Production-Ready**: Built-in retry logic, error handling, and detailed logging

## 📋 Supported Vendors

| Vendor | Device Types | Status |
|--------|--------------|--------|
| **Cisco** | IOS, IOS-XE, NX-OS, IOS-XR, ASA | ✅ Fully Supported |
| **Huawei** | VRP, VRP V8 | ✅ Fully Supported |
| **H3C** | Comware | ✅ Fully Supported |
| **Juniper** | Junos | ✅ Fully Supported |
| **Arista** | EOS | ✅ Fully Supported |
| **HP/HPE** | ProCurve, Comware | ✅ Fully Supported |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- SSH access to target devices
- Common credentials across devices (or device-specific configs)

### Installation

```bash
# Clone the repository
git clone https://github.com/Lawrence-Wei/NetDeviceScanner.git
cd NetDeviceScanner

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file from the example:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Edit `.env` with your SSH credentials:

```env
# SSH credentials for device access
DEVICE_USERNAME=admin
DEVICE_PASSWORD=YourPassword123
DEVICE_SECRET=YourEnablePassword123  # For Cisco enable mode
```

## 📖 Usage

### Option 1: Auto-Discovery (Recommended for Production)

Discover and collect from network segments automatically:

```bash
# Scan single network segment
python main.py scan --network 192.168.1.0/24

# Scan and collect in one step
python main.py scan --network 192.168.1.0/24 --collect

# Scan multiple segments
python main.py scan \
  --network 192.168.1.0/24 \
  --network 10.0.0.0/24 \
  --collect

# Scan from file (for large networks)
python main.py scan --network-file networks.txt --collect
```

**Network file format** (`networks.txt`):
```text
# Core networks
192.168.1.0/24
192.168.2.0/24

# Branch offices
10.1.0.0/24
10.2.0.0/24
```

### Option 2: Manual Configuration

Use predefined device lists for precise control:

```bash
# Use default configuration (config/devices.yaml)
python main.py collect

# Use CSV device list
python main.py collect --source devices.csv --type csv

# Use text file with IP addresses
python main.py collect --source ips.txt --type txt

# Adjust concurrency for large networks
python main.py collect --workers 30 --batch-size 100

# Export to specific format
python main.py collect --export csv --output my_inventory
```

### Testing Connectivity

```bash
# Test all configured devices
python main.py test

# Test single device
python main.py test --ip 192.168.1.1
```

### Data Export & Query

```bash
# Query all devices in database
python main.py query --all

# Query by IP
python main.py query --ip 192.168.1.1

# Query by model
python main.py query --model "C9300"

# Export to Excel
python main.py export --format excel --output inventory_2024

# Export to CSV
python main.py export --format csv

# Export to JSON
python main.py export --format json
```

## 📊 Collected Information

| Field | Description | Example |
|-------|-------------|---------|
| `management_ip` | Device management IP | 192.168.1.1 |
| `hostname` | Device hostname | CORE-SW-01 |
| `model` | Hardware model | C9300-24P-A |
| `serial_number` | Serial number | FCW1234L567 |
| `os_version` | Operating system version | 16.12.4 |
| `os_type` | OS type | IOS, NX-OS, VRP |
| `uptime` | System uptime | 2 years, 15 weeks |
| `total_ports` | Total interface count | 24 |
| `active_ports` | Active interface count | 18 |
| `device_role` | Device role | switch, router, L3 switch |
| `modules` | Hardware modules list | Slot 1: C9300-NM-8X |

## ⚙️ Configuration

### Global Settings (`config/settings.yaml`)

```yaml
# Connection settings
connection:
  timeout: 30          # SSH connection timeout (seconds)
  auth_timeout: 20     # Authentication timeout (seconds)
  read_timeout: 60     # Command execution timeout (seconds)
  max_retries: 3       # Retry attempts on failure
  retry_delay: 5       # Delay between retries (seconds)

# Concurrency settings
concurrency:
  max_workers: 20      # Maximum concurrent threads
  batch_size: 50       # Devices per batch
  batch_delay: 2       # Delay between batches (seconds)

# Storage settings
storage:
  db_type: "sqlite"
  sqlite_path: "./data/devices.db"
  export_dir: "./exports"
  log_dir: "./logs"

# Logging settings
logging:
  level: "INFO"        # DEBUG, INFO, WARNING, ERROR
  max_size: 10         # Max log file size (MB)
  backup_count: 5      # Number of backup files
```

### Device List (`config/devices.yaml`)

```yaml
devices:
  - ip: "192.168.1.1"
    hostname: "CORE-SW-01"
    device_type: "ios"
    role: "L3 switch"
    location: "Data Center A"

  - ip: "192.168.1.2"
    device_type: "nxos"
    role: "L3 switch"
    # Uses credentials from .env file

  # Device with specific credentials
  - ip: "10.0.0.1"
    device_type: "ios"
    role: "router"
    username: "core_admin"
    password: "SpecialPass123"
    secret: "SpecialEnable123"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  scan   │ │ collect │ │  test   │ │ export  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └─────────────┴─────────────┴─────────────┘           │
│                         │                                   │
│                         ▼                                   │
│              ┌─────────────────────┐                       │
│              │     main.py         │                       │
│              │  (CLI Entry Point)  │                       │
│              └──────────┬──────────┘                       │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │    Scanner     │  │   Collector    │  │    Storage   │  │
│  │ (Auto-Discover)│  │ (Concurrent)   │  │ (SQLite)     │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │   Connector    │  │     Parser     │  │   Exporter   │  │
│  │  (SSH/Netmiko) │  │ (Text Parsing) │  │ (Excel/CSV)  │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Advanced Usage

### Performance Tuning

For large networks (500+ devices):

```bash
# Increase workers and batch size
python main.py collect \
  --workers 50 \
  --batch-size 100 \
  --source large_network.yaml
```

Adjust `config/settings.yaml`:

```yaml
concurrency:
  max_workers: 50      # Increase for better network bandwidth
  batch_size: 100      # Larger batches
  batch_delay: 3       # Longer delay between batches

connection:
  timeout: 60          # Longer timeout for slow devices
  max_retries: 5       # More retries for unreliable networks
```

### Batch Processing Workflow

```bash
# Step 1: Scan and save device list
python main.py scan \
  --network 10.0.0.0/16 \
  --save discovered_devices.yaml

# Step 2: Review and edit the device list
# (Remove unwanted devices, add locations, etc.)

# Step 3: Collect in batches
python main.py collect \
  --source discovered_devices.yaml \
  --workers 30 \
  --batch-size 100
```

### Custom Export Script

```python
from src.storage import DataStorage, DataExporter

# Load data from database
storage = DataStorage()
devices = storage.get_all_devices()

# Custom processing
cisco_devices = [d for d in devices if 'cisco' in d['os_type'].lower()]

# Export
exporter = DataExporter()
exporter.export_to_excel(cisco_devices, "cisco_inventory")
```

## 🐛 Troubleshooting

### Connection Timeout

```bash
# Increase timeout values
python main.py collect --timeout 60

# Or modify config/settings.yaml
connection:
  timeout: 60
  read_timeout: 120
```

### Authentication Failures

1. Verify credentials in `.env` file
2. Check device SSH accessibility:
   ```bash
   ssh -v admin@192.168.1.1
   ```
3. Review logs: `logs/collector_YYYYMMDD.log`

### Slow Performance

1. **Network bandwidth**: Reduce `max_workers` if network is congested
2. **Device CPU**: Increase `batch_delay` to give devices processing time
3. **Large networks**: Use `--network-file` instead of multiple `--network` args

### Device Type Detection Issues

Force specific device type:

```yaml
# config/devices.yaml
devices:
  - ip: "192.168.1.1"
    device_type: "cisco_ios"  # Force Cisco IOS type
```

## 📝 Logging

Logs are stored in `logs/` directory:

- `collector_YYYYMMDD.log` - Collection activity and errors
- `scanner_YYYYMMDD.log` - Network scanning results
- `export_YYYYMMDD.log` - Export operations

View recent errors:

```bash
# Linux/macOS
tail -f logs/collector_$(date +%Y%m%d).log | grep ERROR

# Windows (PowerShell)
Get-Content logs/collector_$(Get-Date -Format 'yyyyMMdd').log -Wait | Select-String ERROR
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Netmiko](https://github.com/ktbyers/netmiko) - Multi-vendor SSH library
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Pandas](https://pandas.pydata.org/) - Data processing and export
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

## 📧 Contact

Lawrence Wei - [@Lawrence-Wei](https://github.com/Lawrence-Wei)

Project Link: [https://github.com/Lawrence-Wei/NetDeviceScanner](https://github.com/Lawrence-Wei/NetDeviceScanner)

---

## Roadmap

- [ ] Web UI dashboard (Flask/FastAPI)
- [ ] REST API for integration
- [ ] CMDB integration module
- [ ] Scheduled task support
- [ ] Configuration backup feature
- [ ] SNMP discovery option
- [ ] Multi-threading performance metrics

---

**Happy Scanning! 🚀**
