# Ubuntu 测试人员快速指南

## ⚠️ 重要说明

**.env 文件不在压缩包中是正常的！**

出于安全考虑，包含密码的 `.env` 文件不会被打包分发。您需要手动创建。

### 关于 Linux 隐藏文件

在 Linux/Ubuntu 中，以点(`.`)开头的文件是**隐藏文件**：

```bash
# ✗ 这样看不到 .env 文件
ls

# ✓ 使用 -a 参数可以看到隐藏文件
ls -a

# ✓ 查看 .env 文件详细信息
ls -la .env

# ✓ 直接访问 .env 文件（无论是否隐藏都可以访问）
cat .env
nano .env
```

**结论**：`.env` 文件在 Ubuntu 上完全可以正常访问，只是默认的 `ls` 命令不显示而已。

---

## 🚀 3 步快速开始

### 方法1：自动配置（最简单）

```bash
# 1. 解压
unzip hardware-info-retriever_v1.0.0_20260105.zip
cd hardware-info-retriever

# 2. 运行自动配置脚本
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh

# 3. 脚本会自动：
#    - 检查 Python 版本
#    - 创建虚拟环境
#    - 安装依赖
#    - 创建 .env 文件
#    - 引导您填入凭据
```

### 方法2：手动配置

```bash
# 1. 解压
unzip hardware-info-retriever_v1.0.0_20260105.zip
cd hardware-info-retriever

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建 .env 文件（关键步骤！）
cp .env.example .env

# 5. 编辑 .env 文件，填入实际凭据
nano .env

# 填入以下内容（替换为实际值）：
# DEVICE_USERNAME=admin
# DEVICE_PASSWORD=your_password
# DEVICE_SECRET=your_enable_password

# 保存: Ctrl+X, 然后 Y, 然后 Enter

# 6. 验证配置
python3 verify_system.py

# 7. 开始测试
python3 main.py scan --network 192.168.1.0/24 --collect
```

---

## ❓ 为什么没有 .env 文件？

1. **安全原因**：`.env` 文件包含敏感的用户名和密码
2. **最佳实践**：凭据文件不应该被版本控制或打包分发
3. **解决方案**：从 `.env.example` 模板创建自己的 `.env` 文件

---

## 📝 .env 文件内容示例

创建 `.env` 文件后，填入以下内容：

```bash
# 通用设备凭据（支持多厂商）
DEVICE_USERNAME=admin
DEVICE_PASSWORD=your_actual_password_here
DEVICE_SECRET=your_enable_password_here
```

**注意**：
- 将 `your_actual_password_here` 替换为真实密码
- 不要保留示例中的值
- 不要在密码周围加引号

---

## 🧪 测试步骤

### 1. 验证系统
```bash
python3 verify_system.py
```

应该看到所有测试通过的 ✓ 标记。

### 2. 测试单个设备连接（可选）
```bash
python3 main.py test --ip 192.168.1.1
```

### 3. 小范围扫描测试
```bash
# 测试小网段（例如 /28 只有 14 个 IP）
python3 main.py scan --network 192.168.1.0/28 --collect
```

### 4. 查看结果
```bash
# 查询所有采集的设备
python3 main.py query --all

# 导出为 Excel
python3 main.py export --format excel

# 查看导出文件
ls -lh exports/
```

---

## 🔍 常见问题

### Q1: 运行 `cat .env` 显示文件不存在

**A**: 这是正常的！需要先创建：
```bash
cp .env.example .env
nano .env
```

### Q2: 提示 `python: command not found`

**A**: Ubuntu 使用 `python3`：
```bash
python3 main.py ...
```

### Q3: 虚拟环境激活失败

**A**: Linux 使用不同的路径：
```bash
source .venv/bin/activate  # Linux
# 不是: .venv\Scripts\activate  (这是 Windows)
```

### Q4: 权限被拒绝

**A**: 添加执行权限：
```bash
chmod +x setup_ubuntu.sh
```

---

## 📚 详细文档

如果遇到问题，查看：

1. **[TROUBLESHOOTING_UBUNTU.md](TROUBLESHOOTING_UBUNTU.md)** - Ubuntu 故障排除完整指南
2. **[QUICK_START.md](QUICK_START.md)** - 详细快速开始指南
3. **[README.md](README.md)** - 完整使用文档

---

## 📊 测试清单

- [ ] 解压文件
- [ ] 创建虚拟环境
- [ ] 安装依赖
- [ ] **创建 .env 文件**（重要！）
- [ ] 填入实际凭据
- [ ] 运行 `python3 verify_system.py`
- [ ] 测试单个设备连接
- [ ] 小范围扫描测试
- [ ] 查看结果

---

## 🆘 需要帮助？

**遇到 ".env 文件不存在" 问题？**

运行这个命令创建文件：
```bash
cp .env.example .env && nano .env
```

**其他问题？**

1. 查看日志：`cat logs/device_collection.log`
2. 运行诊断：`python3 verify_system.py --full`
3. 查看故障排除文档：`TROUBLESHOOTING_UBUNTU.md`

---

**祝测试顺利！** 🎉
