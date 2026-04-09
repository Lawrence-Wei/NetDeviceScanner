# 网络设备信息收集系统

> Multi-Vendor Network Device Hardware Information Retriever  
> 版本: 2.0.0 | Python 3.8+

## 简介

这是一个用于批量收集网络设备（路由器、交换机）硬件信息的 Python 工具。支持**多厂商设备**（Cisco、华为、H3C、Juniper、Arista、HP），大规模设备采集（400-500台以上），通过 SSH 连接设备并自动解析设备信息。

## 🆕 v2.0 新特性

- ✅ **多厂商支持**：Cisco、华为、H3C、Juniper、Arista、HP
- ✅ **网段文件**：支持从文件读取大量网段（解决命令行太长问题）
- ✅ **自动识别**：Netmiko autodetect 自动识别设备类型
- ✅ **混合环境**：可在同一网段中识别不同厂商设备
- ✅ **零配置**：网络扫描 + 自动发现，无需手动配置设备清单

## 支持的厂商

| 厂商 | 设备类型 | 状态 |
|------|---------|------|
| Cisco | IOS, IOS-XE, NX-OS, IOS-XR, ASA | ✅ 完全支持 |
| 华为 (Huawei) | VRP, VRP V8 | ✅ 完全支持 |
| 新华三 (H3C) | Comware | ✅ 完全支持 |
| Juniper | Junos | ✅ 完全支持 |
| Arista | EOS | ✅ 完全支持 |
| HP/HPE | ProCurve, Comware | ✅ 完全支持 |

## 功能特性

- ✅ **批量采集**：支持并发连接（默认20并发），快速采集大量设备
- ✅ **多厂商支持**：自动识别并采集不同厂商设备
- ✅ **网络扫描**：自动发现网段中的网络设备（零配置）
- ✅ **网段文件**：从文件读取大量网段（支持注释、空行）
- ✅ **信息全面**：采集 hostname、型号、序列号、版本、端口数、uptime 等
- ✅ **多数据源**：支持 YAML、CSV、TXT 格式的设备清单
- ✅ **数据导出**：支持 Excel、CSV、JSON 格式导出
- ✅ **数据存储**：SQLite 数据库持久化存储
- ✅ **进度显示**：实时显示采集进度和统计
- ✅ **错误处理**：自动重试（3次）、详细错误日志
- ✅ **内置测试**：包含验证脚本和集成测试

## 采集的信息

| 字段 | 说明 | 支持厂商 |
|------|------|---------|
| hostname | 设备主机名 | 全部 |
| model | 设备型号（如 C9300-24P） | 全部 |
| serial_number | 序列号 | 全部 |
| os_version | 系统版本 | 全部 |
| os_type | 系统类型（IOS/VRP/EOS/Junos） | 全部 |
| uptime | 运行时间 | Cisco, Huawei, H3C, Arista |
| total_ports | 总端口数 | 全部 |
| management_ip | 管理 IP | 全部 |
| device_role | 设备角色（switch/router） | 全部 |

## 安装

### 快速开始（Ubuntu/Linux）

```bash
# 1. 解压文件
unzip hardware-info-retriever_v*.zip
cd hardware-info-retriever

# 2. 运行自动配置脚本
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh

# 3. 开始使用
python3 main.py scan --network 192.168.1.0/24 --collect
```

🔗 **Ubuntu 用户**：遇到问题？查看 [TROUBLESHOOTING_UBUNTU.md](TROUBLESHOOTING_UBUNTU.md)

---

### 详细安装步骤

#### 1. 克隆或下载项目

```bash
cd hardware-info-retriever
```

#### 2. 创建虚拟环境（推荐）

**Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Ubuntu/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置凭据

⚠️ **重要**：`.env` 文件不包含在压缩包中（安全原因），需要手动创建

##### 📋 .env 文件是什么？

`.env` 文件用于**存储 SSH 登录凭据**，这样程序可以自动登录网络设备采集信息。

