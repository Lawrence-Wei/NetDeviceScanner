# 设备信息采集问题排查指南

## 问题描述

在批量采集中，某个特定设备（如 192.168.12.14）的信息不完整：
- ❌ 型号缺失（应该是 Cisco 1921）
- ❌ 角色识别错误（应该是路由器，但识别为其他）
- ✅ 其他设备信息正常

## 可能的原因

### 1. 设备输出格式不在已知模式中 ⭐ 最可能

**原因**：不同型号的 Cisco 设备，`show version` 输出格式可能不同。

#### Cisco 1921 的特殊性

Cisco 1921 是 ISR G2（第二代集成服务路由器），其 `show version` 输出格式可能与交换机不同：

**典型的 1921 输出格式**：
```
Cisco IOS Software, C1900 Software (C1900-UNIVERSALK9-M), Version 15.1(4)M4
...
cisco CISCO1921/K9 (revision 1.0) with 479232K/45056K bytes of memory.
Processor board ID FTX1234A5B6
...
```

**当前解析器的型号匹配模式**：
```python
model_patterns = [
    r'cisco\s+(WS-\S+)',        # ✅ Catalyst 交换机 (WS-C2960X-48FPD-L)
    r'cisco\s+(C\d+\S*)',       # ✅ Catalyst 9000系列 (C9300-24P)
    r'cisco\s+Nexus\s*(\S+)',   # ✅ Nexus (N9K-C93180YC-EX)
    r'cisco\s+(N\d+\S*)',       # ✅ Nexus简写 (N9K)
    r'cisco\s+(ISR\S*)',        # ✅ ISR路由器 (ISR4451)
    r'cisco\s+(ASR\S*)',        # ✅ ASR路由器 (ASR1001)
    r'cisco\s+(\S+)\s+\([^)]+\)\s+processor',  # ⚠️ 通用格式
    r'Model\s+number\s*:\s*(\S+)',  # ✅ NX-OS格式
    r'Hardware:\s*(\S+)',       # ✅ 某些版本
]
```

**问题**：`cisco CISCO1921/K9` 不匹配上述任何模式！

- ❌ `C\d+\S*` 模式期望 `C` 后面紧跟数字，但实际是 `CISCO1921`
- ⚠️ `\S+\s+\([^)]+\)\s+processor` 可能匹配到 `CISCO1921/K9 (revision 1.0)`，但提取的是整个字符串

### 2. 角色判断逻辑过于简单

**当前的角色判断代码**（在 scanner.py）：
```python
role = 'switch'  # 默认值
if 'router' in output.lower():
    role = 'router'
elif 'nexus' in output.lower() or 'catalyst' in output.lower():
    if 'l3' in output.lower() or 'layer 3' in output.lower():
        role = 'L3 switch'
    else:
        role = 'switch'
```

**问题**：
- Cisco 1921 的 `show version` 可能**不包含** `'router'` 这个关键字
- 默认值是 `'switch'`，所以会错误识别为交换机

### 3. 网络超时或连接不稳定

**可能性较小**（因为其他设备正常），但如果该设备：
- 网络延迟高
- CPU 负载重
- 老旧硬件响应慢

可能导致命令输出不完整。

### 4. SSH 配置差异

某些老旧设备的 SSH 配置可能不同：
- SSH v1 vs SSH v2
- 加密算法不支持
- 输出缓冲区设置

## 排查步骤

### 步骤1：使用诊断工具

```bash
# 运行单设备诊断
python diagnose_device.py 192.168.12.14
```

**诊断工具会**：
1. ✅ 连接设备并自动检测类型
2. ✅ 执行所有采集命令
3. ✅ 显示命令输出的关键部分
4. ✅ 测试所有型号匹配模式
5. ✅ 保存完整输出到文件（diagnostic_*.txt）
6. ✅ 提供详细的分析建议

