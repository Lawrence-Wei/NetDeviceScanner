# 🚀 快速开始指南

## 两个核心问题的解决方案

### 问题1：网段太多怎么办？

**解决方案**：使用网段文件

```bash
# 创建网段文件 networks.txt
cat > networks.txt << EOF
192.168.1.0/24
192.168.2.0/24
10.0.0.0/16
172.16.0.0/12
EOF

# 使用文件扫描
python main.py scan --network-file networks.txt --collect
```

### 问题2：如何支持多厂商设备？

**解决方案**：系统自动识别

支持：Cisco、华为、H3C、Juniper、Arista、HP

```bash
# 自动识别所有厂商
python main.py scan --network 192.168.1.0/24 --collect
```

---

## 3分钟快速上手

### 1. 安装（1分钟）

**Ubuntu/Linux**:
```bash
# 解压
unzip hardware-info-retriever_v*.zip
cd hardware-info-retriever

# 安装依赖
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**Windows**:
```bash
# 解压
unzip hardware-info-retriever.zip
cd hardware-info-retriever

# 安装依赖
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置凭据（30秒）

⚠️ **重要**：需要手动创建 `.env` 文件（出于安全考虑，不包含在压缩包中）

**Ubuntu/Linux**:
```bash
# 从模板创建
cp .env.example .env

# 编辑文件（选择一种编辑器）
nano .env          # 简单编辑器
# 或
vim .env           # Vim 编辑器
# 或
gedit .env         # 图形界面编辑器
```

**Windows**:
```bash
copy .env.example .env
notepad .env
```

**填入以下内容**：

```bash
DEVICE_USERNAME=admin
DEVICE_PASSWORD=your_password
DEVICE_SECRET=enable_password
```

### 3. 运行（1分钟）

```bash
# 扫描 + 采集 + 导出（一步完成）
python main.py scan --network 192.168.1.0/24 --collect
python main.py export --format excel
```

完成！查看 `exports/` 目录下的 Excel 文件。

---

## 实际场景示例

### 场景1：纯 Cisco 环境（400-500台）

```bash
# 单个大网段
python main.py scan --network 10.0.0.0/16 --collect
```

**性能**：
- 扫描时间：约 15 分钟（/16 网段）
- 采集时间：约 20 分钟（400台，20并发）
- 总计：约 35 分钟

### 场景2：混合厂商环境

```bash
# 自动识别 Cisco + Huawei + H3C
python main.py scan --network-file networks.txt --collect
```

### 场景3：超多网段（50+ 个）

创建 `all_networks.txt`：

```text
# 总部
192.168.0.0/16

# 20个分支
10.1.0.0/24
10.2.0.0/24
...
10.20.0.0/24

# 数据中心
172.16.0.0/12
```

运行：

```bash
python main.py scan --network-file all_networks.txt --collect
```

### 场景4：大型网络（1000+ 设备）

```bash
# 第一步：扫描并保存
python main.py scan \
  --network-file networks.txt \
  --scan-workers 100 \
  --save devices.yaml

# 第二步：分批采集
python main.py collect \
  --source devices.yaml \
  --workers 50 \
  --batch-size 100
```

---

## 常用命令速查

| 需求 | 命令 |
|------|------|
| 扫描单网段 | `python main.py scan --network 192.168.1.0/24 --collect` |
| 扫描多网段 | `python main.py scan --network-file networks.txt --collect` |
| 查看所有设备 | `python main.py query --all` |
| 导出Excel | `python main.py export --format excel` |
| 测试连接 | `python main.py test --ip 192.168.1.1` |
| 清空数据 | `python main.py clear --confirm` |

---

## 网段文件格式

`networks.txt` 示例：

```text
# 注释行（以 # 开头）

# 核心网段
192.168.1.0/24
192.168.2.0/24

# 分支机构
10.0.0.0/16

# 数据中心
172.16.0.0/12
```

**规则**：
- 每行一个网段
- 支持 CIDR 格式（/8 到 /30）
- 支持注释（# 开头）
- 空行自动忽略

---

## 性能调优

### 扫描性能

```bash
# 默认（50并发）
--scan-workers 50

# 小网段（/24）
--scan-workers 30

# 大网段（/16）
--scan-workers 100
```

### 采集性能

```bash
# 默认（20并发）
--workers 20

# 中型（100-200台）
--workers 30

# 大型（400-500台）
--workers 50
```

---

## 故障排除

### 找不到设备

```bash
# 检查：
1. ping 192.168.1.1  # 网络连通性
2. telnet 192.168.1.1 22  # SSH 端口
3. 检查凭据（.env 文件）
```

### 认证失败

```bash
# 检查凭据
cat .env

# 测试单个设备
python main.py test --ip 192.168.1.1
```

### 查看详细日志

```bash
# 日志位置
logs/device_collection.log

# 实时查看
tail -f logs/device_collection.log
```

---

## 下一步

- 📚 详细文档：[MULTI_VENDOR_GUIDE.md](MULTI_VENDOR_GUIDE.md)
- 🏭 生产部署：[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
- 📋 完整说明：[README.md](README.md)

---

**问题反馈**：检查 `logs/` 目录获取详细错误信息
