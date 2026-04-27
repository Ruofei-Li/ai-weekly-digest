#!/bin/bash
# AI Weekly Digest wrapper for launchd
# 特性：休眠错过时间 → 唤醒后自动补执行，一天只执行一次
set -e

LOCK_DIR="$HOME/.local/share/ai-weekly-digest"
LOCK_FILE="$LOCK_DIR/last_run.txt"
TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
HOUR=$(TZ=Asia/Shanghai date +%H)
WEEKDAY=$(TZ=Asia/Shanghai date +%u)

# 1: 只在周一执行
if [ "$WEEKDAY" != "1" ]; then
    exit 0
fi

# 2: 9点之前不执行（但9点之后还在睡，错过没关系，醒来会补跑）
if [ "$HOUR" -lt 9 ]; then
    exit 0
fi

# 3: 今天已经执行过就不重复执行
if [ -f "$LOCK_FILE" ] && [ "$(cat "$LOCK_FILE")" = "$TODAY" ]; then
    exit 0
fi

# 4: 确保锁目录存在
mkdir -p "$LOCK_DIR"

# 5: 运行周报
cd "$(dirname "$0")"
echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] 开始执行 AI 周报..."
python3 src/main.py
echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] 执行完成"

# 6: 标记今日已执行
echo "$TODAY" > "$LOCK_FILE"
