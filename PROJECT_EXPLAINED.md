# Hardware Info Retriever - 项目完整解析

## 📋 项目概述

**项目名称**: 网络设备信息收集系统 (Network Device Hardware Information Retriever)  
**版本**: 2.0.0  
**用途**: 批量采集网络设备（路由器/交换机）的硬件信息  
**支持厂商**: Cisco、华为(Huawei)、新华三(H3C)、Juniper、Arista、HP/HPE  
**并发能力**: 支持400-500台设备同时采集  

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层 (CLI)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  scan   │ │ collect │ │  test   │ │ export  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └─────────────┴─────────────┴─────────────┘           │
│                         │                                   │
│                         ▼                                   │
│              ┌─────────────────────┐                       │
│              │     main.py         │  ← 命令行入口         │
│              │   (参数解析/路由)    │                       │
│              └──────────┬──────────┘                       │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     业务逻辑层                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  Scanner       │  │  Collector     │  │   Storage    │  │
│  │  (网络扫描)     │  │  (并发采集)     │  │  (数据存储)   │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  Connector     │  │   Parser       │  │   Exporter   │  │
│  │  (SSH连接)      │  │  (输出解析)     │  │  (数据导出)   │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据访问层                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Netmiko (SSH连接库)                        │ │
│  │   - Cisco IOS/NX-OS/IOS-XE                             │ │
│  │   - Huawei VRP                                         │ │
│  │   - H3C Comware                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              SQLite (数据存储)                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 目录结构详解

```
hardware-info-retriever/
│
├── 📄 main.py                    # 主入口 - 命令行接口(CLI)
│                                 # 负责: 参数解析、命令路由、结果显示
│
├── 📄 verify_system.py           # 环境验证脚本
│                                 # 检查: Python版本、依赖安装、配置完整性
│
├── 📄 test_integration.py        # 集成测试脚本
│                                 # 测试: 解析逻辑、导出功能、数据库操作
│
├── 📄 production_check.py        # 生产环境检查
│                                 # 检查: 网络连通性、配置参数优化建议
│
├── 📄 diagnose_device.py         # 设备诊断工具
│                                 # 用于: 调试单个设备的连接/解析问题
│
├── 📄 pack_project.py            # 项目打包脚本
│                                 # 功能: 打包分发、生成压缩包
│
│
├── 📁 config/                    # 配置目录
│   ├── settings.yaml            # 系统配置(超时、并发、日志等)
│   ├── devices.yaml             # 设备清单(手动配置时使用)
│   ├── devices_template.csv     # CSV模板
│   └── devices_template.txt     # TXT模板
│
├── 📁 src/                       # 核心源码目录
│   ├── __init__.py              # 包初始化
│   ├── models.py                # 数据模型定义
│   ├── config_manager.py        # 配置管理器
│   ├── connector.py             # SSH连接器(Netmiko封装)
│   ├── parser.py                # 命令输出解析器
│   ├── collector.py             # 并发采集器
│   ├── storage.py               # 数据存储(SQLite+导出)
│   ├── scanner.py               # 网络扫描器
│   ├── logger.py                # 日志配置
│   ├── vendor_commands.py       # 厂商命令映射
│   └── vendor_parsers.py        # 厂商解析器
│
├── 📁 data/                      # 数据目录
│   └── devices.db               # SQLite数据库(运行时生成)
│
├── 📁 exports/                   # 导出目录
│   └── *.xlsx/*.csv/*.json      # 导出文件
│
├── 📁 logs/                      # 日志目录
│   └── collector_*.log          # 采集日志
│
└── 📁 docs/                      # 文档目录
    ├── CREDENTIALS_GUIDE.md     # 凭据管理指南
    └── ...                      # 其他文档
```

---

## 🔧 核心模块详解

### 1. main.py - 主入口程序

```python
"""
功能: 命令行接口(CLI)入口
设计模式: 命令模式(Command Pattern)

支持命令:
- scan:    自动扫描发现设备 → 零配置采集
- collect: 从配置文件中采集 → 精准控制
- test:    测试设备连接性 → 验证环境
- export:  导出已有数据 → 数据再利用
- query:   查询数据库 → 信息检索
- clear:   清空数据库 → 重置环境

工作流程:
1. 解析命令行参数 (argparse)
2. 加载配置 (ConfigManager)
3. 设置日志 (setup_logging)
4. 路由到对应命令处理函数
5. 执行并显示结果 (rich库美化输出)
"""
```