**输出示例**：
```
================================================================================
诊断设备: 192.168.12.14
================================================================================

📋 步骤1: 连接设备
   用户名: admin
   使用Enable: 是

🔍 步骤2: 自动检测设备类型...
   ✓ 检测到设备类型: cisco_ios

🔓 步骤3: 进入特权模式...
   ✓ 已进入特权模式

📡 步骤4: 获取设备基本信息...
   主机名: ROUTER-1921
   提示符: ROUTER-1921#

📝 步骤5: 执行采集命令...
   厂商: cisco
   命令集: ['show version', 'show inventory', 'show interface status', ...]

   执行: show version
   ✓ 输出行数: 45
   前10行预览:
      1: Cisco IOS Software, C1900 Software (C1900-UNIVERSALK9-M), Version 15.1(4)M4
      2: Technical Support: http://www.cisco.com/techsupport
      3: Copyright (c) 1986-2012 by Cisco Systems, Inc.
      4: Compiled Tue 20-Mar-12 19:52 by prod_rel_team
      5:
      6: ROM: System Bootstrap, Version 15.0(1r)M15, RELEASE SOFTWARE (fc1)
      7:
      8: ROUTER-1921 uptime is 45 days, 12 hours, 30 minutes
      9: System returned to ROM by power-on
      10: System image file is "flash:c1900-universalk9-mz.SPA.151-4.M4.bin"

   🔍 分析 show version 输出:
      尝试匹配的型号模式:
      ✗ Catalyst 交换机格式: 未匹配
      ✗ Catalyst 9000系列格式: 未匹配
      ✗ ISR路由器格式: 未匹配
      ✗ CISCO+数字格式: 未匹配
      ✗ 纯数字格式(如1921): 未匹配
      ✓ 通用processor格式: 匹配到 'CISCO1921/K9'  ← 找到了！

      包含'cisco'的行:
         cisco CISCO1921/K9 (revision 1.0) with 479232K/45056K bytes of memory.

      包含'model'的行:
         (无)

   🎭 分析设备角色:
      ✗ 未发现 'router' 关键字  ← 问题原因！
      ✗ 未发现 'switch' 关键字
```

### 步骤2：检查诊断文件

诊断工具会生成文件：`diagnostic_192.168.12.14_YYYYMMDD_HHMMSS.txt`

**重点检查**：
1. `show version` 的完整输出
2. 找到包含型号信息的那一行
3. 检查是否有 "router" 关键字

### 步骤3：手动连接测试

如果诊断工具也失败，手动测试：

```bash
# Windows
ssh admin@192.168.12.14

# 登录后
enable
show version
show inventory
show interface status
```

保存输出，检查：
- 型号信息在哪一行？
- 格式是什么？

## 解决方案

根据诊断结果选择对应的解决方案：

### 解决方案1：添加 Cisco 1921 型号模式 ⭐ 推荐

如果诊断发现型号格式是 `cisco CISCO1921/K9`，需要添加新的匹配模式。

**修改文件**：`src/parser.py`

**在第 181-196 行左右，找到型号模式列表，添加新模式**：

```python
# 解析型号
model_patterns = [
    r'cisco\s+(WS-\S+)',  # Catalyst 交换机
    r'cisco\s+(C\d+\S*)',  # Catalyst 9000 系列
    r'cisco\s+(CISCO\d+/?\S*)',  # ← 添加这一行！支持 CISCO1921/K9 格式
    r'cisco\s+(\d{4}/?\S*)',  # ← 添加这一行！支持纯数字格式 1921, 2811, 2901等
    r'cisco\s+Nexus\s*(\S+)',  # Nexus
    r'cisco\s+(N\d+\S*)',  # Nexus 简写
    r'cisco\s+(ISR\S*)',  # ISR 路由器
    r'cisco\s+(ASR\S*)',  # ASR 路由器
    r'cisco\s+(\S+)\s+\([^)]+\)\s+processor',  # 通用
    r'Model\s+number\s*:\s*(\S+)',  # NX-OS
    r'Hardware:\s*(\S+)',  # 某些版本
]
```

### 解决方案2：改进角色判断逻辑

如果设备输出中没有 'router' 关键字，改进判断逻辑。

**修改文件**：`src/scanner.py`

**在第 290-297 行左右，改进角色判断**：

```python
# 简单判断角色
output = conn.send_command('show version', read_timeout=10)

role = 'switch'  # 默认
if 'router' in output.lower():
    role = 'router'
# ← 添加基于型号的判断
elif any(model in output.upper() for model in ['CISCO1921', 'CISCO2911', 'CISCO2901', 'ISR', 'ASR']):
    role = 'router'
elif any(model in output.upper() for model in ['2811', '2821', '2851', '1841', '1921', '2901', '2911', '3925', '3945']):
    role = 'router'
elif 'nexus' in output.lower() or 'catalyst' in output.lower():
    if 'l3' in output.lower() or 'layer 3' in output.lower():
        role = 'L3 switch'
    else:
        role = 'switch'
```

### 解决方案3：使用更健壮的角色判断

**添加基于接口类型的判断**：

