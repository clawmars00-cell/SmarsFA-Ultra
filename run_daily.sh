#!/bin/bash
# 每日 Controller 运行脚本
# 运行时间: 每天 7:00 AM

cd /home/mars/.openclaw/workspace/SmarsFA

echo "Starting daily controller run..."
python3.12 controller/scheduler_v2.py

echo "Daily run complete!"
