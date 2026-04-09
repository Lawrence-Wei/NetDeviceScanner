"""
单设备诊断工具
Diagnostic Tool for Single Device

用于诊断特定设备信息采集问题
"""

import sys
import logging
from netmiko import ConnectHandler
from src.config_manager import ConfigManager
from src.parser import OutputParser
from src.models import DeviceInfo
from src.vendor_commands import VENDOR_COMMAND_MAP, get_vendor_from_device_type

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose_device(ip: str):
    """
    诊断单个设备
    
    Args:
        ip: 设备IP地址
    """
    print("=" * 80)
    print(f"诊断设备: {ip}")
    print("=" * 80)
    
    # 加载配置
    config_manager = ConfigManager()
    credentials = config_manager.credentials
    
    print(f"\n📋 步骤1: 连接设备")
    print(f"   用户名: {credentials.username}")
    print(f"   使用Enable: {'是' if credentials.secret else '否'}")
    
    # 连接参数
    device_params = {
        'device_type': 'autodetect',  # 自动检测
        'host': ip,
        'username': credentials.username,
        'password': credentials.password,
        'secret': credentials.secret if credentials.secret else '',
        'timeout': 30,
        'session_timeout': 60,
    }
    
    try:
        # 连接设备
        from netmiko import SSHDetect
        
        print(f"\n🔍 步骤2: 自动检测设备类型...")
        guesser = SSHDetect(**device_params)
        best_match = guesser.autodetect()
        print(f"   ✓ 检测到设备类型: {best_match}")
        
        # 使用检测到的设备类型连接
        device_params['device_type'] = best_match
        conn = ConnectHandler(**device_params)
        
        # Enable 模式
        if credentials.secret and hasattr(conn, 'enable'):
            print(f"\n🔓 步骤3: 进入特权模式...")
            conn.enable()
            print(f"   ✓ 已进入特权模式")
        
        # 获取设备信息
        print(f"\n📡 步骤4: 获取设备基本信息...")
        prompt = conn.find_prompt()
        hostname = prompt.rstrip('#>').strip()
        print(f"   主机名: {hostname}")
        print(f"   提示符: {prompt}")
        
        # 执行命令
        print(f"\n📝 步骤5: 执行采集命令...")
        
        # 根据设备类型获取命令
        vendor = get_vendor_from_device_type(best_match)
        print(f"   厂商: {vendor}")
        
        commands = VENDOR_COMMAND_MAP.get(best_match, VENDOR_COMMAND_MAP.get('cisco_ios', {}))
        print(f"   命令集: {list(commands.keys())}")
        
        raw_output = {}
        
        for cmd_name, cmd in commands.items():
            print(f"\n   执行: {cmd}")
            try:
                output = conn.send_command(cmd, read_timeout=30)
                raw_output[cmd] = output
                
                # 显示输出的关键部分
                lines = output.split('\n')
                print(f"   ✓ 输出行数: {len(lines)}")
                
                # 显示前10行
                print(f"   前10行预览:")
                for i, line in enumerate(lines[:10], 1):
                    print(f"      {i}: {line}")
                
                # 如果是 show version，分析型号信息
                if 'show version' in cmd.lower() or 'display version' in cmd.lower():
                    print(f"\n   🔍 分析 show version 输出:")
                    
                    # 查找可能的型号信息
                    import re
                    model_patterns = [
                        (r'cisco\s+(WS-\S+)', 'Catalyst 交换机格式'),
                        (r'cisco\s+(C\d+\S*)', 'Catalyst 9000系列格式'),
                        (r'cisco\s+(ISR\d+)', 'ISR路由器格式'),
                        (r'cisco\s+(CISCO\d+)', 'CISCO+数字格式'),
                        (r'cisco\s+(\d+\S*)', '纯数字格式(如1921)'),
                        (r'cisco\s+(\S+)\s+\([^)]+\)\s+processor', '通用processor格式'),
                        (r'Model\s+number\s*:\s*(\S+)', 'Model number格式'),
                        (r'Hardware:\s*(\S+)', 'Hardware格式'),
                    ]
                    
                    print(f"      尝试匹配的型号模式:")
                    for pattern, desc in model_patterns:
                        match = re.search(pattern, output, re.IGNORECASE)
                        if match:
                            print(f"      ✓ {desc}: 匹配到 '{match.group(1)}'")
                        else:
                            print(f"      ✗ {desc}: 未匹配")
                    
                    # 查找包含 "cisco" 或 "model" 的行
                    print(f"\n      包含'cisco'的行:")
                    for line in lines:
                        if 'cisco' in line.lower():
                            print(f"         {line}")
                    
                    print(f"\n      包含'model'的行:")
                    for line in lines:
                        if 'model' in line.lower():
                            print(f"         {line}")
                    
                    # 角色判断分析
                    print(f"\n   🎭 分析设备角色:")
                    if 'router' in output.lower():
                        print(f"      ✓ 发现 'router' 关键字 → 应识别为路由器")
                    else:
                        print(f"      ✗ 未发现 'router' 关键字")
                    
                    if 'switch' in output.lower():
                        print(f"      ✓ 发现 'switch' 关键字")
                    else:
                        print(f"      ✗ 未发现 'switch' 关键字")
                
            except Exception as e:
                print(f"   ✗ 执行失败: {e}")
        
        conn.disconnect()
        
        # 解析测试
        print(f"\n" + "=" * 80)
        print(f"📊 步骤6: 测试解析器")
        print("=" * 80)
        
        device_info = DeviceInfo(
            management_ip=ip,
            device_type=best_match,
            raw_output=raw_output,
            collection_status="success"
        )
        
        parser = OutputParser()
        parsed_info = parser.parse_device_info(device_info)
        
        print(f"\n解析结果:")
        print(f"   主机名: {parsed_info.hostname or '(未识别)'}")
        print(f"   型号: {parsed_info.model or '(未识别) ← ⚠️ 问题在这里！'}")
        print(f"   序列号: {parsed_info.serial_number or '(未识别)'}")
        print(f"   系统类型: {parsed_info.os_type or '(未识别)'}")
        print(f"   系统版本: {parsed_info.os_version or '(未识别)'}")
        print(f"   角色: {parsed_info.device_role or '(未识别)'}")
        print(f"   端口数: {parsed_info.total_ports}")
        
        # 保存完整输出到文件
        import json
        from datetime import datetime
        
        output_file = f"diagnostic_{ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"设备诊断报告: {ip}\n")
            f.write(f"时间: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("检测到的设备类型:\n")
            f.write(f"  {best_match}\n\n")
            
            f.write("解析结果:\n")
            f.write(f"  主机名: {parsed_info.hostname}\n")
            f.write(f"  型号: {parsed_info.model}\n")
            f.write(f"  序列号: {parsed_info.serial_number}\n")
            f.write(f"  系统类型: {parsed_info.os_type}\n")
            f.write(f"  系统版本: {parsed_info.os_version}\n")
            f.write(f"  角色: {parsed_info.device_role}\n")
            f.write(f"  端口数: {parsed_info.total_ports}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("完整命令输出:\n")
            f.write("=" * 80 + "\n\n")
            
            for cmd, output in raw_output.items():
                f.write(f"\n{'=' * 80}\n")
                f.write(f"命令: {cmd}\n")
                f.write(f"{'=' * 80}\n")
                f.write(output)
                f.write("\n\n")
        
        print(f"\n✓ 完整输出已保存到: {output_file}")
        print(f"\n💡 分析建议:")
        if not parsed_info.model:
            print(f"   1. 型号未识别 - 可能原因:")
            print(f"      • 设备输出格式不在已知模式中")
            print(f"      • 需要添加新的正则表达式模式")
            print(f"      • 请查看上面的 '包含cisco的行' 找到实际格式")
        
        if parsed_info.device_role != 'router':
            print(f"   2. 角色识别错误 - 可能原因:")
            print(f"      • show version 输出中没有 'router' 关键字")
            print(f"      • 需要改进角色判断逻辑")
        
        print(f"\n📧 如需技术支持，请提供:")
        print(f"   1. 本次诊断的完整输出")
        print(f"   2. 诊断文件: {output_file}")
        
    except Exception as e:
        logger.exception(f"诊断失败")
        print(f"\n✗ 诊断失败: {e}")
        print(f"\n可能的原因:")
        print(f"   1. 网络连接问题")
        print(f"   2. 用户名密码错误")
        print(f"   3. SSH未启用")
        print(f"   4. 防火墙阻止")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python diagnose_device.py <设备IP>")
        print("示例: python diagnose_device.py 192.168.12.14")
        sys.exit(1)
    
    device_ip = sys.argv[1]
    diagnose_device(device_ip)
