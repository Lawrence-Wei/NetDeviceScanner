"""
并发采集器模块
支持大规模并发采集设备信息
"""

import logging
import time
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

from .models import DeviceConfig, DeviceInfo
from .connector import DeviceConnector
from .parser import OutputParser, get_parser


logger = logging.getLogger(__name__)
console = Console()


@dataclass
class CollectionResult:
    """采集结果统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    devices: List[DeviceInfo] = None
    
    def __post_init__(self):
        if self.devices is None:
            self.devices = []
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return (self.success / self.total * 100) if self.total > 0 else 0


class DeviceCollector:
    """设备信息采集器"""
    
    def __init__(self,
                 max_workers: int = 20,
                 batch_size: int = 50,
                 batch_delay: int = 2,
                 connection_settings: dict = None):
        """
        初始化采集器
        
        Args:
            max_workers: 最大并发数
            batch_size: 批次大小
            batch_delay: 批次间隔（秒）
            connection_settings: 连接设置
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        
        conn_settings = connection_settings or {}
        self.connector = DeviceConnector(
            timeout=conn_settings.get("timeout", 30),
            auth_timeout=conn_settings.get("auth_timeout", 20),
            read_timeout=conn_settings.get("read_timeout", 60),
            max_retries=conn_settings.get("max_retries", 3),
            retry_delay=conn_settings.get("retry_delay", 5)
        )
    
    def _collect_single_device(self, device_config: DeviceConfig) -> DeviceInfo:
        """
        采集单个设备信息
        
        Args:
            device_config: 设备配置
            
        Returns:
            设备信息
        """
        # 连接并采集原始数据
        device_info = self.connector.connect_and_collect(device_config)
        
        # 解析数据
        if device_info.collection_status == "success":
            parser = get_parser(device_config.device_type)
            device_info = parser.parse_device_info(device_info)
        
        return device_info
    
    def collect_devices(self, 
                       devices: List[DeviceConfig],
                       progress_callback: Callable[[int, int, DeviceInfo], None] = None,
                       show_progress: bool = True) -> CollectionResult:
        """
        批量采集设备信息
        
        Args:
            devices: 设备配置列表
            progress_callback: 进度回调函数 (completed, total, device_info)
            show_progress: 是否显示进度条
            
        Returns:
            采集结果
        """
        result = CollectionResult(total=len(devices))
        
        if not devices:
            return result
        
        # 分批处理
        batches = [
            devices[i:i + self.batch_size] 
            for i in range(0, len(devices), self.batch_size)
        ]
        
        completed_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
            disable=not show_progress
        ) as progress:
            
            task = progress.add_task(
                "[cyan]采集设备信息...", 
                total=len(devices)
            )
            
            for batch_idx, batch in enumerate(batches):
                if batch_idx > 0:
                    # 批次间隔
                    time.sleep(self.batch_delay)
                
                # 并发处理当前批次
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_device = {
                        executor.submit(self._collect_single_device, dev): dev 
                        for dev in batch
                    }
                    
                    for future in as_completed(future_to_device):
                        device_config = future_to_device[future]
                        
                        try:
                            device_info = future.result()
                            result.devices.append(device_info)
                            
                            if device_info.collection_status == "success":
                                result.success += 1
                            else:
                                result.failed += 1
                                
                        except Exception as e:
                            logger.error(f"设备 {device_config.ip} 采集异常: {e}")
                            result.failed += 1
                            
                            # 创建失败的设备信息
                            failed_info = DeviceInfo(
                                management_ip=device_config.ip,
                                device_type=device_config.device_type,
                                device_role=device_config.role,
                                collection_status="failed",
                                error_message=str(e)
                            )
                            result.devices.append(failed_info)
                        
                        completed_count += 1
                        progress.update(task, completed=completed_count)
                        
                        # 调用进度回调
                        if progress_callback:
                            progress_callback(
                                completed_count, 
                                len(devices), 
                                device_info if 'device_info' in dir() else None
                            )
        
        return result
    
    def collect_single(self, device_config: DeviceConfig) -> DeviceInfo:
        """
        采集单个设备（便捷方法）
        
        Args:
            device_config: 设备配置
            
        Returns:
            设备信息
        """
        return self._collect_single_device(device_config)
    
    def test_connectivity(self, 
                         devices: List[DeviceConfig],
                         show_progress: bool = True) -> dict:
        """
        测试设备连接性
        
        Args:
            devices: 设备配置列表
            show_progress: 是否显示进度条
            
        Returns:
            {ip: (is_reachable, message)}
        """
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            disable=not show_progress
        ) as progress:
            
            task = progress.add_task(
                "[cyan]测试连接...", 
                total=len(devices)
            )
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_device = {
                    executor.submit(self.connector.test_connection, dev): dev 
                    for dev in devices
                }
                
                for future in as_completed(future_to_device):
                    device = future_to_device[future]
                    try:
                        success, message = future.result()
                        results[device.ip] = (success, message)
                    except Exception as e:
                        results[device.ip] = (False, str(e))
                    
                    progress.advance(task)
        
        return results