**关键函数说明**:

| 函数 | 功能 | 参数说明 |
|------|------|----------|
| `create_parser()` | 创建参数解析器 | 定义所有CLI参数 |
| `cmd_scan()` | 扫描命令处理 | 自动发现网段中的设备 |
| `cmd_collect()` | 采集命令处理 | 批量采集设备信息 |
| `cmd_test()` | 测试命令处理 | 验证SSH连接 |
| `cmd_export()` | 导出命令处理 | 导出Excel/CSV/JSON |
| `cmd_query()` | 查询命令处理 | 查询数据库 |

---

### 2. models.py - 数据模型

```python
"""
功能: 定义所有数据结构 (使用Python dataclass)

核心类:
1. DeviceInfo       - 设备完整信息(采集结果)
2. DeviceConfig     - 设备配置(连接参数)
3. DeviceCredentials- 凭据信息(用户名/密码)
4. ModuleInfo       - 模块信息(板卡/模块)
5. InterfaceInfo    - 接口信息(端口状态)
6. CollectionResult - 采集结果统计

设计原则:
- 使用dataclass减少样板代码
- 类型注解增强可读性
- to_dict()/to_flat_dict() 支持序列化
"""
```

**DeviceInfo字段说明**:

```python
@dataclass
class DeviceInfo:
    # 基本信息
    management_ip: str      # 管理IP地址(主键)
    hostname: str           # 设备主机名
    model: str              # 设备型号(如 C9300-24P)
    serial_number: str      # 序列号
    
    # 系统信息
    os_version: str         # 系统版本
    os_type: str            # IOS / NX-OS / IOS-XE / VRP
    uptime: str             # 运行时间(人类可读)
    uptime_seconds: int     # 运行时间(秒,用于计算)
    
    # 硬件信息
    total_ports: int        # 总端口数
    active_ports: int       # 活动端口数
    modules: List[ModuleInfo]  # 模块列表
    
    # 分类信息
    device_role: str        # switch/router/L3 switch
    device_type: str        # ios/nxos/ios_xe/huawei
    location: str           # 位置信息
    
    # 元数据
    collection_time: datetime   # 采集时间
    collection_status: str      # pending/success/failed
    error_message: str          # 错误信息(失败时)
    raw_output: Dict[str, str]  # 原始命令输出(调试)
```

---

### 3. collector.py - 并发采集器

```python
"""
功能: 批量并发采集设备信息

核心类: DeviceCollector

并发策略:
1. 分批处理: 将大列表分成小批次(batch_size)
2. 批间延迟: 每批之间等待几秒(batch_delay)
   - 目的: 避免瞬间大量连接压垮网络/设备
3. 线程池: 每批内使用ThreadPoolExecutor并发
   - 线程数: max_workers(默认20)

处理流程:
    设备列表 [1000台]
        ↓ 分批 (batch_size=50)
    批次1 [50台] → 并发采集(20线程) → 等待2秒 → 批次2 [50台]
        ↓
    结果汇总 → 保存数据库 → 导出文件

异常处理:
- 单个设备失败不影响其他设备
- 自动重试3次(config/settings.yaml配置)
- 详细记录错误日志
"""
```

**关键代码解析**:

```python
def collect_devices(self, devices: List[DeviceConfig]) -> CollectionResult:
    # 1. 分批处理 - 避免内存和连接数爆炸
    batches = [
        devices[i:i + self.batch_size] 
        for i in range(0, len(devices), self.batch_size)
    ]
    
    for batch_idx, batch in enumerate(batches):
        if batch_idx > 0:
            time.sleep(self.batch_delay)  # 批次间延迟
        
        # 2. 线程池并发 - 提高采集速度
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_device = {
                executor.submit(self._collect_single_device, dev): dev 
                for dev in batch
            }
            
            # 3. 异步获取结果 - 完成一个处理一个
            for future in as_completed(future_to_device):
                device_info = future.result()
                # 处理结果...
```

