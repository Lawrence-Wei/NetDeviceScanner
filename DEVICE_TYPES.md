# 设备类型参考指南

## 问题：不支持的设备类型错误

如果遇到类似错误：
```
不支持的设备类型: ios
```

说明配置文件中的 `device_type` 值不正确。

---

## 支持的设备类型

### Cisco 设备

| 完整类型名 | 简写别名 | 适用设备 |
|-----------|---------|---------|
| **cisco_ios** | `ios` | Catalyst 交换机、ISR 路由器（IOS 12.x - 15.x） |
| **cisco_xe** | `ios_xe` | Catalyst 9000 系列（IOS-XE 16.x+） |
| **cisco_nxos** | `nxos` | Nexus 交换机（NX-OS） |
| **cisco_xr** | - | ASR 9000 系列路由器（IOS-XR） |
| **cisco_asa** | - | ASA 防火墙 |

### 其他厂商

| 完整类型名 | 厂商 | 适用设备 |
|-----------|------|---------|
| **huawei** | 华为 | S 系列交换机、AR 路由器（VRP 5.x） |
| **huawei_vrpv8** | 华为 | S 系列交换机（VRP 8.x） |
| **hp_comware** | H3C/HP | S 系列、H3C 交换机（Comware 5.x/7.x） |
| **juniper** | Juniper | EX/QFX 系列交换机（Junos） |
| **juniper_junos** | Juniper | 同上 |
| **arista_eos** | Arista | 所有 Arista 交换机（EOS） |
| **hp_procurve** | HP | ProCurve 系列交换机 |

---

## 配置示例

### 推荐方式：使用完整类型名

```yaml
devices:
  - ip: "192.168.10.7"
    device_type: "cisco_ios"      # ✓ 推荐
    role: "switch"
    
  - ip: "192.168.10.8"
    device_type: "cisco_nxos"     # ✓ 推荐
    role: "switch"
```

### 兼容方式：使用简写别名

```yaml
devices:
  - ip: "192.168.10.7"
    device_type: "ios"            # ✓ 支持（别名）
    role: "switch"
    
  - ip: "192.168.10.8"
    device_type: "nxos"           # ✓ 支持（别名）
    role: "switch"
```

---

## 常见错误修复

### 错误1：`不支持的设备类型: ios`

**原因**：在 v1.0 版本，此错误确实存在  
**修复**：v2.0+ 已支持 `ios` 作为 `cisco_ios` 的别名

**解决方案**（如果仍然报错）：
```yaml
# 方法1：使用完整类型名
device_type: "cisco_ios"

# 方法2：确认已更新到 v2.0+
python verify_system.py
```

### 错误2：`不支持的设备类型: IOS`（大写）

**原因**：设备类型区分大小写  
**解决方案**：使用小写
```yaml
device_type: "ios"        # ✓ 正确
device_type: "IOS"        # ✗ 错误
```

### 错误3：不确定设备类型

**解决方案**：使用自动扫描
```bash
# 让系统自动识别设备类型
python main.py scan --network 192.168.10.0/24 --save devices.yaml
```

系统会自动识别并生成正确的 `device_type`。

---

## 如何确定设备类型

### 方法1：查看设备型号

| 设备型号前缀 | device_type |
|-------------|-------------|
| Catalyst 2960/3750/3850 | `cisco_ios` 或 `ios` |
| Catalyst 9200/9300/9400/9500 | `cisco_xe` 或 `ios_xe` |
| Nexus 3000/5000/7000/9000 | `cisco_nxos` 或 `nxos` |
| ASR 9000 | `cisco_xr` |
| 华为 S5700/S6700 | `huawei` |
| H3C S5100/S5500 | `hp_comware` |

### 方法2：SSH 登录查看

Cisco IOS:
```
Router>show version
Cisco IOS Software, C3750E Software...
```

Cisco NX-OS:
```
switch# show version
Cisco Nexus Operating System (NX-OS) Software
```

Cisco IOS-XE:
```
Switch>show version
Cisco IOS XE Software, Version 16.12.04
```

华为 VRP:
```
<Huawei>display version
Huawei Versatile Routing Platform Software
```

### 方法3：使用自动扫描（推荐）

```bash
# 自动识别并保存
python main.py scan --network 192.168.10.0/24 --save devices.yaml

# 查看识别结果
cat devices.yaml
```

---

## 配置文件完整示例

### config/devices.yaml

```yaml
# ========================================
# 设备清单配置文件
# ========================================

devices:
  # Cisco IOS 交换机
  - ip: "192.168.10.7"
    device_type: "cisco_ios"     # 或简写: "ios"
    role: "switch"
    location: "核心机房"
    
  # Cisco Nexus 交换机
  - ip: "192.168.10.8"
    device_type: "cisco_nxos"    # 或简写: "nxos"
    role: "L3 switch"
    
  # Cisco Catalyst 9000（IOS-XE）
  - ip: "192.168.10.9"
    device_type: "cisco_xe"      # 或简写: "ios_xe"
    role: "switch"
    
  # 华为交换机
  - ip: "192.168.10.10"
    device_type: "huawei"
    role: "switch"
    
  # H3C 交换机
  - ip: "192.168.10.11"
    device_type: "hp_comware"
    role: "switch"
```

---

## 快速修复步骤

如果遇到 `不支持的设备类型: ios` 错误：

```bash
# 1. 编辑配置文件
nano config/devices.yaml

# 2. 将设备类型改为完整名称
# 从: device_type: "ios"
# 改为: device_type: "cisco_ios"

# 3. 保存文件

# 4. 重新运行
python main.py collect
```

或者直接使用自动扫描：

```bash
# 跳过手动配置，让系统自动识别
python main.py scan --network 192.168.10.0/24 --collect
```

---

## 验证配置

运行测试命令验证设备类型是否正确：

```bash
# 测试单个设备
python main.py test --ip 192.168.10.7

# 验证配置文件
python verify_system.py --full
```

---

## 获取帮助

查看支持的所有设备类型：
```bash
python main.py --help
```

查看详细文档：
- [README.md](README.md) - 完整使用文档
- [MULTI_VENDOR_GUIDE.md](MULTI_VENDOR_GUIDE.md) - 多厂商支持指南
