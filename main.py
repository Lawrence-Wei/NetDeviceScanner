#!/usr/bin/env python3
"""
思科网络设备信息收集系统 - 命令行接口
Cisco Network Device Hardware Information Retriever - CLI

支持功能：
- 批量收集设备信息（hostname, 型号, 序列号, IOS版本, 端口数, uptime等）
- 支持 IOS / NX-OS / IOS-XE 设备
- 多种数据源（YAML配置、CSV文件、文本文件）
- 并发采集（支持400-500台设备）
- 数据导出（Excel/CSV/JSON）
- 数据库存储（SQLite）
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.collector import DeviceCollector, CollectionResult
from src.storage import DataStorage, DataExporter
from src.logger import setup_logging, get_logger
from src.models import DeviceConfig, DeviceCredentials


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="思科网络设备信息收集系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置文件采集
  python main.py collect
  
  # 从CSV文件导入设备列表并采集
  python main.py collect --source devices.csv
  
  # 从文本文件导入IP列表并采集
  python main.py collect --source ips.txt --type txt
  
  # 测试设备连接
  python main.py test
  
  # 导出数据库中的数据
  python main.py export --format excel
  
  # 查询设备信息
  python main.py query --ip 192.168.1.1
  python main.py query --model C9300
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='配置目录路径',
        default=None
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # collect 命令
    collect_parser = subparsers.add_parser('collect', help='采集设备信息')
    collect_parser.add_argument(
        '--source', '-s',
        help='设备列表文件路径（CSV/TXT）',
        default=None
    )
    collect_parser.add_argument(
        '--type', '-t',
        choices=['yaml', 'csv', 'txt'],
        help='设备列表文件类型',
        default='yaml'
    )
    collect_parser.add_argument(
        '--workers', '-w',
        type=int,
        help='并发数（默认: 20）',
        default=20
    )
    collect_parser.add_argument(
        '--batch-size', '-b',
        type=int,
        help='批次大小（默认: 50）',
        default=50
    )
    collect_parser.add_argument(
        '--export', '-e',
        choices=['excel', 'csv', 'json', 'none'],
        help='采集后自动导出格式',
        default='excel'
    )
    collect_parser.add_argument(
        '--output', '-o',
        help='导出文件名（不含扩展名）',
        default=None
    )
    collect_parser.add_argument(
        '--username', '-u',
        help='SSH用户名（覆盖配置）',
        default=None
    )
    collect_parser.add_argument(
        '--password', '-p',
        help='SSH密码（覆盖配置）',
        default=None
    )
    collect_parser.add_argument(
        '--group', '-g',
        help='采集指定设备组',
        default=None
    )
    
    # scan 命令 - 自动发现设备
    scan_parser = subparsers.add_parser('scan', help='自动扫描和发现网络设备')
    scan_parser.add_argument(
        '--network', '-n',
        action='append',
        help='IP网段（可多次使用），如: 192.168.1.0/24',
        default=None
    )
    scan_parser.add_argument(
        '--network-file', '-nf',
        help='从文件读取网段列表（每行一个网段）',
        default=None
    )
    scan_parser.add_argument(
        '--username', '-u',
        help='SSH用户名',
        default=None
    )
    scan_parser.add_argument(
        '--password', '-p',
        help='SSH密码',
        default=None
    )
    scan_parser.add_argument(
        '--secret',
        help='Enable密码',
        default=None
    )
    scan_parser.add_argument(
        '--scan-workers',
        type=int,
        help='扫描并发数（默认: 50）',
        default=50
    )
    scan_parser.add_argument(
        '--timeout',
        type=int,
        help='扫描超时（秒，默认: 5）',
        default=5
    )
    scan_parser.add_argument(
        '--save',
        help='保存发现的设备到YAML文件',
        default=None
    )
    scan_parser.add_argument(
        '--collect',
        action='store_true',
        help='扫描后立即采集信息'
    )
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='测试设备连接')
    test_parser.add_argument(
        '--source', '-s',
        help='设备列表文件路径',
        default=None
    )
    test_parser.add_argument(
        '--type', '-t',
        choices=['yaml', 'csv', 'txt'],
        default='yaml'
    )
    test_parser.add_argument(
        '--ip',
        help='测试单个IP',
        default=None
    )
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument(
        '--format', '-f',
        choices=['excel', 'csv', 'json'],
        help='导出格式',
        default='excel'
    )
    export_parser.add_argument(
        '--output', '-o',
        help='导出文件名（不含扩展名）',
        default=None
    )
    export_parser.add_argument(
        '--filter',
        help='过滤条件 (JSON格式)',
        default=None
    )
    
    # query 命令
    query_parser = subparsers.add_parser('query', help='查询设备信息')
    query_parser.add_argument(
        '--ip',
        help='按IP查询',
        default=None
    )
    query_parser.add_argument(
        '--hostname',
        help='按主机名查询',
        default=None
    )
    query_parser.add_argument(
        '--model',
        help='按型号查询',
        default=None
    )
    query_parser.add_argument(
        '--serial',
        help='按序列号查询',
        default=None
    )
    query_parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='显示所有设备'
    )
    
    # clear 命令
    clear_parser = subparsers.add_parser('clear', help='清空数据库')
    clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='确认清空'
    )
    
    return parser


def load_devices(config_manager: ConfigManager, args) -> list:
    """根据参数加载设备列表"""
    if args.source:
        source_path = Path(args.source)
        if not source_path.exists():
            console.print(f"[red]错误: 文件不存在 - {args.source}[/red]")
            sys.exit(1)
        
        source_type = args.type
        if source_type == 'csv':
            devices = config_manager.load_devices_from_csv(str(source_path))
        elif source_type == 'txt':
            devices = config_manager.load_devices_from_text(str(source_path))
        else:
            # 重新加载 YAML
            devices = config_manager.devices
    elif hasattr(args, 'group') and args.group:
        devices = config_manager.get_devices_by_group(args.group)
    else:
        devices = config_manager.devices
    
    # 覆盖凭据
    if hasattr(args, 'username') and args.username:
        creds = DeviceCredentials(
            username=args.username,
            password=args.password or "",
            secret=os.getenv("CISCO_SECRET", "")
        )
        for dev in devices:
            dev.credentials = creds
    
    return devices


def cmd_collect(args, config_manager: ConfigManager, logger):
    """执行采集命令"""
    # 加载设备列表
    devices = load_devices(config_manager, args)
    
    if not devices:
        console.print("[yellow]警告: 没有找到要采集的设备[/yellow]")
        console.print("请检查配置文件 config/devices.yaml 或使用 --source 指定设备列表")
        return
    
    console.print(Panel(
        f"[bold cyan]设备信息采集[/bold cyan]\n\n"
        f"设备数量: [green]{len(devices)}[/green]\n"
        f"并发数: [green]{args.workers}[/green]\n"
        f"批次大小: [green]{args.batch_size}[/green]",
        title="任务信息"
    ))
    
    # 创建采集器
    conn_settings = config_manager.get_connection_settings()
    collector = DeviceCollector(
        max_workers=args.workers,
        batch_size=args.batch_size,
        batch_delay=config_manager.get_concurrency_settings().get('batch_delay', 2),
        connection_settings=conn_settings
    )
    
    # 开始采集
    start_time = datetime.now()
    result = collector.collect_devices(devices)
    end_time = datetime.now()
    
    # 显示结果统计
    duration = (end_time - start_time).total_seconds()
    
    console.print("\n")
    console.print(Panel(
        f"[bold]采集完成[/bold]\n\n"
        f"总数: {result.total}\n"
        f"成功: [green]{result.success}[/green]\n"
        f"失败: [red]{result.failed}[/red]\n"
        f"成功率: [cyan]{result.success_rate:.1f}%[/cyan]\n"
        f"耗时: [yellow]{duration:.1f}秒[/yellow]",
        title="结果统计"
    ))
    
    # 保存到数据库
    storage = DataStorage(
        db_path=config_manager.get_storage_settings().get('sqlite_path')
    )
    saved_count = storage.save_devices(result.devices)
    logger.info(f"已保存 {saved_count} 条记录到数据库")
    storage.close()
    
    # 导出
    if args.export and args.export != 'none':
        exporter = DataExporter(
            export_dir=config_manager.get_storage_settings().get('export_dir')
        )
        filepath = exporter.export(
            result.devices,
            format=args.export,
            filename=args.output
        )
        console.print(f"\n[green]数据已导出到: {filepath}[/green]")
    
    # 显示失败的设备
    failed_devices = [d for d in result.devices if d.collection_status == "failed"]
    if failed_devices:
        console.print("\n[yellow]失败的设备:[/yellow]")
        table = Table(show_header=True)
        table.add_column("IP", style="cyan")
        table.add_column("错误信息", style="red")
        
        for dev in failed_devices[:20]:  # 最多显示20条
            table.add_row(dev.management_ip, dev.error_message[:50])
        
        console.print(table)
        
        if len(failed_devices) > 20:
            console.print(f"... 还有 {len(failed_devices) - 20} 台设备失败")


def cmd_test(args, config_manager: ConfigManager, logger):
    """执行连接测试命令"""
    devices = load_devices(config_manager, args)
    
    # 如果指定了单个IP
    if args.ip:
        from src.models import DeviceCredentials
        default_creds = config_manager._get_default_credentials()
        devices = [DeviceConfig(
            ip=args.ip,
            device_type="ios",
            credentials=default_creds
        )]
    
    if not devices:
        console.print("[yellow]警告: 没有找到要测试的设备[/yellow]")
        return
    
    console.print(f"[cyan]测试 {len(devices)} 台设备的连接...[/cyan]\n")
    
    collector = DeviceCollector(
        max_workers=min(len(devices), 20),
        connection_settings=config_manager.get_connection_settings()
    )
    
    results = collector.test_connectivity(devices)
    
    # 显示结果
    table = Table(show_header=True, title="连接测试结果")
    table.add_column("IP", style="cyan")
    table.add_column("状态")
    table.add_column("消息")
    
    success_count = 0
    for ip, (success, message) in sorted(results.items()):
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        if success:
            success_count += 1
        table.add_row(ip, status, message[:50])
    
    console.print(table)
    console.print(f"\n成功: {success_count}/{len(results)}")


def cmd_export(args, config_manager: ConfigManager, logger):
    """执行导出命令"""
    storage = DataStorage(
        db_path=config_manager.get_storage_settings().get('sqlite_path')
    )
    
    # 获取数据
    if args.filter:
        import json
        filter_dict = json.loads(args.filter)
        records = storage.search_devices(**filter_dict)
    else:
        records = storage.get_all_devices()
    
    storage.close()
    
    if not records:
        console.print("[yellow]数据库中没有数据[/yellow]")
        return
    
    # 转换为 DeviceInfo 对象
    from src.models import DeviceInfo, ModuleInfo
    devices = []
    for r in records:
        dev = DeviceInfo(
            management_ip=r['management_ip'],
            hostname=r['hostname'],
            model=r['model'],
            serial_number=r['serial_number'],
            os_version=r['os_version'],
            os_type=r['os_type'],
            uptime=r['uptime'],
            uptime_seconds=r.get('uptime_seconds', 0),
            total_ports=r.get('total_ports', 0),
            active_ports=r.get('active_ports', 0),
            device_role=r['device_role'],
            device_type=r['device_type'],
            location=r.get('location', ''),
            collection_status=r['collection_status']
        )
        
        # 添加模块
        for m in r.get('modules_detail', []):
            dev.modules.append(ModuleInfo(
                slot=m.get('slot', ''),
                description=m.get('description', ''),
                model=m.get('model', ''),
                serial_number=m.get('serial_number', '')
            ))
        
        devices.append(dev)
    
    # 导出
    exporter = DataExporter(
        export_dir=config_manager.get_storage_settings().get('export_dir')
    )
    filepath = exporter.export(
        devices,
        format=args.format,
        filename=args.output
    )
    
    console.print(f"[green]数据已导出到: {filepath}[/green]")
    console.print(f"共 {len(devices)} 条记录")


def cmd_query(args, config_manager: ConfigManager, logger):
    """执行查询命令"""
    storage = DataStorage(
        db_path=config_manager.get_storage_settings().get('sqlite_path')
    )
    
    if args.ip:
        records = [storage.get_device_by_ip(args.ip)]
        records = [r for r in records if r]
    elif args.all:
        records = storage.get_all_devices()
    else:
        search_params = {}
        if args.hostname:
            search_params['hostname'] = args.hostname
        if args.model:
            search_params['model'] = args.model
        if args.serial:
            search_params['serial_number'] = args.serial
        
        if search_params:
            records = storage.search_devices(**search_params)
        else:
            console.print("[yellow]请指定查询条件，或使用 --all 显示所有设备[/yellow]")
            storage.close()
            return
    
    storage.close()
    
    if not records:
        console.print("[yellow]没有找到匹配的设备[/yellow]")
        return
    
    # 显示结果
    table = Table(show_header=True, title=f"查询结果 ({len(records)} 条)")
    table.add_column("IP", style="cyan")
    table.add_column("主机名")
    table.add_column("型号")
    table.add_column("序列号")
    table.add_column("系统版本")
    table.add_column("Uptime")
    table.add_column("端口数")
    table.add_column("角色")
    table.add_column("状态")
    
    for r in records:
        status_style = "green" if r['collection_status'] == 'success' else "red"
        table.add_row(
            r['management_ip'],
            r['hostname'] or '-',
            r['model'] or '-',
            r['serial_number'] or '-',
            (r['os_version'] or '-')[:20],
            (r['uptime'] or '-')[:30],
            str(r.get('total_ports', '-')),
            r['device_role'] or '-',
            f"[{status_style}]{r['collection_status']}[/{status_style}]"
        )
    
    console.print(table)


def cmd_scan(args, config_manager: ConfigManager, logger):
    """执行网络扫描和设备发现"""
    from src.scanner import NetworkScanner
    from src.models import DeviceCredentials
    
    # 确定网段来源
    networks = []
    if args.network:
        networks.extend(args.network)
    
    if args.network_file:
        file_networks = NetworkScanner.load_networks_from_file(args.network_file)
        networks.extend(file_networks)
    
    if not networks:
        console.print("[red]错误: 需要指定网段（--network 或 --network-file）[/red]")
        console.print("示例:")
        console.print("  python main.py scan --network 192.168.1.0/24")
        console.print("  python main.py scan --network-file networks.txt")
        return
    
    console.print(Panel(
        f"[bold cyan]网络设备自动发现[/bold cyan]\n\n"
        f"扫描网段: [green]{len(networks)} 个网段[/green]\n"
        f"网段列表: [green]{', '.join(networks[:5])}{'...' if len(networks) > 5 else ''}[/green]\n"
        f"扫描并发: [green]{args.scan_workers}[/green]",
        title="扫描任务"
    ))
    
    # 获取凭据
    username = args.username or os.getenv("CISCO_USERNAME", "") or os.getenv("DEVICE_USERNAME", "")
    password = args.password or os.getenv("CISCO_PASSWORD", "") or os.getenv("DEVICE_PASSWORD", "")
    secret = args.secret or os.getenv("CISCO_SECRET", "") or os.getenv("DEVICE_SECRET", "")
    
    if not username or not password:
        console.print("[red]错误: 需要提供SSH凭据[/red]")
        console.print("方法1: 使用 --username 和 --password 参数")
        console.print("方法2: 在 .env 文件中配置 DEVICE_USERNAME 和 DEVICE_PASSWORD")
        return
    
    credentials = DeviceCredentials(
        username=username,
        password=password,
        secret=secret
    )
    
    # 创建扫描器
    scanner = NetworkScanner(
        credentials=credentials,
        ssh_port=22,
        timeout=args.timeout,
        max_workers=args.scan_workers
    )
    
    # 扫描和识别
    console.print("\n[cyan]正在扫描网络...[/cyan]")
    devices = scanner.scan_and_identify(networks)
    
    if not devices:
        console.print("\n[yellow]未发现任何网络设备[/yellow]")
        return
    
    # 统计厂商信息
    from src.vendor_commands import get_vendor_from_device_type, VENDOR_FRIENDLY_NAMES
    vendor_counts = {}
    for dev in devices:
        vendor = get_vendor_from_device_type(dev.device_type)
        vendor_name = VENDOR_FRIENDLY_NAMES.get(vendor, vendor.upper())
        vendor_counts[vendor_name] = vendor_counts.get(vendor_name, 0) + 1
    
    vendor_summary = ", ".join([f"{v}: {c}" for v, c in vendor_counts.items()])
    
    # 显示结果
    console.print(f"\n[green]✓ 发现 {len(devices)} 台网络设备[/green]")
    console.print(f"[cyan]厂商分布: {vendor_summary}[/cyan]\n")
    
    table = Table(show_header=True, title="发现的设备")
    table.add_column("IP", style="cyan")
    table.add_column("Hostname")
    table.add_column("类型")
    table.add_column("角色")
    table.add_column("厂商")
    
    for dev in devices:
        vendor = get_vendor_from_device_type(dev.device_type)
        vendor_name = VENDOR_FRIENDLY_NAMES.get(vendor, vendor.upper())
        table.add_row(
            dev.ip,
            dev.hostname or "未知",
            dev.device_type.upper(),
            dev.role,
            vendor_name
        )
    
    console.print(table)
    
    # 保存到文件
    if args.save:
        import yaml
        output = {
            'devices': [
                {
                    'ip': d.ip,
                    'hostname': d.hostname,
                    'device_type': d.device_type,
                    'role': d.role,
                }
                for d in devices
            ]
        }
        
        with open(args.save, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, allow_unicode=True, default_flow_style=False)
        
        console.print(f"\n[green]设备列表已保存到: {args.save}[/green]")
    
    # 立即采集
    if args.collect:
        console.print("\n[cyan]开始采集设备信息...[/cyan]\n")
        
        from src.collector import DeviceCollector
        from src.storage import DataStorage, DataExporter
        
        collector = DeviceCollector(
            max_workers=20,
            batch_size=50,
            connection_settings=config_manager.get_connection_settings()
        )
        
        result = collector.collect_devices(devices)
        
        # 保存结果
        storage = DataStorage(
            db_path=config_manager.get_storage_settings().get('sqlite_path')
        )
        storage.save_devices(result.devices)
        storage.close()
        
        # 导出
        exporter = DataExporter(
            export_dir=config_manager.get_storage_settings().get('export_dir')
        )
        filepath = exporter.export_to_excel(result.devices, "auto_discovered")
        
        console.print(f"\n[green]采集完成，数据已导出到: {filepath}[/green]")


def cmd_clear(args, config_manager: ConfigManager, logger):
    """执行清空命令"""
    if not args.confirm:
        console.print("[yellow]警告: 此操作将清空所有数据！[/yellow]")
        console.print("请使用 --confirm 参数确认操作")
        return
    
    storage = DataStorage(
        db_path=config_manager.get_storage_settings().get('sqlite_path')
    )
    
    if storage.clear_all():
        console.print("[green]数据库已清空[/green]")
    else:
        console.print("[red]清空失败[/red]")
    
    storage.close()


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 初始化配置
    config_manager = ConfigManager(args.config)
    
    # 设置日志
    log_settings = config_manager.get_logging_settings()
    log_level = "DEBUG" if args.verbose else log_settings.get('level', 'INFO')
    setup_logging(
        level=log_level,
        log_dir=config_manager.get_storage_settings().get('log_dir'),
        max_size=log_settings.get('max_size', 10),
        backup_count=log_settings.get('backup_count', 5)
    )
    logger = get_logger(__name__)
    
    # 显示标题
    console.print(Panel(
        "[bold cyan]思科网络设备信息收集系统[/bold cyan]\n"
        "[dim]Cisco Network Device Hardware Information Retriever[/dim]",
        border_style="cyan"
    ))
    
    # 执行命令
    commands = {
        'scan': cmd_scan,
        'collect': cmd_collect,
        'test': cmd_test,
        'export': cmd_export,
        'query': cmd_query,
        'clear': cmd_clear
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        try:
            cmd_func(args, config_manager, logger)
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)
        except Exception as e:
            logger.exception("执行命令时发生错误")
            console.print(f"[red]错误: {e}[/red]")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