---

### 4. connector.py - SSH连接器

```python
"""
功能: 使用Netmiko库建立SSH连接并执行命令

核心类: DeviceConnector

工作流程:
1. 建立SSH连接 (netmiko.ConnectHandler)
2. 执行多条show命令
3. 收集原始输出
4. 关闭连接
5. 返回原始数据给Parser解析

支持厂商:
- Cisco IOS, IOS-XE, NX-OS, IOS-XR, ASA
- Huawei VRP, VRP V8
- H3C Comware
- Juniper Junos
- Arista EOS
- HP ProCurve, Comware

命令列表(每个厂商不同):
- show version        → 获取版本、型号、序列号、uptime
- show inventory      → 获取硬件清单、模块信息
- show ip interface brief → 获取接口IP
- show interfaces status  → 获取端口状态
- show module         → 获取模块信息
"""
```

**连接流程图**:

```
开始
  ↓
读取设备配置(IP/类型/凭据)
  ↓
创建Netmiko连接参数
  ↓
ConnectHandler() 建立SSH
  ↓
执行show version
执行show inventory
执行show interfaces...
  ↓
收集所有输出
  ↓
断开SSH连接
  ↓
返回DeviceInfo(原始数据)
  ↓
结束
```

---

### 5. parser.py - 输出解析器

```python
"""
功能: 解析show命令的文本输出，提取结构化数据

设计模式: 策略模式 (Strategy Pattern)
- 基类: OutputParser
- 子类: CiscoIOSParser, CiscoNXOSParser, HuaweiParser...

解析内容:
1. Hostname: 从prompt或show version提取
2. Model: 从Hardware/Model字段提取
3. Serial Number: 从Processor ID/序列号字段提取
4. OS Version: 从Software/Version字段提取
5. Uptime: 从uptime字段提取并转换为秒
6. Total Ports: 统计interface数量
7. Modules: 从show inventory解析板卡信息

解析方法: 正则表达式匹配
"""
```

**解析示例** (Cisco IOS show version):

```
输入文本:
Cisco IOS Software, C9300-24P Software...
Processor board ID FCW1234L567
Hostname: CORE-SW-01
Uptime: 2 years, 15 weeks, 3 days...

正则匹配:
- Model:     r"Model number\s*:\s*(\S+)" → C9300-24P
- Serial:    r"Processor board ID\s+(\S+)" → FCW1234L567
- Hostname:  r"^\s*([A-Za-z0-9_-]+)\s*#" → CORE-SW-01
- Uptime:    复杂正则转换为秒数
```

---

### 6. scanner.py - 网络扫描器

```python
"""
功能: 自动发现网络中的设备

核心类: NetworkScanner

扫描流程:
1. 生成网段中的所有IP (ipaddress.ip_network)
2. 并发检测SSH端口(22)是否开放
3. 对开放SSH的主机尝试登录
4. 使用Netmiko autodetect自动识别设备类型
5. 获取hostname和角色信息
6. 生成设备清单

特点:
- 零配置: 不需要预先知道设备清单
- 混合环境: 同一网段可以识别不同厂商设备
- 自动过滤: 跳过非网络设备(服务器、PC等)
"""
```

**扫描流程图**:

```
输入网段: 192.168.1.0/24
  ↓
生成IP列表 (254个IP)
  ↓
并发端口扫描 (检查22端口)
  ↓
筛选出开放SSH的主机 (假设50台)
  ↓
尝试SSH登录 + 自动识别设备类型
  ↓
获取hostname
  ↓
输出设备清单
```

---

### 7. storage.py - 数据存储

```python
"""
功能: 数据持久化存储和导出

核心类:
1. DataStorage - SQLite数据库操作
2. DataExporter - Excel/CSV/JSON导出

DataStorage功能:
- 创建设备表 (SQLAlchemy ORM)
- 插入/更新设备记录
- 查询设备(按IP/型号/主机名)
- 搜索功能
- 清空数据

DataExporter功能:
- 导出为Excel (.xlsx) - 使用pandas+openpyxl
- 导出为CSV (.csv) - 使用pandas
- 导出为JSON (.json) - 使用标准库json
"""
```

