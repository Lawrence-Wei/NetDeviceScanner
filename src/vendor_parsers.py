"""
多厂商设备输出解析器
Multi-Vendor Output Parser

支持解析不同厂商设备的命令输出
"""

import re
import logging
from typing import Optional
from .models import DeviceInfo
from .vendor_commands import get_vendor_from_device_type


logger = logging.getLogger(__name__)


class HuaweiParser:
    """华为设备解析器"""
    
    @staticmethod
    def parse_version(device_info: DeviceInfo, output: str):
        """解析 display version"""
        # 主机名
        hostname_match = re.search(r'sysname\s+(\S+)', output, re.I)
        if hostname_match and not device_info.hostname:
            device_info.hostname = hostname_match.group(1)
        
        # 系统版本
        device_info.os_type = "VRP"
        version_match = re.search(r'Version\s+([\d.()]+\S*)', output, re.I)
        if version_match:
            device_info.os_version = version_match.group(1)
        
        # 型号 - 多种格式
        model_patterns = [
            r'Huawei\s+(\S+)\s+[Rr]outer',
            r'Huawei\s+(\S+)\s+[Ss]witch',
            r'HUAWEI\s+(\S+)\s+uptime',
            r'(\S+)\s+uptime is',
        ]
        for pattern in model_patterns:
            match = re.search(pattern, output)
            if match:
                device_info.model = match.group(1)
                break
        
        # Uptime
        uptime_match = re.search(r'uptime is\s+(.+?)(?:\n|$)', output, re.I)
        if uptime_match:
            device_info.uptime = uptime_match.group(1).strip()
    
    @staticmethod
    def parse_device(device_info: DeviceInfo, output: str):
        """解析 display device"""
        # 序列号
        serial_match = re.search(r'ESN\s+:\s*(\S+)', output)
        if not serial_match:
            serial_match = re.search(r'SN\s+:\s*(\S+)', output)
        if serial_match:
            device_info.serial_number = serial_match.group(1)
        
        # 模块信息
        module_lines = re.findall(
            r'Slot\s+(\d+)\s+:\s*(.+?)(?:Online|Offline|Present|Absent)',
            output,
            re.I
        )
        device_info.module_count = len(module_lines)
    
    @staticmethod
    def parse_interfaces(device_info: DeviceInfo, output: str):
        """解析 display interface brief"""
        # 统计接口
        interface_lines = output.strip().split('\n')
        interface_count = 0
        
        for line in interface_lines:
            # 跳过表头
            if 'Interface' in line or 'InUti' in line:
                continue
            if re.match(r'^\s*\w+Ethernet', line) or re.match(r'^\s*GE', line):
                interface_count += 1
        
        device_info.total_ports = interface_count


class H3CParser:
    """H3C/HP Comware 设备解析器"""
    
    @staticmethod
    def parse_version(device_info: DeviceInfo, output: str):
        """解析 display version"""
        # 主机名
        hostname_match = re.search(r'sysname\s+(\S+)', output, re.I)
        if hostname_match and not device_info.hostname:
            device_info.hostname = hostname_match.group(1)
        
        # 系统版本
        device_info.os_type = "Comware"
        version_match = re.search(r'Version\s+([\d.()]+\S*)', output, re.I)
        if version_match:
            device_info.os_version = version_match.group(1)
        
        # 型号
        model_patterns = [
            r'H3C\s+(\S+)\s+Software',
            r'HP\s+(\S+)\s+Software',
            r'(\S+)\s+uptime is',
        ]
        for pattern in model_patterns:
            match = re.search(pattern, output)
            if match:
                device_info.model = match.group(1)
                break
        
        # Uptime
        uptime_match = re.search(r'uptime is\s+(.+?)(?:\n|$)', output, re.I)
        if uptime_match:
            device_info.uptime = uptime_match.group(1).strip()
    
    @staticmethod
    def parse_device_manuinfo(device_info: DeviceInfo, output: str):
        """解析 display device manuinfo"""
        # 序列号
        serial_match = re.search(r'DEVICE_SERIAL_NUMBER\s*:\s*(\S+)', output)
        if serial_match:
            device_info.serial_number = serial_match.group(1)
    
    @staticmethod
    def parse_interfaces(device_info: DeviceInfo, output: str):
        """解析 display interface brief"""
        # 统计接口
        interface_lines = re.findall(r'^\s*(GE|XGE|FE|Eth)', output, re.M)
        device_info.total_ports = len(interface_lines)


