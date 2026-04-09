# 凭据管理指南

## 问题：不同设备的SSH凭据可能不一样？

**答案：是的！您的担心完全正确。** 这是现实中非常常见的情况。

## 常见场景

### 场景1：不同部门的设备
```
财务部门网段：192.168.10.0/24
  - 管理员：finance_admin
  - 密码：Finance@2024

IT部门网段：192.168.20.0/24
  - 管理员：it_admin
  - 密码：ITAdmin@2024
```

### 场景2：不同安全级别
```
普通办公区：
  - 用户名：admin
  - 密码：Office123

核心机房（高安全）：
  - 用户名：coreadmin
  - 密码：V3ryS3cur3P@ss!
  - Enable密码：V3ryS3cur3Enable!
```

### 场景3：老旧设备
```
新设备（2024年购买）：
  - 用户名：admin
  - 密码：NewPassword2024

老设备（2018年购买）：
  - 用户名：oldadmin
  - 密码：LegacyPass2018
  - 原因：从未修改过，怕改了出问题
```

### 场景4：不同厂商
```
Cisco设备：
  - 用户名：cisco_admin
  - 密码：Cisco@123

华为设备：
  - 用户名：huawei_admin
  - 密码：Huawei@456

H3C设备：
  - 用户名：h3c_admin
  - 密码：H3C@789
```

## 解决方案

### 方案1：统一凭据（最简单，但不现实）

如果所有设备都使用相同的用户名和密码：

```bash
# .env 文件
DEVICE_USERNAME=admin
DEVICE_PASSWORD=SamePassword123
DEVICE_SECRET=SameEnable123
```

**优点**：
- ✅ 配置简单，只需要一个 .env 文件
- ✅ 维护方便，改密码只改一个地方

**缺点**：
- ❌ 不符合安全最佳实践
- ❌ 现实中很难做到所有设备统一密码
- ❌ 老旧设备可能无法修改

### 方案2：混合凭据（推荐，灵活实用）

**工作原理**：
1. `.env` 文件配置**默认凭据**（大部分设备使用）
2. `devices.yaml` 中为**特殊设备**单独指定凭据
3. 系统自动优先使用设备的专用凭据，找不到就用默认凭据

**实际配置示例**：

#### 步骤1：配置默认凭据（.env 文件）

```bash
# .env - 大部分设备使用这个凭据
DEVICE_USERNAME=admin
DEVICE_PASSWORD=CommonPassword123
DEVICE_SECRET=CommonEnable123
```

#### 步骤2：为特殊设备指定凭据（devices.yaml）

```yaml
devices:
  # 普通设备 - 自动使用 .env 默认凭据
  - ip: "192.168.1.1"
    device_type: "cisco_ios"
    role: "switch"
    # 不配置 username/password，自动用 .env

  - ip: "192.168.1.2"
    device_type: "cisco_ios"
    role: "switch"
    # 同上

  # 特殊设备1 - 老旧设备，还在用旧密码
  - ip: "192.168.2.100"
    device_type: "ios"
    role: "switch"
    location: "老旧机房"
    username: "oldadmin"        # 覆盖 .env 默认值
    password: "OldPass2018"
    secret: "OldEnable2018"

  # 特殊设备2 - 核心路由器，高安全密码
  - ip: "10.0.0.1"
    device_type: "cisco_ios"
    role: "router"
    location: "核心机房"
    username: "coreadmin"       # 覆盖 .env 默认值
    password: "V3ryS3cur3!"
    secret: "V3ryS3cur3Enable!"

  # 特殊设备3 - 华为设备，不同账号
  - ip: "192.168.3.1"
    device_type: "huawei"
    role: "switch"
    location: "分支机房"
    username: "huawei_admin"    # 华为特有账号
    password: "Huawei@2024"

  # 特殊设备4 - 测试环境，简单密码
  - ip: "192.168.100.1"
    device_type: "ios"
    role: "switch"
    location: "测试实验室"
    username: "testuser"
    password: "test123"
    # 没有 secret - 这台设备不需要 enable 密码

  # 更多普通设备 - 都用默认凭据
  - ip: "192.168.1.3"
    device_type: "cisco_ios"
    # 自动用 .env

  - ip: "192.168.1.4"
    device_type: "cisco_nxos"
    # 自动用 .env
```

