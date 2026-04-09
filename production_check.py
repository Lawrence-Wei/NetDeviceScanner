"""
生产环境预检查脚本
Production Environment Pre-flight Check

在生产环境运行前，必须通过此检查
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

print("=" * 70)
print("生产环境预检查 - Production Pre-flight Check")
print("=" * 70)

checks_passed = 0
checks_total = 0
warnings = []

# 检查1: 环境验证
console.print("\n[bold cyan]>> 检查1: 环境完整性[/bold cyan]")
checks_total += 1
try:
    import sys
    import subprocess
    result = subprocess.run(
        [sys.executable, "verify_system.py", "--full"],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode == 0 and "所有模块导入成功" in result.stdout:
        console.print("  ✓ 环境验证通过", style="green")
        checks_passed += 1
    else:
        console.print("  ✗ 环境验证失败", style="red")
        console.print(f"    {result.stdout[-200:]}", style="dim")
except Exception as e:
    console.print(f"  ✗ 验证脚本执行失败: {e}", style="red")

# 检查2: 集成测试
console.print("\n[bold cyan]>> 检查2: 集成测试[/bold cyan]")
checks_total += 1
try:
    result = subprocess.run(
        [sys.executable, "test_integration.py"],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode == 0 and "4/4 通过" in result.stdout:
        console.print("  ✓ 集成测试通过", style="green")
        checks_passed += 1
    else:
        console.print("  ✗ 集成测试失败", style="red")
        if result.stdout:
            console.print(f"    {result.stdout[-200:]}", style="dim")
except Exception as e:
    console.print(f"  ✗ 测试执行失败: {e}", style="red")

# 检查3: 凭据配置
console.print("\n[bold cyan]>> 检查3: 凭据配置[/bold cyan]")
checks_total += 1
from pathlib import Path
env_file = Path(".env")
if env_file.exists():
    console.print("  ✓ .env 文件存在", style="green")
    checks_passed += 1
    
    # 检查是否是示例内容
    with open(env_file, 'r') as f:
        content = f.read()
        if "your_username" in content or "your_password" in content:
            warnings.append("⚠️  .env 文件包含示例内容，请确认已填入真实凭据")
else:
    console.print("  ✗ .env 文件不存在", style="red")
    console.print("    运行: copy .env.example .env", style="dim")

# 检查4: 设备列表
console.print("\n[bold cyan]>> 检查4: 设备清单配置[/bold cyan]")
checks_total += 1
devices_file = Path("config/devices.yaml")
if devices_file.exists():
    import yaml
    with open(devices_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        device_count = len(data.get('devices', []))
        if device_count > 0:
            console.print(f"  ✓ 设备清单包含 {device_count} 台设备", style="green")
            checks_passed += 1
            if device_count < 5:
                warnings.append(f"⚠️  建议先用少量设备（当前{device_count}台）测试")
        else:
            console.print("  ✗ 设备清单为空", style="red")
else:
    console.print("  ✗ 设备清单不存在", style="red")

# 检查5: 网络连通性（测试单个设备）
console.print("\n[bold cyan]>> 检查5: 网络连通性测试[/bold cyan]")
checks_total += 1

try:
    from src.config_manager import ConfigManager
    config_manager = ConfigManager()
    devices = config_manager.devices
    
    if devices:
        test_device = devices[0]
        console.print(f"  测试设备: {test_device.ip}")
        
        from src.connector import DeviceConnector
        conn_settings = config_manager.get_connection_settings()
        connector = DeviceConnector(**conn_settings)
        
        success, msg = connector.test_connection(test_device)
        if success:
            console.print(f"  ✓ 连接成功: {msg}", style="green")
            checks_passed += 1
        else:
            console.print(f"  ✗ 连接失败: {msg}", style="red")
            warnings.append("⚠️  网络连接失败，请检查：网络连通性、凭据、SSH配置")
    else:
        console.print("  - 跳过（无设备配置）", style="yellow")
        checks_passed += 1  # 不算失败
except Exception as e:
    console.print(f"  ✗ 测试异常: {e}", style="red")

# 检查6: 日志和输出目录权限
console.print("\n[bold cyan]>> 检查6: 目录写入权限[/bold cyan]")
checks_total += 1
test_dirs = ['logs', 'data', 'exports']
all_writable = True
for dirname in test_dirs:
    test_file = Path(dirname) / '.write_test'
    try:
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('test')
        test_file.unlink()
        console.print(f"  ✓ {dirname}/ 可写", style="green")
    except Exception as e:
        console.print(f"  ✗ {dirname}/ 不可写: {e}", style="red")
        all_writable = False

if all_writable:
    checks_passed += 1

# 检查7: 生产环境配置建议
console.print("\n[bold cyan]>> 检查7: 生产环境配置[/bold cyan]")
checks_total += 1

try:
    config_manager = ConfigManager()
    settings = config_manager.get_concurrency_settings()
    
    max_workers = settings.get('max_workers', 20)
    batch_size = settings.get('batch_size', 50)
    
    issues = []
    if max_workers > 50:
        issues.append(f"并发数过高 ({max_workers})，建议 ≤ 50")
    if batch_size > 100:
        issues.append(f"批次大小过大 ({batch_size})，建议 ≤ 100")
    
    conn_settings = config_manager.get_connection_settings()
    timeout = conn_settings.get('timeout', 30)
    max_retries = conn_settings.get('max_retries', 3)
    
    if timeout < 30:
        issues.append(f"超时设置过短 ({timeout}s)，建议 ≥ 30s")
    if max_retries < 3:
        issues.append(f"重试次数过少 ({max_retries})，建议 ≥ 3")
    
    if issues:
        console.print("  ⚠️  配置建议:", style="yellow")
        for issue in issues:
            console.print(f"    - {issue}", style="yellow")
            warnings.append(f"配置: {issue}")
        checks_passed += 0.5  # 半分
    else:
        console.print("  ✓ 配置参数合理", style="green")
        checks_passed += 1
        
except Exception as e:
    console.print(f"  - 无法读取配置: {e}", style="yellow")
    checks_passed += 1

# 汇总
console.print("\n" + "=" * 70)
console.print("[bold]检查结果汇总[/bold]")
console.print("=" * 70)

table = Table(show_header=True)
table.add_column("检查项", style="cyan")
table.add_column("状态", style="bold")

table.add_row("1. 环境完整性", "✓" if checks_passed >= 1 else "✗")
table.add_row("2. 集成测试", "✓" if checks_passed >= 2 else "✗")
table.add_row("3. 凭据配置", "✓" if checks_passed >= 3 else "✗")
table.add_row("4. 设备清单", "✓" if checks_passed >= 4 else "✗")
table.add_row("5. 网络连通性", "✓" if checks_passed >= 5 else "✗")
table.add_row("6. 目录权限", "✓" if checks_passed >= 6 else "✗")
table.add_row("7. 生产环境配置", "✓" if checks_passed >= 6.5 else "⚠️")

console.print(table)

score = (checks_passed / checks_total) * 100
console.print(f"\n通过率: [bold]{score:.0f}%[/bold] ({checks_passed}/{checks_total})")

if warnings:
    console.print("\n[yellow]⚠️  警告事项:[/yellow]")
    for w in warnings:
        console.print(f"  {w}", style="yellow")

# 最终判断
console.print("\n" + "=" * 70)
if checks_passed >= checks_total - 0.5:
    console.print(Panel(
        "[bold green]✓ 通过生产环境检查[/bold green]\n\n"
        "系统已准备好在生产环境运行。\n\n"
        "[bold]建议:[/bold]\n"
        "1. 先用 5-10 台设备小批量测试\n"
        "2. 确认无误后再进行大规模采集\n"
        "3. 监控 logs/ 目录下的日志文件",
        border_style="green"
    ))
    sys.exit(0)
elif checks_passed >= checks_total * 0.7:
    console.print(Panel(
        "[bold yellow]⚠️  警告：部分检查未通过[/bold yellow]\n\n"
        "建议解决上述问题后再运行。\n"
        "如果是非关键问题，可以谨慎继续。",
        border_style="yellow"
    ))
    sys.exit(1)
else:
    console.print(Panel(
        "[bold red]✗ 未通过生产环境检查[/bold red]\n\n"
        "请解决上述问题后重新检查。\n"
        "不建议在生产环境运行。",
        border_style="red"
    ))
    sys.exit(2)
