#!/bin/bash
# ====================================
# Ubuntu/Linux 快速配置脚本
# Quick Setup Script for Ubuntu/Linux
# ====================================

echo "=========================================="
echo "网络设备信息收集系统 - Ubuntu 配置向导"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "[1/5] 检查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✓ $PYTHON_VERSION"
else
    echo "  ✗ 未找到 Python3，请先安装:"
    echo "    sudo apt update"
    echo "    sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# 检查虚拟环境
echo ""
echo "[2/5] 检查虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv .venv
    echo "  ✓ 虚拟环境创建成功"
else
    echo "  ✓ 虚拟环境已存在"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "[3/5] 安装依赖..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✓ 依赖安装完成"

# 配置 .env 文件
echo ""
echo "[4/5] 配置凭据..."
if [ ! -f ".env" ]; then
    echo "  .env 文件不存在，从模板创建..."
    cp .env.example .env
    echo "  ✓ .env 文件已创建"
    echo ""
    echo "  ⚠️  需要编辑 .env 文件填入实际凭据"
    echo ""
    
    # 询问是否立即编辑
    read -p "  是否现在编辑 .env 文件? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 检查可用的编辑器
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        elif command -v vi &> /dev/null; then
            vi .env
        else
            echo "  未找到文本编辑器，请手动编辑："
            echo "    nano .env"
        fi
    else
        echo "  请稍后手动编辑："
        echo "    nano .env"
        echo ""
        echo "  需要修改的内容："
        echo "    DEVICE_USERNAME=你的用户名"
        echo "    DEVICE_PASSWORD=你的密码"
        echo "    DEVICE_SECRET=你的enable密码"
    fi
else
    echo "  ✓ .env 文件已存在"
    echo "  当前配置："
    grep "^DEVICE_USERNAME=" .env || grep "^CISCO_USERNAME=" .env || echo "    未配置用户名"
fi

# 验证系统
echo ""
echo "[5/5] 验证系统..."
python3 verify_system.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ 系统验证通过"
else
    echo "  ⚠️  系统验证有警告，运行以下命令查看详情："
    echo "    python3 verify_system.py"
fi

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 确认凭据配置正确："
echo "   cat .env"
echo ""
echo "2. 测试连接（可选）："
echo "   python3 main.py test --ip <设备IP>"
echo ""
echo "3. 开始扫描："
echo "   python3 main.py scan --network 192.168.1.0/24 --collect"
echo ""
echo "4. 查看帮助："
echo "   python3 main.py --help"
echo ""
echo "提示: 记得激活虚拟环境："
echo "   source .venv/bin/activate"
echo ""