**优点**：
- ✅ 灵活：支持不同设备使用不同凭据
- ✅ 简单：大部分设备只需配置 .env
- ✅ 安全：特殊设备可以用更强密码
- ✅ 实用：适应现实环境的复杂情况

### 方案3：完全独立凭据（最灵活，但配置量大）

每台设备都单独配置凭据：

```yaml
devices:
  - ip: "192.168.1.1"
    device_type: "cisco_ios"
    username: "admin1"
    password: "Pass1"
    secret: "Enable1"

  - ip: "192.168.1.2"
    device_type: "cisco_ios"
    username: "admin2"
    password: "Pass2"
    secret: "Enable2"

  # ... 400台设备都要单独配置
```

**优点**：
- ✅ 最高安全性，每台设备独立密码

**缺点**：
- ❌ 配置工作量巨大（400-500台设备）
- ❌ 维护困难，改密码要改很多地方
- ❌ 容易出错

## 推荐配置流程

### 第1步：统计设备凭据情况

按照这个表格整理您的设备：

| 网段/区域 | 设备数量 | 用户名 | 密码 | Enable密码 | 备注 |
|----------|---------|--------|------|-----------|------|
| 192.168.1.0/24 | 50 | admin | Pass123 | Enable123 | 新设备 |
| 192.168.2.0/24 | 30 | admin | Pass123 | Enable123 | 新设备 |
| 192.168.10.0/24 | 10 | oldadmin | OldPass | OldEnable | 老设备 |
| 10.0.0.0/24 | 5 | coreadmin | SecurePass! | SecureEnable! | 核心区 |
| 172.16.0.0/16 | 20 | huawei_admin | Huawei@2024 | - | 华为设备 |

### 第2步：确定默认凭据

选择**使用最多**的凭据作为默认值：

```bash
# .env - 使用最多的凭据（例如上表中的 admin/Pass123）
DEVICE_USERNAME=admin
DEVICE_PASSWORD=Pass123
DEVICE_SECRET=Enable123
```

### 第3步：标记特殊设备

在 `devices.yaml` 中，只为**不使用默认凭据**的设备配置 username/password：

```yaml
devices:
  # 大部分设备（80台）- 不配置凭据
  - ip: "192.168.1.1"
    device_type: "cisco_ios"
    # 自动用 .env 默认凭据

  - ip: "192.168.1.2"
    device_type: "cisco_ios"
    # 自动用 .env 默认凭据

  # ... 省略80台类似配置 ...

  # 特殊设备（10台老设备）- 单独配置
  - ip: "192.168.10.1"
    device_type: "ios"
    username: "oldadmin"
    password: "OldPass"
    secret: "OldEnable"

  - ip: "192.168.10.2"
    device_type: "ios"
    username: "oldadmin"
    password: "OldPass"
    secret: "OldEnable"

  # ... 省略其他8台 ...

  # 核心设备（5台）- 单独配置
  - ip: "10.0.0.1"
    device_type: "cisco_ios"
    username: "coreadmin"
    password: "SecurePass!"
    secret: "SecureEnable!"

  # ... 省略其他4台 ...
```

## 安全建议

### 1. 不要在代码中写密码
❌ **错误做法**：
```python
password = "MyPassword123"  # 不要这样！
```

✅ **正确做法**：
```bash
# .env 文件
DEVICE_PASSWORD=MyPassword123
```

### 2. .env 文件不要提交到 Git
```bash
# .gitignore 文件已经包含：
.env
```

### 3. 定期更换密码

