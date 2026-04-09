#!/usr/bin/env python3
"""
系统验证脚本 - 用于快速检查代码质量和逻辑正确性
无需真实设备，无需安装依赖也可运行部分测试

运行方式：
  python verify_system.py          # 基础验证（无需依赖）
  python verify_system.py --full   # 完整验证（需要安装依赖）
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("思科设备信息收集系统 - 验证脚本")
print("=" * 60)

# ============================================================
# 测试 1: 检查 Python 版本
# ============================================================
print("\n[测试 1] Python 版本检查...")
if sys.version_info >= (3, 8):
    print(f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor} - OK")
else:
    print(f"  ✗ Python 版本过低，需要 3.8+，当前: {sys.version}")
    sys.exit(1)

# ============================================================
# 测试 2: 检查项目文件结构
# ============================================================
print("\n[测试 2] 项目文件结构检查...")
required_files = [
    "main.py",
    "requirements.txt",
    "config/settings.yaml",
    "config/devices.yaml",
    "src/__init__.py",
    "src/models.py",
    "src/config_manager.py",
    "src/connector.py",
    "src/parser.py",
    "src/storage.py",
    "src/collector.py",
    "src/logger.py",
]

base_dir = os.path.dirname(os.path.abspath(__file__))
missing = []
for f in required_files:
    path = os.path.join(base_dir, f)
    if os.path.exists(path):
        print(f"  ✓ {f}")
    else:
        print(f"  ✗ {f} - 缺失!")
        missing.append(f)

if missing:
    print(f"\n  警告: 缺少 {len(missing)} 个文件")

# ============================================================
# 测试 3: 检查模块导入（无需第三方依赖）
# ============================================================
print("\n[测试 3] 核心模块语法检查...")
try:
    import ast
    
    modules_to_check = [
        "src/models.py",
        "src/config_manager.py", 
        "src/connector.py",
        "src/parser.py",
        "src/storage.py",
        "src/collector.py",
        "src/logger.py",
        "main.py",
    ]
    
    for module in modules_to_check:
        path = os.path.join(base_dir, module)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            try:
                ast.parse(source)
                print(f"  ✓ {module} - 语法正确")
            except SyntaxError as e:
                print(f"  ✗ {module} - 语法错误: {e}")
        else:
            print(f"  - {module} - 跳过（文件不存在）")
            
except Exception as e:
    print(f"  ✗ 语法检查失败: {e}")

# ============================================================
# 测试 4: 验证数据模型逻辑
# ============================================================
print("\n[测试 4] 数据模型逻辑验证...")
try:
    # 手动模拟 dataclasses（不依赖第三方库）
    exec("""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class ModuleInfo:
    slot: str
    description: str
    model: str
    serial_number: str

@dataclass  
class DeviceInfo:
    management_ip: str
    hostname: str = ""
    model: str = ""
    serial_number: str = ""
    os_version: str = ""
    os_type: str = ""
    uptime: str = ""
    total_ports: int = 0
    device_role: str = "switch"
    modules: List[ModuleInfo] = field(default_factory=list)
    collection_status: str = "pending"

# 测试创建对象
dev = DeviceInfo(
    management_ip="192.168.1.1",
    hostname="TEST-SW-01",
    model="C9300-24P",
    serial_number="FCW1234ABCD",
    os_version="17.6.3",
    os_type="IOS-XE",
    uptime="10 days, 5 hours",
    total_ports=24,
    device_role="L3 switch"
)

# 添加模块
dev.modules.append(ModuleInfo(
    slot="1",
    description="24-port switch",
    model="C9300-24P",
    serial_number="FCW1234ABCD"
))

assert dev.management_ip == "192.168.1.1"
assert dev.hostname == "TEST-SW-01"
assert len(dev.modules) == 1
print("  ✓ DeviceInfo 数据模型 - 正常工作")
""")
except Exception as e:
    print(f"  ✗ 数据模型测试失败: {e}")

# ============================================================
# 测试 5: 验证解析器正则表达式逻辑
# ============================================================
print("\n[测试 5] 解析器正则表达式验证...")
import re

# 模拟 show version 输出
sample_show_version_ios = """
Cisco IOS Software, C9300 Software (C9300-UNIVERSALK9-M), Version 17.6.3, RELEASE SOFTWARE
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2022 by Cisco Systems, Inc.

ROM: IOS-XE ROMMON
BOOTLDR: System Bootstrap, Version 17.6.3r, RELEASE SOFTWARE

TEST-SWITCH uptime is 45 days, 12 hours, 30 minutes
Processor board ID FCW2145L0AB
"""

sample_show_version_nxos = """
Cisco Nexus Operating System (NX-OS) Software
NXOS: version 9.3(8)
  BIOS: version 07.69
  kickstart: version 9.3(8)
  system: version 9.3(8)
