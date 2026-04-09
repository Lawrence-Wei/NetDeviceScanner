#!/bin/bash
# ====================================
# .env 文件验证脚本
# 用于测试人员验证文件是否存在
# ====================================

echo "======================================"
echo ".env 文件检测工具"
echo "======================================"
echo ""

echo "检查1: .env 文件是否存在？"
if [ -f ".env" ]; then
    echo "  ✓ .env 文件存在"
    echo ""
    echo "  文件信息："
    ls -lh .env
    echo ""
    echo "  文件内容（仅显示变量名，不显示密码）："
    grep "^DEVICE_" .env | sed 's/=.*/=***/' || echo "  （未找到 DEVICE_ 变量）"
    grep "^CISCO_" .env | sed 's/=.*/=***/' || echo "  （未找到 CISCO_ 变量）"
else
    echo "  ✗ .env 文件不存在"
    echo ""
    echo "原因分析："
    echo "  1. .env 文件确实不在压缩包中（这是正常的，安全原因）"
    echo "  2. 需要从 .env.example 创建"
    echo ""
    
    if [ -f ".env.example" ]; then
        echo "  ✓ 找到 .env.example 模板文件"
        echo ""
        echo "解决方案："
        echo "  运行以下命令创建 .env 文件："
        echo ""
        echo "    cp .env.example .env"
        echo "    nano .env"
        echo ""
        read -p "是否现在创建 .env 文件？(y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo "  ✓ .env 文件已创建"
            echo ""
            echo "  下一步：编辑文件填入凭据"
            echo "    nano .env"
        fi
    else
        echo "  ✗ 也没有找到 .env.example 模板"
        echo "  请确认您在正确的目录中"
    fi
fi

echo ""
echo "======================================"
echo "关于 Linux 隐藏文件的说明"
echo "======================================"
echo ""
echo "在 Linux/Ubuntu 中，以点(.)开头的文件是隐藏文件："
echo ""
echo "  ✗ ls                 # 不显示 .env"
echo "  ✓ ls -a              # 显示 .env"
echo "  ✓ ls -la .env        # 显示 .env 详细信息"
echo "  ✓ cat .env           # 查看 .env 内容"
echo "  ✓ nano .env          # 编辑 .env"
echo ""
echo "测试命令："
echo ""

# 显示当前目录所有文件（包括隐藏文件）
echo "当前目录的所有文件（包括隐藏文件）："
ls -la | grep "^\." | head -10

echo ""
echo "======================================"
echo "压缩包验证"
echo "======================================"
echo ""

# 检查是否有压缩包
if ls hardware-info-retriever*.zip 1> /dev/null 2>&1; then
    echo "找到压缩包："
    ls -lh hardware-info-retriever*.zip
    echo ""
    echo "检查压缩包中是否包含 .env 文件："
    for zip_file in hardware-info-retriever*.zip; do
        if unzip -l "$zip_file" 2>/dev/null | grep -q "\.env$"; then
            echo "  ⚠️  压缩包中包含 .env 文件（不应该！）"
        else
            echo "  ✓ 压缩包中不包含 .env 文件（正确）"
        fi
        
        if unzip -l "$zip_file" 2>/dev/null | grep -q "\.env\.example"; then
            echo "  ✓ 压缩包中包含 .env.example 模板（正确）"
        else
            echo "  ✗ 压缩包中没有 .env.example 模板（应该有）"
        fi
    done
else
    echo "当前目录没有压缩包"
fi

echo ""
echo "======================================"
echo "结论"
echo "======================================"
echo ""
echo "1. .env 文件不在压缩包中是**正常的**（安全设计）"
echo "2. .env 是隐藏文件，但 Linux 可以正常访问"
echo "3. 需要从 .env.example 手动创建"
echo "4. 使用 'ls -a' 可以看到隐藏文件"
echo ""
