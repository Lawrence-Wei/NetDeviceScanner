"""
数据存储模块
负责数据的持久化存储和导出
"""

import os
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .models import DeviceInfo


logger = logging.getLogger(__name__)
Base = declarative_base()


class DeviceRecord(Base):
    """设备记录数据库模型"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    management_ip = Column(String(50), nullable=False, index=True)
    hostname = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), index=True)
    os_version = Column(String(100))
    os_type = Column(String(50))
    uptime = Column(String(200))
    uptime_seconds = Column(Integer)
    total_ports = Column(Integer)
    active_ports = Column(Integer)
    module_count = Column(Integer)
    modules_detail = Column(Text)  # JSON 格式
    device_role = Column(String(50))
    device_type = Column(String(50))
    location = Column(String(200))
    collection_time = Column(DateTime, default=datetime.now)
    collection_status = Column(String(50))
    error_message = Column(Text)
    raw_output = Column(Text)  # JSON 格式


class DataStorage:
    """数据存储管理器"""
    
    def __init__(self, db_path: str = None, export_dir: str = None):
        """
        初始化存储管理器
        
        Args:
            db_path: 数据库文件路径
            export_dir: 导出目录
        """
        base_dir = Path(__file__).parent.parent
        
        self.db_path = db_path or str(base_dir / "data" / "devices.db")
        self.export_dir = Path(export_dir) if export_dir else base_dir / "exports"
        
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_device(self, device_info: DeviceInfo) -> bool:
        """
        保存单个设备信息到数据库
        
        Args:
            device_info: 设备信息对象
            
        Returns:
            是否成功
        """
        try:
            # 检查是否已存在
            existing = self.session.query(DeviceRecord).filter(
                DeviceRecord.management_ip == device_info.management_ip
            ).first()
            
            modules_json = json.dumps([
                {
                    "slot": m.slot,
                    "description": m.description,
                    "model": m.model,
                    "serial_number": m.serial_number
                } for m in device_info.modules
            ], ensure_ascii=False)
            
            raw_output_json = json.dumps(device_info.raw_output, ensure_ascii=False)
            
            if existing:
                # 更新现有记录
                existing.hostname = device_info.hostname
                existing.model = device_info.model
                existing.serial_number = device_info.serial_number
                existing.os_version = device_info.os_version
                existing.os_type = device_info.os_type
                existing.uptime = device_info.uptime
                existing.uptime_seconds = device_info.uptime_seconds
                existing.total_ports = device_info.total_ports
                existing.active_ports = device_info.active_ports
                existing.module_count = len(device_info.modules)
                existing.modules_detail = modules_json
                existing.device_role = device_info.device_role
                existing.device_type = device_info.device_type
                existing.location = device_info.location
                existing.collection_time = device_info.collection_time
                existing.collection_status = device_info.collection_status
                existing.error_message = device_info.error_message
                existing.raw_output = raw_output_json
            else:
                # 创建新记录
                record = DeviceRecord(
                    management_ip=device_info.management_ip,
                    hostname=device_info.hostname,
                    model=device_info.model,
                    serial_number=device_info.serial_number,
                    os_version=device_info.os_version,
                    os_type=device_info.os_type,
                    uptime=device_info.uptime,
                    uptime_seconds=device_info.uptime_seconds,
                    total_ports=device_info.total_ports,
                    active_ports=device_info.active_ports,
                    module_count=len(device_info.modules),
                    modules_detail=modules_json,
                    device_role=device_info.device_role,
                    device_type=device_info.device_type,
                    location=device_info.location,
                    collection_time=device_info.collection_time,
                    collection_status=device_info.collection_status,
                    error_message=device_info.error_message,
                    raw_output=raw_output_json
                )
                self.session.add(record)
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存设备 {device_info.management_ip} 失败: {e}")
            self.session.rollback()
            return False
    
    def save_devices(self, devices: List[DeviceInfo]) -> int:
        """
        批量保存设备信息
        
        Args:
            devices: 设备信息列表
            
        Returns:
            成功保存的数量
        """
        success_count = 0
        for device in devices:
            if self.save_device(device):
                success_count += 1
        return success_count
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """获取所有设备记录"""
        records = self.session.query(DeviceRecord).all()
        return [self._record_to_dict(r) for r in records]
    
    def get_device_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """根据IP获取设备记录"""
        record = self.session.query(DeviceRecord).filter(
            DeviceRecord.management_ip == ip
        ).first()
        return self._record_to_dict(record) if record else None
    
    def search_devices(self, **kwargs) -> List[Dict[str, Any]]:
        """
        搜索设备
        
        Args:
            **kwargs: 搜索条件，如 hostname="xxx", model="xxx"
            
        Returns:
            匹配的设备列表
        """
        query = self.session.query(DeviceRecord)
        
        for key, value in kwargs.items():
            if hasattr(DeviceRecord, key) and value:
                column = getattr(DeviceRecord, key)
                query = query.filter(column.like(f'%{value}%'))
        
        records = query.all()
        return [self._record_to_dict(r) for r in records]
    
    def _record_to_dict(self, record: DeviceRecord) -> Dict[str, Any]:
        """将数据库记录转换为字典"""
        return {
            "id": record.id,
            "management_ip": record.management_ip,
            "hostname": record.hostname,
            "model": record.model,
            "serial_number": record.serial_number,
            "os_version": record.os_version,
            "os_type": record.os_type,
            "uptime": record.uptime,
            "uptime_seconds": record.uptime_seconds,
            "total_ports": record.total_ports,
            "active_ports": record.active_ports,
            "module_count": record.module_count,
            "modules_detail": json.loads(record.modules_detail) if record.modules_detail else [],
            "device_role": record.device_role,
            "device_type": record.device_type,
            "location": record.location,
            "collection_time": record.collection_time.isoformat() if record.collection_time else None,
            "collection_status": record.collection_status,
            "error_message": record.error_message
        }
    
    def delete_device(self, ip: str) -> bool:
        """删除设备记录"""
        try:
            self.session.query(DeviceRecord).filter(
                DeviceRecord.management_ip == ip
            ).delete()
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"删除设备 {ip} 失败: {e}")
            self.session.rollback()
            return False
    
    def clear_all(self) -> bool:
        """清空所有记录"""
        try:
            self.session.query(DeviceRecord).delete()
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            self.session.rollback()
            return False
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()
        self.engine.dispose()  # 释放连接池，确保文件锁释放


class DataExporter:
    """数据导出器"""
    
    def __init__(self, export_dir: str = None):
        """
        初始化导出器
        
        Args:
            export_dir: 导出目录
        """
        base_dir = Path(__file__).parent.parent
        self.export_dir = Path(export_dir) if export_dir else base_dir / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_excel(self, devices: List[DeviceInfo], filename: str = None) -> str:
        """
        导出到 Excel 文件
        
        Args:
            devices: 设备信息列表
            filename: 文件名（不含扩展名）
            
        Returns:
            导出文件的完整路径
        """
        if not filename:
            filename = f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = self.export_dir / f"{filename}.xlsx"
        
        # 转换为扁平化字典列表
        data = [d.to_flat_dict() for d in devices]
        
        # 创建 DataFrame
        df = pd.DataFrame(data)
        
        # 导出到 Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='设备信息', index=False)
            
            # 调整列宽
            worksheet = writer.sheets['设备信息']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        logger.info(f"数据已导出到: {filepath}")
        return str(filepath)
    
    def export_to_csv(self, devices: List[DeviceInfo], filename: str = None) -> str:
        """
        导出到 CSV 文件
        
        Args:
            devices: 设备信息列表
            filename: 文件名（不含扩展名）
            
        Returns:
            导出文件的完整路径
        """
        if not filename:
            filename = f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = self.export_dir / f"{filename}.csv"
        
        # 转换为扁平化字典列表
        data = [d.to_flat_dict() for d in devices]
        
        # 写入 CSV
        if data:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        logger.info(f"数据已导出到: {filepath}")
        return str(filepath)
    
    def export_to_json(self, devices: List[DeviceInfo], filename: str = None) -> str:
        """
        导出到 JSON 文件
        
        Args:
            devices: 设备信息列表
            filename: 文件名（不含扩展名）
            
        Returns:
            导出文件的完整路径
        """
        if not filename:
            filename = f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = self.export_dir / f"{filename}.json"
        
        # 转换为字典列表
        data = [d.to_dict() for d in devices]
        
        # 写入 JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已导出到: {filepath}")
        return str(filepath)
    
    def export(self, devices: List[DeviceInfo], format: str = "excel", filename: str = None) -> str:
        """
        通用导出方法
        
        Args:
            devices: 设备信息列表
            format: 导出格式 (excel, csv, json)
            filename: 文件名（不含扩展名）
            
        Returns:
            导出文件的完整路径
        """
        format_map = {
            "excel": self.export_to_excel,
            "xlsx": self.export_to_excel,
            "csv": self.export_to_csv,
            "json": self.export_to_json
        }
        
        export_func = format_map.get(format.lower())
        if not export_func:
            raise ValueError(f"不支持的导出格式: {format}")
        
        return export_func(devices, filename)