- **DEVICE_USERNAME** = 登录交换机/路由器的 SSH 用户名
- **DEVICE_PASSWORD** = 登录交换机/路由器的 SSH 密码  
- **DEVICE_SECRET** = Enable 密码（Cisco 设备需要，用于进入特权模式）

💡 **"DEVICE"含义**：网络设备（Device）的统称，包括所有品牌的交换机、路由器

##### 创建步骤：

**Windows**:
```bash
copy .env.example .env
notepad .env
```

**Ubuntu/Linux**:
```bash
cp .env.example .env
nano .env  # 或使用 vim, gedit 等编辑器
```

##### 填入您的实际凭据：

```bash
# 示例：如果您的交换机登录账号是 admin，密码是 Cisco@123
DEVICE_USERNAME=admin
DEVICE_PASSWORD=Cisco@123
DEVICE_SECRET=Cisco@123      # Enable 密码，如果有的话
```

🔒 **安全提示**：
- `.env` 文件包含敏感信息，请勿分享或提交到代码仓库
- 建议使用只读权限的设备账号（无需配置权限）
- 确保所有设备使用相同的凭据，或使用设备通用账号

## 配置设备清单

### ⚠️ 重要：不同设备可能有不同的凭据

您的担心完全正确！**现实中常见情况**：

- 🏢 **不同部门**的设备可能使用不同密码
- 🔒 **高安全区域**的设备可能有更复杂的密码
- 🛠️ **老旧设备**可能还在使用旧的凭据
- 🏭 **不同厂商**的设备可能有不同的默认账号

### 解决方案：灵活配置

#### 方案 1：所有设备使用相同凭据（最简单）

如果您的所有设备使用相同的用户名和密码：

```bash
# 只需配置 .env 文件
DEVICE_USERNAME=admin
DEVICE_PASSWORD=CommonPassword123
DEVICE_SECRET=CommonEnable123
```

#### 方案 2：部分设备有不同凭据（推荐）

**工作原理**：
1. `.env` 文件配置**默认凭据**（大部分设备使用）
2. `devices.yaml` 中为**特殊设备**单独指定凭据
3. 系统会自动优先使用设备的专用凭据

**实际示例**：

```yaml
# config/devices.yaml
devices:
  # 普通设备：使用 .env 中的默认凭据
  - ip: "192.168.1.1"
    device_type: "cisco_ios"
    role: "switch"
    # 不配置 username/password，自动使用 .env 中的值

  - ip: "192.168.1.2"
    device_type: "cisco_ios"
    role: "switch"
    # 同上

  # 特殊设备1：老旧设备，还在用旧密码
  - ip: "192.168.2.1"
    device_type: "ios"
    role: "switch"
    location: "老旧机房"
    # 单独指定这台设备的凭据
    username: "oldadmin"
    password: "OldPassword123"
    secret: "OldEnable123"

  # 特殊设备2：核心机房，高安全凭据
  - ip: "10.0.0.1"
    device_type: "cisco_ios"
    role: "router"
    location: "核心区域"
    username: "coreadmin"
    password: "V3ryS3cur3P@ss!"
    secret: "V3ryS3cur3Enable!"

  # 特殊设备3：华为设备，不同的默认账号
  - ip: "192.168.3.1"
    device_type: "huawei"
    role: "switch"
    username: "huawei_admin"  # 华为特有账号
    password: "Huawei@2024"
```

**优势**：
- ✅ 大部分设备使用默认凭据，配置简单
- ✅ 特殊设备单独配置，灵活处理
- ✅ 修改默认密码时，只需更新 .env 文件

📖 **详细说明**：查看 [凭据管理指南](docs/CREDENTIALS_GUIDE.md) 了解更多实际场景和配置示例

### 方式一：YAML 配置（推荐）

编辑 `config/devices.yaml`：

