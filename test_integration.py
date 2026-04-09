#!/usr/bin/env python3
"""
集成测试 - 模拟设备输出测试完整的解析流程
这个测试不需要真实设备，但测试了完整的数据处理流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import DeviceInfo, DeviceConfig, DeviceCredentials
from src.parser import OutputParser, get_parser

print("=" * 60)
print("集成测试 - 模拟设备解析")
print("=" * 60)

# 模拟真实的 show 命令输出
MOCK_IOS_OUTPUTS = {
    "show version": """
Cisco IOS Software, C9300 Software (C9300-UNIVERSALK9-M), Version 17.6.3, RELEASE SOFTWARE (fc4)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2022 by Cisco Systems, Inc.
Compiled Sun 29-May-22 01:26 by mcpre

ROM: IOS-XE ROMMON
BOOTLDR: System Bootstrap, Version 17.6.3r, RELEASE SOFTWARE

CORE-SW-01 uptime is 45 days, 12 hours, 30 minutes
Uptime for this control processor is 45 days, 12 hours, 32 minutes
System returned to ROM by Power Cycle
System image file is "flash:packages.conf"

cisco C9300-24P (X86) processor with 1419044K/6147K bytes of memory.
Processor board ID FCW2145L0AB
1 Virtual Ethernet interface
52 Gigabit Ethernet interfaces
4 Ten Gigabit Ethernet interfaces
2048K bytes of non-volatile configuration memory.
8388608K bytes of physical memory.
""",
    
    "show inventory": """
NAME: "Chassis", DESCR: "Cisco Catalyst 9300-24P Switch"
PID: C9300-24P         , VID: V02  , SN: FCW2145L0AB

NAME: "Power Supply Module 0", DESCR: "Cisco Catalyst 9300 715WAC power supply"  
PID: PWR-C1-715WAC     , VID: V01  , SN: DTN2139V0HK

NAME: "Power Supply Module 1", DESCR: "Cisco Catalyst 9300 715WAC power supply"
PID: PWR-C1-715WAC     , VID: V01  , SN: DTN2139V0HL

NAME: "Network Module 0", DESCR: "Cisco Catalyst 9300 4x10G Network Module"
PID: C9300-NM-4G       , VID: V01  , SN: FOC21473GT5
""",
    
    "show interfaces status": """
Port      Name               Status       Vlan       Duplex  Speed Type
Gi1/0/1   Server-01          connected    10         a-full  a-1000 10/100/1000BaseTX
Gi1/0/2   Server-02          connected    10         a-full  a-1000 10/100/1000BaseTX
Gi1/0/3                      notconnect   1          auto    auto 10/100/1000BaseTX
Gi1/0/4   Printer            connected    20         a-full  a-100  10/100/1000BaseTX
Gi1/0/5                      disabled     1          auto    auto 10/100/1000BaseTX
Te1/1/1   Uplink             connected    trunk      full    10G  10GBase-SR
Te1/1/2                      notconnect   1          full    10G  10GBase-SR
""",
    
    "show ip interface brief": """
Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  unassigned      YES unset  administratively down down    
Vlan10                 192.168.10.1    YES NVRAM  up                    up      
Vlan20                 192.168.20.1    YES NVRAM  up                    up      
GigabitEthernet0/0     192.168.1.100   YES NVRAM  up                    up      
""",
    
    "show module": ""
}

MOCK_NXOS_OUTPUTS = {
    "show version": """
Cisco Nexus Operating System (NX-OS) Software
TAC support: http://www.cisco.com/tac
Copyright (C) 2002-2022, Cisco and/or its affiliates.
All rights reserved.
The copyrights to certain works contained in this software are
owned by other third parties and used and distributed under their own
licenses, such as open source.  This software is provided "as is," and unless
otherwise stated, there is no warranty, express or implied.

Software
  BIOS: version 07.69
  NXOS: version 9.3(8)
  BIOS compile time:  06/01/2021
  NXOS image file is: bootflash:///nxos.9.3.8.bin
  NXOS compile time:  2/26/2022 19:00:00

Hardware
  cisco Nexus9000 C9336C-FX2 Chassis 
  Intel(R) Xeon(R) CPU D-1526 @ 1.80GHz with 24576380 kB of memory.
  Processor Board ID FDO24261WAT

  Device name: NEXUS-CORE-01
  bootflash:   53298520 kB

Kernel uptime is 120 day(s), 5 hour(s), 30 minute(s), 15 second(s)

plugin
  Core Plugin, Ethernet Plugin
""",
    
    "show inventory": """
NAME: "Chassis",  DESCR: "Nexus9000 C9336C-FX2 Chassis"
PID: N9K-C9336C-FX2    ,  VID: V02 ,  SN: FDO24261WAT

NAME: "Slot 1",  DESCR: "36x100G/40G QSFP28 Ethernet Module"
PID: N9K-C9336C-FX2    ,  VID: V02 ,  SN: FDO24261WAT

