"""
网络设备自动发现模块
Network Device Auto-Discovery

通过网络扫描自动发现网络设备，无需手动配置
支持：
- IP 段扫描（支持从文件读取）
- SSH 端口检测
- 自动设备类型识别（Cisco, Huawei, H3C, Juniper, Arista, HP）
"""

import socket
import logging
import concurrent.futures
from typing import List, Tuple, Optional
from ipaddress import IPv4Network, IPv4Address
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

from .models import DeviceConfig, DeviceCredentials
from .vendor_commands import get_vendor_from_device_type, VENDOR_FRIENDLY_NAMES


logger = logging.getLogger(__name__)


class NetworkScanner:
    """网络扫描器 - 支持多厂商设备自动发现"""
    
    def __init__(self, 
                 credentials: DeviceCredentials,
                 ssh_port: int = 22,
                 timeout: int = 5,
                 max_workers: int = 50):
        """
        初始化扫描器
        
        Args:
            credentials: SSH 凭据
            ssh_port: SSH 端口
            timeout: 连接超时
            max_workers: 扫描并发数
        """
        self.credentials = credentials
        self.ssh_port = ssh_port
        self.timeout = timeout
        self.max_workers = max_workers
    
    @staticmethod
    def load_networks_from_file(file_path: str) -> List[str]:
        """
        从文件加载网段列表
        
        支持格式：
        - 每行一个网段：192.168.1.0/24
        - 支持注释（# 开头）
        - 自动忽略空行
        
        Args:
            file_path: 网段文件路径
            
        Returns:
            网段列表
        """
        networks = []
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"网段文件不存在: {file_path}")
            return networks
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 忽略空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 验证网段格式
                    try:
                        IPv4Network(line, strict=False)
                        networks.append(line)
                        logger.debug(f"加载网段: {line}")
                    except ValueError as e:
                        logger.warning(f"第{line_num}行网段格式无效: {line} - {e}")
            
            logger.info(f"从文件加载了 {len(networks)} 个网段")
            
        except Exception as e:
            logger.error(f"读取网段文件失败: {e}")
        
        return networks
    
    def scan_network(self, network: str) -> List[str]:
        """
        扫描网络段，找出开放 SSH 端口的主机
        
        Args:
            network: IP 网段，如 "192.168.1.0/24"
            
        Returns:
            开放 SSH 的 IP 列表
        """
        logger.info(f"扫描网段: {network}")
        
        try:
            net = IPv4Network(network, strict=False)
        except ValueError as e:
            logger.error(f"无效的网段: {network} - {e}")
            return []
        
        # 获取所有可用 IP（排除网络地址和广播地址）
        hosts = list(net.hosts())
        logger.info(f"扫描 {len(hosts)} 个 IP 地址...")
        
        reachable_hosts = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {
                executor.submit(self._check_ssh_port, str(ip)): str(ip)
                for ip in hosts
            }
            
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    is_open = future.result()
                    if is_open:
                        reachable_hosts.append(ip)
                        logger.info(f"  ✓ {ip} - SSH 端口开放")
                except Exception as e:
                    logger.debug(f"  - {ip} - 检查失败: {e}")
        
        logger.info(f"找到 {len(reachable_hosts)} 台开放 SSH 的主机")
        return reachable_hosts
    
    def _check_ssh_port(self, ip: str) -> bool:
        """检查 SSH 端口是否开放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, self.ssh_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def identify_devices(self, 
                        ip_list: List[str],
                        progress_callback=None) -> List[DeviceConfig]:
        """
        识别设备类型并创建配置
        
        Args:
            ip_list: IP 地址列表
            progress_callback: 进度回调函数
            
        Returns:
            已识别的设备配置列表
        """
        logger.info(f"识别 {len(ip_list)} 台设备...")
        
        identified_devices = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(20, len(ip_list))) as executor:
            future_to_ip = {
                executor.submit(self._identify_single_device, ip): ip
                for ip in ip_list
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                completed += 1
                
                try:
                    device_config = future.result()
                    if device_config:
                        identified_devices.append(device_config)
                        logger.info(
                            f"  ✓ {ip} - {device_config.device_type.upper()} "
                            f"({device_config.hostname or 'N/A'})"
                        )
                    else:
                        logger.warning(f"  ✗ {ip} - 无法识别")
                        
                except Exception as e:
                    logger.error(f"  ✗ {ip} - 识别失败: {e}")
                
                if progress_callback:
                    progress_callback(completed, len(ip_list))
        
        logger.info(f"成功识别 {len(identified_devices)} 台思科设备")
        return identified_devices
    
    def _identify_single_device(self, ip: str) -> Optional[DeviceConfig]:
        """
        识别单个设备 - 支持多厂商
        
        策略:
        1. 使用 Netmiko autodetect 自动检测设备类型
        2. 支持 Cisco, Huawei, H3C, Juniper, Arista, HP
        3. 返回正确的设备配置
        """
        device_params = {
            'device_type': 'autodetect',
            'host': ip,
            'username': self.credentials.username,
            'password': self.credentials.password,
            'timeout': self.timeout,
        }
        
        if self.credentials.secret:
            device_params['secret'] = self.credentials.secret
        
        try:
            from netmiko import SSHDetect
            
            # 使用 netmiko 的自动检测
            guesser = SSHDetect(**device_params)
            best_match = guesser.autodetect()
            guesser.connection.disconnect()
            
            if best_match:
                # 获取厂商信息
                vendor = get_vendor_from_device_type(best_match)
                vendor_name = VENDOR_FRIENDLY_NAMES.get(vendor, vendor.upper())
                
                logger.info(f"{ip} - 检测到 {vendor_name} 设备 ({best_match})")
                
                # 获取基本信息
                hostname, role = self._get_device_info(ip, best_match)
                
                return DeviceConfig(
                    ip=ip,
                    device_type=best_match,  # 直接使用 Netmiko 设备类型
                    role=role,
                    hostname=hostname,
                    port=self.ssh_port,
                    credentials=self.credentials
                )
            
        except NetmikoAuthenticationException:
            logger.warning(f"{ip} - 认证失败")
        except NetmikoTimeoutException:
            logger.debug(f"{ip} - 连接超时")
        except Exception as e:
            logger.debug(f"{ip} - 检测失败: {e}")
        
        return None
    
    def _map_netmiko_type(self, netmiko_type: str) -> str:
        """将 Netmiko 设备类型映射到我们的类型（已弃用，直接使用 Netmiko 类型）"""
        return netmiko_type
    
    def _get_device_info(self, ip: str, device_type: str) -> Tuple[str, str]:
        """
        获取设备基本信息（hostname 和角色）
        
        Returns:
            (hostname, role)
        """
        try:
            device_params = {
                'device_type': device_type,
                'host': ip,
                'username': self.credentials.username,
                'password': self.credentials.password,
                'timeout': self.timeout,
            }
            
            if self.credentials.secret:
                device_params['secret'] = self.credentials.secret
            
            with ConnectHandler(**device_params) as conn:
                if self.credentials.secret:
                    conn.enable()
                
                # 获取 hostname（从提示符）
                prompt = conn.find_prompt()
                hostname = prompt.rstrip('#>').strip()
                
                # 简单判断角色
                output = conn.send_command('show version', read_timeout=10)
                
                role = 'switch'  # 默认
                
                # 1. 关键字判断
                if 'router' in output.lower():
                    role = 'router'
                # 2. 基于型号判断（ISR G2和老型号路由器）
                elif any(model in output.upper() for model in [
                    'CISCO1921', 'CISCO2911', 'CISCO2901', 'CISCO3925', 'CISCO3945',
                    'ISR', 'ASR'
                ]):
                    role = 'router'
                # 3. 基于纯数字型号判断（需要更精确匹配避免误判）
                elif any(f'cisco {model}' in output.lower() for model in [
                    '1841', '2811', '2821', '2851', '1921', '2901', '2911', '3925', '3945'
                ]):
                    role = 'router'
                # 4. Nexus/Catalyst 判断
                elif 'nexus' in output.lower() or 'catalyst' in output.lower():
                    if 'l3' in output.lower() or 'layer 3' in output.lower():
                        role = 'L3 switch'
                    else:
                        role = 'switch'
                
                return hostname, role
                
        except Exception as e:
            logger.debug(f"获取设备信息失败 ({ip}): {e}")
            return '', 'switch'
    
    def scan_and_identify(self, 
                         networks: List[str],
                         progress_callback=None) -> List[DeviceConfig]:
        """
        一站式扫描和识别
        
        Args:
            networks: 网段列表，如 ["192.168.1.0/24", "10.0.0.0/24"]
            progress_callback: 进度回调
            
        Returns:
            已识别的设备配置列表
        """
        all_hosts = []
        
        # 扫描所有网段
        for network in networks:
            hosts = self.scan_network(network)
            all_hosts.extend(hosts)
        
        # 去重
        all_hosts = list(set(all_hosts))
        logger.info(f"总共发现 {len(all_hosts)} 台主机")
        
        # 识别设备
        devices = self.identify_devices(all_hosts, progress_callback)
        
        return devices


def auto_discover(
    networks: List[str],
    username: str,
    password: str,
    secret: str = None,
    ssh_port: int = 22,
    scan_timeout: int = 5,
    max_scan_workers: int = 50
) -> List[DeviceConfig]:
    """
    自动发现网络中的思科设备（便捷函数）
    
    Args:
        networks: 网段列表
        username: SSH 用户名
        password: SSH 密码
        secret: enable 密码
        ssh_port: SSH 端口
        scan_timeout: 扫描超时
        max_scan_workers: 扫描并发数
        
    Returns:
        已识别的设备配置列表
        
    Example:
        >>> devices = auto_discover(
        ...     networks=["192.168.1.0/24", "10.0.0.0/24"],
        ...     username="admin",
        ...     password="password",
        ...     secret="enable_pass"
        ... )
        >>> print(f"发现 {len(devices)} 台设备")
    """
    credentials = DeviceCredentials(
        username=username,
        password=password,
        secret=secret
    )
    
    scanner = NetworkScanner(
        credentials=credentials,
        ssh_port=ssh_port,
        timeout=scan_timeout,
        max_workers=max_scan_workers
    )
    
    return scanner.scan_and_identify(networks)
