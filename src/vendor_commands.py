"""
多厂商设备命令映射
Multi-Vendor Device Command Mapping

支持的设备厂商：
- Cisco (IOS, IOS-XE, NX-OS)
- Huawei (VRP)
- H3C (Comware)
- Juniper (Junos)
- Arista (EOS)
- HP/HPE (ProCurve, Comware)
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class VendorCommands:
    """厂商命令集"""
    version_cmd: str          # 获取版本信息
    inventory_cmd: str        # 获取硬件清单
    interface_cmd: str        # 获取接口状态
    module_cmd: str          # 获取模块信息
    hostname_cmd: str        # 获取主机名（可选）


# 各厂商支持的 Netmiko 设备类型
VENDOR_DEVICE_TYPES = {
    "cisco": ["cisco_ios", "cisco_xe", "cisco_nxos", "cisco_xr", "cisco_asa"],
    "huawei": ["huawei", "huawei_vrpv8"],
    "h3c": ["hp_comware"],
    "juniper": ["juniper", "juniper_junos"],
    "arista": ["arista_eos"],
    "hp": ["hp_procurve", "hp_comware"],
}


# 厂商命令映射
VENDOR_COMMAND_MAP = {
    # Cisco IOS / IOS-XE
    "cisco_ios": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show running-config | include hostname"
    ),
    
    # 别名：ios -> cisco_ios（向后兼容）
    "ios": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show running-config | include hostname"
    ),
    
    # Cisco IOS-XE (与 IOS 基本相同)
    "cisco_xe": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show running-config | include hostname"
    ),
    
    # 别名：ios_xe -> cisco_xe（向后兼容）
    "ios_xe": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show running-config | include hostname"
    ),
    
    # Cisco NX-OS
    "cisco_nxos": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show hostname"
    ),
    
    # 别名：nxos -> cisco_nxos（向后兼容）
    "nxos": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interface status",
        module_cmd="show module",
        hostname_cmd="show hostname"
    ),
    
    # Cisco IOS-XR
    "cisco_xr": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interfaces brief",
        module_cmd="show platform",
        hostname_cmd="show running-config hostname"
    ),
    
    # Huawei VRP
    "huawei": VendorCommands(
        version_cmd="display version",
        inventory_cmd="display device",
        interface_cmd="display interface brief",
        module_cmd="display device",
        hostname_cmd="display current-configuration | include sysname"
    ),
    
    # Huawei VRP V8
    "huawei_vrpv8": VendorCommands(
        version_cmd="display version",
        inventory_cmd="display device",
        interface_cmd="display interface brief",
        module_cmd="display device",
        hostname_cmd="display current-configuration | include sysname"
    ),
    
    # H3C Comware
    "hp_comware": VendorCommands(
        version_cmd="display version",
        inventory_cmd="display device manuinfo",
        interface_cmd="display interface brief",
        module_cmd="display device",
        hostname_cmd="display current-configuration | include sysname"
    ),
    
    # Juniper Junos
    "juniper_junos": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show chassis hardware",
        interface_cmd="show interfaces terse",
        module_cmd="show chassis fpc",
        hostname_cmd="show configuration system host-name"
    ),
    
    # Arista EOS
    "arista_eos": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show inventory",
        interface_cmd="show interfaces status",
        module_cmd="show module",
        hostname_cmd="show hostname"
    ),
    
    # HP ProCurve
    "hp_procurve": VendorCommands(
        version_cmd="show version",
        inventory_cmd="show system",
        interface_cmd="show interfaces brief",
        module_cmd="show modules",
        hostname_cmd="show running-config | include hostname"
    ),
}


def get_vendor_from_device_type(device_type: str) -> str:
    """
    根据设备类型获取厂商名称
    
    Args:
        device_type: Netmiko 设备类型
        
    Returns:
        厂商名称
    """
    for vendor, types in VENDOR_DEVICE_TYPES.items():
        if device_type in types:
            return vendor
    return "unknown"


def get_commands_for_device(device_type: str) -> VendorCommands:
    """
    获取特定设备类型的命令集
    
    Args:
        device_type: Netmiko 设备类型
        
    Returns:
        VendorCommands 对象，如果不支持则返回 None
    """
    return VENDOR_COMMAND_MAP.get(device_type)


def get_supported_vendors() -> List[str]:
    """获取支持的厂商列表"""
    return list(VENDOR_DEVICE_TYPES.keys())


def get_supported_device_types() -> List[str]:
    """获取所有支持的设备类型"""
    all_types = []
    for types in VENDOR_DEVICE_TYPES.values():
        all_types.extend(types)
    return all_types


def is_device_type_supported(device_type: str) -> bool:
    """检查设备类型是否支持"""
    return device_type in VENDOR_COMMAND_MAP


# 厂商友好名称映射
VENDOR_FRIENDLY_NAMES = {
    "cisco": "Cisco",
    "huawei": "华为 (Huawei)",
    "h3c": "新华三 (H3C)",
    "juniper": "Juniper",
    "arista": "Arista",
    "hp": "HP/HPE",
}


def get_vendor_friendly_name(vendor: str) -> str:
    """获取厂商友好名称"""
    return VENDOR_FRIENDLY_NAMES.get(vendor, vendor.upper())
