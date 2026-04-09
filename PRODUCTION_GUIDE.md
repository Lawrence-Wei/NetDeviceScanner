# 生产环境快速开始指南

## 概述

此工具用于**自动发现和采集**思科网络设备信息，无需手动配置设备清单。

---

## 零配置使用（推荐）

### 1. 安装（仅需一次）

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置凭据

创建 `.env` 文件：
```
CISCO_USERNAME=your_admin_username
CISCO_PASSWORD=your_password
CISCO_SECRET=your_enable_password
```

### 3. 生产环境检查

```bash
python production_check.py
```

确保显示：`✓ 通过生产环境检查`

### 4. 自动发现并采集

```bash
# 一条命令完成所有工作
python main.py scan --network 192.168.0.0/16 --collect
```

**就这么简单！** 结果自动保存到：
- 数据库：`data/devices.db`
- Excel：`exports/auto_discovered_YYYYMMDD_HHMMSS.xlsx`

---

## 多网段采集

```bash
python main.py scan \
  --network 192.168.0.0/16 \
  --network 10.0.0.0/16 \
  --network 172.16.0.0/12 \
  --collect
```

---

## 分步操作（可选）

如果想先看看发现了哪些设备，再决定是否采集：

```bash
# 1. 扫描并保存设备清单
python main.py scan --network 192.168.1.0/24 --save devices.yaml

# 2. 查看 devices.yaml 确认设备列表

# 3. 采集信息
python main.py collect --source devices.yaml
```

---

## 查看结果

```bash
# 查看所有设备
python main.py query --all

# 按型号查询
python main.py query --model C9300

# 导出到Excel
python main.py export --format excel
```

---

## 性能调优

### 小型网络（<100台）
```bash
python main.py scan --network 192.168.1.0/24 --collect
# 使用默认参数即可
```

### 中型网络（100-500台）
```bash
python main.py scan \
  --network 192.168.0.0/16 \
  --scan-workers 50 \
  --collect
```

### 大型网络（500+台）
```bash
# 先扫描（快速）
python main.py scan \
  --network 10.0.0.0/16 \
  --scan-workers 100 \
  --timeout 3 \
  --save large_network.yaml

# 再分批采集（避免压力过大）
python main.py collect \
  --source large_network.yaml \
  --workers 30 \
  --batch-size 100
```

---

## 常见问题

### Q: 扫描需要多久？
A: 
- `/24` 网段（254个IP）：约10-30秒
- `/16` 网段（65534个IP）：约5-15分钟（取决于 `--scan-workers` 参数）

### Q: 如何处理失败的设备？
A: 
- 系统自动重试3次
- 失败设备记录在日志：`logs/collector_YYYYMMDD.log`
- 查看：`python main.py query --all`（状态列显示 failed）

### Q: 如何只扫描特定子网？
A:
```bash
# 只扫描 .1 到 .50
python main.py scan --network 192.168.1.0/27 --collect

# 多个不连续网段
python main.py scan \
  --network 192.168.1.0/24 \
  --network 192.168.10.0/24 \
  --collect
```

### Q: 凭据错误怎么办？
A: 编辑 `.env` 文件，或使用命令行参数：
```bash
python main.py scan \
  --network 192.168.1.0/24 \
  --username admin \
  --password yourpass \
  --secret enablepass \
  --collect
```

### Q: 非思科设备会被采集吗？
A: 不会。系统只识别思科设备（IOS/IOS-XE/NX-OS），其他设备自动忽略。

---

## 日志和故障排查

### 查看实时日志
```bash
# Windows
Get-Content logs\collector_*.log -Wait -Tail 50

# Linux/Mac
tail -f logs/collector_*.log
```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 连接超时 | 网络不通或SSH未启用 | 检查网络连通性，增加 `--timeout` |
| 认证失败 | 用户名密码错误 | 确认 `.env` 文件凭据正确 |
| 未发现设备 | 网段无思科设备 | 确认网段正确，检查防火墙 |

---

## 技术支持

出现问题时，提供以下信息：

1. 运行 `python production_check.py` 的输出
2. 日志文件：`logs/collector_YYYYMMDD.log`
3. 设备类型和 IOS 版本（如果能手动连接）

---

## 安全提示

⚠️  **重要**：
1. `.env` 文件包含敏感凭据，不要分享或提交到版本控制
2. 建议使用只读用户（查询权限即可，无需配置权限）
3. 在生产环境先小范围测试，确认无误后再大规模运行
