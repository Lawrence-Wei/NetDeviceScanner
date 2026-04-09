#!/usr/bin/env python3
"""
项目打包脚本
创建一个可分发的 ZIP 压缩包，排除虚拟环境和敏感文件

使用方法:
    python pack_project.py
    
输出:
    hardware-info-retriever_v1.0.0_YYYYMMDD.zip
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path

# 项目版本
VERSION = "1.0.0"

# 要排除的文件和目录
EXCLUDE_PATTERNS = [
    '.venv',
    'venv',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.env',           # 包含凭据，不打包
    '.git',
    '.gitignore',     # 可选：如果不用git可以排除
    'data/*.db',      # 排除数据库文件
    'logs/*.log',     # 排除日志文件
    'exports/*',      # 排除导出文件
    '*.zip',          # 排除已有的压缩包
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    'Thumbs.db',
    '.DS_Store',
]

# 必须包含的空目录（创建 .gitkeep）
KEEP_DIRS = ['data', 'exports', 'logs']


def should_exclude(path: str) -> bool:
    """检查文件是否应该被排除"""
    path_parts = Path(path).parts
    name = os.path.basename(path)
    
    for pattern in EXCLUDE_PATTERNS:
        # 目录匹配
        if pattern in path_parts:
            return True
        # 通配符匹配
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        # 路径匹配
        if '/' in pattern or '\\' in pattern:
            if pattern.replace('/', os.sep).replace('\\', os.sep) in path:
                return True
        # 精确匹配
        if name == pattern:
            return True
    
    return False


def create_package():
    """创建项目压缩包"""
    # 项目根目录
    project_dir = Path(__file__).parent
    project_name = project_dir.name
    
    # 输出文件名
    date_str = datetime.now().strftime("%Y%m%d")
    zip_filename = f"{project_name}_v{VERSION}_{date_str}.zip"
    zip_path = project_dir / zip_filename
    
    print(f"打包项目: {project_name}")
    print(f"版本: {VERSION}")
    print(f"输出: {zip_filename}")
    print("-" * 50)
    
    file_count = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            # 过滤目录（就地修改 dirs 列表以跳过子目录）
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                
                if should_exclude(rel_path):
                    continue
                
                # 跳过当前脚本生成的zip文件
                if file.endswith('.zip'):
                    continue
                
                # 添加到压缩包（保持目录结构）
                arcname = os.path.join(project_name, rel_path)
                zipf.write(file_path, arcname)
                print(f"  添加: {rel_path}")
                file_count += 1
        
        # 为空目录添加 .gitkeep 文件
        for keep_dir in KEEP_DIRS:
            gitkeep_path = os.path.join(project_name, keep_dir, '.gitkeep')
            zipf.writestr(gitkeep_path, '')
            print(f"  添加: {keep_dir}/.gitkeep (占位)")
    
    print("-" * 50)
    print(f"✓ 打包完成!")
    print(f"  文件数: {file_count}")
    print(f"  大小: {zip_path.stat().st_size / 1024:.1f} KB")
    print(f"  位置: {zip_path}")
    
    print(f"""
发送给他人后的使用说明:

1. 解压文件:
   unzip {zip_filename}
   cd {project_name}

2. 创建虚拟环境并安装依赖:
   python -m venv .venv
   .venv\\Scripts\\activate  (Windows)
   pip install -r requirements.txt

3. 验证系统:
   python verify_system.py --full
   python test_integration.py

4. 配置凭据:
   copy .env.example .env
   (编辑 .env 填入 SSH 用户名密码)

5. 开始使用:
   python main.py --help
""")
    
    return zip_path


if __name__ == "__main__":
    create_package()