```yaml
devices:
  - ip: "192.168.1.1"
    hostname: "CORE-SW-01"
    device_type: "ios"          # ios, nxos, ios_xe
    role: "L3 Switch"           # switch, router, L3 switch
    location: "数据中心A"

  - ip: "192.168.1.2"
    device_type: "nxos"
    role: "L3 Switch"
```

### 方式二：CSV 文件

创建 CSV 文件（参考 `config/devices_template.csv`）：

```csv
ip,device_type,role,hostname,location
192.168.1.1,ios,L3 switch,CORE-SW-01,数据中心
192.168.1.2,nxos,L3 switch,CORE-SW-02,数据中心
```

### 方式三：IP 列表文本文件

创建文本文件（参考 `config/devices_template.txt`）：

```
# 每行一个IP
192.168.1.1
192.168.1.2
192.168.2.1
```

## 使用方法

### 🔥 方式1：自动扫描（推荐 - 零配置）

**适用场景**：生产环境有大量设备，无法手动配置清单，支持混合厂商

```bash
# 扫描单个网段，自动发现所有网络设备
python main.py scan --network 192.168.1.0/24

# 扫描多个网段
python main.py scan --network 192.168.1.0/24 --network 10.0.0.0/24

# 🆕 从文件读取大量网段（解决命令行太长问题）
python main.py scan --network-file networks.txt

# 扫描并立即采集信息（一步完成）
python main.py scan --network 192.168.1.0/24 --collect

# 扫描并保存设备清单到文件（供后续使用）
python main.py scan --network 192.168.1.0/24 --save discovered_devices.yaml
```

**工作原理**：
1. 扫描指定网段，检测开放 SSH 端口的主机
2. 尝试 SSH 连接，自动识别设备类型（Cisco/Huawei/H3C/Juniper等）
3. 自动获取 hostname 和设备角色
4. 生成设备清单或直接采集

**网段文件格式** (`networks.txt`)：

```text
# 核心网段
192.168.1.0/24
192.168.2.0/24

# 分支机构
10.1.0.0/24
10.2.0.0/24

# 数据中心
172.16.0.0/16
```

### 方式2：手动配置采集

### 手动配置采集

**适用场景**：设备数量少，或需要精确控制

```bash
# 使用默认配置（config/devices.yaml）
python main.py collect

# 指定 CSV 文件
python main.py collect --source devices.csv --type csv

# 指定 IP 列表文件
python main.py collect --source ips.txt --type txt
```

### 调整并发参数

```bash
# 设置并发数为 30，批次大小为 100
python main.py collect --workers 30 --batch-size 100
```

### 指定导出格式

```bash
# 导出为 Excel
python main.py collect --export excel --output my_devices

# 导出为 CSV
python main.py collect --export csv

# 不自动导出
python main.py collect --export none
```

### 测试连接

```bash
# 测试所有设备连接
python main.py test

# 测试单个设备
python main.py test --ip 192.168.1.1
```

### 查询数据库

```bash
# 按 IP 查询
python main.py query --ip 192.168.1.1

# 按型号查询
python main.py query --model C9300

# 按主机名查询
python main.py query --hostname CORE

# 显示所有设备
python main.py query --all
```

### 导出已有数据

```bash
# 导出全部数据到 Excel
python main.py export --format excel

# 导出到 CSV
python main.py export --format csv --output inventory
```

### 清空数据库

```bash
python main.py clear --confirm
```

## 高级配置

编辑 `config/settings.yaml` 可调整：

- 连接超时时间
- 并发数和批次设置
- 数据库路径
- 日志级别

```yaml
connection:
  timeout: 30
  max_retries: 3

concurrency:
  max_workers: 20
  batch_size: 50
```

## 项目结构

