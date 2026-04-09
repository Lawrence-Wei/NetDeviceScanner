"""
命令输出解析器模块
解析网络设备命令输出，提取关键信息
支持多厂商：Cisco, Huawei, H3C, Juniper, Arista, HP
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import timedelta

from .models import DeviceInfo, ModuleInfo, InterfaceInfo
from .vendor_commands import get_vendor_from_device_type
from .vendor_parsers import get_parser_for_vendor


logger = logging.getLogger(__name__)


class OutputParser:
    """命令输出解析器"""
    
    def parse_device_info(self, device_info: DeviceInfo) -> DeviceInfo:
        """
        解析设备信息 - 支持多厂商
        
        Args:
            device_info: 包含原始输出的设备信息对象
            
        Returns:
            解析后的设备信息对象
        """
        if device_info.collection_status != "success":
            return device_info
        
        raw_output = device_info.raw_output
        device_type = device_info.device_type.lower()
        
        # 获取厂商
        vendor = get_vendor_from_device_type(device_type)
        
        try:
            # 尝试使用厂商特定解析器
            if vendor != "cisco" and vendor != "unknown":
                vendor_parser = get_parser_for_vendor(vendor)
                if vendor_parser:
                    logger.info(f"使用 {vendor} 厂商解析器")
                    self._parse_with_vendor_parser(device_info, raw_output, vendor_parser, device_type)
                    return device_info
            
            # Cisco 设备或未知设备使用原有解析逻辑
            # 解析 show version 或 display version
            version_output = self._get_output(raw_output, ["show version", "display version"])
            if version_output:
                self._parse_show_version(device_info, version_output, device_type)
            
            # 解析 show inventory 或 display device
            inventory_output = self._get_output(raw_output, ["show inventory", "display device", "show chassis hardware"])
            if inventory_output:
                self._parse_show_inventory(device_info, inventory_output, device_type)
            
            # 解析接口状态
            interface_output = self._get_output(raw_output, ["show interface", "display interface brief", "show interfaces"])
            if interface_output:
                self._parse_interface_status(device_info, interface_output, device_type)
            
            # 解析模块信息
            module_output = self._get_output(raw_output, ["show module", "display device"])
            if module_output:
                self._parse_show_module(device_info, module_output, device_type)
            
            # 计算端口数量
            self._calculate_port_count(device_info)
            
        except Exception as e:
            logger.error(f"解析设备 {device_info.management_ip} 输出时出错: {e}")
            device_info.error_message = f"解析错误: {e}"
        
        return device_info
    
    def _parse_with_vendor_parser(self, device_info: DeviceInfo, raw_output: Dict, vendor_parser, device_type: str):
        """使用厂商特定解析器"""
        # 解析版本信息
        version_output = self._get_output(raw_output, ["show version", "display version"])
        if version_output:
            vendor_parser.parse_version(device_info, version_output)
        
        # 解析设备/清单信息
        inventory_output = self._get_output(raw_output, [
            "show inventory", 
            "display device", 
            "display device manuinfo",
            "show chassis hardware",
            "show system"
        ])
        if inventory_output:
            # 根据厂商调用不同方法
            if hasattr(vendor_parser, 'parse_device'):
                vendor_parser.parse_device(device_info, inventory_output)
            elif hasattr(vendor_parser, 'parse_device_manuinfo'):
                vendor_parser.parse_device_manuinfo(device_info, inventory_output)
            elif hasattr(vendor_parser, 'parse_chassis_hardware'):
                vendor_parser.parse_chassis_hardware(device_info, inventory_output)
            elif hasattr(vendor_parser, 'parse_system'):
                vendor_parser.parse_system(device_info, inventory_output)
        
        # 解析接口信息
        interface_output = self._get_output(raw_output, [
            "show interface", 
            "display interface brief",
            "show interfaces"
        ])
        if interface_output:
            vendor_parser.parse_interfaces(device_info, interface_output)
    
    def _get_output(self, raw_output: Dict[str, str], command_prefixes: List[str]) -> str:
        """根据命令前缀列表获取输出（支持多种命令格式）"""
        if isinstance(command_prefixes, str):
            command_prefixes = [command_prefixes]
        
        for prefix in command_prefixes:
            for cmd, output in raw_output.items():
                if cmd.lower().startswith(prefix.lower()):
                    return output
        return ""
    
    def _parse_show_version(self, device_info: DeviceInfo, output: str, device_type: str):
        """解析 show version 输出"""
        
        # 解析主机名
        if not device_info.hostname:
            # 根据设备类型使用不同的解析顺序
            if device_type in ["nxos", "cisco_nxos"]:
                hostname_patterns = [
                    r'Device name:\s*(\S+)',  # NX-OS 优先
                    r'switchname:\s*(\S+)',   # NX-OS 备选
                    r'^(\S+)\s+uptime',       # 通用
                ]
            else:
                hostname_patterns = [
                    r'^(\S+)\s+uptime',       # IOS
                    r'Device name:\s*(\S+)',  # 备选
                    r'^(\S+)#',               # 从提示符
                ]
            for pattern in hostname_patterns:
                match = re.search(pattern, output, re.MULTILINE | re.IGNORECASE)
                if match:
                    device_info.hostname = match.group(1)
                    break
        
        # 解析系统类型和版本
        if device_type in ["nxos", "cisco_nxos"]:
            device_info.os_type = "NX-OS"
            # NX-OS 版本
            version_patterns = [
                r'NXOS:\s*version\s+(\S+)',
                r'system:\s*version\s+(\S+)',
                r'kickstart:\s*version\s+(\S+)',
                r'NXOS\s+image\s+file.*?version\s+(\S+)',
            ]
        else:
            # 判断是 IOS 还是 IOS-XE
            if "IOS-XE" in output or "IOS XE" in output:
                device_info.os_type = "IOS-XE"
            else:
                device_info.os_type = "IOS"
            
            version_patterns = [
                r'Version\s+(\S+)',
                r'IOS.*?Version\s+(\S+)',
                r'Cisco IOS Software.*?Version\s+(\S+)',
            ]
        
        for pattern in version_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                device_info.os_version = match.group(1).rstrip(',')
                break
        
        # 解析型号
        model_patterns = [
            r'cisco\s+(WS-\S+)',  # Catalyst 交换机
            r'cisco\s+(C\d+\S*)',  # Catalyst 9000 系列
            r'cisco\s+(CISCO\d+/?\S*)',  # ISR G2 路由器 (CISCO1921/K9, CISCO2911/K9)
            r'cisco\s+(\d{4}/?\S*)',  # 老型号路由器 (1921, 2911, 2811, 1841)
            r'cisco\s+Nexus\s*(\S+)',  # Nexus
            r'cisco\s+(N\d+\S*)',  # Nexus 简写
            r'cisco\s+(ISR\S*)',  # ISR 路由器
            r'cisco\s+(ASR\S*)',  # ASR 路由器
            r'cisco\s+(\S+)\s+\([^)]+\)\s+processor',  # 通用
            r'Model\s+number\s*:\s*(\S+)',  # NX-OS
            r'Hardware:\s*(\S+)',  # 某些版本
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                device_info.model = match.group(1)
                break
        
        # 解析序列号
        serial_patterns = [
            r'Processor\s+board\s+ID\s+(\S+)',  # IOS
            r'System\s+serial\s+number\s*:\s*(\S+)',  # 某些设备
            r'Serial\s+Number\s*:\s*(\S+)',  # NX-OS
        ]
        
        for pattern in serial_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                device_info.serial_number = match.group(1)
                break
        
        # 解析 uptime
        uptime_patterns = [
            r'uptime\s+is\s+(.+?)(?:\n|$)',  # IOS
            r'Kernel\s+uptime\s+is\s+(.+?)(?:\n|$)',  # NX-OS
            r'System\s+uptime\s*:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in uptime_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                device_info.uptime = match.group(1).strip()
                device_info.uptime_seconds = self._parse_uptime_to_seconds(device_info.uptime)
                break
    
    def _parse_uptime_to_seconds(self, uptime_str: str) -> int:
        """将 uptime 字符串转换为秒数"""
        total_seconds = 0
        
        # 解析年
        years = re.search(r'(\d+)\s*year', uptime_str, re.IGNORECASE)
        if years:
            total_seconds += int(years.group(1)) * 365 * 24 * 3600
        
        # 解析周
        weeks = re.search(r'(\d+)\s*week', uptime_str, re.IGNORECASE)
        if weeks:
            total_seconds += int(weeks.group(1)) * 7 * 24 * 3600
        
        # 解析天
        days = re.search(r'(\d+)\s*day', uptime_str, re.IGNORECASE)
        if days:
            total_seconds += int(days.group(1)) * 24 * 3600
        
        # 解析小时
        hours = re.search(r'(\d+)\s*hour', uptime_str, re.IGNORECASE)
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        
        # 解析分钟
        minutes = re.search(r'(\d+)\s*minute', uptime_str, re.IGNORECASE)
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        
        # 解析秒
        seconds = re.search(r'(\d+)\s*second', uptime_str, re.IGNORECASE)
        if seconds:
            total_seconds += int(seconds.group(1))
        
        return total_seconds
    
    def _parse_show_inventory(self, device_info: DeviceInfo, output: str, device_type: str):
        """解析 show inventory 输出"""
        
        # 查找所有模块/组件
        # 格式通常是:
        # NAME: "xxx", DESCR: "xxx"
        # PID: xxx, VID: xxx, SN: xxx
        
        pattern = r'NAME:\s*"([^"]+)".*?DESCR:\s*"([^"]*)".*?PID:\s*(\S+).*?SN:\s*(\S+)'
        
        matches = re.findall(pattern, output, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            name, descr, pid, sn = match
            
            # 跳过空或无效的条目
            if not sn or sn.upper() in ['N/A', 'NA', '']:
                continue
            
            module = ModuleInfo(
                slot=name.strip(),
                description=descr.strip(),
                model=pid.strip(),
                serial_number=sn.strip()
            )
            device_info.modules.append(module)
        
        # 如果主序列号为空，尝试从 inventory 获取机箱序列号
        if not device_info.serial_number and device_info.modules:
            for module in device_info.modules:
                if 'chassis' in module.slot.lower() or module.slot == '1':
                    device_info.serial_number = module.serial_number
                    break
        
        # 如果型号为空，尝试从 inventory 获取
        if not device_info.model and device_info.modules:
            for module in device_info.modules:
                if 'chassis' in module.slot.lower():
                    device_info.model = module.model
                    break
    
    def _parse_interface_status(self, device_info: DeviceInfo, output: str, device_type: str):
        """解析接口状态输出"""
        
        interfaces = []
        
        # IOS/IOS-XE show interfaces status 格式
        # Port      Name               Status       Vlan       Duplex  Speed Type
        # Gi0/1     Server1            connected    10         a-full  a-1000 10/100/1000BaseTX
        
        lines = output.strip().split('\n')
        
        for line in lines:
            # 跳过标题行和空行
            if not line.strip() or 'Port' in line or 'Name' in line or '---' in line:
                continue
            
            # 尝试解析接口行
            # 匹配常见的接口名称格式
            interface_pattern = r'^(\S+)\s+'
            match = re.match(interface_pattern, line)
            
            if match:
                interface_name = match.group(1)
                
                # 检查是否是有效的接口名称
                if self._is_valid_interface(interface_name):
                    status = "unknown"
                    if 'connected' in line.lower() or 'up' in line.lower():
                        status = "up"
                    elif 'notconnect' in line.lower() or 'down' in line.lower():
                        status = "down"
                    elif 'disabled' in line.lower():
                        status = "disabled"
                    elif 'err-disabled' in line.lower():
                        status = "err-disabled"
                    
                    interfaces.append(InterfaceInfo(
                        name=interface_name,
                        status=status
                    ))
        
        device_info.interfaces = interfaces
    
    def _is_valid_interface(self, name: str) -> bool:
        """检查是否是有效的接口名称"""
        valid_prefixes = [
            'Gi', 'Fa', 'Te', 'Eth', 'Po', 'Vl',  # 常见缩写
            'GigabitEthernet', 'FastEthernet', 'TenGigabitEthernet',
            'Ethernet', 'Port-channel', 'Vlan',
            'mgmt', 'Management',  # 管理接口
            'Twe',  # 25G/40G
            'Hun', 'Fo',  # 100G/40G
        ]
        
        for prefix in valid_prefixes:
            if name.startswith(prefix):
                return True
        return False
    
    def _parse_show_module(self, device_info: DeviceInfo, output: str, device_type: str):
        """解析 show module 输出"""
        
        # 如果已经从 inventory 获取了足够的模块信息，跳过
        if device_info.modules:
            return
        
        # NX-OS show module 格式
        # Mod  Ports  Module-Type                         Model              Status
        # ---  -----  ----------------------------------- ------------------ ----------
        # 1    48     48x10GE + 4x40GE Ethernet Module    N9K-X9464PX        active
        
        lines = output.strip().split('\n')
        
        for line in lines:
            # 跳过标题行
            if not line.strip() or 'Mod' in line or '---' in line:
                continue
            
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                module = ModuleInfo(
                    slot=f"Module {parts[0]}",
                    description=" ".join(parts[2:-2]) if len(parts) > 4 else "",
                    model=parts[-2] if len(parts) > 3 else "",
                    serial_number=""
                )
                device_info.modules.append(module)
    
    def _calculate_port_count(self, device_info: DeviceInfo):
        """计算端口数量"""
        
        # 总端口数
        device_info.total_ports = len(device_info.interfaces)
        
        # 活动端口数
        device_info.active_ports = sum(
            1 for iface in device_info.interfaces 
            if iface.status.lower() in ['up', 'connected']
        )
        
        # 如果接口列表为空，尝试从模块估算
        if device_info.total_ports == 0 and device_info.modules:
            for module in device_info.modules:
                # 尝试从描述中提取端口数
                port_match = re.search(r'(\d+)\s*(?:port|x\d+G)', module.description, re.IGNORECASE)
                if port_match:
                    device_info.total_ports += int(port_match.group(1))


class IOSParser(OutputParser):
    """IOS 专用解析器"""
    pass


class NXOSParser(OutputParser):
    """NX-OS 专用解析器"""
    
    def _parse_show_version(self, device_info: DeviceInfo, output: str, device_type: str):
        """NX-OS 专用 show version 解析"""
        super()._parse_show_version(device_info, output, device_type)
        
        # NX-OS 特定的解析
        if not device_info.model:
            match = re.search(r'cisco\s+Nexus\s*\d*\s*(\S+)', output, re.IGNORECASE)
            if match:
                device_info.model = f"Nexus {match.group(1)}"


def get_parser(device_type: str) -> OutputParser:
    """根据设备类型获取对应的解析器"""
    if device_type.lower() in ['nxos', 'cisco_nxos']:
        return NXOSParser()
    return OutputParser()
