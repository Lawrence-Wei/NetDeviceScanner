# 多厂商设备支持指南
Multi-Vendor Device Support Guide

## 📋 目录

1. [支持的厂商](#支持的厂商)
2. [网段文件使用](#网段文件使用)
3. [多厂商扫描](#多厂商扫描)
4. [使用示例](#使用示例)
5. [注意事项](#注意事项)

---

## 支持的厂商

| 厂商 | 设备类型 | 系统版本 | 状态 |
|------|---------|---------|------|
| **Cisco** | IOS, IOS-XE, NX-OS, IOS-XR, ASA | All | ✅ 完全支持 |
| **华为 (Huawei)** | VRP, VRP V8 | V5/V8 | ✅ 完全支持 |
| **新华三 (H3C)** | Comware | V5/V7 | ✅ 完全支持 |
| **Juniper** | Junos | All | ✅ 完全支持 |
| **Arista** | EOS | All | ✅ 完全支持 |
| **HP/HPE** | ProCurve, Comware | All | ✅ 完全支持 |

### 自动识别

系统使用 **Netmiko autodetect** 功能，可以自动识别：

- ✅ Cisco 设备（通过 SSH banner）
- ✅ Huawei 设备（通过提示符）
- ✅ H3C 设备（通过 SSH banner）
- ✅ Juniper 设备（通过 SSH banner）
- ✅ Arista 设备（通过提示符）
- ✅ HP 设备（通过 SSH banner）

### 采集的信息

所有厂商都支持采集：

| 字段 | 说明 | 备注 |
|------|------|------|
| Hostname | 主机名 | 自动识别 |
| Model | 型号 | 从 show version 解析 |
| Serial Number | 序列号 | 从 inventory 或 device 命令解析 |
| OS Version | 系统版本 | IOS/VRP/EOS/Junos 等 |
| Uptime | 运行时间 | 部分厂商支持 |
| Total Ports | 端口数量 | 统计物理接口 |
| Management IP | 管理IP | 扫描获得 |
| Device Role | 设备角色 | 自动判断（switch/router/L3 switch） |

---

## 网段文件使用

### 问题场景

如果你有**非常多的网段**（例如 50+ 个），命令行会很长：

```bash
# 这样太长了 ❌
python main.py scan \
  --network 192.168.1.0/24 \
  --network 192.168.2.0/24 \
  --network 192.168.3.0/24 \
  ... (还有 50 个)
```

### 解决方案：使用网段文件

#### 1. 创建网段文件

创建 `networks.txt` 文件：

```text
# 网段列表 - 支持注释
# 每行一个网段

# 核心网段
192.168.1.0/24
192.168.2.0/24
192.168.3.0/24

# 分支1
10.0.1.0/24
10.0.2.0/24

# 分支2
10.10.0.0/16

# 数据中心
172.16.0.0/12
```

**格式说明**：

- ✅ 每行一个网段
- ✅ 支持 CIDR 格式（/24, /16 等）
- ✅ 支持注释（`#` 开头）
- ✅ 空行自动忽略
- ✅ UTF-8 编码

#### 2. 使用网段文件

```bash
# 从文件读取网段
python main.py scan --network-file networks.txt --collect
```

#### 3. 混合使用

可以同时使用文件和命令行参数：

```bash
# 文件 + 命令行
python main.py scan \
  --network-file networks.txt \
  --network 192.168.100.0/24 \
  --collect
```

---

## 多厂商扫描

### 混合环境扫描

系统可以在**同一个网段**中自动识别不同厂商的设备：

```bash
# 自动识别 Cisco + Huawei + H3C + Juniper
python main.py scan \
  --network 10.0.0.0/16 \
  --network-file other_networks.txt \
  --collect
```

### 输出示例

```
✓ 发现 127 台网络设备
厂商分布: Cisco: 85, 华为 (Huawei): 30, 新华三 (H3C): 10, Juniper: 2

┌────────────────────────────────────────────────────────────┐
│                        发现的设备                           │
├──────────────┬─────────────┬────────────┬────────┬─────────┤
│ IP           │ Hostname    │ 类型       │ 角色   │ 厂商    │
├──────────────┼─────────────┼────────────┼────────┼─────────┤
│ 192.168.1.1  │ CORE-SW-01  │ CISCO_IOS  │ switch │ Cisco   │
│ 192.168.1.2  │ HW-AGG-01   │ HUAWEI     │ router │ 华为    │
│ 192.168.1.3  │ H3C-DIST-01 │ HP_COMWARE │ L3 sw  │ 新华三  │
│ 192.168.1.4  │ JUN-CORE-01 │ JUNIPER    │ router │ Juniper │
└──────────────┴─────────────┴────────────┴────────┴─────────┘
```

### 凭据配置

不同厂商可能使用不同凭据，建议：

#### 方法1：环境变量（推荐）

编辑 `.env` 文件：

```bash
# 通用设备凭据（多厂商）
DEVICE_USERNAME=admin
DEVICE_PASSWORD=your_password
DEVICE_SECRET=enable_password

# 或者使用旧的 Cisco 变量（仍然支持）
CISCO_USERNAME=admin
CISCO_PASSWORD=your_password
```

#### 方法2：命令行参数

```bash
python main.py scan \
  --network-file networks.txt \
  --username admin \
  --password mypass \
  --collect
```

---

## 使用示例

### 示例1：纯思科环境（原有场景）

```bash
# 400-500 台思科交换机
python main.py scan --network 10.0.0.0/16 --collect
```

### 示例2：混合厂商环境

```bash
# Cisco + Huawei 混合
python main.py scan \
  --network-file all_networks.txt \
  --username admin \
  --password mypass \
  --collect
```

### 示例3：多个独立网段

创建 `production_networks.txt`：

```text
# 总部
192.168.0.0/16

# 分支机构
10.1.0.0/16
10.2.0.0/16
10.3.0.0/16
10.4.0.0/16

# 数据中心
172.16.0.0/12
```

运行：

```bash
python main.py scan \
  --network-file production_networks.txt \
  --scan-workers 100 \
  --collect \
  --workers 30
```

### 示例4：先扫描，后采集

```bash
# 第一步：扫描并保存设备列表
python main.py scan \
  --network-file networks.txt \
  --save discovered_devices.yaml

# 第二步：检查设备列表（可选）
# 编辑 discovered_devices.yaml，删除不需要的设备

# 第三步：批量采集
python main.py collect \
  --source discovered_devices.yaml \
  --workers 30
```

### 示例5：非常大的网络（1000+ 设备）

```bash
# 使用高并发 + 分批处理
python main.py scan \
  --network-file large_networks.txt \
  --scan-workers 100 \
  --save all_devices.yaml

# 分批采集（减少压力）
python main.py collect \
  --source all_devices.yaml \
  --workers 50 \
  --batch-size 100
```

---

## 注意事项

### 1. 凭据兼容性

| 厂商 | SSH认证 | Enable/Super | 备注 |
|------|---------|--------------|------|
| Cisco | ✅ | ✅ secret | IOS需要enable |
| Huawei | ✅ | ✅ super | 部分需要super密码 |
| H3C | ✅ | ✅ super | 类似Huawei |
| Juniper | ✅ | ❌ | 无需enable |
| Arista | ✅ | ✅ enable | 类似Cisco |
| HP ProCurve | ✅ | ✅ manager/operator | 权限分级 |

**建议**：使用统一的管理员账号，避免认证问题。

### 2. 命令差异

系统已自动处理不同厂商的命令差异：

| 功能 | Cisco | Huawei/H3C | Juniper |
|------|-------|------------|---------|
| 版本 | `show version` | `display version` | `show version` |
| 清单 | `show inventory` | `display device` | `show chassis hardware` |
| 接口 | `show interface` | `display interface brief` | `show interfaces terse` |

你**不需要关心**这些差异，系统会自动使用正确的命令。

### 3. 网段扫描性能

| 网段大小 | 扫描时间（默认50并发） | 建议 |
|---------|---------------------|------|
| /24 (254 hosts) | ~30秒 | 标准 |
| /22 (1022 hosts) | ~2分钟 | 标准 |
| /16 (65534 hosts) | ~15-30分钟 | 提高并发到100 |

```bash
# 大网段使用高并发
python main.py scan \
  --network 10.0.0.0/16 \
  --scan-workers 100 \
  --collect
```

### 4. 实验环境建议

如果你的实验环境有**非网络设备**（服务器、PC等）：

- ✅ **不用担心**：系统只连接 SSH 22 端口
- ✅ **自动过滤**：非网络设备会被自动跳过
- ✅ **不会出错**：认证失败的设备直接忽略

### 5. 错误处理

系统对每个设备独立处理：

```
✓ 192.168.1.1 - 采集成功
✓ 192.168.1.2 - 采集成功
✗ 192.168.1.3 - 认证失败（跳过）
✓ 192.168.1.4 - 采集成功
✗ 192.168.1.5 - 超时（跳过）
```

单个设备失败**不影响**其他设备。

---

## 快速参考

### 常用命令

```bash
# 1. 单网段扫描（Cisco）
python main.py scan --network 192.168.1.0/24 --collect

# 2. 多网段扫描（混合厂商）
python main.py scan \
  --network-file networks.txt \
  --collect

# 3. 高性能扫描（大型网络）
python main.py scan \
  --network-file networks.txt \
  --scan-workers 100 \
  --collect \
  --workers 50

# 4. 导出结果
python main.py export --format excel
```

### 网段文件模板

保存为 `networks.txt`：

```text
# ====================================
# 网段配置文件
# 格式：每行一个网段（CIDR）
# ====================================

# 核心网段
192.168.0.0/16

# 分支机构
10.1.0.0/24
10.2.0.0/24
10.3.0.0/24

# 数据中心
172.16.0.0/12
```

---

## 总结

### ✅ 解决了你的两个问题

1. **网段太多**：使用 `--network-file networks.txt`
2. **多厂商支持**：自动识别 Cisco + Huawei + H3C + Juniper + Arista + HP

### 使用流程

```
1. 创建网段文件 (networks.txt)
   ↓
2. 配置凭据 (.env 文件)
   ↓
3. 扫描设备
   python main.py scan --network-file networks.txt --collect
   ↓
4. 导出结果
   python main.py export --format excel
```

### 性能参考

- **400-500 台设备**：30-40 分钟（默认配置）
- **1000+ 台设备**：60-90 分钟（优化配置）

完成！🎉