NAME: "Power Supply 1",  DESCR: "Nexus9000 C9336C-FX2 PSU"
PID: N9K-PAC-650W-B    ,  VID: V01 ,  SN: ART2441F5QJ

NAME: "Fan 1",  DESCR: "Nexus9000 C9336C-FX2 Fan Module"
PID: N9K-C9336C-FAN    ,  VID: V01 ,  SN: N/A
""",
    
    "show interface status": """
Port          Name               Status    Vlan      Duplex  Speed   Type
Eth1/1        spine-1            connected trunk     full    100G    QSFP-100G-SR4
Eth1/2        spine-2            connected trunk     full    100G    QSFP-100G-SR4
Eth1/3        --                 notconnec 1         auto    auto    QSFP-100G-SR4
Eth1/4        leaf-1             connected 100       full    40G     QSFP-40G-SR4
""",
    
    "show ip interface brief vrf all": """
IP Interface Status for VRF "default"
Interface            IP Address      Interface Status
Eth1/1               10.0.0.1        protocol-up/link-up/admin-up       
Vlan100              192.168.100.1   protocol-up/link-up/admin-up
mgmt0                10.1.1.100      protocol-up/link-up/admin-up
""",
    
    "show module": """
Mod  Ports  Module-Type                         Model              Status
---  -----  ----------------------------------- ------------------ ----------
1    36     36x100G/40G QSFP28 Ethernet Module  N9K-C9336C-FX2     active