**数据库表结构**:

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    management_ip VARCHAR(15) UNIQUE NOT NULL,  -- 管理IP(唯一)
    hostname VARCHAR(100),                       -- 主机名
    model VARCHAR(100),                          -- 型号
    serial_number VARCHAR(100),                  -- 序列号
    os_version VARCHAR(200),                     -- 系统版本
    os_type VARCHAR(50),                         -- 系统类型
    uptime VARCHAR(100),                         -- 运行时间
    uptime_seconds INTEGER,                      -- 运行时间(秒)
    total_ports INTEGER,                         -- 总端口数
    active_ports INTEGER,                        -- 活动端口数
    modules_detail TEXT,                         -- 模块详情(JSON)
    device_role VARCHAR(50),                     -- 设备角色
    device_type VARCHAR(50),                     -- 设备类型
    location VARCHAR(200),                       -- 位置
    collection_time DATETIME,                    -- 采集时间
    collection_status VARCHAR(20),               -- 采集状态
    error_message TEXT                           -- 错误信息
);
```

---

## 📊 工作流程详解

### 场景1: 自动发现采集 (推荐用于生产环境)

```bash
python main.py scan --network 192.168.1.0/24 --collect
```

**执行流程**:

```
1. 参数解析
   └─ network=192.168.1.0/24, collect=True

2. 加载配置
   └─ config/settings.yaml (超时、并发等)
   └─ .env (SSH凭据)

3. 网络扫描 (scanner.py)
   ├─ 生成IP范围: 192.168.1.1 ~ 192.168.1.254
   ├─ 并发检测22端口 (50线程)
   ├─ 发现50台开放SSH的主机
   ├─ 尝试SSH登录 + 自动识别设备类型
   ├─ 获取hostname
   └─ 返回设备清单 (50台DeviceConfig)

4. 信息采集 (collector.py)
   ├─ 分批次: 50台 ÷ 50 = 1批
   ├─ 并发采集: 20线程同时连接
   ├─ 每台设备执行:
   │   ├─ connector.py: SSH连接
   │   ├─ 执行5条show命令
   │   ├─ parser.py: 解析输出
   │   └─ 返回DeviceInfo
   └─ 汇总结果: 50台设备信息

5. 数据存储 (storage.py)
   ├─ 保存到SQLite: data/devices.db
   └─ 导出到Excel: exports/auto_discovered.xlsx

6. 结果显示
   ├─ 成功: 48台
   ├─ 失败: 2台 (显示错误信息)
   └─ 耗时: 45秒
```

---

### 场景2: 配置文件采集 (推荐用于精确控制)

```bash
python main.py collect --source devices.yaml
```

**执行流程**:

```
1. 加载设备清单
   └─ config/devices.yaml
      ├─ IP: 192.168.1.1, 类型: ios, 角色: switch
      ├─ IP: 192.168.1.2, 类型: nxos, 角色: L3 switch
      └─ ... (共100台)

2. 验证凭据
   ├─ 从.env加载默认凭据
   ├─ 检查devices.yaml中是否有设备专用凭据
   └─ 合并凭据配置

3. 批量采集
   ├─ 分批: 100台 ÷ 50 = 2批
   ├─ 批次1: 50台 → 并发采集 → 等待2秒
   ├─ 批次2: 50台 → 并发采集
   └─ 收集结果

4. 数据存储
   ├─ 保存到SQLite
   └─ 导出到Excel (默认)

5. 显示统计
   ├─ 成功率: 98%
   ├─ 失败的设备列表
   └─ 导出文件路径
```

---

## ⚙️ 配置文件详解

### settings.yaml 配置项

```yaml
# ========================================
# 连接设置
# ========================================
connection:
  timeout: 30          # SSH连接超时(秒)
  auth_timeout: 20     # 认证超时(秒)
  read_timeout: 60     # 命令执行超时(秒)
  max_retries: 3       # 失败重试次数
  retry_delay: 5       # 重试间隔(秒)

