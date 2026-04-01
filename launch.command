#!/bin/bash
# 双击此文件即可启动 RemindApp
cd "$(dirname "$0")"

# 检查依赖
if ! python3 -c "import rumps" 2>/dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

python3 main.py