Mod  Sw              Hw      Slot
---  --------------  ------  ----
1    9.3(8)          2.0     LC1 
"""
}


def test_ios_parsing():
    """测试 IOS 输出解析"""
    print("\n[测试] IOS 设备解析...")
    
    device_info = DeviceInfo(
        management_ip="192.168.1.100",
        device_type="ios",
        device_role="L3 switch",
        collection_status="success"
    )
    device_info.raw_output = MOCK_IOS_OUTPUTS
    
    parser = get_parser("ios")
    result = parser.parse_device_info(device_info)
    
    errors = []
    
    # 验证解析结果
    if result.hostname != "CORE-SW-01":
        errors.append(f"hostname: 期望 'CORE-SW-01', 得到 '{result.hostname}'")
    else:
        print(f"  ✓ hostname: {result.hostname}")
    
    if result.serial_number != "FCW2145L0AB":
        errors.append(f"serial: 期望 'FCW2145L0AB', 得到 '{result.serial_number}'")
    else:
        print(f"  ✓ serial_number: {result.serial_number}")
    
    if "17.6.3" not in result.os_version:
        errors.append(f"version: 期望包含 '17.6.3', 得到 '{result.os_version}'")
    else:
        print(f"  ✓ os_version: {result.os_version}")
    
    if "C9300" not in result.model:
        errors.append(f"model: 期望包含 'C9300', 得到 '{result.model}'")
    else:
        print(f"  ✓ model: {result.model}")
    
    if "45 days" not in result.uptime:
        errors.append(f"uptime: 期望包含 '45 days', 得到 '{result.uptime}'")
    else:
        print(f"  ✓ uptime: {result.uptime}")
    
    if len(result.modules) < 3:
        errors.append(f"modules: 期望 >= 3, 得到 {len(result.modules)}")
    else:
        print(f"  ✓ modules: {len(result.modules)} 个")
    
    if result.total_ports < 5:
        errors.append(f"total_ports: 期望 >= 5, 得到 {result.total_ports}")
    else:
        print(f"  ✓ total_ports: {result.total_ports}")
    
    if result.active_ports < 3:
        errors.append(f"active_ports: 期望 >= 3, 得到 {result.active_ports}")
    else:
        print(f"  ✓ active_ports: {result.active_ports}")
    
    if errors:
        print("\n  ✗ IOS 解析有问题:")
        for e in errors:
            print(f"    - {e}")
        return False
    
    print("\n  ✓ IOS 解析测试全部通过!")
    return True


def test_nxos_parsing():
    """测试 NX-OS 输出解析"""
    print("\n[测试] NX-OS 设备解析...")
    
    device_info = DeviceInfo(
        management_ip="10.1.1.100",
        device_type="nxos",
        device_role="L3 switch",
        collection_status="success"
    )
    device_info.raw_output = MOCK_NXOS_OUTPUTS
    
    parser = get_parser("nxos")
    result = parser.parse_device_info(device_info)
    
    errors = []
    
    if result.hostname != "NEXUS-CORE-01":
        errors.append(f"hostname: 期望 'NEXUS-CORE-01', 得到 '{result.hostname}'")
    else:
        print(f"  ✓ hostname: {result.hostname}")
    
    if result.serial_number != "FDO24261WAT":
        errors.append(f"serial: 期望 'FDO24261WAT', 得到 '{result.serial_number}'")
    else:
        print(f"  ✓ serial_number: {result.serial_number}")
    
    if "9.3(8)" not in result.os_version:
        errors.append(f"version: 期望包含 '9.3(8)', 得到 '{result.os_version}'")
    else:
        print(f"  ✓ os_version: {result.os_version}")
    
    if "NX-OS" not in result.os_type:
        errors.append(f"os_type: 期望 'NX-OS', 得到 '{result.os_type}'")
    else:
        print(f"  ✓ os_type: {result.os_type}")
    
    if "120 day" not in result.uptime:
        errors.append(f"uptime: 期望包含 '120 day', 得到 '{result.uptime}'")
    else:
        print(f"  ✓ uptime: {result.uptime}")
    
    if len(result.modules) < 2:
        errors.append(f"modules: 期望 >= 2, 得到 {len(result.modules)}")
    else:
        print(f"  ✓ modules: {len(result.modules)} 个")
    
    if errors:
        print("\n  ✗ NX-OS 解析有问题:")
        for e in errors:
            print(f"    - {e}")
        return False
    
    print("\n  ✓ NX-OS 解析测试全部通过!")
    return True


def test_data_export():
    """测试数据导出功能"""
    print("\n[测试] 数据导出...")
    
    from src.storage import DataExporter
    from src.models import ModuleInfo
    import tempfile
    import os
    
    # 创建测试数据
    device = DeviceInfo(
        management_ip="192.168.1.1",
        hostname="TEST-SW",
        model="C9300-24P",
        serial_number="FCW123",
        os_version="17.6.3",
        os_type="IOS-XE",
        uptime="10 days",
        total_ports=24,
        active_ports=12,
        device_role="switch"
    )
    device.modules.append(ModuleInfo("1", "Switch", "C9300-24P", "FCW123"))
    
    # 测试导出
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = DataExporter(export_dir=tmpdir)
        
        # CSV
        csv_path = exporter.export_to_csv([device], "test")
        if os.path.exists(csv_path):
            print(f"  ✓ CSV 导出成功: {os.path.basename(csv_path)}")
        else:
            print("  ✗ CSV 导出失败")
            return False
        
        # JSON
        json_path = exporter.export_to_json([device], "test")
        if os.path.exists(json_path):
            print(f"  ✓ JSON 导出成功: {os.path.basename(json_path)}")
        else:
            print("  ✗ JSON 导出失败")
            return False
        
        # Excel
        xlsx_path = exporter.export_to_excel([device], "test")
        if os.path.exists(xlsx_path):
            print(f"  ✓ Excel 导出成功: {os.path.basename(xlsx_path)}")
        else:
            print("  ✗ Excel 导出失败")
            return False
    
    print("\n  ✓ 数据导出测试全部通过!")
    return True


def test_database():
    """测试数据库存储"""
    print("\n[测试] 数据库存储...")
    
    from src.storage import DataStorage
    from src.models import ModuleInfo
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = DataStorage(db_path=db_path)
        
        # 创建测试数据
        device = DeviceInfo(
            management_ip="192.168.1.1",
            hostname="TEST-SW",
            model="C9300-24P",
            serial_number="FCW123",
            os_version="17.6.3",
            collection_status="success"
        )
        
        # 保存
        if storage.save_device(device):
            print("  ✓ 保存设备成功")
        else:
            print("  ✗ 保存设备失败")
            return False
        
        # 查询
        result = storage.get_device_by_ip("192.168.1.1")
        if result and result['hostname'] == "TEST-SW":
            print("  ✓ 查询设备成功")
        else:
            print("  ✗ 查询设备失败")
            return False
        
        # 更新（再次保存同一IP）
        device.hostname = "TEST-SW-UPDATED"
        if storage.save_device(device):
            result = storage.get_device_by_ip("192.168.1.1")
            if result['hostname'] == "TEST-SW-UPDATED":
                print("  ✓ 更新设备成功")
            else:
                print("  ✗ 更新设备失败")
                return False
        
        # 搜索
        results = storage.search_devices(model="C9300")
        if len(results) == 1:
            print("  ✓ 搜索设备成功")
        else:
            print("  ✗ 搜索设备失败")
            return False
        
        storage.close()
    
    print("\n  ✓ 数据库测试全部通过!")
    return True


if __name__ == "__main__":
    print("\n运行集成测试...\n")
    
    results = []
    results.append(("IOS 解析", test_ios_parsing()))
    results.append(("NX-OS 解析", test_nxos_parsing()))
    results.append(("数据导出", test_data_export()))
    results.append(("数据库存储", test_database()))
    
    print("\n" + "=" * 60)
    print("集成测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} - {name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    if passed == len(results):
        print("\n✅ 所有集成测试通过！系统逻辑验证完成。")
        print("\n⚠️  注意: 这仍然不能替代真实设备的测试。")
        print("   建议: 先用 1-2 台真实设备测试，确认后再批量运行。")
    else:
        print("\n❌ 部分测试失败，请检查相关模块。")
        sys.exit(1)