建议每 3-6 个月更换一次密码：

```bash
# 更新 .env 文件
DEVICE_USERNAME=admin
DEVICE_PASSWORD=NewPassword2024Q1  # 新密码
```

### 4. 使用强密码

**弱密码示例**（不要用）：
- ❌ admin
- ❌ 123456
- ❌ password

**强密码示例**（推荐）：
- ✅ Cisco@2024!Secure
- ✅ Network#Admin$2024
- ✅ MyC0mpany#Passw0rd!

## 常见问题

### Q1：我有400台设备，每台都要配置凭据吗？

**A1**：不需要！使用混合方案：
- 在 .env 配置最常用的凭据（假设300台设备用这个）
- 只在 devices.yaml 中单独配置其他100台特殊设备

### Q2：如何知道某台设备用的是默认凭据还是专用凭据？

**A2**：看 devices.yaml 中有没有配置 username：
```yaml
# 这台用默认凭据（.env）
- ip: "192.168.1.1"
  device_type: "cisco_ios"

# 这台用专用凭据
- ip: "192.168.1.2"
  device_type: "cisco_ios"
  username: "special_admin"  # 有这一行就是专用凭据
  password: "SpecialPass"
```

### Q3：修改默认密码后，已经有专用凭据的设备会受影响吗？

**A3**：不会！已配置专用凭据的设备不受 .env 修改影响：
```bash
# 修改 .env 默认密码
DEVICE_PASSWORD=NewDefaultPass

# devices.yaml 中有专用凭据的设备，仍然用自己的密码，不受影响
- ip: "192.168.10.1"
  username: "oldadmin"
  password: "OldPass"  # 这个不会改变
```

### Q4：我的设备有些需要 enable 密码，有些不需要，怎么办？

**A4**：不需要 enable 的设备，不配置 secret 就行：
```yaml
# 需要 enable 的设备
- ip: "192.168.1.1"
  device_type: "cisco_ios"
  username: "admin"
  password: "Pass123"
  secret: "Enable123"      # 需要 enable

# 不需要 enable 的设备
- ip: "192.168.1.2"
  device_type: "huawei"
  username: "admin"
  password: "Pass123"
  # 没有 secret 行 - 不需要 enable
```

### Q5：我能用 Excel 管理凭据吗？

**A5**：可以！工作流程：

1. 在 Excel 中整理设备列表：
   | IP | 设备类型 | 用户名 | 密码 | Enable |
   |---|---------|-------|------|--------|
   | 192.168.1.1 | cisco_ios | admin | Pass1 | Enable1 |
   | 192.168.1.2 | cisco_ios | admin | Pass1 | Enable1 |

2. 统计哪个凭据最常用（例如 admin/Pass1）

3. 把最常用的凭据放到 .env：
   ```bash
   DEVICE_USERNAME=admin
   DEVICE_PASSWORD=Pass1
   DEVICE_SECRET=Enable1
   ```

4. 在 Excel 中筛选出**不是默认凭据**的设备

5. 只把特殊设备写到 devices.yaml：
   ```yaml
   devices:
     # 只写特殊设备
     - ip: "192.168.10.1"
       device_type: "ios"
       username: "special_admin"
       password: "SpecialPass"
   ```

## 总结

✅ **最佳实践**：
1. 用 .env 配置默认凭据（大部分设备）
2. 用 devices.yaml 为特殊设备配置专用凭据
3. 定期更换密码
4. 不要把密码提交到 Git

✅ **记住**：
- 系统会**优先使用** devices.yaml 中的专用凭据
- 找不到专用凭据时，才使用 .env 的默认凭据
- 这样既简单又灵活，适应现实环境

❓ **还有问题**：
- 查看 [README.md](../README.md) 的凭据配置章节
- 查看 [config/devices.yaml](../config/devices.yaml) 的实际示例
- 查看 [.env.example](../.env.example) 的详细说明