```
hardware-info-retriever/
├── main.py                  # 主程序入口（CLI）
├── verify_system.py         # 环境验证脚本
├── test_integration.py      # 集成测试脚本
├── requirements.txt         # 依赖列表
├── .env.example             # 环境变量模板
├── config/
│   ├── settings.yaml        # 系统配置
│   ├── devices.yaml         # 设备清单
│   ├── devices_template.csv # CSV 模板
│   └── devices_template.txt # TXT 模板
├── src/
│   ├── __init__.py
│   ├── models.py            # 数据模型
│   ├── config_manager.py    # 配置管理
│   ├── connector.py         # SSH 连接器（Netmiko）
│   ├── parser.py            # 命令输出解析
│   ├── collector.py         # 并发采集器
│   ├── storage.py           # SQLite + 导出
│   └── logger.py            # 日志配置
├── data/                    # 数据库文件（运行时生成）
├── exports/                 # 导出文件
└── logs/                    # 日志文件
```

---

## 🏭 生产环境使用指南

### 关键要求

| 要求 | 说明 |
|------|------|
| **零配置** | 使用 `scan` 命令自动发现，无需手动配置 |
| **稳定性** | 运行 `production_check.py` 确保系统就绪 |
| **渐进式** | 先小批量测试（5-10台），再批量运行 |
| **监控** | 实时查看 `logs/` 目录下的日志 |

### 生产环境工作流程

```bash
# 1. 环境检查（必须100%通过）
python production_check.py

# 2. 小批量测试（先测试一个网段）
python main.py scan --network 192.168.1.0/24 --collect
# 检查结果，确认无误

# 3. 批量采集（多个网段）
python main.py scan \
  --network 192.168.1.0/24 \
  --network 192.168.2.0/24 \
  --network 10.0.0.0/22 \
  --collect

# 4. 导出结果
python main.py export --format excel --output production_inventory
```

### 性能调优

```bash
# 对于大型网络（500+设备）
python main.py scan \
  --network 10.0.0.0/16 \
  --scan-workers 100 \    # 增加扫描并发
  --timeout 3 \            # 减少超时（如果网络很好）
  --save large_network.yaml

# 然后分批采集
python main.py collect --source large_network.yaml --workers 30 --batch-size 100
```

### 错误处理策略

系统内置：
- 自动重试 3 次（可在 `config/settings.yaml` 调整）
- 失败设备单独记录到日志
- 不会因为单个设备失败而中断整体任务

查看失败设备：
```bash
# 查看日志
cat logs/collector_YYYYMMDD.log | grep "✗"

# 或在采集结果中查看
python main.py query --all
```

---

## ⚠️ 收到此项目后的验证流程

**重要**：在使用前请按以下步骤验证系统完整性。

### 步骤 1：创建虚拟环境并安装依赖

```bash
cd hardware-info-retriever

# 创建虚拟环境
python -m venv .venv

# 激活（Windows）
.venv\Scripts\activate

# 激活（Linux/Mac）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2：运行环境验证（约30秒）

```bash
python verify_system.py --full
```

期望输出：所有测试项显示 ✓

### 步骤 3：运行集成测试（约5秒）

```bash
python test_integration.py
```

期望输出：`总计: 4/4 通过`

这将验证：
- IOS 设备输出解析逻辑
- NX-OS 设备输出解析逻辑
- Excel/CSV/JSON 导出功能
- SQLite 数据库读写

### 步骤 4：配置凭据

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，填入真实的 SSH 凭据。

### 步骤 5：生产环境预检查（推荐）

```bash
python production_check.py
```

此脚本会：
- 验证环境完整性
- 测试网络连通性
- 检查配置参数是否适合生产环境
- 提供优化建议

### 步骤 6：测试单台真实设备（可选）

```bash
python main.py test --ip <你的交换机IP>
```

### 步骤 7：小批量测试（强烈推荐）

```bash
# 方法A: 自动发现小网段
python main.py scan --network 192.168.1.0/28 --collect

# 方法B: 手动配置5-10台
python main.py collect --source config/devices.yaml
```

### 步骤 8：批量采集（生产环境）

```bash
# 自动发现所有设备
python main.py scan \
  --network 192.168.0.0/16 \
  --network 10.0.0.0/16 \
  --collect