```python
# 更智能的角色判断
output = conn.send_command('show version', read_timeout=10)

role = 'switch'  # 默认

# 1. 关键字判断
if 'router' in output.lower():
    role = 'router'
# 2. 型号判断
elif any(keyword in output.upper() for keyword in [
    'CISCO1921', 'CISCO2911', 'CISCO2901', 'CISCO3925', 'CISCO3945',
    'ISR', 'ASR', '1841', '2811', '2821', '2851', '1921', '2901', '2911'
]):
    role = 'router'
# 3. 接口判断（可选，需要额外命令）
else:
    try:
        int_output = conn.send_command('show ip interface brief', read_timeout=10)
        # 如果有 Serial, GigabitEthernet0/0, GigabitEthernet0/1（而不是很多端口），可能是路由器
        if 'Serial' in int_output or int_output.count('GigabitEthernet') < 10:
            role = 'router'
    except:
        pass

# 4. Nexus/Catalyst 判断
if 'nexus' in output.lower() or 'catalyst' in output.lower():
    if 'l3' in output.lower() or 'layer 3' in output.lower():
        role = 'L3 switch'
    else:
        role = 'switch'
```

### 解决方案4：增加超时时间

如果是老旧设备响应慢：

**修改文件**：`config/settings.yaml`

```yaml
connection:
  timeout: 60        # 从 30 增加到 60
  session_timeout: 120  # 从 60 增加到 120
```

## 快速修复步骤

### 最快的解决方案（5分钟）

1. **打开** `src/parser.py`

2. **找到第 181 行**左右的 `model_patterns` 列表

3. **在第 3 行位置添加**：
   ```python
   r'cisco\s+(CISCO\d+/?\S*)',  # CISCO1921/K9 等格式
   r'cisco\s+(\d{4}/?\S*)',     # 1921, 2911 等纯数字格式
   ```

4. **打开** `src/scanner.py`

5. **找到第 291 行**左右的角色判断代码

6. **在 `if 'router'` 后面添加**：
   ```python
   elif any(m in output.upper() for m in ['1921', '2911', '2901', 'ISR', 'ASR']):
       role = 'router'
   ```

7. **重新运行采集**：
   ```bash
   python main.py scan --network 192.168.12.0/28 --collect
   ```

## 验证修复

修复后，再次运行诊断：

```bash
python diagnose_device.py 192.168.12.14
```

**期望结果**：
```
解析结果:
   主机名: ROUTER-1921
   型号: CISCO1921/K9  ← ✓ 正确识别
   序列号: FTX1234A5B6
   系统类型: IOS
   系统版本: 15.1(4)M4
   角色: router  ← ✓ 正确识别
   端口数: 2
```

## 预防措施

为了避免类似问题：

### 1. 使用诊断工具测试新设备

在加入大批量采集前，先用诊断工具测试：

```bash
python diagnose_device.py <新设备IP>
```

### 2. 保留原始日志

启用详细日志：

```yaml
# config/settings.yaml
logging:
  level: DEBUG  # 开发/测试时使用 DEBUG
  file: logs/collection.log
```

### 3. 分批采集

对于多型号混合环境：

```bash
# 先测试几台
python main.py scan --network 192.168.12.0/28 --collect

# 检查 exports/auto_discovered.xlsx

# 确认无问题后再大批量采集
python main.py scan --network-file networks.txt --collect
```

## 技术支持

如果问题仍未解决，请提供：

1. ✅ 诊断工具输出（完整的终端输出）
2. ✅ 诊断文件（diagnostic_*.txt）
3. ✅ 设备型号和IOS版本
4. ✅ 从该设备手动执行 `show version` 的输出

## 常见 Cisco 路由器型号模式

供参考，已知的 Cisco 路由器型号输出格式：

| 系列 | 典型输出 | 当前是否支持 |
|------|---------|------------|
| ISR 4000 | `cisco ISR4451/K9` | ✅ 支持 (ISR) |
| ISR G2 | `cisco CISCO1921/K9` | ❌ 需要添加 |
| ISR G2 | `cisco CISCO2911/K9` | ❌ 需要添加 |
| ISR G1 | `cisco 2811` | ❌ 需要添加 |
| ASR | `cisco ASR1001-X` | ✅ 支持 (ASR) |
| 老型号 | `cisco 1841` | ❌ 需要添加 |

## 总结

**最可能的原因**：
1. ⭐ Cisco 1921 的型号格式 (`CISCO1921/K9`) 不在已知模式中
2. ⭐ `show version` 输出中没有 'router' 关键字

**推荐操作**：
1. 🔧 运行诊断工具确认问题
2. 🔧 添加新的型号匹配模式
3. 🔧 改进角色判断逻辑
4. ✅ 重新测试

**预计修复时间**：5-10分钟
