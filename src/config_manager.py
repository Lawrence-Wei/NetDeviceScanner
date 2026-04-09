"""
配置管理模块
加载和管理系统配置
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from dataclasses import dataclass

from .models import DeviceConfig, DeviceCredentials


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = Path(config_dir) if config_dir else self.base_dir / "config"
        
        # 加载环境变量
        env_file = self.base_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # 加载配置
        self.settings = self._load_settings()
        self.devices = self._load_devices()
        
        # 确保必要目录存在
        self._ensure_directories()
    
    def _load_yaml(self, filename: str) -> dict:
        """加载YAML文件"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 替换环境变量
            content = self._substitute_env_vars(content)
            return yaml.safe_load(content)
    
    def _substitute_env_vars(self, content: str) -> str:
        """替换配置中的环境变量"""
        pattern = r'\$\{(\w+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        
        return re.sub(pattern, replacer, content)
    
    def _load_settings(self) -> dict:
        """加载系统设置"""
        try:
            return self._load_yaml("settings.yaml")
        except FileNotFoundError:
            # 返回默认配置
            return {
                "connection": {
                    "timeout": 30,
                    "auth_timeout": 20,
                    "read_timeout": 60,
                    "max_retries": 3,
                    "retry_delay": 5
                },
                "concurrency": {
                    "max_workers": 20,
                    "batch_size": 50,
                    "batch_delay": 2
                },
                "storage": {
                    "db_type": "sqlite",
                    "sqlite_path": "./data/devices.db",
                    "export_dir": "./exports",
                    "log_dir": "./logs"
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
    
    def _load_devices(self) -> List[DeviceConfig]:
        """加载设备列表"""
        try:
            data = self._load_yaml("devices.yaml")
        except FileNotFoundError:
            return []
        
        devices = []
        default_creds = self._get_default_credentials()
        
        for dev in data.get("devices", []):
            # 处理凭据
            if any(k in dev for k in ["username", "password"]):
                creds = DeviceCredentials(
                    username=dev.get("username", default_creds.username),
                    password=dev.get("password", default_creds.password),
                    secret=dev.get("secret", default_creds.secret)
                )
            else:
                creds = default_creds
            
            device = DeviceConfig(
                ip=dev["ip"],
                device_type=dev.get("device_type", "ios"),
                role=dev.get("role", "switch"),
                hostname=dev.get("hostname"),
                location=dev.get("location", ""),
                port=dev.get("port", 22),
                credentials=creds
            )
            devices.append(device)
        
        return devices
    
    def _get_default_credentials(self) -> DeviceCredentials:
        """获取默认凭据"""
        creds = self.settings.get("credentials", {})
        return DeviceCredentials(
            username=creds.get("default_username", os.getenv("CISCO_USERNAME", "")),
            password=creds.get("default_password", os.getenv("CISCO_PASSWORD", "")),
            secret=creds.get("default_secret", os.getenv("CISCO_SECRET", ""))
        )
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        storage = self.settings.get("storage", {})
        
        dirs = [
            self.base_dir / "data",
            self.base_dir / storage.get("export_dir", "./exports"),
            self.base_dir / storage.get("log_dir", "./logs")
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def get_connection_settings(self) -> dict:
        """获取连接设置"""
        return self.settings.get("connection", {})
    
    def get_concurrency_settings(self) -> dict:
        """获取并发设置"""
        return self.settings.get("concurrency", {})
    
    def get_device_type_config(self, device_type: str) -> dict:
        """获取特定设备类型的配置"""
        device_types = self.settings.get("device_types", {})
        return device_types.get(device_type, device_types.get("ios", {}))
    
    def get_storage_settings(self) -> dict:
        """获取存储设置"""
        return self.settings.get("storage", {})
    
    def get_logging_settings(self) -> dict:
        """获取日志设置"""
        return self.settings.get("logging", {})
    
    def get_devices_by_group(self, group_name: str) -> List[DeviceConfig]:
        """按组获取设备"""
        try:
            data = self._load_yaml("devices.yaml")
        except FileNotFoundError:
            return []
        
        groups = data.get("device_groups", {})
        group = groups.get(group_name, {})
        group_ips = set(group.get("devices", []))
        
        return [d for d in self.devices if d.ip in group_ips]
    
    def load_devices_from_csv(self, csv_path: str) -> List[DeviceConfig]:
        """从CSV文件加载设备列表"""
        import csv
        
        devices = []
        default_creds = self._get_default_credentials()
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                device = DeviceConfig(
                    ip=row.get("ip", row.get("IP", row.get("management_ip", ""))),
                    device_type=row.get("device_type", row.get("type", "ios")),
                    role=row.get("role", "switch"),
                    hostname=row.get("hostname", row.get("name", None)),
                    location=row.get("location", ""),
                    port=int(row.get("port", 22)),
                    credentials=default_creds
                )
                if device.ip:
                    devices.append(device)
        
        return devices
    
    def load_devices_from_text(self, text_path: str) -> List[DeviceConfig]:
        """从文本文件加载设备IP列表（每行一个IP）"""
        devices = []
        default_creds = self._get_default_credentials()
        
        with open(text_path, 'r', encoding='utf-8') as f:
            for line in f:
                ip = line.strip()
                if ip and not ip.startswith('#'):
                    device = DeviceConfig(
                        ip=ip,
                        device_type="ios",
                        role="switch",
                        credentials=default_creds
                    )
                    devices.append(device)
        
        return devices