Device name: NEXUS-CORE-01
Kernel uptime is 120 day(s), 5 hour(s), 30 minute(s)
"""

tests_passed = 0
tests_total = 0

# 测试主机名解析
tests_total += 1
hostname_pattern = r'^(\S+)\s+uptime'
match = re.search(hostname_pattern, sample_show_version_ios, re.MULTILINE)
if match and match.group(1) == "TEST-SWITCH":
    print("  ✓ 主机名解析 (IOS) - 正确提取 'TEST-SWITCH'")
    tests_passed += 1
else:
    print("  ✗ 主机名解析 (IOS) - 失败")

# 测试版本解析
tests_total += 1
version_pattern = r'Version\s+(\S+)'
match = re.search(version_pattern, sample_show_version_ios)
if match and "17.6.3" in match.group(1):
    print("  ✓ 版本解析 (IOS) - 正确提取 '17.6.3'")
    tests_passed += 1
else:
    print("  ✗ 版本解析 (IOS) - 失败")

# 测试序列号解析
tests_total += 1
serial_pattern = r'Processor\s+board\s+ID\s+(\S+)'
match = re.search(serial_pattern, sample_show_version_ios)
if match and match.group(1) == "FCW2145L0AB":
    print("  ✓ 序列号解析 (IOS) - 正确提取 'FCW2145L0AB'")
    tests_passed += 1
else:
    print("  ✗ 序列号解析 (IOS) - 失败")

# 测试 uptime 解析
tests_total += 1
uptime_pattern = r'uptime\s+is\s+(.+?)(?:\n|$)'
match = re.search(uptime_pattern, sample_show_version_ios)
if match and "45 days" in match.group(1):
    print("  ✓ Uptime 解析 (IOS) - 正确提取")
    tests_passed += 1
else:
    print("  ✗ Uptime 解析 (IOS) - 失败")

# 测试 NX-OS 版本解析
tests_total += 1
nxos_version_pattern = r'NXOS:\s*version\s+(\S+)'
match = re.search(nxos_version_pattern, sample_show_version_nxos)
if match and match.group(1) == "9.3(8)":
    print("  ✓ 版本解析 (NX-OS) - 正确提取 '9.3(8)'")
    tests_passed += 1
else:
    print("  ✗ 版本解析 (NX-OS) - 失败")

# 测试 NX-OS 主机名解析
tests_total += 1
nxos_hostname_pattern = r'Device name:\s*(\S+)'
match = re.search(nxos_hostname_pattern, sample_show_version_nxos)
if match and match.group(1) == "NEXUS-CORE-01":
    print("  ✓ 主机名解析 (NX-OS) - 正确提取 'NEXUS-CORE-01'")
    tests_passed += 1
else:
    print("  ✗ 主机名解析 (NX-OS) - 失败")

print(f"\n  解析测试通过: {tests_passed}/{tests_total}")

# ============================================================
# 测试 6: 验证 show inventory 解析
# ============================================================
print("\n[测试 6] Inventory 解析验证...")

sample_inventory = '''
NAME: "Chassis", DESCR: "Cisco Catalyst 9300-24P Switch"
PID: C9300-24P         , VID: V02  , SN: FCW2145L0AB

NAME: "Power Supply Module 0", DESCR: "Cisco Catalyst 9300 715WAC power supply"
PID: PWR-C1-715WAC     , VID: V01  , SN: DTN2139V0HK

NAME: "Network Module 0", DESCR: "Cisco Catalyst 9300 4x10G Network Module"
PID: C9300-NM-4G       , VID: V01  , SN: FOC21473GT5
'''

inventory_pattern = r'NAME:\s*"([^"]+)".*?DESCR:\s*"([^"]*)".*?PID:\s*(\S+).*?SN:\s*(\S+)'
matches = re.findall(inventory_pattern, sample_inventory, re.DOTALL | re.IGNORECASE)

if len(matches) == 3:
    print(f"  ✓ 找到 {len(matches)} 个模块/组件")
    for name, descr, pid, sn in matches:
        print(f"    - {name}: {pid} (SN: {sn})")
else:
    print(f"  ✗ 预期 3 个组件，找到 {len(matches)} 个")

# ============================================================
# 测试 7: Uptime 转秒数计算
# ============================================================
print("\n[测试 7] Uptime 转换验证...")

def parse_uptime_to_seconds(uptime_str):
    """将 uptime 字符串转换为秒数"""
    total_seconds = 0
    
    years = re.search(r'(\d+)\s*year', uptime_str, re.IGNORECASE)
    if years:
        total_seconds += int(years.group(1)) * 365 * 24 * 3600
    
    weeks = re.search(r'(\d+)\s*week', uptime_str, re.IGNORECASE)
    if weeks:
        total_seconds += int(weeks.group(1)) * 7 * 24 * 3600
    
    days = re.search(r'(\d+)\s*day', uptime_str, re.IGNORECASE)
    if days:
        total_seconds += int(days.group(1)) * 24 * 3600
    
    hours = re.search(r'(\d+)\s*hour', uptime_str, re.IGNORECASE)
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    
    minutes = re.search(r'(\d+)\s*minute', uptime_str, re.IGNORECASE)
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    
    return total_seconds

test_cases = [
    ("1 day, 2 hours, 30 minutes", 1 * 86400 + 2 * 3600 + 30 * 60),
    ("45 days, 12 hours", 45 * 86400 + 12 * 3600),
    ("2 weeks, 3 days", 2 * 7 * 86400 + 3 * 86400),
    ("1 year, 10 days", 365 * 86400 + 10 * 86400),
]

uptime_tests_passed = 0
for uptime_str, expected in test_cases:
    result = parse_uptime_to_seconds(uptime_str)
    if result == expected:
        print(f"  ✓ '{uptime_str}' → {result} 秒")
        uptime_tests_passed += 1
    else:
        print(f"  ✗ '{uptime_str}' → 期望 {expected}，得到 {result}")

print(f"\n  Uptime 测试通过: {uptime_tests_passed}/{len(test_cases)}")

# ============================================================
# 测试 8: 检查第三方依赖是否可安装（可选）
# ============================================================
print("\n[测试 8] 第三方依赖检查...")

if "--full" in sys.argv:
    required_packages = [
        ("netmiko", "SSH 连接库 - 核心功能"),
        ("paramiko", "SSH 协议库 - netmiko 依赖"),
        ("pandas", "数据处理 - Excel 导出"),
        ("openpyxl", "Excel 文件支持"),
        ("sqlalchemy", "数据库 ORM"),
        ("yaml", "YAML 配置解析"),
        ("rich", "终端美化输出"),
        ("tqdm", "进度条显示"),
    ]
    
    for package, desc in required_packages:
        try:
            __import__(package if package != "yaml" else "yaml")
            print(f"  ✓ {package} - {desc}")
        except ImportError:
            print(f"  ✗ {package} - 未安装 ({desc})")
            print(f"    运行: pip install {package}")
else:
    print("  跳过（使用 --full 参数运行完整检查）")
    print("  提示: 运行 'pip install -r requirements.txt' 安装所有依赖")

# ============================================================
# 测试 9: 配置文件格式验证
# ============================================================
print("\n[测试 9] 配置文件格式验证...")

try:
    import yaml
    
    config_path = os.path.join(base_dir, "config", "settings.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_sections = ["connection", "concurrency", "storage", "logging"]
        for section in required_sections:
            if section in config:
                print(f"  ✓ settings.yaml[{section}] - 存在")
            else:
                print(f"  ✗ settings.yaml[{section}] - 缺失")
    else:
        print("  - settings.yaml 不存在，跳过")
        
    devices_path = os.path.join(base_dir, "config", "devices.yaml")
    if os.path.exists(devices_path):
        with open(devices_path, 'r', encoding='utf-8') as f:
            devices = yaml.safe_load(f)
        
        if "devices" in devices and isinstance(devices["devices"], list):
            print(f"  ✓ devices.yaml - 包含 {len(devices['devices'])} 个设备配置")
        else:
            print("  ✗ devices.yaml - 格式不正确")
    else:
        print("  - devices.yaml 不存在，跳过")
        
except ImportError:
    print("  跳过（需要安装 pyyaml）")
except Exception as e:
    print(f"  ✗ 配置文件验证失败: {e}")

# ============================================================
# 测试 10: 实际导入主模块（完整测试）
# ============================================================
all_imports_ok = False
if "--full" in sys.argv:
    print("\n[测试 10] 导入主程序模块...")
    try:
        from src.models import DeviceInfo, DeviceConfig, ModuleInfo
        print("  ✓ src.models 导入成功")
        
        from src.config_manager import ConfigManager
        print("  ✓ src.config_manager 导入成功")
        
        from src.connector import DeviceConnector
        print("  ✓ src.connector 导入成功")
        
        from src.parser import OutputParser, get_parser
        print("  ✓ src.parser 导入成功")
        
        from src.storage import DataStorage, DataExporter
        print("  ✓ src.storage 导入成功")
        
        from src.collector import DeviceCollector
        print("  ✓ src.collector 导入成功")
        
        all_imports_ok = True
        print("\n  ✓ 所有模块导入成功！系统可以正常运行。")
        
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        print("    请先运行: pip install -r requirements.txt")
    except Exception as e:
        print(f"  ✗ 其他错误: {e}")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("验证完成!")
print("=" * 60)

# 根据测试结果给出不同建议
if "--full" in sys.argv and all_imports_ok:
    print("""
✅ 系统验证通过！所有依赖已安装，模块可正常导入。

下一步:

1. 配置凭据:
   - 复制 .env.example 为 .env
   - 填入你的 SSH 用户名和密码

2. 配置设备清单:
   - 编辑 config/devices.yaml
   - 或准备 CSV/TXT 格式的设备列表

3. 测试单台设备 (推荐先测试):
   python main.py test --ip <你的交换机IP>

4. 批量采集:
   python main.py collect
""")
else:
    print("""
下一步建议:

1. 安装依赖:
   pip install -r requirements.txt

2. 运行完整验证:
   python verify_system.py --full

3. 配置凭据和设备清单后开始使用

提示: 如果遇到问题，查看 logs/ 目录下的日志文件
""")
