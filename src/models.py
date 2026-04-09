"""
数据模型定义
定义设备信息的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class DeviceRole(Enum):
    """设备角色枚举"""
    SWITCH = "switch"
    ROUTER = "router"
    L3_SWITCH = "L3 switch"
    UNKNOWN = "unknown"


class DeviceType(Enum):
    """设备类型枚举"""
    IOS = "ios"
    NXOS = "nxos"
    IOS_XE = "ios_xe"


@dataclass
class ModuleInfo:
    """模块信息"""
    slot: str
    description: str
    model: str
    serial_number: str
    hardware_version: Optional[str] = None


@dataclass
class InterfaceInfo:
    """接口信息"""
    name: str
    status: str
    ip_address: Optional[str] = None
    description: Optional[str] = None
    speed: Optional[str] = None
    duplex: Optional[str] = None


@dataclass
class DeviceInfo:
    """设备完整信息"""
    # 基本信息
    management_ip: str
    hostname: str = ""
    model: str = ""
    serial_number: str = ""
    
    # 系统信息
    os_version: str = ""
    os_type: str = ""  # IOS / NX-OS / IOS-XE
    uptime: str = ""
    uptime_seconds: int = 0
    
    # 硬件信息
    total_ports: int = 0
    active_ports: int = 0
    modules: List[ModuleInfo] = field(default_factory=list)
    
    # 分类信息
    device_role: str = "unknown"
    device_type: str = "ios"
    location: str = ""
    
    # 接口信息
    interfaces: List[InterfaceInfo] = field(default_factory=list)
    
    # 元数据
    collection_time: datetime = field(default_factory=datetime.now)
    collection_status: str = "pending"  # pending, success, failed
    error_message: str = ""
    raw_output: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "management_ip": self.management_ip,
            "hostname": self.hostname,
            "model": self.model,
            "serial_number": self.serial_number,
            "os_version": self.os_version,
            "os_type": self.os_type,
            "uptime": self.uptime,
            "uptime_seconds": self.uptime_seconds,
            "total_ports": self.total_ports,
            "active_ports": self.active_ports,
            "module_count": len(self.modules),
            "modules_detail": [
                {
                    "slot": m.slot,
                    "description": m.description,
                    "model": m.model,
                    "serial_number": m.serial_number
                } for m in self.modules
            ],
            "device_role": self.device_role,
            "device_type": self.device_type,
            "location": self.location,
            "collection_time": self.collection_time.isoformat(),
            "collection_status": self.collection_status,
            "error_message": self.error_message
        }
    
    def to_flat_dict(self) -> dict:
        """转换为扁平化字典格式（用于导出）"""
        modules_str = "; ".join([
            f"{m.slot}: {m.model} ({m.serial_number})" 
            for m in self.modules
        ]) if self.modules else ""
        
        return {
            "管理IP": self.management_ip,
            "主机名": self.hostname,
            "型号": self.model,
            "序列号": self.serial_number,
            "系统版本": self.os_version,
            "系统类型": self.os_type,
            "运行时间": self.uptime,
            "总端口数": self.total_ports,
            "活动端口数": self.active_ports,
            "模块数量": len(self.modules),
            "模块详情": modules_str,
            "设备角色": self.device_role,
            "位置": self.location,
            "采集时间": self.collection_time.strftime("%Y-%m-%d %H:%M:%S"),
            "采集状态": self.collection_status,
            "错误信息": self.error_message
        }


@dataclass
class DeviceCredentials:
    """设备凭据"""
    username: str
    password: str
    secret: Optional[str] = None
    
    
@dataclass
class DeviceConfig:
    """设备配置"""
    ip: str
    device_type: str = "ios"
    role: str = "switch"
    hostname: Optional[str] = None
    location: Optional[str] = None
    port: int = 22
    credentials: Optional[DeviceCredentials] = None