class JuniperParser:
    """Juniper 设备解析器"""
    
    @staticmethod
    def parse_version(device_info: DeviceInfo, output: str):
        """解析 show version"""
        # 主机名
        hostname_match = re.search(r'Hostname:\s+(\S+)', output)
        if hostname_match and not device_info.hostname:
            device_info.hostname = hostname_match.group(1)
        
        # 系统版本
        device_info.os_type = "Junos"
        version_match = re.search(r'Junos:\s+([\d.A-Z]+)', output)
        if version_match:
            device_info.os_version = version_match.group(1)
        
        # 型号
        model_match = re.search(r'Model:\s+(\S+)', output)
        if model_match:
            device_info.model = model_match.group(1)
    
    @staticmethod
    def parse_chassis_hardware(device_info: DeviceInfo, output: str):
        """解析 show chassis hardware"""
        # 序列号
        serial_match = re.search(r'Chassis\s+\S+\s+(\S+)', output)
        if serial_match:
            device_info.serial_number = serial_match.group(1)
    
    @staticmethod
    def parse_interfaces(device_info: DeviceInfo, output: str):
        """解析 show interfaces terse"""
        # 统计物理接口
        interface_lines = re.findall(r'^\s*(ge-|xe-|et-)', output, re.M | re.I)
        device_info.total_ports = len(interface_lines)


class AristaParser:
    """Arista 设备解析器"""
    
    @staticmethod
    def parse_version(device_info: DeviceInfo, output: str):
        """解析 show version"""
        # 主机名
        hostname_match = re.search(r'Hostname:\s+(\S+)', output)
        if hostname_match and not device_info.hostname:
            device_info.hostname = hostname_match.group(1)
        
        # 系统版本
        device_info.os_type = "EOS"
        version_match = re.search(r'Software image version:\s+([\d.]+)', output)
        if version_match:
            device_info.os_version = version_match.group(1)
        
        # 型号
        model_match = re.search(r'Hardware version:\s+(\S+)', output)
        if not model_match:
            model_match = re.search(r'Model:\s+(\S+)', output)
        if model_match:
            device_info.model = model_match.group(1)
        
        # 序列号
        serial_match = re.search(r'Serial number:\s+(\S+)', output)
        if serial_match:
            device_info.serial_number = serial_match.group(1)
        
        # Uptime
        uptime_match = re.search(r'Uptime:\s+(.+?)(?:\n|$)', output)
        if uptime_match:
            device_info.uptime = uptime_match.group(1).strip()
    
    @staticmethod
    def parse_interfaces(device_info: DeviceInfo, output: str):
        """解析 show interfaces status"""
        # 统计接口
        interface_lines = re.findall(r'^\s*Ethernet\d+', output, re.M)
        device_info.total_ports = len(interface_lines)


class HPProCurveParser:
    """HP ProCurve 设备解析器"""
    
    @staticmethod
    def parse_version(device_info: DeviceInfo, output: str):
        """解析 show version"""
        # 系统版本
        device_info.os_type = "ProCurve"
        version_match = re.search(r'Version\s+([\d.]+)', output)
        if version_match:
            device_info.os_version = version_match.group(1)
        
        # 型号
        model_match = re.search(r'ProCurve\s+(\S+)', output)
        if model_match:
            device_info.model = model_match.group(1)
    
    @staticmethod
    def parse_system(device_info: DeviceInfo, output: str):
        """解析 show system"""
        # 主机名
        hostname_match = re.search(r'Name\s+:\s+(\S+)', output)
        if hostname_match and not device_info.hostname:
            device_info.hostname = hostname_match.group(1)
        
        # 序列号
        serial_match = re.search(r'Serial Number\s+:\s+(\S+)', output)
        if serial_match:
            device_info.serial_number = serial_match.group(1)


# 厂商解析器映射
VENDOR_PARSERS = {
    "huawei": HuaweiParser,
    "h3c": H3CParser,
    "juniper": JuniperParser,
    "arista": AristaParser,
    "hp": HPProCurveParser,
}


def get_parser_for_vendor(vendor: str):
    """获取厂商对应的解析器类"""
    return VENDOR_PARSERS.get(vendor)
