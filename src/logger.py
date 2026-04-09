"""
日志配置模块
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from rich.logging import RichHandler
from rich.console import Console


def setup_logging(
    level: str = "INFO",
    log_dir: str = None,
    log_format: str = None,
    max_size: int = 10,
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        level: 日志级别
        log_dir: 日志目录
        log_format: 日志格式
        max_size: 单个日志文件最大大小（MB）
        backup_count: 保留的日志文件数量
        
    Returns:
        根日志记录器
    """
    # 日志目录
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    else:
        log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器（使用 Rich）
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=False,
        rich_tracebacks=True
    )
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = log_dir / f"collector_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("netmiko").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取命名日志记录器"""
    return logging.getLogger(name)
