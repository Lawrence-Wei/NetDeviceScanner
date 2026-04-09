# Ubuntu/Linux 故障排除指南

## 问题1：无法访问 .env 文件

### 症状
```bash
ls
# 看不到 .env 文件

cat .env
# cat: .env: No such file or directory
```

### 原因分析

有**两个**可能的原因：

#### 原因1：文件真的不存在（最常见）
`.env` 文件出于安全考虑不包含在压缩包中（包含敏感凭据）

#### 原因2：文件存在但被隐藏
在 Linux/Ubuntu 中，以点(`.`)开头的文件是隐藏文件，`ls` 命令默认不显示

### ✅ 解决方案

**步骤1：检查文件是否真的存在**

```bash
# 使用 -a 参数显示隐藏文件
ls -a | grep env

# 或直接尝试访问
cat .env
```

**如果显示 "No such file or directory"**，说明文件不存在，需要创建：

**方法1：自动配置（推荐）**
```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

**方法2：手动创建**
```bash
# 1. 从模板复制
cp .env.example .env

# 2. 编辑文件（选择一种）
nano .env           # 简单易用
vim .env            # Vim 编辑器
gedit .env          # 图形界面（需要桌面环境）

# 3. 填入实际凭据
DEVICE_USERNAME=admin
DEVICE_PASSWORD=your_actual_password
DEVICE_SECRET=your_enable_password

# 4. 保存并退出
# nano: Ctrl+X, 然后 Y, 然后 Enter
# vim:  按 Esc, 然后输入 :wq, 按 Enter
```

**方法3：命令行直接创建**
```bash
cat > .env << EOF
DEVICE_USERNAME=admin
DEVICE_PASSWORD=your_password
DEVICE_SECRET=your_enable_password
EOF
```

---

## 问题2：Python 命令不存在

### 症状
```bash
python main.py
# python: command not found
```

### ✅ 解决方案

Ubuntu/Linux 使用 `python3` 而不是 `python`：

```bash
# 使用 python3
python3 main.py scan --network 192.168.1.0/24 --collect

# 或创建别名（可选）
alias python=python3
```

---

## 问题3：虚拟环境激活失败

### 症状
```bash
.venv\Scripts\activate
# bash: .venv\Scripts\activate: No such file or directory
```

### 原因
Windows 和 Linux 的路径分隔符不同

### ✅ 解决方案

**Linux/Ubuntu**:
```bash
source .venv/bin/activate
```

**Windows**:
```bash
.venv\Scripts\activate
```

---

## 问题4：权限不足

### 症状
```bash
./setup_ubuntu.sh
# bash: ./setup_ubuntu.sh: Permission denied
```

### ✅ 解决方案

```bash
# 添加执行权限
chmod +x setup_ubuntu.sh

# 然后运行
./setup_ubuntu.sh
```

---

## 问题5：缺少 Python 依赖

### 症状
```bash
ModuleNotFoundError: No module named 'netmiko'
```

### ✅ 解决方案

```bash
# 确认虚拟环境已激活
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python3 verify_system.py --full
```

---

## 问题6：.env 文件权限问题

### 症状
```bash
cat .env
# cat: .env: Permission denied
```

### ✅ 解决方案

```bash
# 检查 .env 文件
cat .env
# 或
ls -la .env
```

### Q6: 为什么 ls 看不到 .env 文件，但 cat .env 可以访问？

**A**: Linux 隐藏文件机制

```bash
# .env 是隐藏文件（以点开头）

# ✗ ls 默认不显示隐藏文件
ls

# ✓ 使用 -a 参数可以看到
ls -a

# ✓ 直接访问完全没问题（无论是否隐藏）
cat .env
nano .env
vim .env
```

**验证脚本**：
```bash
# 运行检测脚本
chmod +x check_env.sh
./check_env.sh
```

---

## 问题7：.env 文件权限问题

### 症状
```bash
unzip hardware-info-retriever.zip
# unzip: command not found
```

### ✅ 解决方案

```bash
# 安装 unzip
sudo apt update
sudo apt install unzip

# 或使用 Python 解压
python3 -m zipfile -e hardware-info-retriever_v*.zip .
```

---

## 完整配置流程（Ubuntu/Linux）

```bash
# 1. 解压文件
unzip hardware-info-retriever_v*.zip
cd hardware-info-retriever

# 2. 运行自动配置脚本（推荐）
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh

# 或手动配置
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # 编辑填入凭据

# 3. 验证
python3 verify_system.py

# 4. 测试
python3 main.py test --ip 192.168.1.1

# 5. 开始使用
python3 main.py scan --network 192.168.1.0/24 --collect
```

---

## 常见环境检查命令

```bash
# 检查 Python 版本
python3 --version

# 检查虚拟环境
which python3
# 应显示: /path/to/hardware-info-retriever/.venv/bin/python3

# 查看已安装的包
pip list

# 检查 .env 文件
cat .env
# 或
ls -la .env

# 检查网络连通性
ping 192.168.1.1

# 检查 SSH 端口
nc -zv 192.168.1.1 22
# 或
telnet 192.168.1.1 22
```

---

## 快速测试清单

```bash
# ✅ Python 版本 >= 3.8
python3 --version

# ✅ 虚拟环境已创建
ls .venv/

# ✅ 虚拟环境已激活
which python3 | grep .venv

# ✅ 依赖已安装
pip list | grep netmiko

# ✅ .env 文件存在
ls -la .env

# ✅ .env 文件有内容
cat .env | grep DEVICE_USERNAME

# ✅ 系统验证通过
python3 verify_system.py
```

---

## 获取帮助

如果以上方法都无法解决问题：

1. **查看详细日志**：
   ```bash
   cat logs/device_collection.log
   ```

2. **运行完整验证**：
   ```bash
   python3 verify_system.py --full
   ```

3. **查看环境信息**：
   ```bash
   python3 --version
   pip list
   pwd
   ls -la
   ```

4. **联系支持**时提供：
   - 操作系统版本：`lsb_release -a`
   - Python 版本：`python3 --version`
   - 错误信息：完整的错误输出
   - 日志文件：`logs/` 目录下的文件