# ========================================
# 并发设置 (性能调优关键)
# ========================================
concurrency:
  max_workers: 20      # 最大并发线程数
                       # 建议: 根据网络带宽调整
                       # 100M网络: 10-20
                       # 1G网络: 30-50
  batch_size: 50       # 每批处理的设备数
  batch_delay: 2       # 批次间延迟(秒)
                       # 目的: 避免瞬间大量连接

# ========================================
# 设备类型命令映射
# ========================================
device_types:
  ios:                  # 设备类型标识
    netmiko_type: "cisco_ios"  # Netmiko设备类型名
    commands:            # 要执行的命令列表
      - "show version"
      - "show inventory"
      - "show ip interface brief"
      - "show interfaces status"
      - "show module"
  
  nxos:                 # NX-OS设备
    netmiko_type: "cisco_nxos"
    commands:
      - "show version"
      - "show inventory"
      - "show ip interface brief vrf all"  # NX-OS特有
      - "show interface status"
      - "show module"

# ========================================
# 存储设置
# ========================================
storage:
  db_type: "sqlite"           # 数据库类型
  sqlite_path: "./data/devices.db"   # 数据库路径
  export_dir: "./exports"     # 导出目录
  log_dir: "./logs"           # 日志目录

# ========================================
# 日志设置
# ========================================
logging:
  level: "INFO"          # 日志级别: DEBUG/INFO/WARNING/ERROR
  max_size: 10           # 单个日志文件最大(MB)
  backup_count: 5        # 保留日志文件数量
```

---

## 🎯 使用示例

### 示例1: 快速开始 (自动发现)

```bash
# 1. 扫描单个网段
python main.py scan --network 192.168.1.0/24

# 2. 扫描并立即采集
python main.py scan --network 192.168.1.0/24 --collect

# 3. 扫描多个网段
python main.py scan \
  --network 192.168.1.0/24 \
  --network 10.0.0.0/24 \
  --collect

# 4. 从文件读取网段 (推荐大量网段)
python main.py scan --network-file networks.txt --collect
```

### 示例2: 从配置文件采集

```bash
# 使用默认配置 (config/devices.yaml)
python main.py collect

# 使用CSV文件
python main.py collect --source devices.csv --type csv

# 使用IP列表文件
python main.py collect --source ips.txt --type txt

# 调整并发数 (大型网络)
python main.py collect --workers 30 --batch-size 100

# 指定导出格式
python main.py collect --export csv --output my_devices
```

### 示例3: 测试连接

```bash
# 测试所有设备
python main.py test

# 测试单个设备
python main.py test --ip 192.168.1.1
```

### 示例4: 数据查询和导出

```bash
# 查询所有设备
python main.py query --all

# 按IP查询
python main.py query --ip 192.168.1.1

# 按型号查询
python main.py query --model C9300

# 导出为Excel
python main.py export --format excel --output inventory

# 导出为CSV
python main.py export --format csv
```

---

## 🔍 关键设计决策

### 1. 为什么使用Netmiko而不是Paramiko?

| 特性 | Paramiko | Netmiko |
|------|----------|---------|
| 定位 | 通用SSH库 | 网络设备专用 |
| 设备识别 | 需手动实现 | 内置autodetect |
| 命令模式 | 需处理enable模式 | 自动处理 |
| 厂商支持 | 需自行适配 | 内置多厂商支持 |
| 学习成本 | 高 | 低 |

**结论**: Netmiko专为网络自动化设计，减少重复造轮子。

---

### 2. 为什么选择SQLite而不是MySQL/PostgreSQL?

| 特性 | SQLite | MySQL/PostgreSQL |
|------|--------|------------------|
| 部署 | 零配置 | 需安装服务端 |
| 便携性 | 单个文件 | 需数据库服务器 |
| 并发 | 足够(写锁) | 更高 |
| 规模 | <1TB足够 | 无限制 |
| 适用场景 | 单机工具 | 多人协作 |

**结论**: 单机工具场景下，SQLite更简单、更便携。

---

### 3. 并发策略设计

**问题**: 为什么要分批次 + 批间延迟?

**答案**:
1. **避免网络拥塞**: 瞬间发起1000个连接会压垮网络
2. **避免设备过载**: 交换机CPU处理SSH会话有上限
3. **可控性**: 失败一批不影响其他批次
4. **可调性**: 通过batch_delay参数适配不同网络环境

**参数建议**:
- 小型网络(<100台): batch_size=50, batch_delay=1
- 中型网络(100-500台): batch_size=50, batch_delay=2
- 大型网络(500+台): batch_size=100, batch_delay=3

---

### 4. 数据采集范围

**采集哪些信息?**
- ✅ 基本信息: IP、hostname、model、序列号
- ✅ 系统信息: OS版本、运行时间
- ✅ 硬件信息: 端口数、模块清单
- ❌ 接口详细配置: 过于庞大
- ❌ 路由表: 动态变化
- ❌ ARP表: 敏感信息

**设计原则**: 采集静态的、用于资产管理的硬件信息，不采集动态运行数据。

---

## 🐛 常见问题

### Q1: 连接超时怎么办?

```bash
# 增加超时时间
python main.py collect --timeout 60

