"""
设备连接器模块
负责与网络设备建立SSH连接并执行命令
支持多厂商：Cisco, Huawei, H3C, Juniper, Arista, HP
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from netmiko.exceptions import NetmikoBaseException
from paramiko.ssh_exception import SSHException

from .models import DeviceConfig, DeviceInfo
from .vendor_commands import get_commands_for_device, is_device_type_supported


logger = logging.getLogger(__name__)


class DeviceConnector:
    """设备连接器 - 支持多厂商设备"""
    
    def __init__(self, 
                 timeout: int = 30,
                 auth_timeout: int = 20,
                 read_timeout: int = 60,
                 max_retries: int = 3,
                 retry_delay: int = 5):
        """
        初始化连接器
        
        Args:
            timeout: 连接超时时间
            auth_timeout: 认证超时时间
            read_timeout: 读取超时时间
            max_retries: 最大重试次数
            retry_delay: 重试间隔
        """
        self.timeout = timeout
        self.auth_timeout = auth_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _get_commands(self, device_type: str) -> List[str]:
        """获取设备需要执行的命令列表"""
        vendor_cmds = get_commands_for_device(device_type)
        if not vendor_cmds:
            logger.warning(f"不支持的设备类型: {device_type}, 使用默认 Cisco IOS 命令")
            vendor_cmds = get_commands_for_device("cisco_ios")
        
        # 返回命令列表
        return [
            vendor_cmds.version_cmd,
            vendor_cmds.inventory_cmd,
            vendor_cmds.interface_cmd,
            vendor_cmds.module_cmd,
        ]
    
    def connect_and_collect(self, device_config: DeviceConfig) -> DeviceInfo:
        """
        连接设备并收集信息
        
        Args:
            device_config: 设备配置
            
        Returns:
            DeviceInfo: 设备信息对象
        """
        device_info = DeviceInfo(
            management_ip=device_config.ip,
            device_type=device_config.device_type,
            device_role=device_config.role,
            location=device_config.location or "",
            hostname=device_config.hostname or ""
        )
        
        # 检查设备类型是否支持
        if not is_device_type_supported(device_config.device_type):
            device_info.collection_status = "failed"
            
            # 提供更友好的错误提示
            suggestion = ""
            if device_config.device_type.lower() in ["ios", "ios_xe", "nxos"]:
                type_map = {
                    "ios": "cisco_ios",
                    "ios_xe": "cisco_xe", 
                    "nxos": "cisco_nxos"
                }
                suggested = type_map.get(device_config.device_type.lower())
                if suggested:
                    suggestion = f" (建议使用: {suggested}，但 '{device_config.device_type}' 已支持作为别名)"
            
            device_info.error_message = f"不支持的设备类型: {device_config.device_type}{suggestion}"
            logger.error(f"{device_config.ip} - {device_info.error_message}")
            logger.info(f"支持的设备类型: {', '.join(['cisco_ios', 'cisco_xe', 'cisco_nxos', 'huawei', 'hp_comware', 'juniper', 'arista_eos'])}")
            return device_info
        
        commands = self._get_commands(device_config.device_type)
        
        # 构建连接参数
        device_params = {
            "device_type": device_config.device_type,
            "host": device_config.ip,
            "port": device_config.port,
            "username": device_config.credentials.username,
            "password": device_config.credentials.password,
            "timeout": self.timeout,
            "auth_timeout": self.auth_timeout,
            "read_timeout_override": self.read_timeout,
            "fast_cli": False,  # 对于大型输出更稳定
        }
        
        # 如果有enable密码
        if device_config.credentials.secret:
            device_params["secret"] = device_config.credentials.secret
        
        # 重试机制
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"连接设备 {device_config.ip} (尝试 {attempt}/{self.max_retries})")
                
                with ConnectHandler(**device_params) as conn:
                    # 进入enable模式
                    if device_config.credentials.secret:
                        conn.enable()
                    
                    # 执行命令并收集输出
                    raw_output = {}
                    for cmd in commands:
                        try:
                            output = conn.send_command(
                                cmd,
                                read_timeout=self.read_timeout,
                                strip_prompt=True,
                                strip_command=True
                            )
                            raw_output[cmd] = output
                            logger.debug(f"命令 '{cmd}' 执行成功")
                        except Exception as e:
                            logger.warning(f"命令 '{cmd}' 执行失败: {e}")
                            raw_output[cmd] = ""
                    
                    device_info.raw_output = raw_output
                    device_info.collection_status = "success"
                    logger.info(f"设备 {device_config.ip} 信息收集完成")
                    return device_info
                    
            except NetmikoTimeoutException as e:
                last_error = f"连接超时: {e}"
                logger.warning(f"设备 {device_config.ip} {last_error}")
                
            except NetmikoAuthenticationException as e:
                last_error = f"认证失败: {e}"
                logger.error(f"设备 {device_config.ip} {last_error}")
                break  # 认证失败不重试
                
            except SSHException as e:
                last_error = f"SSH错误: {e}"
                logger.warning(f"设备 {device_config.ip} {last_error}")
                
            except NetmikoBaseException as e:
                last_error = f"Netmiko错误: {e}"
                logger.warning(f"设备 {device_config.ip} {last_error}")
                
            except Exception as e:
                last_error = f"未知错误: {e}"
                logger.error(f"设备 {device_config.ip} {last_error}")
            
            # 重试前等待
            if attempt < self.max_retries:
                time.sleep(self.retry_delay)
        
        # 所有重试都失败
        device_info.collection_status = "failed"
        device_info.error_message = last_error or "未知错误"
        logger.error(f"设备 {device_config.ip} 收集失败: {device_info.error_message}")
        return device_info
    
    def test_connection(self, device_config: DeviceConfig) -> Tuple[bool, str]:
        """
        测试设备连接
        
        Args:
            device_config: 设备配置
            
        Returns:
            (是否成功, 消息)
        """
        netmiko_type = self._get_netmiko_device_type(device_config.device_type)
        
        device_params = {
            "device_type": netmiko_type,
            "host": device_config.ip,
            "port": device_config.port,
            "username": device_config.credentials.username,
            "password": device_config.credentials.password,
            "timeout": self.timeout,
            "auth_timeout": self.auth_timeout,
        }
        
        if device_config.credentials.secret:
            device_params["secret"] = device_config.credentials.secret
        
        try:
            with ConnectHandler(**device_params) as conn:
                # 简单测试 - 获取提示符
                prompt = conn.find_prompt()
                return True, f"连接成功，设备提示符: {prompt}"
                
        except NetmikoTimeoutException:
            return False, "连接超时"
        except NetmikoAuthenticationException:
            return False, "认证失败"
        except SSHException as e:
            return False, f"SSH错误: {e}"
        except Exception as e:
            return False, f"连接失败: {e}"