```

---

## 验证层次说明

| 验证层次 | 工具 | 检测的问题 | 耗时 |
|---------|------|-----------|------|
| 环境检查 | `verify_system.py --full` | 依赖缺失、语法错误、配置问题 | ~30秒 |
| 逻辑测试 | `test_integration.py` | 解析bug、数据流问题 | ~5秒 |
| 连接测试 | `main.py test --ip x.x.x.x` | 网络/认证问题 | 需设备 |
| 实际采集 | `main.py collect` | 设备兼容性 | 需设备 |

---

## 核心依赖说明

| 库 | 用途 | 说明 |
|---|------|------|
| netmiko | SSH连接 | 网络自动化标准库，专为Cisco设备设计 |
| paramiko | SSH协议 | netmiko的底层依赖 |
| pandas | 数据处理 | Excel/CSV导出 |
| openpyxl | Excel支持 | pandas写入xlsx格式需要 |
| sqlalchemy | 数据库ORM | SQLite持久化存储 |
| pyyaml | YAML解析 | 配置文件读取 |
| rich | 终端美化 | 进度条、表格显示 |

---

## 📚 文档

- **[MULTI_VENDOR_GUIDE.md](MULTI_VENDOR_GUIDE.md)** - 多厂商设备支持详细指南
- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** - 生产环境部署指南
- **[SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)** - 解决方案总结

---

## 注意事项

### 多厂商环境
1. **凭据统一**：建议使用统一的管理员账号和密码
2. **命令差异**：系统自动处理不同厂商的命令差异（show vs display）
3. **混合扫描**：可以在同一网段中识别不同厂商设备
4. **自动过滤**：非网络设备（服务器、PC）自动跳过

### 大规模部署
1. **网段文件**：超过 10 个网段建议使用 `--network-file`
2. **并发调优**：
   - 扫描并发：`--scan-workers 100`（大网段）
   - 采集并发：`--workers 30-50`（400-500 台设备）
3. **批次处理**：超过 1000 台设备建议先扫描保存，再分批采集

### 凭据安全
1. **不要分享**：不要将 `.env` 文件分享或提交到版本控制
2. **权限控制**：使用只读账号，无需配置权限
3. **定期轮换**：定期更换密码

### 其他
1. **超时设置**：老旧设备可能需要更长的超时时间
2. **设备类型**：系统自动识别，无需手动指定

## 故障排除

### 连接超时
- 检查网络连通性（ping 测试）
- 增加 `--timeout` 参数值
- 确认 SSH 端口已启用（默认 22）

### 认证失败
- 确认用户名密码正确（检查 .env 文件）
- 检查 AAA 配置
- 确认用户有足够权限（查看设备权限）
- 📖 查看 [凭据管理指南](docs/CREDENTIALS_GUIDE.md) 了解多凭据配置

### 设备识别失败
- 查看日志：`logs/` 目录下的日志文件
- 确认设备支持 SSH
- 检查是否为支持的厂商（Cisco/Huawei/H3C/Juniper/Arista/HP）

### 解析失败
- 查看详细日志获取错误信息
- 某些老旧版本可能输出格式不同
- 提issue报告不支持的设备类型

---

## 文档导航

- 📖 [凭据管理指南](docs/CREDENTIALS_GUIDE.md) - 如何为不同设备配置不同的SSH凭据
- 📋 [设备类型说明](docs/DEVICE_TYPES.md) - 支持的设备类型和别名
- 🐧 [Ubuntu 测试指南](docs/UBUNTU_TESTER_GUIDE.md) - Ubuntu系统测试步骤
- 🔧 [Ubuntu 故障排除](TROUBLESHOOTING_UBUNTU.md) - Ubuntu常见问题解决

---

## 技术支持

如遇问题，请提供：
1. `python verify_system.py --full` 的输出
2. `logs/` 目录下的最新日志文件
3. 设备类型和 IOS 版本

## License

MIT License