# 或在settings.yaml中修改
connection:
  timeout: 60
  read_timeout: 120
```

### Q2: 如何提高采集速度?

```bash
# 增加并发数(确保网络带宽足够)
python main.py collect --workers 50 --batch-size 100

# 减少批次延迟(如果网络设备性能强)
# 修改settings.yaml
concurrency:
  batch_delay: 1  # 默认是2秒
```

### Q3: 部分设备凭据不同怎么办?

```yaml
# 在devices.yaml中为特殊设备指定凭据
devices:
  - ip: "192.168.1.1"
    device_type: "ios"
    # 使用.env中的默认凭据

  - ip: "192.168.2.1"
    device_type: "ios"
    username: "special_admin"      # 专用账号
    password: "SpecialPass123"
    secret: "SpecialEnable123"
```

### Q4: 如何定期自动采集?

```bash
# 使用Linux crontab
# 每天凌晨2点执行
0 2 * * * cd /path/to/hardware-info-retriever && python main.py collect >> /var/log/hw_collect.log 2>&1
```

---

## 📈 扩展思路

### 1. 添加Web界面

可以使用Flask/FastAPI包装现有功能:
```python
from flask import Flask, jsonify
from main import cmd_collect

app = Flask(__name__)

@app.route('/api/collect', methods=['POST'])
def api_collect():
    # 调用采集逻辑
    result = cmd_collect(args, config_manager, logger)
    return jsonify(result)
```

### 2. 集成CMDB

修改storage.py，将数据同步到现有CMDB:
```python
class DataStorage:
    def sync_to_cmdb(self, devices):
        # 调用CMDB API
        for dev in devices:
            cmdb_api.create_or_update_asset(dev)
```

### 3. 添加邮件报告

采集完成后发送邮件:
```python
def send_report(result):
    msg = f"采集完成: {result.success}/{result.total}"
    send_email(to="admin@company.com", subject="设备采集报告", body=msg)
```

---

## 📚 相关文档

| 文档 | 内容 |
|------|------|
| README.md | 快速开始指南 |
| MULTI_VENDOR_GUIDE.md | 多厂商设备支持详情 |
| PRODUCTION_GUIDE.md | 生产环境部署指南 |
| TROUBLESHOOTING_UBUNTU.md | Ubuntu常见问题 |
| CREDENTIALS_GUIDE.md | 凭据管理详细说明 |

---

## 🎓 学习要点

通过阅读此项目，你可以学习到:

1. **Python项目结构**: 如何组织中等规模Python项目
2. **并发编程**: ThreadPoolExecutor + 批处理策略
3. **数据库操作**: SQLAlchemy ORM使用
4. **配置管理**: YAML + 环境变量 + 优先级设计
5. **命令行工具**: argparse + rich美化输出
6. **网络自动化**: Netmiko库的使用
7. **数据解析**: 正则表达式提取结构化数据
8. **测试实践**: 单元测试 + 集成测试

---

**项目路径**: `D:\Dev\hardware-info-retriever_v1.0.0_20260108\hardware-info-retriever`  
**创建日期**: 2026-01-08  
**解释日期**: 2026-04-09
